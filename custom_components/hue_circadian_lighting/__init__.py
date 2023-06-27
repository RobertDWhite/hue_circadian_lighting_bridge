"""The hue_circadian component."""

import asyncio
import aiohue
from aiohue import HueBridgeV2
from homeassistant.core import callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry

DOMAIN = "hue_circadian"

async def async_setup_platform(
    hass, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up the Hue Circadian component."""
    bridges = await discover_hue_bridges(config)
    if bridges:
        for bridge in bridges:
            hue_circadian = HueCircadian(hass, bridge, config.get("hue_keyword"))
            async_add_entities([hue_circadian])

async def discover_hue_bridges(config):
    """Discover Hue bridges."""
    bridges = []
    hue_bridges = config.get("hue_bridges", [])

    for hue_bridge in hue_bridges:
        bridge_ip = hue_bridge["bridge_ip"]
        bridge_username = hue_bridge["bridge_username"]
        sensor_entity_id = hue_bridge["sensor_entity_id"]

        bridge = await discover_bridge(bridge_ip, bridge_username)
        if bridge is not None:
            bridge["sensor_entity_id"] = sensor_entity_id
            bridges.append(bridge)

    return bridges

async def discover_bridge(bridge_ip, bridge_username):
    """Discover a Hue bridge."""
    try:
        async with HueBridgeV2(bridge_ip, bridge_username) as bridge:
            await bridge.initialize()
            return bridge
    except aiohue.errors.Unauthorized:
        return None

class HueCircadian(Entity):
    """Representation of the Hue Circadian component."""

    def __init__(self, hass, bridge, hue_keyword):
        """Initialize the Hue Circadian component."""
        self._hass = hass
        self._bridge = bridge
        self._sensor_entity_id = bridge.get("sensor_entity_id")
        self._hue_keyword = hue_keyword

        self._sensor_state = None
        self._available = False

    async def async_added_to_hass(self):
        """Run when the component is added to Home Assistant."""
        self._hass.async_create_task(self._initialize())

    async def _initialize(self):
        """Initialize the component."""
        if self._sensor_entity_id is not None:
            sensor_state = self._hass.states.get(self._sensor_entity_id)
            if sensor_state is not None:
                self._sensor_state = sensor_state.state

            # Subscribe to state changes of the Circadian Lighting sensor
            self._hass.helpers.dispatcher.async_dispatcher_connect(
                f"state_changed.{self._sensor_entity_id}", self._state_changed_callback
            )

        # Verify if the Hue Bridge is available
        self._available = await self._verify_bridge_available()

    async def _verify_bridge_available(self):
        """Verify if the Hue Bridge is available."""
        try:
            await self._bridge.initialize()
            return True
        except aiohue.errors.RequestError:
            return False

    @callback
    def _state_changed_callback(self, entity_id, old_state, new_state):
        """Handle state changes of the Circadian Lighting sensor."""
        self._sensor_state = new_state.state
        self._hass.async_create_task(self._update_hue_scenes())

    async def _update_hue_scenes(self):
        """Update all Hue Bridge scenes with the Circadian Lighting sensor values."""
        if not self._available or self._sensor_state is None:
            return

        # Get the values from the sensor state
        percent = self._sensor_state
        # Extract other values like colortemp, rgb_color, xy_color from the sensor state

        scenes = await self._bridge.scenes.get_all()
        for scene in scenes.values():
            if self._hue_keyword in scene.name:
                # Update the scene with the desired values
                scene.percent = percent
                # Update other values like colortemp, rgb_color, xy_color

                # Commit the changes to the scene
                await scene.update()

async def async_setup(hass, config):
    """Set up the Hue Circadian component."""
    return True

async def async_setup_entry(hass, entry: ConfigEntry):
    """Set up the Hue Circadian config entry."""
    config = entry.data
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "hue_circadian")
    )
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_unload(entry, "hue_circadian")
    )
    return True
