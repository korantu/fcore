import time

from fcore import *


def test_read_legacy_db_files():
    """Each directory in the root folder contains a 'kdl.dots' text file"""
    assert len(collect_legacy_db_files()) > 1


# sync up - load past db
def test_load_legacy_db():
    """Read all from old db - and making sure all is recorded"""
    expected = 31274  # number of lines in the legacy db
    total = 0
    paths_seen = []
    for path in collect_legacy_db_files():
        paths_seen.append(path)
        content = path.read_text().strip().splitlines()
        total += len(content)

    assert len(paths_seen) == 161
    assert total == expected, "Legacy db is not complete"

    old_db = load_legacy_db()

    db = load_db()

    full_db = old_db.extend(db)
    full_db = full_db.unique(subset="time").sort("time", descending=True)

    save_db(full_db)


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


def test_search():
    cmd = Commands()
    out = list(cmd.search("musu"))
    assert len(out) == 1

    assert note_dir(out[0]).exists(), "Should be able to extract dir"

    assert len(list(cmd.search("-"))) > 30000, "Return all"

    def docd(inp):
        """Change dir to a note"""
        return f"cd {note_dir(inp)}"

    def doopen(inp: str):
        """Open something meaningful"""
        first = inp.split(" ")[0]
        first_path = note_dir(inp) / first
        if inp.startswith("http"):
            return f"open {first}"
        if first_path.exists():
            return f"open {first_path}"

    assert docd(out[0]) == "cd /Users/kdl/me/legacy-dots-reference-list-history"


def test_search_project():
    """Search for a project"""
    common = search_project("action")
    # drop duplicate paths:
    common = common.unique(subset="path")
    assert len(common) > 1

    common = search_project("action frame")

    common = search_project("@")
    print(common)
