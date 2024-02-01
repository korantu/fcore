# idea is to do repl only
import os
from pathlib import Path
import readline
import sys

from fcore import load_db

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


class Repl:
    def header(self) -> str:
        return "Answers any question"

    def ask(self, q) -> str:
        return f"Answer for {q}"


class ReplSimpleSearch:
    def __init__(self):
        self.db = load_db()

    def header(self):
        return "Simple Search REPL"

    def narrow(self, db, token):
        return db.filter(db["text"].str.to_lowercase().str.contains(token))

    def ask(self, question):
        tokens = question.lower().split()
        if len(tokens) == 0:
            return "Please ask a question"

        answers = self.narrow(self.db, tokens[0])
        for token in tokens[1:]:
            answers = self.narrow(answers, token)

        return "\n".join(answers["text"].to_list())


def start():
    r = ReplSimpleSearch()

    print(r.header())

    while i := input():
        print(r.ask(i))


if __name__ == "__main__":

    try:
        start()
    except KeyboardInterrupt:
        print("Bye.")
        exit(0)
