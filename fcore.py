from pathlib import Path
import time

import polars as pl

ROOT = Path("/Users/kdl/me")

DB = ROOT / "db.arrow"

assert ROOT.exists(), "Root path does not exist"


def schema():
    """Return the schema of the db"""
    db_schema = dict(path=[], text=[], time=[])
    return db_schema


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
    old_db = [path / name for path in ROOT.iterdir() if (path / name).exists()]
    old_db.append(ROOT / name)
    return old_db


def load_legacy_db():
    """Return dataframe of legacy db"""
    structure = schema()
    for path in collect_legacy_db_files():
        content = path.read_text().strip().splitlines()
        for line in content:
            structure["path"].append(str(path.parent)[len(str(ROOT)) + 1 :])
            structure["text"].append(line[14:])
            structure["time"].append(line[:13])

    df = pl.DataFrame(structure)
    df = df.unique(subset=["time"]).sort("time", descending=True)
    return df


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
    """Search for a project; unuque if only one match per project needed"""
    db = load_db()
    tokens = q.split(" ")
    for token in tokens:
        # special case for this location
        if token == "@":  # @ is a special token for this location
            db = db.filter(pl.col("path").str.contains(project()))
            continue
        db = db.filter(
            pl.col("path").str.to_lowercase().str.contains(token)
            | pl.col("text").str.to_lowercase().str.contains(token)
        )
    if unique:
        db = db.unique(subset=["path"])
    return db


def search(tokens: list):
    """Search for a project; unuque if only one match per project needed"""
    db = load_db()
    unique = False
    for token in tokens:
        # special case for this location
        if token == "@":  # @ is a special token for this location
            db = db.filter(pl.col("path").str.contains(project()))
            continue
        if token == ".":  # unique indicator
            unique = True
            continue
        db = db.filter(
            pl.col("path").str.to_lowercase().str.contains(token)
            | pl.col("text").str.to_lowercase().str.contains(token)
        )
    return db if not unique else db.unique(subset=["path"])


class Commands:
    def fp(self, *q):
        """Find Project - output matching projects"""
        db = search_project(" ".join(q), unique=True).sort("time", descending=True)
        for dir, text in zip(db["path"], db["text"]):
            print(f"{ROOT}/{dir} {text}")

    def fn(self, *q):
        """Find Note - output all matching notes"""
        db = search_project(" ".join(q)).sort("time", descending=True)
        for t, n in zip(db["time"], db["text"]):
            print(f"{n} # [{t}]")

    def fo(self, *q):
        """Find Openable - output runnable"""
        db = search_project("http " + " ".join(q)).sort("time", descending=True)
        for dir, text in zip(db["path"], db["text"]):
            print(f"{text} [{dir}]")

    def search(self, *q):
        """Search - output all matching notes"""
        db = search(q).sort("time", descending=True)
        for p, t, n in zip(db["path"], db["time"], db["text"]):
            print(f"{p}|{n} -> [{t}]")

    def an(self, *q):
        """Add Note - add a note to the db"""
        db = add_note(" ".join(q))
        print(f"{db.shape[0]} notes.")

    def launch(self):
        """Read stdin and print the command suitable to launch the line"""
        line = input()
        url = line.split(" ")[0]
        print(f"open '{url}'")

    def cd(self):
        """Read stdin and change dir to first component"""
        line = input()
        dir = line.split(" ")[0]
        print(f"cd {dir}")

    def alias(self):
        """Generate aliases for shells and fzf"""

        q = "{q}"
        fzf_default = 'FZF_DEFAULT_COMMAND="echo Enter a search query"'

        out = f"""
        alias fp='{fzf_default} fzf --disabled --bind "change:reload(eval f fp {q})" | f cd | source'
        alias fn='{fzf_default} fzf --disabled --bind "change:reload(eval f fn {q})" | pbcopy; echo "Copied to clipboard"'
        alias fo='{fzf_default} fzf --disabled --bind "change:reload(eval f fo {q})" | f launch | source'
        alias an='f an '
        """

        print(out)

    def script(self):
        """Generate script to use as the f command and put it on the path as f; Use as
        pipenv run python fcore.py script | source
        """
        import sys

        this_file = Path(__file__).absolute()
        executable = Path(sys.executable).absolute()
        path = Path("~/.local/bin/f").expanduser().absolute()

        all = '"\\$@"'

        assert path.exists(), f"About to put binary on [{path}], but it does not exist"

        steps = [
            f"echo \\#!/bin/sh > {path}",
            f"echo {executable} {this_file} {all} >> {path}",
            f"chmod +x {path}",
        ]

        print("\n".join(steps))


if __name__ == "__main__":
    import fire

    fire.Fire(Commands)
