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
    def __init__(self, port, baud, info_q):
        self.serial = serial.Serial(port, baud, timeout=5)
        self.info_q = info_q

    def reset(self):
        log.info('Resetting')
        self.serial.setDTR(0)

        # There is presumably some latency required.
        time.sleep(1)
        self.serial.setDTR(1)
        time.sleep(3)
        ack = self.__get_acknowledgement('start')
        self.info('Reset got %s', ack)

    def write(self, msg):
        msg = msg.split(';')[0] # Ignore comments
        msg = msg.strip()
        #msg = msg.replace(' ', '').replace('\t', '').strip()
        if len(msg) == 0:
            return
        log.debug('Sending: %s', msg)
        msg = msg.encode()
        self.serial.write(msg + b'\n')
        ack = self.__get_acknowledgement('ok')
        log.debug('Got ACK: %s', ack)

    def __get_acknowledgement(self, ack):
        while True:
            response = self.serial.readline().strip()
            log.debug('got %s', response)
            if ack.lower() in response.decode('ascii').lower():
                return response

            # We assume it's informational
            self.info_q.put(response)

    def close(self):
        self.serial.close()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=False, default='/dev/ttyUSB0')
    parser.add_argument('--baudrate', required=False, default=115200, type=int)
    parser.add_argument('file')
    args = parser.parse_args()
    return args

def main():
    info_q = Queue()
    args = parse_args()
    assert Path(args.file).exists(), "%s does not exist" % args.file

    p = Printer(args.port, args.baudrate, info_q)
    current_percentage = 0
    current_line = 0
    lines = open(args.file, 'r').readlines()

    for line in lines:
        current_line += 1
        p.write(line)
        time.sleep(0.001)

        while not info_q.empty():
            info_line = info_q.get_nowait()
            if info_line is not None:
                log.info(info_line)
        if int(current_line/len(lines)) > current_percentage:
            current_percentage = int(current_line/len(lines))
            log.info("Print status: %s %%", current_percentage)
    
    p.close()

main()
