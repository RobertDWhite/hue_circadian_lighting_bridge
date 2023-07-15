# hue_circadian_lighting
 
This is the first iteration of a custom component written specifically to interface with the Circadian Lighting custom component (https://github.com/claytonjn/hass-circadian_lighting). 

This custom component allows you to automatically sync the values from the Circadian Lighting custom component to each of your scenes named "Circadian" across all of your bridges connected to Home Assistant. Add scenes named "Circadian" to be automatically updated, and use these scens with your Hue switches/dimmers/buttons, allowing you to turn your lights on to the right temperature.

1) You must have hass-circadian_lighting installed and working.
2) You must have your Hue Bridges added to Home Assistant.
3) You must create scenes named "Circadian", which can be used with your Hue switches/dimmers. These will be updated with values from Circaidan Lighting automatically.
4) Add the following to your configuration.yaml

```
circadian_lighting_bridge:
```

5) Add "https://github.com/RobertDWhite/hue_circadian_lighting_bridge" to your HACS custom repositories to easily install.
