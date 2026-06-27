import pytest

from asset_publish_tool.core.shot_naming import format_shot_name


def test_format_shot_name_single_digit():
    assert format_shot_name(1) == "shot001"


def test_format_shot_name_double_digit():
    assert format_shot_name(10) == "shot010"


def test_format_shot_name_triple_digit():
    assert format_shot_name(120) == "shot120"


def test_format_shot_name_string_input():
    assert format_shot_name("15") == "shot015"


def test_format_shot_name_rejects_invalid_input():
    with pytest.raises(ValueError):
        format_shot_name("abc")
