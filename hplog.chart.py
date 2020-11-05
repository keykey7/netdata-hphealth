# -*- coding: utf-8 -*-
# Description: hp-health sensors netdata python.d module
# Author: Put your name here (your github login)
# SPDX-License-Identifier: GPL-3.0-or-later
# https://learn.netdata.cloud/docs/agent/collectors/python.d.plugin/

from bases.FrameworkServices.ExecutableService import ExecutableService
import re



# class BaseParser:
#     def __init__(self):
#         self.id = None
#         self.title = None
#         self.current = None
#         self.threshold = None
#         self.parse_line(line)
#
#     def parse_line(self, line):
#         raise NotImplementedError
#
#     def units(self):
#         raise NotImplementedError
#
#     def type(self):
#         raise NotImplementedError
#
#     def context(self):
#         return "".join([c if c.isalnum() else "" for c in self.title]).lower()
#
#     def params(self):
#
#         # [chart_name] + [name, title, units, family, context, charttype],
#         return [self.context() + "." + self.type().lower()] + \
#                [None, self.title + " " + self.type(), self.units(), self.type(), self.context(), 'line']
#
#
# class TemperatureParser(BaseParser):
#
#     def from_to(self, value: str, default):
#         if value is None:
#             return default
#         result_str = value.strip().split(["-", " ", ":"], 2)
#         assert len(result_str) == 2
#         return [ int(x) for x in result_str ]
#
#     def __init__(self, configuration):
#         self.id = configuration["id"]
#
#
#
#
#
# class TemperatureSensor(BaseSensor):
#     # ID     TYPE        LOCATION      STATUS    CURRENT  THRESHOLD
#     # 17  Basic Sensor Pwr. Supply Bay Normal    84F/ 29C ---F/---C "
#     #  4  Basic Sensor Mem. Brd. (4)  Normal    93F/ 34C 188F/ 87C
#     #  3  Basic Sensor CPU (3)         Normal   ---F/---C 158F/ 70C
#     # 15  Basic Sensor System Board    Absent   ---F/---C ---F/---C
#     temperature_regex = re.compile(
#         r'(?P<id>\d+) .{13} (?P<title>.+) (?:\w+) +'
#         r'[- 0-9]{3}F/(?P<current>[- 0-9]{3})C [- 0-9]{3}F/(?P<threshold>[- 0-9]{3})C' r'')
#
#     def parse_line(self, line):
#         match = TemperatureSensor.temperature_regex.fullmatch(line)
#         assert match is not None, "unexpected temperature line '{0}', not matching regex: {1}" \
#             .format(line, TemperatureSensor.temperature_regex.pattern)
#         self.id = "t." + match.group("id")
#         self.title = match.group("title").strip()
#         if self.title.endswith(')'):
#             self.title = self.title[:self.title.rindex('(')].rstrip()
#         current_str = match.group("current")
#         self.current = None if current_str == '---' else int(current_str)
#         threshold_str = match.group("threshold")
#         self.threshold = None if threshold_str == '---' else int(threshold_str)
#
#     def units(self):
#         return "deg celsius"
#
#     def type(self):
#         return "Temperature"
#
#
# class FanSensor(BaseSensor):
#     # ID     TYPE        LOCATION      STATUS  REDUNDANT FAN SPEED
#     #  1  Basic Fan    Virtual         Absent     N/A     Unknown
#     #  1  Var. Speed   Processor Zone  Nominal    Yes     Low    ( 18)
#     #  3  Var. Speed   Virtual         Normal     Yes     Normal   ( 29)
#     #  8  Var. Speed   Pwr. Supply Bay Nominal    Yes     Low    ( 20)
#     fan_regex = re.compile(r'(?P<id>\d+) .{13} (?P<title>.{15}) .+?(?:\( *(?P<current>\d+)\))?')
#
#     def parse_line(self, line):
#         match = FanSensor.fan_regex.fullmatch(line)
#         assert match is not None, "unexpected fan line '{0}', not matching regex: {1}" \
#             .format(line, FanSensor.fan_regex.pattern)
#         self.id = "f." + match.group("id")
#         self.title = match.group("title").strip()
#         if match.group("current") is not None:
#             self.current = int(match.group("current"))
#
#     def units(self):
#         return "percentage"
#
#     def type(self):
#         return "Fan"
#
#
# class PowerSensor(BaseSensor):
#     # ID     TYPE        LOCATION      STATUS  REDUNDANT
#     #  1  Standard     Pwr. Supply Bay Normal     Yes
#     #  1  Standard     Pwr. Supply Bay Failed     No
#     power_regex = re.compile(r'(?P<id>\d+) .{13} (?P<title>.{15}) (?P<isok>Normal|Nominal).+')
#
#     def parse_line(self, line):
#         match = PowerSensor.power_regex.fullmatch(line)
#         assert match is not None, "unexpected power line '{0}', not matching regex: {1}" \
#             .format(line, PowerSensor.power_regex.pattern)
#         self.id = "p." + match.group("id")
#         self.title = match.group("title").strip()
#         self.current = 0 if match.group("isok") is not None else 1
#         self.threshold = 1
#
#     def units(self):
#         return None
#
#     def type(self):
#         return "Power"
#
# # https://learn.netdata.cloud/docs/agent/health/reference
# #
# #  alarm: thermal_45C
# #     on: CONTEXT
# # lookup: average -1m foreach 4*C_*
# #  every: 30s
# #   warn: $this > 40
# #   crit: $this > 45
# - dimension name like: #2 45C
# - round threashold down to lower 5 deg?

ORDER = []

CHARTS = {}


class HphealthService(ExecutableService):

    def __init__(self, configuration=None, name=None):
        ExecutableService.__init__(self, configuration=configuration, name=name)
        self.command = "hpasmcli"
        if 'command' in self.configuration:
            self.command = self.configuration['command']
            del(self.configuration['command'])  # prevent sideffects in super.check()
        self.args = "show temp;show fans;show powersupply"
        if 'args' in self.configuration:
            self.args = self.configuration['args']
            assert "\"" not in self.args
        self.last_data = None
        self.defined = False

    def _get_raw_data(self, stderr=False, command=None):
        if command is None:
            command = self.command_and_args()
        self.last_data = super()._get_raw_data(stderr, command)
        return self.last_data

    def command_and_args(self):
        return "{0} -s \"{1}\"".format(self.command, self.args)

    def check_binary(self):
        return super().check()

    def check(self):
        if self.check_binary():
            return True
        if self.last_data is None:  # not even executed
            self.error("command {0} was not found. try installing the 'hp-health' package from HPE"
                       .format(self.command))
            return False
        if len(self.last_data) == 0 or "must be root" not in self.last_data[0]:
            self.debug("unknown error when executing `{0}`: {1}"
                       .format(self.command_and_args(), self.last_data))
            return False
        command_nosudo = self.command_and_args()
        self.debug("command `{0}` was not executed as root, trying sudo".format(command_nosudo))
        self.command = "sudo -n {0}".format(self.command)
        if self.check_binary():
            return True
        self.error("executing `{0}` failed, however the executable {1} exists. "
                   "Allow passwordless access for examply by executing `sudo visudo` "
                   "and adding the line `netdata ALL=(ALL:ALL) NOPASSWD:{1}`"
                   .format(self.command, command_nosudo))

    def add_chart(self, context, kind, tilte, units, dim_id, dim_name):
        # [context.family/ambient.temperature,
        # name/None, title/Human Readable, units/Celsius, type/temperature, context/ambient, 'line']
        chart_name = context + "." + kind
        if chart_name not in self.charts:
            self.charts.add_chart([chart_name, None, tilte, units, kind, context, 'line'])
        new_chart = self.charts[chart_name]
        new_chart.add_dimension([dim_id, dim_name])

    def parse_temperature(self, line):
        if line.startswith("---"):
            return None, None
        # #2        PROCESSOR_ZONE       40C/104F   70C/158F
        # #35       I/O_ZONE              -          -
        parts = line.split()
        assert len(parts) == 4, line
        if parts[2] == '-':
            return None, None
        sensor_id = parts[0][1:]  # 2
        threshold_str = parts[3].split('C', 1)[0]  # 70
        dim_id = sensor_id + "_" + threshold_str
        temperature = int(parts[2].split('C', 1)[0])  # 40
        if not self.defined:
            title = parts[1].replace('_', ' ').title()  # Processor Zone
            context = "".join([c if c.isalnum() else "" for c in parts[1]]).lower()
            dim_name = "#{0} (max {1}C)".format(sensor_id, threshold_str)
            self.add_chart(context, "temperature", title, "Celsius", dim_id, dim_name)
        return dim_id, temperature

    def parse_fan(self, line):
        return None, None  # TODO

    def parse_power(self, line):
        return None, None  # TODO

    def _get_data(self):
        lines = self._get_raw_data()
        assert len(lines) > 0 and "must be root" not in lines[0]
        mode = None
        data = dict()
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                mode = None  # empty line resets
            elif mode is not None:
                dim_id, value = mode(line)
                if dim_id is not None:
                    data[dim_id] = value
            elif line.startswith("Sensor"):
                mode = self.parse_temperature
            elif line.startswith("Fan"):
                mode = self.parse_fan
            elif line.startswith("Power"):
                mode = self.parse_fan
            else:
                raise AssertionError("unexpected output on line {0}: {1}".format(i, line))
        self.defined = True
        return data
