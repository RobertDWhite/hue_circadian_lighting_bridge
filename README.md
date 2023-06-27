# hue_circadian_lighting
 
This is the first attempt and iteration of a custom component written specifically to interface with the Circadian Lighting custom component (https://github.com/claytonjn/hass-circadian_lighting). You must have hass-circadian_lighting installed and working, and you must have your Hue Bridges added to Home Assistant.

Add the following to your configuration.yaml

```
hue_circadian:
  hue_keyword: "Circadian"
  hue_bridges:
    - sensor_entity_id: sensor.circadian_lights
```