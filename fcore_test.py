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


def test_sqlite_db():
    """Export thing in sqlite db"""
    db = load_db()
    assert len(db) > 10000
    dbh = db.head()
    for i in zip(dbh["time"], dbh["path"], dbh["text"]):
        print(i)

    import sqlite3 as sql

    conn = sql.connect("/tmp/fcode.db")
    conn.execute("drop table if exists fcode")
    conn.execute("create table if not exists fcode (time, path, text)")
    conn.commit()
    data = []
    for i in db.to_pandas().itertuples():
        data.append(i[1:])

    conn.executemany("insert into fcode values (?, ?, ?)", data)
    conn.commit()
    
    # load and compare
    conn = sql.connect("/tmp/fcode.db")
    result = conn.execute("select * from fcode").fetchall()
    assert len(result) == len(db), "Sqlite db is not complete"

    # benchmark
    N = 10
    started = time.time()
    for _ in range(N):
        obtained = conn.execute("select * from fcode").fetchall()
        assert len(obtained) == len(db), "Sqlite db is not complete"
    ended = time.time()
    print(f"Time to load db: {(ended - started) / N}")

    # print first 10
    for i in result[:10]:
        print(i)


def test_time_db():
    db = load_db()
    db = db.select(pl.col("time").str.slice(0, 10).cast(pl.Int64).alias("ts"))
    assert len(db) - len(set(db["ts"].to_list())) == 0, "Seconds have to be unique"
    


def test_detect_project():
    """Detect the project name from the current path"""
    assert "fcore" in str(project())


def test_timestamp():
    """Return a timestamp in milliseconds"""
    print(timestamp())
    assert len(timestamp()) == 13


def test_add_search_note():
    ts = timestamp()

    add_note(f"Senpusechka fcode on {ts}")

    found = search([ts])
    assert len(found) == 1


def test_time_remdering():
    ts = timestamp()

    assert human_time(ts) == "just now"

    assert human_time(int(ts) - 1000 * 60 * 60 * 24 * 2) == "2d ago"

    assert human_time(1000000000) == "1970-01-12"
