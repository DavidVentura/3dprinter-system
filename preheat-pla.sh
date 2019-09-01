#!/bin/bash
mosquitto_pub -h iot.labs -t "PRINTER_POWER/set" -m 1
sleep 1

# bed async
mosquitto_pub -h iot.labs -t 'printer/commands' -m 'raw M140 S50'
# extruder async
mosquitto_pub -h iot.labs -t 'printer/commands' -m 'raw M104 S180'

# bed sync
#mosquitto_pub -h iot.labs -t topic -m 'M190 S50'
# nozzle sync
#mosquitto_pub -h iot.labs -t topic -m 'M109 S180'
