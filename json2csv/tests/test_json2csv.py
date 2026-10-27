import csv
import json

import pytest

from json2csv import convert, json_records_to_rows, main


def write_json(tmp_path, records, name="in.json"):
    p = tmp_path / name
    p.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    return p


def test_happy_path(tmp_path):
    src = write_json(tmp_path, [{"a": 1, "b": 2}, {"a": 3, "b": 4}])
    dst = tmp_path / "out.csv"
    assert convert(str(src), str(dst)) == 2
    assert dst.read_text(encoding="utf-8").splitlines() == ["a,b", "1,2", "3,4"]


def test_missing_keys_filled_empty(tmp_path):
    src = write_json(tmp_path, [{"a": 1}, {"b": 2}])
    dst = tmp_path / "out.csv"
    convert(str(src), str(dst))
    assert dst.read_text(encoding="utf-8").splitlines() == ["a,b", "1,", ",2"]


def test_null_values_become_empty(tmp_path):
    src = write_json(tmp_path, [{"a": None}])
    dst = tmp_path / "out.csv"
    convert(str(src), str(dst))
    with open(dst, newline="", encoding="utf-8") as fh:
        assert list(csv.reader(fh)) == [["a"], [""]]


def test_unicode_and_special_chars(tmp_path):
    src = write_json(tmp_path, [{"n": "Hà Nội", "note": 'has "quotes", comma'}])
    dst = tmp_path / "out.csv"
    convert(str(src), str(dst))
    text = dst.read_text(encoding="utf-8")
    assert "Hà Nội" in text
    assert '"has ""quotes"", comma"' in text


def test_empty_array_produces_empty_file(tmp_path):
    src = write_json(tmp_path, [])
    dst = tmp_path / "out.csv"
    assert convert(str(src), str(dst)) == 0
    assert dst.read_text(encoding="utf-8") == ""


def test_non_object_record_rejected(tmp_path):
    src = write_json(tmp_path, [1, 2])
    dst = tmp_path / "out.csv"
    with pytest.raises(ValueError, match="record at index 0"):
        convert(str(src), str(dst))


def test_top_level_not_array_rejected(tmp_path):
    src = write_json(tmp_path, {"a": 1})
    dst = tmp_path / "out.csv"
    with pytest.raises(ValueError, match="must be an array"):
        convert(str(src), str(dst))


def test_cli_returns_zero(tmp_path, capsys):
    src = write_json(tmp_path, [{"x": "1"}])
    dst = tmp_path / "out.csv"
    assert main([str(src), str(dst)]) == 0
    assert dst.read_text(encoding="utf-8").splitlines() == ["x", "1"]


def test_cli_error_path(tmp_path, capsys):
    rc = main([str(tmp_path / "missing.json"), str(tmp_path / "out.csv")])
    assert rc == 1
    assert "error" in capsys.readouterr().err.lower()
