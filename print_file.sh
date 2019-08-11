#!/bin/bash
set -eu
#function finish {
#    echo "Exiting in 5 seconds.."
#    sleep 5
#    mosquitto_pub -h iot.labs -t "PRINTER_POWER/set" -m 0
#}

#trap finish EXIT
[ -f "$1" ] || (echo "File $1 does not exist" && exit 1)
mosquitto_pub -h iot.labs -t "PRINTER_POWER/set" -m 1
sleep 1

mosquitto_pub -h iot.labs -t "printer/print" -m "$1"
