# -*- coding: utf-8 -*-
# Description: hp-health sensors netdata python.d module
# Author: Put your name here (your github login)
# SPDX-License-Identifier: GPL-3.0-or-later
# https://learn.netdata.cloud/docs/agent/collectors/python.d.plugin/

from bases.FrameworkServices.ExecutableService import ExecutableService
import re

COMMAND = "sudo hplog -t -f -p"

ORDER = []

CHARTS = {}


class BaseSensor:
    def __init__(self, line):
        self.id = None
        self.title = None
        self.current = None
        self.threshold = None
        self.parse_line(line)

    def parse_line(self, line):
        raise NotImplementedError

    def units(self):
        raise NotImplementedError

    def type(self):
        raise NotImplementedError

    def context(self):
        return "".join([c if c.isalnum() else "" for c in self.title]).lower()

    def params(self):
        # [chart_name] + [name, title, units, family, context, charttype],
        return [self.context() + "." + self.type().lower()] + \
               [None, self.title + " " + self.type(), self.units(), self.type(), self.context(), 'line']


class TemperatureSensor(BaseSensor):
    # ID     TYPE        LOCATION      STATUS    CURRENT  THRESHOLD
    # 17  Basic Sensor Pwr. Supply Bay Normal    84F/ 29C ---F/---C "
    #  4  Basic Sensor Mem. Brd. (4)  Normal    93F/ 34C 188F/ 87C
    #  3  Basic Sensor CPU (3)         Normal   ---F/---C 158F/ 70C
    temperature_regex = re.compile(
        r'(?P<id>\d+) .{13} (?P<title>.+) (?:\w+) +'
        r'[- 0-9]{3}F/(?P<current>[- 0-9]{3})C [- 0-9]{3}F/(?P<threshold>[- 0-9]{3})C' r'')

    def parse_line(self, line):
        match = TemperatureSensor.temperature_regex.fullmatch(line)
        assert match is not None, "unexpected temperature line '{0}', not matching regex: {1}" \
            .format(line, TemperatureSensor.temperature_regex.pattern)
        self.id = "t." + match.group("id")
        self.title = match.group("title").strip()
        if self.title.endswith(')'):
            self.title = self.title[:self.title.rindex('(')].rstrip()
        current_str = match.group("current")
        self.current = None if current_str == '---' else int(current_str)
        threshold_str = match.group("threshold")
        self.threshold = None if threshold_str == '---' else int(threshold_str)

    def units(self):
        return "deg celsius"

    def type(self):
        return "Temperature"


class FanSensor(BaseSensor):
    # ID     TYPE        LOCATION      STATUS  REDUNDANT FAN SPEED
    #  1  Basic Fan    Virtual         Absent     N/A     Unknown
    #  1  Var. Speed   Processor Zone  Nominal    Yes     Low    ( 18)
    #  3  Var. Speed   Virtual         Normal     Yes     Normal   ( 29)
    #  8  Var. Speed   Pwr. Supply Bay Nominal    Yes     Low    ( 20)
    fan_regex = re.compile(r'(?P<id>\d+) .{13} (?P<title>.{15}) .+?(?:\( *(?P<current>\d+)\))?')

    def parse_line(self, line):
        match = FanSensor.fan_regex.fullmatch(line)
        assert match is not None, "unexpected fan line '{0}', not matching regex: {1}" \
            .format(line, FanSensor.fan_regex.pattern)
        self.id = "f." + match.group("id")
        self.title = match.group("title").strip()
        if match.group("current") is not None:
            self.current = int(match.group("current"))

    def units(self):
        return "percentage"

    def type(self):
        return "Fan"


class PowerSensor(BaseSensor):
    # ID     TYPE        LOCATION      STATUS  REDUNDANT
    #  1  Standard     Pwr. Supply Bay Normal     Yes
    #  1  Standard     Pwr. Supply Bay Failed     No
    power_regex = re.compile(r'(?P<id>\d+) .{13} (?P<title>.{15}) (?P<isok>Normal|Nominal).+')

    def parse_line(self, line):
        match = PowerSensor.power_regex.fullmatch(line)
        assert match is not None, "unexpected power line '{0}', not matching regex: {1}" \
            .format(line, PowerSensor.power_regex.pattern)
        self.id = "p." + match.group("id")
        self.title = match.group("title").strip()
        self.current = 0 if match.group("isok") is not None else 1
        self.threshold = 1

    def units(self):
        return None

    def type(self):
        return "Power"


class Service(ExecutableService):

    def __init__(self, configuration=None, name=None):
        ExecutableService.__init__(self, configuration=configuration, name=name)
        self.command = COMMAND

    def get_data_obj(self):
        lines = self._get_raw_data()
        if len(lines) == 1 and "must be root" in lines[0]:
            raise AssertionError("command `{0}` must be run as root".format(self.command))
        assert len(lines) > 1
        results = []
        sensor_id = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('ID'):
                sensor_id += 1
                continue
            if sensor_id == 1:
                results.append(TemperatureSensor(line))
            elif sensor_id == 2:
                results.append(FanSensor(line))
            elif sensor_id == 3:
                results.append(PowerSensor(line))
            else:
                raise AssertionError("unexpected line '{0}' #{1}".format(line, sensor_id))
        assert sensor_id == 3, "expected temperature, fans and power"
        return results

    def _check_executable(self):
        return ExecutableService.check(self)

    def _create_definition(self):
        sensors = self.get_data_obj()
        for sensor in sensors:
            chart_name = sensor.params()[0]
            if chart_name not in self.charts:
                self.charts.add_chart(sensor.params())
            new_chart = self.charts[chart_name]
            new_chart.add_dimension([sensor.id])
        return True

    def check(self):
        success = self._check_executable()
        if not success:
            return False
        return self._create_definition()

    def _get_data(self):
        data = dict()
        sensors = self.get_data_obj()
        for sensor in sensors:
            data[sensor.id] = sensor.current
        return data
