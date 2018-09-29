# Python-OBD-MQTT
Raspberry Pi Data logger for car sending data to a MQTT server

This is a work in progress. I haven't even tested the first version yet.

Connect an ELM327 OBD dongle to your Raspberry Pi either by USB or Bluetooth.

Update config.ini accordingly.

[FILE]

enabled= do you want to save the data locally into a file generated each time car is switched on

location= where to save said file, can be left blank to save in the same folder

gps= save gps data to file?

obd= save obd data to file?

Same pretty much applies to [MQTT]


Under [OBD] choose which information is asked from the car.

If GET_DTC=yes DTC data is queried once during engine is turned on.

If GET_CURRENT_DTC=yes DTC data is queried once when engine is turned off.

If CLEAR_DTC=yes DTC is cleared after engine is turned on and DTC data is queried if GET_DTC was enabled.
