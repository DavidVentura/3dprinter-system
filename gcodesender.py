import argparse
import logging
import sys
import time
import serial
from queue import Queue
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
log = logging.getLogger(__name__)

class Printer:
    def __init__(self, port, baud):
        self.serial = serial.Serial(port, baud, timeout=5)

    def write_and_get_ack(self, msg):
        msg = msg.split(';')[0] # Ignore comments
        msg = msg.strip()
        if len(msg) == 0:
            return

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

def send_line_and_wait_ack(printer, line):
    for msg in printer.write_and_get_ack(line):
        log.info(msg)

def main():
    args = parse_args()
    assert Path(args.file).exists(), "%s does not exist" % args.file

    printer = Printer(args.port, args.baudrate)
    time.sleep(1) # wait for init to be done
    send_line_and_wait_ack(printer, 'M115')
    time.sleep(1) # wait for init to be done
    current_percentage = 0
    current_line = 0
    lines = open(args.file, 'r').readlines()
    log.setLevel(logging.INFO)
    log.info("Total lines: %d", len(lines))

    for line in lines:
        current_line += 1

        send_line_and_wait_ack(printer, line)
        if current_line % 500 == 0:
            send_line_and_wait_ack(printer, 'M105')

        perc = int(current_line/len(lines) * 100)
        if perc > current_percentage:
            current_percentage = perc
            log.info("Print status: %s %%", current_percentage)

    p.close()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=False, default='/dev/ttyUSB0')
    parser.add_argument('--baudrate', required=False, default=115200, type=int)
    parser.add_argument('file')
    args = parser.parse_args()
    return args

main()
