from pathlib import Path
import time

import polars as pl
from polars.dependencies import json

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
    db = pl.read_parquet(DB)
    db = db.sort("time")
    return db


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
    # current epoch
    epoch = int(time.time())
    db = load_db()
    unique = False
    for token in tokens:
        # special case for this location
        if token == "@":  # @ is a special token for this location
            db = db.filter(pl.col("path").str.contains(project()))
            continue
        if token == "%":  # % means we only caare for recent events
            two_weeks_ago = epoch - 86400 * 31  # days
            db = db.with_columns(
                pl.col("time").str.slice(0, 10).cast(pl.Int64).alias("ts")
            ).sort("ts")
            db = db.filter(pl.col("ts") > two_weeks_ago)
        if token[0] == "@" and len(token) > 1:  # @ is a special token for this location
            db = db.filter(pl.col("path").str.contains(token[1:]))
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
    return (
        db
        if not unique
        else db.unique(keep="last", maintain_order=True, subset=["path"])
    )


def human_time(t):
    import datetime

    epoch = int(t[:10])

    # convert milliseconds epoch to datetime object
    dt = datetime.datetime.fromtimestamp(epoch)

    # get current datetime
    now = datetime.datetime.now()

    # calculate time difference
    delta = now - dt

    # format time difference in human readable short form
    if delta.days > 20:
        return dt.strftime("%y-%m-%d")
    elif delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds > 3600:
        return f"{delta.seconds // 3600}h ago"
    elif delta.seconds > 60:
        return f"{delta.seconds // 60}m ago"
    else:
        return "just now"


class Commands:
    """Commands for train of thought"""

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
            return f"""echo "{note}" | pbcopy # [{timestamp}]|{space}"""

        def open(space, note, timestamp):
            first = note.split(" ")[0]
            rest = note[len(first) :]
            first_path = ROOT / space / first if len(first) < 80 else None
            if first_path is not None and first.startswith("~"):
                # treat undescore as a space
                if "_" in first:
                    first = first.replace("_", " ")
                # open it with 'open -a' command
                return f"open -a '{first[1:]}' # {rest} -> [{timestamp}]|{space}"
            if first_path is not None and first_path.exists():
                if first_path.is_dir():
                    return f"cd {first_path} # {rest} -> [{timestamp}]|{space}"
                elif ".txt" in str(first_path): # use vim
                    return f"nvim {first_path} # {rest} -> [{timestamp}]|{space}"
                else:
                    return f"open {first_path} # {note} -> [{timestamp}]|{space}"
            if first.startswith("http"):
                return f"open '{first}' # {rest} -> [{timestamp}]|{space}"
            return ""  # useless

        def asis(space, note, timestamp):
            return f"{note} # [{timestamp}]|{space}"

        renderers = {"S": changedir, "O": open, "C": copy, "R": asis}

        renderer = commment

        for k in renderers.keys():
            if k in q:
                renderer = renderers[k]

        # check if it is actually adding needed
        if "A" in q:
            # remove the A
            q = [x for x in q if x != "A"]
            # maybe it is a new project
            if len(q) == 1 and q[0][0] == "@":
                yield f"mkdir {ROOT / q[0][1:]}; cd {ROOT / q[0][1:]}"
                return
            # add the note
            yield f"f an '{' '.join(q)}'"
            return

        # create new dir if cant find anything
        if len(db) == 0 and "S" in q:
            yield f"mkdir {ROOT / q[0]}; cd {ROOT / q[0]}"
            return

        # main renderer
        for p, t, n in zip(db["path"], db["time"], db["text"]):
            if p == "":
                p = "me"  # special case for root location

            # only do time conversion if we got not too many hits:
            if len(db) < 1500:
                t = human_time(t)

            rendered = renderer(p, n, t)
            if rendered != "":
                yield rendered

    def an(self, *q):
        """Add Note - add a note to the db"""
        # make sure only strins are there
        # maybe we need standard input
        if len(q) == 0 or q[0] == ".":
            # read from stdin
            line = input()
            line = line.strip()
            if len(q) > 0 and q[0] == ".":
                line += f" # {' '.join(q[1:])}"
            print(line)
            db = add_note(line)
        else:
            q = [str(x) for x in q]
            db = add_note(" ".join(q))
        print(f"{db.shape[0]} notes.")

    def norm(self, *q):
        """Rename provided file to replace spaces from their names with dashes"""
        path = Path(" ".join(q))
        assert path.exists(), f"Path [{path}] does not exist"
        new_path = path.parent / path.name.replace(" ", "-")
        path.rename(new_path)

    def png(self, *q):
        """paste image from clipboard to current directory, in OSX"""
        import subprocess
        import pyperclip

        name = "-".join(q) + ".png"

        subprocess.run(["pngpaste", name])

        # copy name to clipboard
        pyperclip.copy(name)

        print(f"copied [{name}] to clipboard and added it to note")

        add_note(f"{name}")

    def ls(self, *q):
        # walk directory and print all the files; ignore ".git" and ".DS_Store"; if there are more than 3 files in a directory, print the only the three ones

        def dir_summary(path=Path("."), depth=0):
            files_seen = 0
            lines_per_dir = 4
            for p in path.iterdir():
                if p.name in [
                    ".git",
                    ".DS_Store",
                    "__pycache__",
                    ".ipynb_checkpoints",
                    "node_modules",
                    "venv",
                ]:
                    print(f"{'  '*depth}{p.name}/")
                    continue
                if p.is_dir():
                    print(f"{'  '*depth}{p.name}/")
                    dir_summary(p, depth + 1)
                else:
                    files_seen += 1
                    if files_seen < lines_per_dir:
                        print(f"{'  '*depth}{p.name}")
                    if files_seen == lines_per_dir:
                        print(f"{'  '*depth}...")

        try:
            dir_summary()
        except PermissionError:
            print("Permission error. Try again with sudo.")

    def all(self):
        """Print all notes"""
        db = load_db()

        completed = []
        
        for p, t, n in zip(db["path"], db["time"], db["text"]):
            if p == "":
                p = "me"
            completed.append([p, n, t])

        # save as js file, exported
        with Path("all.json").open("w") as f:
            json.dump(completed, f, indent=4)


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
