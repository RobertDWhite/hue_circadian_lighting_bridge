import json
import logging
from homeassistant import config_entries, core
import voluptuous as vol
import aiohue
import aiohttp
from aiohttp import ClientSession
import asyncio
import requests
import re

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'circadian_lighting_bridge'
BRIDGE_DATA_KEY = "circadian_lighting_bridge_bridge"


async def async_setup(hass, config):
    """Set up the Circadian Lighting Bridge component."""
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN in config:
        for entry in config[DOMAIN]:
            await async_setup_bridge(hass, entry)

    async def sensor_value_changed_event_listener(event):
        """Event listener for sensor value changes."""
        entity_id = 'sensor.circadian_values'
        new_state = event.data.get('new_state')

        if new_state is not None and new_state.entity_id == entity_id:
            _LOGGER.debug("sensor_value_changed_event_listener - New state: %s", new_state)
            print(f"sensor_value_changed_event_listener - New state of {entity_id}: {new_state}")
            await update_hue_scenes(hass, new_state)

    hass.bus.async_listen('state_changed', sensor_value_changed_event_listener)

    return True


def get_hue_gateway_and_key():
    with open('/config/.storage/core.config_entries', 'r') as entries_json:
        response = json.load(entries_json)

    bridges = []

    for entry in response["data"]["entries"]:
        if entry["domain"] == "hue":
            if "data" in entry and "host" in entry["data"] and "api_key" in entry["data"]:
                bridge_ip = entry["data"]["host"]
                bridge_username = entry["data"]["api_key"]
                bridges.append((bridge_ip, bridge_username))
                _LOGGER.info("Bridge IP: %s", bridge_ip)
                _LOGGER.info("Bridge Username: %s", bridge_username)

    if not bridges:
        raise ValueError("No Philips Hue bridges found")

    return bridges


async def update_scene_lights(session, hue_gateway, key, scene, brightness, xy, mired):
    url = f"http://{hue_gateway}/api/{key}/scenes/{scene}/"
    async with session.get(url) as response:
        r = await response.json()
        r = r['lights']
        _LOGGER.debug(f"Updating scene id: {scene}")
        for val in r:
            url = f"http://{hue_gateway}/api/{key}/lights/{val}"
            async with session.get(url) as t_response:
                t = await t_response.json()
                type = t['type']
                url = f"http://{hue_gateway}/api/{key}/scenes/{scene}/lightstates/{val}"
                body = json.dumps({'on': True, 'bri': brightness, 'xy': xy, 'ct': mired})
                async with session.put(url, data=body) as r_response:
                    _LOGGER.debug(f"light id: {val} body {body} status code: {r_response.status}")
                    if r_response.status != 200:
                        _LOGGER.error(f"light id: {val} body {body} status code: {r_response.status}")


async def update_hue_scenes(hass, new_state):
    try:
        bridges = get_hue_gateway_and_key()

        async with ClientSession() as session:
            tasks = []

            for bridge_ip, bridge_username in bridges:
                hue_gateway = bridge_ip
                key = bridge_username

                brightness = get_brightness(hass, new_state)
                xy = get_xy_color(hass, new_state)
                mired = get_colortemp(hass, new_state)

                url = f"http://{hue_gateway}/api/{key}/scenes"
                async with session.get(url) as response:
                    r = await response.json()
                    scenes = []
                    for val in r:
                        name = r[val]['name']
                        if re.match(r"Circadian", name):
                            scenes.append(val)

                    for val in scenes:
                        tasks.append(update_scene_lights(session, hue_gateway, key, val, brightness, xy, mired))

            await asyncio.gather(*tasks)

    except Exception as e:
        raise e


def get_colortemp(hass, new_state):
    entity_id = 'sensor.circadian_values'
    state = hass.states.get(entity_id)
    if state is None:
        raise ValueError(f'Entity {entity_id} not found')

    colortemp_kelvin = state.attributes.get('colortemp')
    if colortemp_kelvin is None:
        raise ValueError(f'colortemp attribute not found for entity {entity_id}')

    # Convert Kelvin to Mireds (Philips Hue uses Mireds)
    colortemp_mireds = int(round(1000000 / colortemp_kelvin))

    return colortemp_mireds


def get_xy_color(hass, new_state):
    entity_id = 'sensor.circadian_values'
    state = hass.states.get(entity_id)
    if state is None:
        raise ValueError(f'Entity {entity_id} not found')

    xy_color = state.attributes.get('xy_color')
    if xy_color is None or len(xy_color) != 2:
        raise ValueError(f'xy_color attribute not found or invalid for entity {entity_id}')

    return xy_color


def get_brightness(hass, new_state):
    colortemp = get_colortemp(hass, new_state)
    brightness = int(round((colortemp / 500) * 254))

    return brightness


async def async_setup_bridge(hass, config_entry):
    """Set up the Circadian Lighting Bridge component."""
    bridges = get_hue_gateway_and_key()

    for bridge_ip, bridge_username in bridges:
        bridge = aiohue.HueBridgeV2(bridge_ip, bridge_username)

        try:
            await bridge.initialize()
            _LOGGER.debug(
                "Unauthorized: Successfully connected to the Philips Hue bridge at %s",
                bridge_ip,
            )
        except aiohue.Unauthorized:
            _LOGGER.error(
                "Unauthorized: Failed to connect to the Philips Hue bridge at %s. "
                "Please make sure you have entered a valid API key.",
                bridge_ip,
            )
            return False
        except aiohue.BridgeBusy:
            _LOGGER.error(
                "BridgeBusy: Failed to connect to the Philips Hue bridge at %s. "
                "The bridge is busy and cannot process the request at the moment.",
                bridge_ip,
            )
            return False
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "ClientError: Error connecting to the Philips Hue bridge at %s: %s",
                bridge_ip,
                str(e),
            )
            return False

        hass.data[DOMAIN][BRIDGE_DATA_KEY] = bridge

        async def retry_connect():
            for _ in range(3): 
                config = bridge.config.get("")
                if config is not None:
                    _LOGGER.debug(
                        "Successfully connected to the Philips Hue bridge at %s",
                        bridge_ip,
                    )
                    return True
                else:
                    _LOGGER.warning(
                        "Retrying connection to the Philips Hue bridge at %s...",
                        bridge_ip,
                    )
                    await asyncio.sleep(5)  # Wait for 5 seconds before retrying
            return False

        if not await retry_connect():
            _LOGGER.error(
                "Failed to connect to the Philips Hue bridge at %s. "
                "API Key: %s"
                "Please check the host and try again.",
                bridge_ip, bridge_username
            )
            return False

    return True


class CircadianLightingBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Circadian Lighting Bridge."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            bridge_id = user_input['bridge_id']
            data = {"bridge_id": bridge_id}

            return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("bridge_id"): str,
                }
            ),
        )


async def async_setup_entry(hass, config_entry):
    """Set up Circadian Lighting Bridge from a config entry."""
    bridge_setup_success = await async_setup_bridge(hass, config_entry)

    if bridge_setup_success:
        entity_id = "sensor.circadian_values"
        sensor_state = await hass.async_add_executor_job(
            hass.states.get, entity_id
        )
        await update_hue_scenes(hass, sensor_state)

    return bridge_setup_success


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    bridge = hass.data[DOMAIN].pop(BRIDGE_DATA_KEY, None)
    if bridge is not None:
        await bridge.close()
    return True