# -*- coding: utf-8 -*-

from hphealth import Service


class MockService(Service):

    def _get_raw_data(self, stderr=False, command=None):
        with open('testdata.txt', 'r') as file:
            self.last_data = file.read().splitlines()
            return self.last_data

    def check_binary(self):
        self.command = [self.command]
        self.get_data()
        return True


def new_service():
    return MockService(configuration={
        "job_name": "",
        "override_name": "",
        "update_every": 0,
        "penalty": 0,
        "priority": 0,
        "chart_cleanup": 0,
        "sudo": "False"
    }, name="fuu")


def test_definition():
    service = new_service()
    assert len(service.charts) == 0, service.charts
    service.check()
    assert len(service.charts) == 9, service.charts


def test_data():
    service = new_service()
    service.check()
    data = service.get_data()
    assert len(data) == 33 + 8 + 3, data
    assert data['tmp1_42'] == 24, "24 degree of first temperature sensor"
    assert data['fan1'] is None
    assert data['fan7'] == 29
    assert data['pwr2'] == 20


def test_gen_health_data():
    for i in range(40, 200, 5):
        print("""
template: temperature_over_threshold_{0}c
      on: hphealth.temperature
  lookup: max -1m unaligned foreach tmp*_{0},tmp*_{1},tmp*_{2},tmp*_{3},tmp*_{4}
   units: °C
   every: 1m
    warn: $this > (($status >= $WARNING)  ? ( {5} ) : ( {6} ))
    crit: $this > (($status >= $CRITICAL) ? ( {6} ) : ( {7} ))
    info: temperature sensor close to {0}C critical threshold
      to: sysadmin""".format(i, i+1, i+2, i+3, i+4, i-10, i-5, i-2))
