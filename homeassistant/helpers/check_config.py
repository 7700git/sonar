async def async_check_ha_config_file(  # noqa: C901
    hass: HomeAssistant,
) -> HomeAssistantConfig:
    """Load and check if Home Assistant configuration file is valid.
    This method is a coroutine.
    """
    result = HomeAssistantConfig()
    async_clear_install_history(hass)

    # Initialize core_config early so closures capture a defined name.
    core_config: dict = {}

    def _pack_error(
        hass: HomeAssistant,
        package: str,
        component: str | None,
        config: ConfigType,
        message: str,
    ) -> None:
        """Handle errors from packages."""
        message_full = f"Setup of package '{package}' failed: {message}"
        domain = f"homeassistant.packages.{package}{'.' + component if component is not None else ''}"
        # Use a safe access to core_config packages
        pack_config = core_config.get(CONF_PACKAGES, {}).get(package, config)
        result.add_warning(message_full, domain, pack_config)

    def _comp_error(
        ex: vol.Invalid | HomeAssistantError,
        domain: str,
        component_config: ConfigType,
        config_to_attach: ConfigType,
    ) -> None:
        """Handle errors from components."""
        if isinstance(ex, vol.Invalid):
            message = format_schema_error(hass, ex, domain, component_config)
        else:
            message = format_homeassistant_error(hass, ex, domain, component_config)

        if domain in frontend_dependencies:
            result.add_error(message, domain, config_to_attach)
        else:
            result.add_warning(message, domain, config_to_attach)

    async def _get_integration(
        hass: HomeAssistant, domain: str
    ) -> loader.Integration | None:
        """Get an integration, returning None on known non-fatal errors."""
        try:
            return await async_get_integration_with_requirements(hass, domain)
        except loader.IntegrationNotFound as ex:
            # Don't spam errors for missing custom integrations when in recovery/safe mode.
            if not hass.config.recovery_mode and not hass.config.safe_mode:
                result.add_warning(f"Integration error: {domain} - {ex}")
            return None
        except RequirementsNotFound as ex:
            result.add_warning(f"Integration error: {domain} - {ex}")
            return None

    async def _load_yaml() -> dict:
        """Load YAML config file from disk or record file errors in result."""
        config_path = hass.config.path(YAML_CONFIG_FILE)
        try:
            exists = await hass.async_add_executor_job(os.path.isfile, config_path)
            if not exists:
                result.add_error("File configuration.yaml not found.")
                return {}
            return await hass.async_add_executor_job(
                load_yaml_config_file, config_path, yaml_loader.Secrets(Path(hass.config.config_dir))
            )
        except FileNotFoundError:
            result.add_error(f"File not found: {config_path}")
            return {}
        except HomeAssistantError as err:
            result.add_error(f"Error loading {config_path}: {err}")
            return {}

    async def _validate_core_and_merge_packages(config: dict) -> None:
        """Validate [homeassistant] core config and merge packages into config."""
        nonlocal core_config
        try:
            core_config = CORE_CONFIG_SCHEMA(core_config)  # type: ignore[assignment]
            result[HOMEASSISTANT_DOMAIN] = core_config
            await merge_packages_config(hass, config, core_config.get(CONF_PACKAGES, {}), _pack_error)
        except vol.Invalid as err:
            result.add_error(
                format_schema_error(hass, err, HOMEASSISTANT_DOMAIN, core_config),
                HOMEASSISTANT_DOMAIN,
                core_config,
            )
            core_config = {}
        # Remove packages key from core_config that we don't want to propagate
        core_config.pop(CONF_PACKAGES, None)

    async def _resolve_frontend_deps(components: set[str]) -> set[str]:
        """Return set of frontend-related dependencies (if frontend/default_config present)."""
        deps: set[str] = set()
        if "frontend" in components or "default_config" in components:
            frontend = await _get_integration(hass, "frontend")
            if frontend:
                await frontend.resolve_dependencies()
                deps = frontend.all_dependencies | {"frontend"}
        return deps

    async def _process_platforms_for_component(component, domain: str, config: dict) -> list:
        """Process platform-level configs for a given component and return list of validated platforms."""
        platforms: list = []
        component_platform_schema = getattr(
            component,
            "PLATFORM_SCHEMA_BASE",
            getattr(component, "PLATFORM_SCHEMA", None),
        )
        if component_platform_schema is None:
            return platforms

        for p_name, p_config in config_per_platform(config, domain):
            # Validate platform config against component platform base schema
            try:
                p_validated = await cv.async_validate(hass, component_platform_schema, p_config)
            except vol.Invalid as ex:
                _comp_error(ex, domain, p_config, p_config)
                continue

            # If platform name is None we keep the validated config as-is (some components do that)
            if p_name is None:
                platforms.append(p_validated)
                continue

            # Load platform integration and validate platform-specific schema if present
            try:
                p_integration = await async_get_integration_with_requirements(hass, p_name)
                platform = await p_integration.async_get_platform(domain)
            except loader.IntegrationNotFound as ex:
                if not hass.config.recovery_mode and not hass.config.safe_mode:
                    result.add_warning(f"Platform error '{domain}' from integration '{p_name}' - {ex}")
                continue
            except (RequirementsNotFound, ImportError) as ex:
                result.add_warning(f"Platform error '{domain}' from integration '{p_name}' - {ex}")
                continue

            platform_schema = getattr(platform, "PLATFORM_SCHEMA", None)
            if platform_schema is not None:
                try:
                    p_validated = platform_schema(p_validated)
                except vol.Invalid as ex:
                    _comp_error(ex, f"{domain}.{p_name}", p_config, p_config)
                    continue

            platforms.append(p_validated)

        return platforms

    async def _process_domain(domain: str, config: dict) -> None:
        """Validate a single domain and attach validated config into result."""
        integration = await _get_integration(hass, domain)
        if not integration:
            return

        try:
            component = await integration.async_get_component()
        except ImportError as ex:
            result.add_warning(f"Component error: {domain} - {ex}")
            return

        # If integration provides a config platform, run it
        config_validator = None
        if integration.platforms_exists(("config",)):
            try:
                config_validator = await integration.async_get_platform("config")
            except ImportError as err:
                # Filter out import error of the config platform itself; only report unexpected imports
                if err.name != f"{integration.pkg_path}.config":
                    result.add_error(f"Error importing config platform {domain}: {err}")
                    return

        if config_validator is not None and hasattr(config_validator, "async_validate_config"):
            try:
                validated = await config_validator.async_validate_config(hass, config)
                if domain in validated:
                    result[domain] = validated[domain]
                return
            except (vol.Invalid, HomeAssistantError) as ex:
                _comp_error(ex, domain, config, config[domain])
                return
            except Exception as err:
                logging.getLogger(__name__).exception("Unexpected error validating config")
                result.add_error(
                    f"Unexpected error calling config validator: {err}",
                    domain,
                    config.get(domain),
                )
                return

        # Fall back to component-level CONFIG_SCHEMA if present
        config_schema = getattr(component, "CONFIG_SCHEMA", None)
        if config_schema is not None:
            try:
                validated_config = await cv.async_validate(hass, config_schema, config)
                if domain in validated_config:
                    result[domain] = validated_config[domain]
            except vol.Invalid as ex:
                _comp_error(ex, domain, config, config[domain])
                return

        # Process per-platform schema and attach to result
        platforms = await _process_platforms_for_component(component, domain, config)

        # Remove original domain-specific entries from config (extract_domain_configs)
        for filter_comp in extract_domain_configs(config, domain):
            if filter_comp in config:
                del config[filter_comp]

        result[domain] = platforms

    # --- Begin linear flow of function using helpers above ---
    # Load YAML
    config = await _load_yaml()
    if not config:
        # Errors were already added to result by _load_yaml (or file absent).
        return result

    # Extract and validate core [homeassistant] config and merge packages
    core_config = config.pop(HOMEASSISTANT_DOMAIN, {})
    await _validate_core_and_merge_packages(config)

    # Components set (domain keys without duplicates)
    components = {cv.domain_key(key) for key in config}

    # Determine frontend dependencies set (used by _comp_error to decide error vs warning)
    frontend_dependencies = await _resolve_frontend_deps(components)

    # Process all domains (sequentially to keep error aggregation simple)
    for domain in components:
        await _process_domain(domain, config)

    return result
