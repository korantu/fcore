from pathlib import Path
from typing import List

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


# renderers


def fp(*q):
    """Find Project - output matching projects"""
    db = search_project(" ".join(q))
    for dir, text in zip(db["path"], db["text"]):
        print(f"{ROOT}/{dir} {text}")


def fn(*q):
    """Find Note - output all matching notes"""
    db = search_note(" ".join(q)).sort("time")
    for t in db["text"]:
        print(t)


def alias():
    """Generate aliases for shells and fzf"""
    import sys

    this_file = Path(__file__).absolute()
    executable = sys.executable
    q = "{q}"
    awk = """{print \\"cd \\" \\$1}"""

    out = f"""
    alias fp='fzf --bind "change:reload(eval {executable} {this_file} fp {q})" | awk "{awk}" | source'
    alias fn='fzf --bind "change:reload(eval {executable} {this_file} fn {q})"'
    """

    print(out)


if __name__ == "__main__":
    import fire

    fire.Fire({"fp": fp, "fn": fn, "alias": alias})
