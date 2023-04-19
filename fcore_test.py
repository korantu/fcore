import time

from fcore import *


def test_read_legacy_db_files():
    """Each directory in the root folder contains a 'kdl.dots' text file"""
    assert len(collect_legacy_db_files()) > 1


def test_save_legacy_db():
    """Iterate through all the legacy db and save them as arrow file"""
    save_legacy_db()
    assert DB.exists(), "Arrow file does not exist"


def test_load_db():
    """Load the db from arrow file"""
    db = pl.read_parquet(DB)
    assert len(db) > 10000

    # time it 10 times:
    N = 10
    started = time.time()
    for _ in range(N):
        db = load_db()
        assert len(db) > 10000
    ended = time.time()
    print(f"Time to load db: {(ended - started) / N}")

    print(db.head())


def test_detect_project():
    assert "fcore" in str(project())
    print(project())


def test_timestamp():
    print(timestamp())
    assert len(timestamp()) == 13


def test_add_note():
    ts = timestamp()

    add_note(f"Senpusechka fcode on {ts}")

    found = search_project(ts, unique=True)
    assert len(found) == 1


def test_search_project():
    """Search for a project"""
    common = search_project("action")
    # drop duplicate paths:
    common = common.unique(subset="path")
    assert len(common) > 1

    common = search_project("action frame")
    print(common)
