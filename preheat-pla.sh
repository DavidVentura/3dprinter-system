#!/bin/bash

# bed async
mosquitto_pub -h iot.labs -t 'printer/commands' -m 'raw M140 S50'

# bed sync
#mosquitto_pub -h iot.labs -t topic -m 'M190 S50'
# nozzle sync
#mosquitto_pub -h iot.labs -t topic -m 'M109 S180'
