# idea is to do repl only
from fcore import load_db


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

    def ask(self, question):
        answers = self.db.filter(self.db["text"].str.contains(question))[
            "text"
        ].to_list()
        return "\n".join(answers)


if __name__ == "__main__":
    r = ReplSimpleSearch()

    print(r.header())

    while i := input():
        print(r.ask(i))
