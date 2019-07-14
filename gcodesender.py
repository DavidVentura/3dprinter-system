import argparse
import logging
import re
import serial
import sys
import time
import paho.mqtt.client as mqtt
from threading import Thread
from functools import partial
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
log = logging.getLogger(__name__)
temp_message_re = re.compile(r'^T:(?P<nozzle_temp>[0-9.]+)\s*/(?P<nozzle_target>[0-9.]+) B:(?P<bed_temp>[0-9.]+)\s*/(?P<bed_target>[0-9.]+)')

class Printer:
    FIRMWARE_INFO = 'M115'
    REPORT_TEMP = 'M105'
    RELATIVE_POSITIONING = 'G91'

    def __init__(self, port, baud, info_callback):
        self.emit_message = info_callback
        self.printing = False
        self.serial = serial.Serial(port, baud, timeout=5)

        time.sleep(1) # wait for init to be done
        for f in self.write_and_get_ack(Printer.FIRMWARE_INFO): # Firmware info
            pass
        time.sleep(1) # wait for init to be done

    def write_and_ignore_result(self, msg):
        for _ in self.write_and_get_ack(msg):
            pass

    def write_and_get_ack(self, msg):
        msg = msg.split(';')[0] # Ignore comments
        msg = msg.strip()
        if len(msg) == 0:
            return []

        log.debug('Sending: %s', msg)
        msg = msg.encode()
        self.serial.write(msg + b'\n')
        return self.__get_acknowledgement('ok')

    def __get_acknowledgement(self, ack):
        while True:
            response = self.serial.readline().strip()
            log.debug('got %s', response)
            if ack.lower() in response.decode('ascii').lower():
                break
            yield response

    def close(self):
        self.serial.close()

    def print_file(self, filename):
        if not Path(filename).exists():
            log.error("%s does not exist", filename)
            return
        if self.printing:
            log.error("Already printing!")
            return

        self.emit_message('PRINTER_STATUS', 'printing')
        self.printing = True
        current_percentage = 0
        current_line = 0
        lines = open(filename, 'r').readlines()
        log.info("Total lines: %d", len(lines))

        for line in lines:
            current_line += 1
            time.sleep(0.001)

            for msg in self.write_and_get_ack(line):
                self.emit_message(topic='INFO', message=msg.decode('ascii'))

            if current_line % 500 == 0:
                for msg in self.write_and_get_ack(Printer.REPORT_TEMP):
                    self.emit_message(topic='TEMP', message=msg.decode('ascii'))

            perc = int(current_line/len(lines) * 100)
            if perc > current_percentage:
                current_percentage = perc
                self.emit_message('JOB_STATUS', str(perc))

            if not self.printing:
                log.warning('Requested to stop print midway')
                self.emit_message('PRINTER_STATUS', 'aborted')
                return

        self.emit_message('PRINTER_STATUS', 'finished')
        self.printing = False

    def command(self, msg):
        if msg == 'stop':
            log.info('Stop printing')
            self.printing = False

        elif msg.startswith('rmove'):
            log.info('rmove')
            _, axis_distance = msg.strip().split(' ')
            self.write_and_ignore_result(Printer.RELATIVE_POSITIONING)
            self.write_and_ignore_result('G0 %s' % axis_distance)
        elif msg.startswith('home'):
            log.info('home')
            # home X Y Z => X Y Z
            axis_to_home = ' '.join(msg.strip().split(' ')[1:])
            self.write_and_ignore_result('G28 %s' % axis_to_home)


def handle_info_msg(topic, message, mqtt_client):
    log.info('handle info msg %s', message)
    try:
        if 'echo:busy: processing' in message:
            return
        parsed_msg = message

        if message.startswith('T:'):
            topic = 'TEMP'
            m = temp_message_re.search(message)
            if m:
                parsed_msg = '%s/%s,%s/%s' % (m.group('nozzle_temp'), m.group('nozzle_target'), m.group('bed_temp'), m.group('bed_target'))

        topic = 'printer/%s' % topic
        mqtt_client.publish(topic, parsed_msg)
    except Exception as e:
        log.exception(e)

def on_message(client, data, message, printer):
    log.info('Received msg: %s on topic %s', message.payload, message.topic)

    msg = message.payload.decode('ascii')
    if message.topic == 'printer/print':
        t = Thread(target=printer.print_file, args=(msg,))
        t.daemon = True
        t.start()
    elif message.topic == 'printer/commands':
        log.info('Command!')
        printer.command(msg)


def main():
    args = parse_args()
    client = mqtt.Client()

    _handle_info_msg = partial(handle_info_msg, mqtt_client=client)
    printer = Printer(args.port, args.baudrate, _handle_info_msg)

    log.setLevel(logging.INFO)

    client.on_message = partial(on_message, printer=printer)
    client.connect('iot.labs')
    client.subscribe("printer/print")
    client.subscribe("printer/commands")

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log.error(e)
    finally:
        printer.close()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=False, default='/dev/ttyUSB0')
    parser.add_argument('--baudrate', required=False, default=115200, type=int)
    args = parser.parse_args()
    return args

main()
