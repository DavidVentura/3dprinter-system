Attempt to simplify / streamline my 3dprinter usage.

Features:
1. GCode sender with progress reports

Reports via MQTT

```bash
printer/PRINTER_STATUS printing
printer/TEMP 176.29/190.00,50.07/50.00
printer/JOB_STATUS 20 # %
printer/PRINTER_STATUS idle
printer/PRINTER_STATUS aborted
```

Triggers via MQTT:

```bash
$ mosquitto_pub -h iot.labs -t "printer/print" -m "CE3_xyzCalibration_cube.gcode"
```

Triggering a job while printing is ignored.


Basic commands via MQTT:

- `stop` will stop the print instead of emitting the next gcode step.
- `rmove X10` / `rmove Y10` etc &ndash; relative moves.
- `home X` / `home X Y` etc &ndash; home axis.

--------

Considering:
- Custom GCode headers.
- Basic web UI to move the print head/bed.
- Cura plugin to output the gcode via SFTP/HTTP.
