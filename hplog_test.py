import pytest
from hplog import Service


class TestService(Service):

    def _check_executable(self):
        return True

    def _get_raw_data(self, stderr=False, command=None):
        return """ID     TYPE        LOCATION      STATUS    CURRENT  THRESHOLD
 1  Basic Sensor Ambient         Normal    75F/ 24C 107F/ 42C
 2  Basic Sensor Processor Zone  Normal   104F/ 40C 158F/ 70C
 3  Basic Sensor Processor Zone  Normal   ---F/---C ---F/---C
 4  Basic Sensor Memory Board    Normal    84F/ 29C 188F/ 87C
 5  Basic Sensor Memory Board    Normal    82F/ 28C 188F/ 87C
 6  Basic Sensor Memory Board    Normal   ---F/---C ---F/---C
 7  Basic Sensor Memory Board    Normal   ---F/---C ---F/---C
 8  Basic Sensor Memory Board    Normal    87F/ 31C 158F/ 70C
 9  Basic Sensor Memory Board    Normal    86F/ 30C 158F/ 70C
10  Basic Sensor Memory Board    Normal    89F/ 32C 158F/ 70C
11  Basic Sensor Memory Board    Normal    86F/ 30C 158F/ 70C
12  Basic Sensor System Board    Normal   ---F/---C ---F/---C
13  Basic Sensor System Board    Normal   111F/ 44C 221F/105C
14  Basic Sensor System Board    Normal    96F/ 36C 158F/ 70C
15  Basic Sensor Pwr. Supply Bay Normal    86F/ 30C ---F/---C
16  Basic Sensor Pwr. Supply Bay Normal    89F/ 32C 158F/ 70C
17  Basic Sensor Pwr. Supply Bay Normal    84F/ 29C ---F/---C
18  Basic Sensor Pwr. Supply Bay Normal    86F/ 30C 149F/ 65C
19  Basic Sensor I/O Zone        Normal   ---F/---C ---F/---C
20  Basic Sensor I/O Zone        Normal   ---F/---C ---F/---C
21  Basic Sensor System Board    Normal    93F/ 34C 239F/115C
22  Basic Sensor System Board    Normal    87F/ 31C 239F/115C
23  Basic Sensor System Board    Normal    84F/ 29C 239F/115C
24  Basic Sensor System Board    Normal    82F/ 28C 239F/115C
25  Basic Sensor System Board    Normal    84F/ 29C 239F/115C
26  Basic Sensor System Board    Normal    84F/ 29C 239F/115C
27  Basic Sensor System Board    Normal    84F/ 29C 158F/ 70C
28  Basic Sensor System Board    Normal    82F/ 28C 158F/ 70C
29  Basic Sensor System Board    Normal    84F/ 29C 158F/ 70C
30  Basic Sensor System Board    Normal    82F/ 28C 158F/ 70C
31  Basic Sensor System Board    Normal   ---F/---C ---F/---C
32  Basic Sensor System Board    Normal    89F/ 32C 149F/ 65C
33  Basic Sensor System Board    Normal    98F/ 37C 158F/ 70C
34  Basic Sensor System Board    Normal    96F/ 36C 150F/ 66C
35  Basic Sensor I/O Zone        Normal   ---F/---C ---F/---C
36  Basic Sensor System Board    Normal    86F/ 30C 149F/ 65C
37  Basic Sensor System Board    Normal    91F/ 33C 158F/ 70C
38  Basic Sensor System Board    Normal    86F/ 30C 158F/ 70C
39  Basic Sensor System Board    Normal   100F/ 38C 158F/ 70C
40  Basic Sensor System Board    Normal    96F/ 36C 158F/ 70C
41  Basic Sensor System Board    Normal    95F/ 35C 147F/ 64C
42  Basic Sensor System Board    Normal   ---F/---C ---F/---C

ID     TYPE        LOCATION      STATUS  REDUNDANT FAN SPEED
 1  Basic Fan    Virtual         Absent     N/A     Unknown
 2  Basic Fan    Virtual         Absent     N/A     Unknown
 3  Var. Speed   Virtual         Normal     Yes     Normal   ( 29)
 4  Var. Speed   Virtual         Normal     Yes     Normal   ( 29)
 5  Var. Speed   Virtual         Normal     Yes     Normal   ( 29)
 6  Var. Speed   Virtual         Normal     Yes     Normal   ( 29)
 7  Var. Speed   Virtual         Normal     Yes     Normal   ( 29)
 8  Var. Speed   Virtual         Normal     Yes     Normal   ( 29)

ID     TYPE        LOCATION      STATUS  REDUNDANT
 1  Standard     Pwr. Supply Bay Normal     Yes
 2  Standard     Pwr. Supply Bay Normal     Yes
""".splitlines()


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
    assert len(service.charts) == 0
    service.check()
    assert len(service.charts) == 6


def test_data():
    service = new_service()
    service.check()
    data = service.get_data()
    assert len(data) == 42
    assert data['1'] == 24  # deg C
