from pathlib import Path
import sys

import pandas as pd
import polars as pl

ROOT = Path("/Users/kdl/me")

DB = ROOT / "db.arrow"

assert ROOT.exists(), "Root path does not exist"


def collect_legacy_db_files():
    """Each directory in the root folder contains a 'dots.kdl' text file"""
    name = "dots.kdl"
    return [path / name for path in ROOT.iterdir() if (path / name).exists()]


def save_legacy_db():
    """Iterate through all the legacy db and save them as arrow file;
    very legacy"""
    structure = dict(path=[], text=[], time=[])
    for path in collect_legacy_db_files():
        content = path.read_text().strip().splitlines()
        for line in content:
            structure["path"].append(str(path.parent)[len(str(ROOT)) + 1 :])
            structure["text"].append(line[14:])
            structure["time"].append(line[:13])

    df = pl.DataFrame(structure)

    df.write_parquet(DB)

    assert DB.exists(), "Arrow file does not exist"


def load_db():
    """Load the db from arrow file"""
    return pl.read_parquet(DB)


def search_project(q: str):
    """Search for a project"""
    db = load_db()
    tokens = q.split(" ")
    for token in tokens:
        db = db.filter(
            pl.col("path").str.to_lowercase().str.contains(token)
            | pl.col("text").str.to_lowercase().str.contains(token)
        )

    filtered = db.unique(subset=["path"])
    return filtered


def search_note(q: str):
    """Search for a project"""
    db = load_db()
    tokens = q.split(" ")
    for token in tokens:
        db = db.filter(
            pl.col("path").str.to_lowercase().str.contains(token)
            | pl.col("text").str.to_lowercase().str.contains(token)
        )

    return db


if __name__ == "__main__":
    args = sys.argv[1:]
    got = search_note(" ".join(args))

    # output:
    for dir, text in zip(got["path"], got["text"]):
        print(f"{text}")
