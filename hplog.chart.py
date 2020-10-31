# -*- coding: utf-8 -*-
# Description: example netdata python.d module
# Author: Put your name here (your github login)
# SPDX-License-Identifier: GPL-3.0-or-later

from bases.FrameworkServices.ExecutableService import ExecutableService

priority = 90000

ORDER = []

CHARTS = {}

class TemperatureSensor:
    def __init__(self, line):
        # ID     TYPE        LOCATION      STATUS    CURRENT  THRESHOLD
        # 17  Basic Sensor Pwr. Supply Bay Normal    84F/ 29C ---F/---C
        assert len(line.rstrip()) == 61, "unexpected line length: " + line
        self.id = line[0:2].strip()
        self.location = line[17:32].strip()
        self.status = line[33:41].strip()
        assert line[46] == '/'
        celsius_str = line[47:50].strip()
        self.celsius = None if celsius_str == '---' else int(celsius_str)
        assert line[50] == 'C'

    def name(self):
        return self.location + " Temperature"


class FanSensor:
    def __init__(self, line):
        pass


class PowerSensor:
    def __init__(self, line):
        pass


class HplogResults:
    def __init__(self):
        self.temperatures = []
        self.fans = []
        self.powers = []


class Service(ExecutableService):

    def __init__(self, configuration=None, name=None):
        ExecutableService.__init__(self, configuration=configuration, name=name)
        self.command = 'sudo hplog -t -f -p'

    def get_data_obj(self):
        lines = self._get_raw_data()
        assert len(lines) > 1

        results = HplogResults()
        sensor_id = 0
        for line in lines:
            if not line.strip():
                continue
            if line.startswith('ID'):
                sensor_id += 1
                continue
            if sensor_id == 1:
                results.temperatures.append(TemperatureSensor(line))
            elif sensor_id == 2:
                results.fans.append(FanSensor(line))
            elif sensor_id == 3:
                results.powers.append(PowerSensor(line))
            else:
                raise AssertionError("unexpected line: " + line)
        assert sensor_id == 3, "expected temperature, fans and power"
        return results

    def _check_executable(self):
        return ExecutableService.check(self)

    def _create_definition(self):
        hp = self.get_data_obj()
        for temp in hp.temperatures:
            chart_name = temp.name()
            if chart_name not in self.charts:
                params = [chart_name] + [None, chart_name, 'Celsius', temp.location, 'hp.temperature', 'line']
                self.charts.add_chart(params)
            new_chart = self.charts[chart_name]
            new_chart.add_dimension([temp.id])
        # TODO: impl fan
        # TODO: impl power
        return True

    def check(self):
        success = self._check_executable()
        if not success:
            return False
        return self._create_definition()

    def _get_data(self):
        data = dict()
        hp = self.get_data_obj()
        for temp in hp.temperatures:
            data[temp.id] = temp.celsius
        return data
