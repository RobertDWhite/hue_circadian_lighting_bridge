import logging
from homeassistant import config_entries
from homeassistant.helpers import discovery

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'circadian_lighting_bridge'


class CircadianLightingBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        return self.async_create_entry(title="Circadian Lighting Bridge", data={})

    async def async_step_import(self, user_input):
        """Handle a flow initialized by configuration import."""
        return await self.async_step_user(user_input)

    async def async_step_discovery(self, discovery_info):
        """Handle a flow initialized by discovery."""
        return await self.async_step_user()


async def async_setup(hass, config):
    """Set up the Circadian Lighting Bridge component."""
    discovery.async_listen(hass, 'circadian_lighting_bridge', CircadianLightingBridgeConfigFlow)
    return True
