"""Config flow for Hue Circadian integration."""
import aiohue
from aiohue import HueBridgeV2
from homeassistant import config_entries
import voluptuous as vol

DOMAIN = "hue_circadian"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is None:
            return self._show_setup_form()

        bridge_ip = user_input["bridge_ip"]
        bridge_username = user_input["bridge_username"]
        sensor_entity_id = user_input["sensor_entity_id"]

        bridge = await self._discover_bridge(bridge_ip, bridge_username)
        if bridge is None:
            return self._show_setup_form({"base": "bridge_not_found"})

        bridge["sensor_entity_id"] = sensor_entity_id

        return self._create_entry(bridge)

    async def _discover_bridge(self, bridge_ip, bridge_username):
        """Discover a Hue bridge."""
        try:
            async with HueBridgeV2(bridge_ip, bridge_username) as bridge:
                await bridge.initialize()
                return bridge
        except aiohue.errors.Unauthorized:
            return None

    def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        # TODO: Implement the setup form for user input
        return self.async_show_form(
            step_id="user", data_schema=self._get_schema(), errors=errors or {}
        )

    def _get_schema(self):
        """Get the data schema for the setup form."""
        # TODO: Define the data schema using Home Assistant data types
        return vol.Schema(
            {
                vol.Required("bridge_ip"): str,
                vol.Required("bridge_username"): str,
                vol.Required("sensor_entity_id"): str,
            }
        )

    def _create_entry(self, bridge):
        """Create the config entry."""
        # TODO: Create the config entry using the bridge data
        return self.async_create_entry(
            title=f"{bridge.bridge_id}", data={},
        )
