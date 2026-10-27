# json2csv

Convert a JSON file containing an array of flat objects into a CSV file.

- Python 3.10+, standard library only.
- Union-of-keys header in first-seen order; missing keys and `null` become empty cells.
- Nested values are stringified as-is (input is expected to be flat objects).
- UTF-8 input (BOM tolerated) and UTF-8 output; quoting/escaping per RFC 4180 via `csv`.

## Usage

```bash
python3 json2csv.py input.json output.csv
```

Example:

```bash
$ cat sample.json
[{"name":"Ann","city":"Hanoi"},{"name":"Bob","age":30}]
$ python3 json2csv.py sample.json out.csv
wrote 2 data row(s) to out.csv
$ cat out.csv
name,city,age
Ann,Hanoi,
Bob,,30
```

## Tests

```bash
pytest tests/ -v
```

9 tests cover: happy path, missing keys, nulls, unicode/quotes, empty array,
non-object records, non-array top level, CLI success and CLI error exit code.
