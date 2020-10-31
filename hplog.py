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
        assert len(line) == 61
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
        self.order = ORDER
        self.definitions = CHARTS
        self.command = 'hplog -t -f -p'

    def get_data_obj(self):
        lines = self._get_raw_data()
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
            if chart_name not in self.definitions:
                # [name, title, units, family, context, charttype],
                self.definitions[chart_name] = {
                    'options': [None, chart_name, 'Celsius', temp.location, 'temperature', 'line'],
                    'lines': []
                }
                self.order.append(chart_name)
                self.charts.add_chart([None, chart_name, 'Celsius', temp.location, 'temperature', 'line'])
            # dimension = [temp.id]
            # self.definitions[chart_name]['lines'].append(dimension)
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
            if temp.id not in self.charts[temp.name()]:
                self.charts[temp.name()].add_dimension([temp.id])
            data[temp.id] = temp.celsius
        # for i in range(1, 4):
        #     dimension_id = ''.join(['random', str(i)])
        #
        #     if dimension_id not in self.charts['random']:
        #         self.charts['random'].add_dimension([dimension_id])
        #
        #     data[dimension_id] = self.random.randint(0, 100)
        return data
