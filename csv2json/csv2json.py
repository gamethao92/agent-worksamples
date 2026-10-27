#!/usr/bin/env python3
"""Convert CSV file(s) to JSON arrays with proper escaping of special characters."""
from __future__ import annotations

import argparse
import csv
import json
import sys


def csv_rows_to_records(path: str, delimiter: str | None = None) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        if delimiter is None:
            try:
                delimiter = csv.Sniffer().sniff(fh.read(4096), delimiters=",;\t|").delimiter
            except csv.Error:
                delimiter = ","
            fh.seek(0)
        reader = csv.DictReader(fh, delimiter=delimiter)
        if reader.fieldnames is None:
            return []
        records = []
        for row in reader:
            # None values appear when a row has fewer fields than the header
            records.append({k: ("" if v is None else v) for k, v in row.items() if k is not None})
    return records


def convert(in_path: str, out_path: str, delimiter: str | None = None, indent: int | None = 2) -> int:
    records = csv_rows_to_records(in_path, delimiter)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=indent)
        fh.write("\n")
    return len(records)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Convert a CSV file to a JSON array of objects.")
    parser.add_argument("input", help="path to CSV file")
    parser.add_argument("output", help="path to JSON file to write")
    parser.add_argument("--delimiter", default=None, help="field delimiter (auto-detected if omitted)")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent; use -1 for compact output")
    args = parser.parse_args(argv)
    indent = None if args.indent < 0 else args.indent
    try:
        n = convert(args.input, args.output, args.delimiter, indent)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {n} record(s) to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
