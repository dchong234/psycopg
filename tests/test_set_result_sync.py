"""
Fail-to-pass tests for Cursor.set_result().

These tests call set_result() directly and verify:
- valid index selection (positive)
- negative indexing (Python-list style)
- IndexError on out-of-range index
- method chaining (returns cursor itself)
"""
import pytest
import psycopg


def test_set_result_no_results_raises(conn):
    """set_result raises IndexError when cursor has no results."""
    cur = conn.cursor()
    with pytest.raises(IndexError):
        cur.set_result(0)


def test_set_result_valid_positive_index(conn):
    """set_result selects the correct result set by positive index."""
    cur = conn.cursor()
    cur.execute("select 'first'; select 'second'")
    cur.set_result(0)
    assert cur.fetchone() == ("first",)
    cur.set_result(1)
    assert cur.fetchone() == ("second",)


def test_set_result_negative_index(conn):
    """set_result supports negative indexing like Python lists."""
    cur = conn.cursor()
    cur.execute("select 10; select 20; select 30")
    cur.set_result(-1)
    assert cur.fetchone() == (30,)
    cur.set_result(-3)
    assert cur.fetchone() == (10,)


def test_set_result_returns_self_for_chaining(conn):
    """set_result returns the cursor so calls can be chained."""
    cur = conn.cursor()
    cur.execute("select 42")
    result = cur.set_result(0)
    assert result is cur


def test_set_result_out_of_range_positive(conn):
    """set_result raises IndexError for a too-large positive index."""
    cur = conn.cursor()
    cur.execute("select 1; select 2")
    with pytest.raises(IndexError):
        cur.set_result(2)


def test_set_result_out_of_range_negative(conn):
    """set_result raises IndexError for a too-large negative index."""
    cur = conn.cursor()
    cur.execute("select 1; select 2")
    with pytest.raises(IndexError):
        cur.set_result(-3)


def test_set_result_rowcount(conn):
    """set_result updates rowcount to match the selected result set."""
    cur = conn.cursor()
    cur.execute("select generate_series(1,5); select generate_series(1,2)")
    cur.set_result(0)
    assert cur.rowcount == 5
    cur.set_result(1)
    assert cur.rowcount == 2


def test_set_result_after_executemany_returning(conn):
    """set_result works across results produced by executemany with returning."""
    cur = conn.cursor()
    cur.executemany(
        "select %s::int",
        [(1,), (2,), (3,)],
        returning=True,
    )
    cur.set_result(0)
    assert cur.fetchone() == (1,)
    cur.set_result(2)
    assert cur.fetchone() == (3,)
