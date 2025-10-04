"""Support for Alexa Flash Briefing skill service endpoint."""

from __future__ import annotations

import hmac
import logging
import uuid
from http import HTTPStatus
from aiohttp.web_response import StreamResponse

from homeassistant.components import http
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import template
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import (
    API_PASSWORD,
    ATTR_MAIN_TEXT,
    ATTR_REDIRECTION_URL,
    ATTR_STREAM_URL,
    ATTR_TITLE_TEXT,
    ATTR_UID,
    ATTR_UPDATE_DATE,
    CONF_AUDIO,
    CONF_DISPLAY_URL,
    CONF_TEXT,
    CONF_TITLE,
    CONF_UID,
    DATE_FORMAT,
)

_LOGGER = logging.getLogger(__name__)

FLASH_BRIEFINGS_API_ENDPOINT = "/api/alexa/flash_briefings/{briefing_id}"


@callback
def async_setup(hass: HomeAssistant, flash_briefing_config: ConfigType) -> None:
    """Activate the Alexa Flash Briefing component."""
    hass.http.register_view(AlexaFlashBriefingView(hass, flash_briefing_config))


class AlexaFlashBriefingView(http.HomeAssistantView):
    """Handle Alexa Flash Briefing skill requests."""

    url = FLASH_BRIEFINGS_API_ENDPOINT
    requires_auth = False
    name = "api:alexa:flash_briefings"

    def __init__(self, hass: HomeAssistant, flash_briefings: ConfigType) -> None:
        """Initialize the Alexa Flash Briefing view."""
        super().__init__()
        self.flash_briefings = flash_briefings

    def _validate_request(
        self, request: http.HomeAssistantRequest, briefing_id: str
    ) -> tuple[bool, tuple[bytes, HTTPStatus] | None]:
        """Validate request authentication and configuration."""
        password = request.query.get(API_PASSWORD)
        if password is None:
            _LOGGER.error(
                "No password provided for Alexa flash briefing: %s", briefing_id
            )
            return False, (b"", HTTPStatus.UNAUTHORIZED)

        expected_password = self.flash_briefings.get(CONF_PASSWORD)
        if not expected_password or not hmac.compare_digest(
            password.encode(), expected_password.encode()
        ):
            _LOGGER.error("Wrong password for Alexa flash briefing: %s", briefing_id)
            return False, (b"", HTTPStatus.UNAUTHORIZED)

        if not isinstance(self.flash_briefings.get(briefing_id), list):
            _LOGGER.error(
                "No configured Alexa flash briefing was found for: %s", briefing_id
            )
            return False, (b"", HTTPStatus.NOT_FOUND)

        return True, None

    def _resolve_value(self, value):
        """Render a template value or return it directly."""
        if isinstance(value, template.Template):
            return value.async_render(parse_result=False)
        return value

    def _build_briefing_item(self, item: dict) -> dict:
        """Build a single Alexa Flash Briefing response item."""
        output = {
            ATTR_TITLE_TEXT: self._resolve_value(item.get(CONF_TITLE)),
            ATTR_MAIN_TEXT: self._resolve_value(item.get(CONF_TEXT)),
            ATTR_STREAM_URL: self._resolve_value(item.get(CONF_AUDIO)),
            ATTR_REDIRECTION_URL: self._resolve_value(item.get(CONF_DISPLAY_URL)),
            ATTR_UID: item.get(CONF_UID) or str(uuid.uuid4()),
            ATTR_UPDATE_DATE: dt_util.utcnow().strftime(DATE_FORMAT),
        }
        return {k: v for k, v in output.items() if v is not None}

    @callback
    def get(
        self, request: http.HomeAssistantRequest, briefing_id: str
    ) -> StreamResponse | tuple[bytes, HTTPStatus]:
        """Handle Alexa Flash Briefing GET requests."""
        _LOGGER.debug("Received Alexa flash briefing request for: %s", briefing_id)

        valid, error_response = self._validate_request(request, briefing_id)
        if not valid:
            return error_response

        items = self.flash_briefings[briefing_id]
        briefing = [self._build_briefing_item(item) for item in items]

        return self.json(briefing)
