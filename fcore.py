import os
from pathlib import Path
import time
from typing import List

import polars as pl

ROOT = Path("/Users/kdl/me")

DB = ROOT / "db.arrow"

assert ROOT.exists(), "Root path does not exist"


def project(current=Path.cwd()):
    """Detect the project name from the current path"""
    assert str(ROOT) in str(current)

    if current.parent == ROOT:
        return str(current.name)
    else:
        return project(current=current.parent)


def timestamp():
    """Return a timestamp in milliseconds"""
    return str(int(time.time() * 1000))


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


def save_db(db):
    """Save the db to arrow file"""
    db.write_parquet(DB)
    return db


def add_note(text: str):
    """Add a note to the db"""
    db = load_db()
    extension = pl.DataFrame(dict(path=[project()], text=[text], time=[timestamp()]))
    db = db.extend(extension)
    save_db(db)
    return db


def search_project(q: str, unique=False):
    """Search for a project"""
    db = load_db()
    tokens = q.split(" ")
    for token in tokens:
        db = db.filter(
            pl.col("path").str.to_lowercase().str.contains(token)
            | pl.col("text").str.to_lowercase().str.contains(token)
        )

    if unique:
        db = db.unique(subset=["path"])
    return db


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
commands = {}


def fp(*q):
    """Find Project - output matching projects"""
    db = search_project(" ".join(q), unique=True).sort("time")
    for dir, text in zip(db["path"], db["text"]):
        print(f"{ROOT}/{dir} {text}")


commands["fp"] = fp


def fn(*q):
    """Find Note - output all matching notes"""
    db = search_note(" ".join(q)).sort("time")
    for t in db["text"]:
        print(t)


commands["fn"] = fn


def fo(*q):
    """Find Openable - output runnable"""
    db = search_project("http " + " ".join(q)).sort("time")
    for dir, text in zip(db["path"], db["text"]):
        print(f"{text} [{dir}]")


commands["fo"] = fo


def an(*q):
    """Add Note - add a note to the db"""
    db = add_note(" ".join(q))
    print(f"{db.shape[0]} notes.")
    


commands["an"] = an


def alias():
    """Generate aliases for shells and fzf"""
    import sys

    this_file = Path(__file__).absolute()
    executable = sys.executable
    q = "{q}"
    fzf_default = 'FZF_DEFAULT_COMMAND="echo Enter a search query"'
    awk_cd = """{print \\"cd \\" \\$1}"""
    awk_open = """{print \\"open \\" \\$1}"""

    out = f"""
    alias fp='{fzf_default} fzf --bind "change:reload(eval {executable} {this_file} fp {q})" | awk "{awk_cd}" | source'
    alias fn='{fzf_default} fzf --bind "change:reload(eval {executable} {this_file} fn {q})"'
    alias fo='{fzf_default} fzf --bind "change:reload(eval {executable} {this_file} fo {q})" | awk "{awk_open}" | source'
    alias an='{executable} {this_file} an '
    """

    print(out)


commands["alias"] = alias


if __name__ == "__main__":
    import fire

    fire.Fire(commands)
