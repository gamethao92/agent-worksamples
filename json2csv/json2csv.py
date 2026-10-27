#!/usr/bin/env python3
"""Convert a JSON array of flat objects to CSV.

Missing keys in some objects are filled with empty strings.
Column order: keys appear in first-seen order across all objects.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys


def json_records_to_rows(records: list[dict]) -> tuple[list[str], list[list[str]]]:
    if not isinstance(records, list):
        raise ValueError("top-level JSON value must be an array")
    headers: list[str] = []
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            raise ValueError(f"record at index {i} is {type(rec).__name__}, expected object")
        for key in rec:
            if key not in headers:
                headers.append(key)
    rows = []
    for rec in records:
        row = []
        for key in headers:
            value = rec.get(key, "")
            row.append("" if value is None else str(value))
        rows.append(row)
    return headers, rows


def convert(in_path: str, out_path: str) -> int:
    with open(in_path, encoding="utf-8-sig") as fh:
        records = json.load(fh)
    headers, rows = json_records_to_rows(records)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if headers:
            writer.writerow(headers)
        writer.writerows(rows)
    return len(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Convert a JSON array of flat objects to CSV.")
    parser.add_argument("input", help="path to JSON file")
    parser.add_argument("output", help="path to CSV file to write")
    args = parser.parse_args(argv)
    try:
        n = convert(args.input, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {n} data row(s) to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
