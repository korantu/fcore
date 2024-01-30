import time

from fcore import load_db
from repl import Repl, ReplSimpleSearch


def test_load_db():
    """Load the db from arrow file"""
    # time it 10 times:
    db = load_db()
        
    N = 10
    started = time.time()
    for _ in range(N):
        db = load_db()
        assert len(db) > 10000
    ended = time.time()
    print(f"Time to load db: {(ended - started) / N}")

    print(db.head())


def test_repl():
    r = Repl()
    assert len(r.header()) > 3


def test_replsimplesearch():
    r = ReplSimpleSearch()
    
    assert len(r.header()) > 3

    results = r.ask("tutu")
    assert len(results) > 0



