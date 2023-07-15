# hue_circadian_lighting
 
This is the first attempt and iteration of a custom component written specifically to interface with the Circadian Lighting custom component (https://github.com/claytonjn/hass-circadian_lighting). 

1) You must have hass-circadian_lighting installed and working.
2) You must have your Hue Bridges added to Home Assistant.
3) You must create scenes named "Circadian", which can be used with your Hue switches/dimmers. These will be updated with values from Circaidan Lighting automatically.
4) Add the following to your configuration.yaml

```
circadian_lighting_bridge:
```
