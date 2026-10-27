# csv2json

Convert a CSV file into a JSON array of objects with correct escaping.

- Python 3.10+, standard library only.
- Handles quoted fields with embedded commas, quotes (`""`) and newlines (RFC 4180).
- Delimiter auto-detected (`,` `;` tab `|`) or forced with `--delimiter`.
- Short rows fill missing columns with `""`; long rows keep the named columns safely.
- UTF-8 in (BOM tolerated) and out, non-ASCII kept readable (`ensure_ascii=False`).

## Usage

```bash
python3 csv2json.py data.csv out.json                 # auto-detect delimiter, indent 2
python3 csv2json.py data.tsv out.json --delimiter $'\t' --indent -1   # compact
```

## Tests

```bash
pytest tests/ -v
```

10 tests cover: basic conversion, embedded quotes/commas/newlines, unicode,
semicolon auto-detection, explicit delimiter, ragged rows, empty file,
compact CLI output and error exit code.
