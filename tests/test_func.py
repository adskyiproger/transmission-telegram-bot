import pytest

from lib.func import bytes_to_human, human_to_bytes


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, "0B"), (1024, "1.0KB"), (1024**3, "1.0GB")],
)
def test_bytes_to_human(value, expected):
    assert bytes_to_human(value) == expected


def test_human_to_bytes():
    assert human_to_bytes("1.5GB") == 1610612736
