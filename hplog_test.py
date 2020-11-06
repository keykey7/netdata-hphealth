import pytest
from hplog import HphealthService


class TestService(HphealthService):

    def _get_raw_data(self, stderr=False, command=None):
        with open('testdata.txt', 'r') as file:
            self.last_data = file.read().splitlines()
            return self.last_data

    def check_binary(self):
        self.get_data()
        return True


def new_service():
    return TestService(configuration={
        "job_name": "",
        "override_name": "",
        "update_every": 0,
        "penalty": 0,
        "priority": 0,
        "chart_cleanup": 0,
    }, name="fuu")


def test_definition():
    service = new_service()
    assert len(service.charts) == 0, service.charts
    service.check()
    assert len(service.charts) == 5, service.charts


def test_data():
    service = new_service()
    service.check()
    data = service.get_data()
    assert len(data) == 33 + 6 + 2, data
    assert data['tmp1_42'] == 24, "24 degree of first temperature sensor"
    assert data['fan1'] is None
    assert data['fan7'] == 29
    assert data['pwr2'] == 20
