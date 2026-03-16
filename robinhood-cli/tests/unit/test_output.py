import json
from robinhood_cli.output import format_currency, format_change, format_percent


def test_format_currency_positive():
    assert format_currency(213.42) == "$213.42"


def test_format_currency_none():
    assert format_currency(None) == "—"


def test_format_change_positive():
    result = format_change(1.84)
    assert "+$1.84" in result


def test_format_change_negative():
    result = format_change(-3.20)
    assert "-$3.20" in result


def test_format_change_none():
    assert format_change(None) == "—"


def test_format_percent_positive():
    result = format_percent(0.87)
    assert "+0.87%" in result


def test_format_percent_negative():
    result = format_percent(-1.27)
    assert "-1.27%" in result
