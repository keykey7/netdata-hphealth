# -*- coding: utf-8 -*-
# Description: hp-health sensors netdata python.d module
# Author: Put your name here (your github login)
# SPDX-License-Identifier: GPL-3.0-or-later
# https://learn.netdata.cloud/docs/agent/collectors/python.d.plugin/

from bases.FrameworkServices.ExecutableService import ExecutableService


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
        self.power_id = None

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
        # Sensor   Location              Temp       Threshold
        # #2        PROCESSOR_ZONE       40C/104F   70C/158F
        # #35       I/O_ZONE              -          -
        parts = line.split()
        assert len(parts) == 4, line
        if parts[2] == '-' or parts[3] == '-':
            return None, None
        sensor_id = parts[0][1:]  # 2
        threshold_str = parts[3].split('C', 1)[0]  # 70
        dim_id = "tmp{0}_{1}".format(sensor_id, threshold_str)
        temperature = int(parts[2].split('C', 1)[0])  # 40
        if not self.defined:
            title, context = self.caps_to_title(parts[1])
            dim_name = "#{0} (max {1}C)".format(sensor_id, threshold_str)
            self.add_chart(context, "temperature", title, "Celsius", dim_id, dim_name)
        return dim_id, temperature

    @staticmethod
    def caps_to_title(part):
        title = part.replace('_', ' ').title()  # Processor Zone
        context = "".join([c if c.isalnum() else "" for c in part]).lower()  # iozone
        return title, context

    def parse_fan(self, line):
        # Fan  Location        Present Speed  of max  Redundant  Partner  Hot-pluggable
        # #2   VIRTUAL         No      -       N/A     N/A        N/A      Yes
        # #3   VIRTUAL         Yes     NORMAL  29%     Yes        0        Yes
        # #4   PROCESSOR_ZONE  Yes     NORMAL  5%      Yes        1        Yes
        # #5   I/O_ZONE        Yes     NORMAL  10%     Yes        1        Yes
        # #6   SYSTEM          Yes     NORMAL  N/A     Yes        1        Yes
        parts = line.split()
        assert len(parts) == 8, line
        sensor_id = parts[0][1:]  # 2
        dim_id = "fan{0}".format(sensor_id)
        speed = None if parts[4] == "N/A" else int(parts[4][:-1])  # 29
        if not self.defined:
            title, context = self.caps_to_title(parts[1])
            self.add_chart(context, "fan", title, "percentage", dim_id, "fan #" + sensor_id)
            # TODO: add information about redundancy (per partner)
        return dim_id, speed

    def parse_power(self, line):
        # Power supply #1
        # 	Present  : Yes
        # 	Redundant: Yes
        # 	Condition: Ok
        # 	Hotplug  : Supported
        # 	Power    : 65 Watts
        if line.startswith("Power  "):  # two spaces to no conflict with the id
            self.power_id += 1
            dim_id = "pwr{0}".format(self.power_id)
            if not self.defined:
                dim_name = "bay #{0}".format(self.power_id)
                self.add_chart("power_watts", "powersupply", "Power Consumption", "Watts", dim_id, dim_name)
            if line.endswith(" Watts"):
                power = int(line.split()[2])  # 65
                return dim_id, power
        # TODO: add information about redundancy
        return None, None

    def _get_data(self):
        lines = self._get_raw_data()
        assert len(lines) > 0 and "must be root" not in lines[0]
        mode = None
        data = dict()
        self.power_id = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                mode = None  # empty line resets
            elif mode is not None:
                if line.startswith("---"):
                    continue
                dim_id, value = mode(line)
                if dim_id is not None:
                    data[dim_id] = value
            elif line.startswith("Sensor"):
                mode = self.parse_temperature
            elif line.startswith("Fan"):
                mode = self.parse_fan
            elif line.startswith("Power supply"):
                mode = self.parse_power
            else:
                raise AssertionError("unexpected output on line {0}: {1}".format(i, line))
        self.defined = True
        return data
