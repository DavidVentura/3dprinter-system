#!/bin/bash
mosquitto_pub -h iot.labs -t 'printer/commands' -m 'stop'
