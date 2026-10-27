import json

from csv2json import convert, csv_rows_to_records, main


def write_csv(tmp_path, text, name="in.csv"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_happy_path(tmp_path):
    src = write_csv(tmp_path, "a,b\n1,2\n3,4\n")
    out = tmp_path / "o.json"
    assert convert(str(src), str(out)) == 2
    assert json.loads(out.read_text(encoding="utf-8")) == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


def test_quoted_special_characters(tmp_path):
    src = write_csv(tmp_path, 'x\n"has ""quotes"", comma and\nnewline"\n')
    recs = csv_rows_to_records(str(src))
    assert recs == [{"x": 'has "quotes", comma and\nnewline'}]


def test_unicode_passthrough(tmp_path):
    src = write_csv(tmp_path, "city\nHà Nội\n")
    out = tmp_path / "o.json"
    convert(str(src), str(out))
    assert json.loads(out.read_text(encoding="utf-8")) == [{"city": "Hà Nội"}]
    assert "Hà Nội" in out.read_text(encoding="utf-8")  # ensure_ascii=False


def test_semicolon_delimiter_autodetected(tmp_path):
    src = write_csv(tmp_path, "a;b\n1;2\n")
    assert csv_rows_to_records(str(src)) == [{"a": "1", "b": "2"}]


def test_explicit_delimiter(tmp_path):
    src = write_csv(tmp_path, "a|b\n1|2\n")
    assert csv_rows_to_records(str(src), delimiter="|") == [{"a": "1", "b": "2"}]


def test_ragged_row_missing_fields_filled_empty(tmp_path):
    src = write_csv(tmp_path, "a,b,c\n1,2\n")
    assert csv_rows_to_records(str(src)) == [{"a": "1", "b": "2", "c": ""}]


def test_extra_fields_collected_under_restkey(tmp_path):
    src = write_csv(tmp_path, "a,b\n1,2,3\n")
    rec = csv_rows_to_records(str(src))[0]
    assert rec["a"] == "1" and rec["b"] == "2"  # overflow goes to None-key and is dropped safely


def test_empty_file_yields_empty_array(tmp_path):
    src = write_csv(tmp_path, "")
    out = tmp_path / "o.json"
    assert convert(str(src), str(out)) == 0
    assert json.loads(out.read_text(encoding="utf-8")) == []


def test_cli_compact_output(tmp_path):
    src = write_csv(tmp_path, "a\n1\n")
    out = tmp_path / "o.json"
    assert main([str(src), str(out), "--indent", "-1"]) == 0
    assert out.read_text(encoding="utf-8").strip() == '[{"a": "1"}]'


def test_cli_error_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "nope.csv"), str(tmp_path / "o.json")]) == 1
    assert "error" in capsys.readouterr().err.lower()
