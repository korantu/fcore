# idea is to do repl only
from dataclasses import dataclass
import os
from pathlib import Path
import readline
import sys

import polars as pl

from fcore import load_db, project, save_db, timestamp

# Find the python executable
PYTHON_EXECUTABLE = Path(sys.executable).absolute()

assert PYTHON_EXECUTABLE.exists(), "Could not find python executable"

HERE = Path(os.path.abspath(__file__)).parent

NAME = "gg"

assert HERE.exists() and HERE.is_dir(), "Could not find project root directory"

# Create a launcher script for the with the correct location
LAUNCHER = f"""#!/bin/sh
cd {HERE}
{PYTHON_EXECUTABLE} repl.py $@"""

# Write the launcher script
SCRIPT = HERE / NAME
SCRIPT.write_text(LAUNCHER)
SCRIPT.chmod(0o755)

# readline stuff

HISTORY_FILE = HERE / "log.txt"


def save_history():
    try:
        readline.write_history_file(HISTORY_FILE)
    except IOError:
        # Handle error if something goes wrong
        pass


# Optionally, load existing history at the start
try:
    readline.read_history_file(HISTORY_FILE)
except FileNotFoundError:
    # No existing history, or file not found. Safe to ignore.
    pass


# Atoms


@dataclass
class Atom:
    text: str
    space: str
    ts: float


def atoms(db) -> list[Atom]:
    return [
        Atom(text, space, float(ts))
        for text, space, ts in zip(db["text"], db["path"], db["time"])
    ]


def human_time(epoch):
    import datetime

    epoch = int(epoch / 1000)

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
        return f"{delta.days}d"
    elif delta.seconds > 3600:
        minutes = (delta.seconds // 60) % 60
        return f"{delta.seconds // 3600}h {minutes}m"
    elif delta.seconds > 60:
        return f"{delta.seconds // 60}m"
    else:
        return "+"


def render_atom(atom: Atom) -> str:
    return f"{atom.space}|> {atom.text}: [{human_time(atom.ts)}]"


def header(db):
    db = db.sort("time", descending=True).limit(10).sort("time", descending=False)
    return "\n".join([render_atom(a) for a in atoms(db)])


class Repl:
    def header(self) -> str:
        return "Answers any question"

    def ask(self, q) -> str:
        return f"Answer for {q}"


class ReplSimpleSearch:
    def __init__(self):
        self.db = load_db()

    def header(self):
        return f"""{header(self.db)}
    And more possible..."""

    def _narrow(self, db, token):
        return db.filter(
            db["text"].str.to_lowercase().str.contains(token)
            | db["path"].str.to_lowercase().str.contains(token)
        )

    def ask(self, question):
        tokens = question.lower().split()
        if len(tokens) == 0:
            return "Please ask a question"

        answers = self._narrow(self.db, tokens[0])
        for token in tokens[1:]:
            answers = self._narrow(answers, token)

        return "\n".join([render_atom(a) for a in atoms(answers)])


class ReplAdd:
    def __init__(self):
        self.db = load_db()

    def header(self):
        return f"""{header(self.db)}
    Add a new entry please"""

    def ask(self, addition):
        """Adding the content of the question"""

        self.db = load_db()
        extension = pl.DataFrame(
            dict(path=[project()], text=[addition], time=[timestamp()])
        )
        self.db = self.db.extend(extension)
        save_db(self.db)
        print("Added")
        return f"""{header(self.db)}"""


MODES = {
    "a": ReplAdd,
    "s": ReplSimpleSearch,
}


def help():
    """Automatically generate hints from modes; Use the class names"""
    hints = []
    for mode_key, mode_class in MODES.items():
        mode_hint = f"{mode_key}: {mode_class.__name__}"
        hints.append(mode_hint)
    return "\n".join(hints)


def start():
    def select_mode():
        r = ReplSimpleSearch()
        print(r.header())
        return r

    r = select_mode()

    while i := input():
        if len(i) <= 1:
            if i in MODES.keys():
                r = MODES[i]()
                print(r.header())
                continue
            else:
                print(help())
                continue
        save_history()
        print(r.ask(i))


if __name__ == "__main__":

    try:
        start()
    except KeyboardInterrupt:
        print("Bye.")
        exit(0)
