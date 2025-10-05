"""Helper to check the configuration file."""
from __future__ import annotations
from collections import OrderedDict
import logging
import os
from pathlib import Path
from typing import NamedTuple, Self
from annotatedyaml import loader as yaml_loader
import voluptuous as vol
from homeassistant import loader
from homeassistant.config import (  # type: ignore[attr-defined]
    CONF_PACKAGES,
    YAML_CONFIG_FILE,
    config_per_platform,
    extract_domain_configs,
    format_homeassistant_error,
    format_schema_error,
    load_yaml_config_file,
    merge_packages_config,
)
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.core_config import CORE_CONFIG_SCHEMA
from homeassistant.exceptions import HomeAssistantError
from homeassistant.requirements import (
    RequirementsNotFound,
    async_clear_install_history,
    async_get_integration_with_requirements,
)
from . import config_validation as cv
from .typing import ConfigType

_LOGGER = logging.getLogger(__name__)


class CheckConfigError(NamedTuple):
    """Configuration check error."""

    message: str
    domain: str | None
    config: ConfigType | None


class HomeAssistantConfig(OrderedDict):
    """Configuration result with errors attribute."""

    def __init__(self) -> None:
        """Initialize HA config."""
        super().__init__()
        self.errors: list[CheckConfigError] = []
        self.warnings: list[CheckConfigError] = []

    def add_error(
        self,
        message: str,
        domain: str | None = None,
        config: ConfigType | None = None,
    ) -> Self:
        """Add an error."""
        self.errors.append(CheckConfigError(str(message), domain, config))
        return self

    @property
    def error_str(self) -> str:
        """Concatenate all errors to a string."""
        return "\n".join([err.message for err in self.errors])

    def add_warning(
        self,
        message: str,
        domain: str | None = None,
        config: ConfigType | None = None,
    ) -> Self:
        """Add a warning."""
        self.warnings.append(CheckConfigError(str(message), domain, config))
        return self

    @property
    def warning_str(self) -> str:
        """Concatenate all warnings to a string."""
        return "\n".join([err.message for err in self.warnings])


async def async_check_ha_config_file(  # noqa: C901
    hass: HomeAssistant,
) -> HomeAssistantConfig:
    """Load and check if Home Assistant configuration file is valid.

    This method is a coroutine.
    """
    result = HomeAssistantConfig()
    async_clear_install_history(hass)

    # --- Helper: pack/package error handler ---
    def _pack_error(
        hass_local: HomeAssistant,
        package: str,
        component: str | None,
        config_part: ConfigType,
        message: str,
    ) -> None:
        """Handle errors from packages."""
        message_full = f"Setup of package '{package}' failed: {message}"
        domain = f"homeassistant.packages.{package}{'.' + component if component is not None else ''}"
        pack_config = core_config.get(CONF_PACKAGES, {}).get(package, config_part)
        result.add_warning(message_full, domain, pack_config)

    # --- Helper: component error handler ---
    def _comp_error(
        ex: vol.Invalid | HomeAssistantError,
        domain: str,
        component_config: ConfigType,
        config_to_attach: ConfigType,
    ) -> None:
        """Handle errors from components and platforms."""
        if isinstance(ex, vol.Invalid):
            message = format_schema_error(hass, ex, domain, component_config)
        else:
            message = format_homeassistant_error(hass, ex, domain, component_config)

        if domain in frontend_dependencies:
            result.add_error(message, domain, config_to_attach)
        else:
            result.add_warning(message, domain, config_to_attach)

    # --- Helper: get integration with requirements and small error handling ---
    async def _get_integration(hass_local: HomeAssistant, domain: str) -> loader.Integration | None:
        """Get an integration, returning None on handled failures."""
        try:
            integration = await async_get_integration_with_requirements(hass_local, domain)
            return integration
        except loader.IntegrationNotFound as ex:
            # Don't show missing integration error in recovery or safe mode
            if not hass_local.config.recovery_mode and not hass_local.config.safe_mode:
                result.add_warning(f"Integration error: {domain} - {ex}")
            return None
        except RequirementsNotFound as ex:
            result.add_warning(f"Integration error: {domain} - {ex}")
            return None

    # --- Helper: load YAML config file safely ---
    async def _load_config_file(path: str) -> dict:
        """Load YAML configuration file, raising handled errors to caller by returning None result via result.add_error."""
        try:
            exists = await hass.async_add_executor_job(os.path.isfile, path)
            if not exists:
                result.add_error("File configuration.yaml not found.")
                return {}
            cfg = await hass.async_add_executor_job(
                load_yaml_config_file, path, yaml_loader.Secrets(Path(hass.config.config_dir))
            )
            return cfg
        except FileNotFoundError:
            result.add_error(f"File not found: {path}")
            return {}
        except HomeAssistantError as err:
            result.add_error(f"Error loading {path}: {err}")
            return {}

    # --- Helper: validate core config and merge packages ---
    async def _validate_core_config(cfg: dict) -> dict:
        """Validate core config (homeassistant) and merge packages."""
        nonlocal result
        core_cfg = cfg.pop(HOMEASSISTANT_DOMAIN, {})
        try:
            validated_core = CORE_CONFIG_SCHEMA(core_cfg)
            result[HOMEASSISTANT_DOMAIN] = validated_core
            # Merge packages (this calls _pack_error on package errors)
            await merge_packages_config(hass, cfg, validated_core.get(CONF_PACKAGES, {}), _pack_error)
            # Remove packages from core_config after merging
            validated_core.pop(CONF_PACKAGES, None)
            return validated_core
        except vol.Invalid as err:
            result.add_error(
                format_schema_error(hass, err, HOMEASSISTANT_DOMAIN, core_cfg),
                HOMEASSISTANT_DOMAIN,
                core_cfg,
            )
            return {}

    # --- Load configuration.yaml ---
    config_path = hass.config.path(YAML_CONFIG_FILE)
    config = await _load_config_file(config_path)
    if not config:
        # Either missing or error already recorded in result
        return result

    # --- Validate and extract core config ---
    core_config = await _validate_core_config(config)

    # --- Prepare frontend dependency resolution ---
    components = {cv.domain_key(key) for key in config}
    frontend_dependencies: set[str] = set()
    if "frontend" in components or "default_config" in components:
        frontend_integration = await _get_integration(hass, "frontend")
        if frontend_integration:
            await frontend_integration.resolve_dependencies()
            frontend_dependencies = frontend_integration.all_dependencies | {"frontend"}

    # --- Helper: process single domain (extract, validate component/platforms) ---
    async def _process_domain(domain: str) -> None:
        """Process and validate a single domain from config."""
        nonlocal config, result
        integration = await _get_integration(hass, domain)
        if not integration:
            return

        try:
            component = await integration.async_get_component()
        except ImportError as ex:
            result.add_warning(f"Component error: {domain} - {ex}")
            return

        # If integration provides 'config' platform, try to use its validator
        config_validator = None
        if integration.platforms_exists(("config",)):
            try:
                config_validator = await integration.async_get_platform("config")
            except ImportError as err:
                # Filter out import error of the config platform.
                # If the config platform contains bad imports, make sure that still fails.
                if err.name != f"{integration.pkg_path}.config":
                    result.add_error(f"Error importing config platform {domain}: {err}")
                    return

        if config_validator is not None and hasattr(config_validator, "async_validate_config"):
            try:
                validated = await config_validator.async_validate_config(hass, config)
                # The validator returns the validated config for this domain
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

        # Fall back to component CONFIG_SCHEMA if present
        config_schema = getattr(component, "CONFIG_SCHEMA", None)
        if config_schema is not None:
            try:
                validated_config = await cv.async_validate(hass, config_schema, config)
                if domain in validated_config:
                    result[domain] = validated_config[domain]
            except vol.Invalid as ex:
                _comp_error(ex, domain, config, config[domain])
                return

        # Determine platform schema (PLATFORM_SCHEMA_BASE or PLATFORM_SCHEMA)
        component_platform_schema = getattr(
            component, "PLATFORM_SCHEMA_BASE", getattr(component, "PLATFORM_SCHEMA", None)
        )
        if component_platform_schema is None:
            # Nothing more to validate for this domain
            return

        platforms = []
        # Iterate platform level entries for this domain
        for p_name, p_config in config_per_platform(config, domain):
            # Validate platform-level config with the component-level platform schema
            try:
                p_validated = await cv.async_validate(hass, component_platform_schema, p_config)
            except vol.Invalid as ex:
                _comp_error(ex, domain, p_config, p_config)
                continue

            # If p_name is None, the platform concept does not apply (some components)
            if p_name is None:
                platforms.append(p_validated)
                continue

            # Load the platform implementation (integration that provides this platform)
            try:
                p_integration = await async_get_integration_with_requirements(hass, p_name)
                platform = await p_integration.async_get_platform(domain)
            except loader.IntegrationNotFound as ex:
                # Don't show missing integration errors in recovery/safe mode
                if not hass.config.recovery_mode and not hass.config.safe_mode:
                    result.add_warning(f"Platform error '{domain}' from integration '{p_name}' - {ex}")
                continue
            except (RequirementsNotFound, ImportError) as ex:
                result.add_warning(f"Platform error '{domain}' from integration '{p_name}' - {ex}")
                continue

            # If the platform defines PLATFORM_SCHEMA, validate against that too
            platform_schema = getattr(platform, "PLATFORM_SCHEMA", None)
            if platform_schema is not None:
                try:
                    p_validated = platform_schema(p_validated)
                except vol.Invalid as ex:
                    _comp_error(ex, f"{domain}.{p_name}", p_config, p_config)
                    continue

            platforms.append(p_validated)

        # Remove domain-specific subconfigs (extract_domain_configs) from original config and set validated result
        for filter_comp in extract_domain_configs(config, domain):
            if filter_comp in config:
                del config[filter_comp]

        result[domain] = platforms

    # --- Process all domains (components) ---
    for domain in components:
        await _process_domain(domain)

    return result
