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


def search(tokens: list):
    """Search for a project; unuque if only one match per project needed;
    next is up"""
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
        if len(token) == 1:  # ignore single tokens
            continue
        db = db.filter(
            pl.col("path").str.to_lowercase().str.contains(token)
            | pl.col("text").str.to_lowercase().str.contains(token)
        )
    return db if not unique else db.unique(subset=["path"])


class Commands:
    def search(self, *q):
        """Search according to the request"""
        
        # make sure all is tring
        q = [str(x) for x in q]

        db = search(q).sort("time", descending=True)  # type: ignore

        def commment(space, note, timestamp):
            return f"# {note} -> [{timestamp}] |{space}"

        def changedir(space, note, timestamp):
            return f"cd {ROOT / space} # {note} -> [{timestamp}]"

        def copy(space, note, timestamp):
            return f"echo {note} | pbcopy # [{timestamp}]|{space}"

        def open(space, note, timestamp):
            first = note.split(" ")[0]
            rest = note[len(first) :]
            first_path = ROOT / space / first
            if first_path.exists():
                return f"open {first_path} # {note} -> [{timestamp}]|{space}"
            if first.startswith("http"):
                return f"open '{first}' # {rest} -> [{timestamp}]|{space}"
            return ""  # useless

        renderers = {"S": changedir, "O": open, "C": copy}

        renderer = commment

        for k in renderers.keys():
            if k in q:
                renderer = renderers[k]

        # check if it is actually adding needed
        if "A" in q:
            # remove the A
            q = [x for x in q if x != "A"]
            # add the note
            yield f"f an '{' '.join(q)}'"
            return

        for p, t, n in zip(db["path"], db["time"], db["text"]):
            if p == "":
                p = "me"  # special case for root location

            rendered = renderer(p, n, t)
            if rendered != "":
                yield rendered

    def an(self, *q):
        """Add Note - add a note to the db"""
        # make sure only strins are there
        q = [str(x) for x in q]
        db = add_note(" ".join(q))
        print(f"{db.shape[0]} notes.")

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
