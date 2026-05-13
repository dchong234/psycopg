"""
Fail-to-pass tests for AsyncCursor.set_result().

These tests call set_result() directly on the async cursor and verify:
- valid index selection (positive)
- negative indexing (Python-list style)
- IndexError on out-of-range index
- method chaining (returns cursor itself)
"""
import pytest
import psycopg


async def test_set_result_no_results_raises(aconn):
    """set_result raises IndexError when cursor has no results."""
    cur = aconn.cursor()
    with pytest.raises(IndexError):
        await cur.set_result(0)


async def test_set_result_valid_positive_index(aconn):
    """set_result selects the correct result set by positive index."""
    cur = aconn.cursor()
    await cur.execute("select 'first'; select 'second'")
    await cur.set_result(0)
    assert (await cur.fetchone()) == ("first",)
    await cur.set_result(1)
    assert (await cur.fetchone()) == ("second",)


async def test_set_result_negative_index(aconn):
    """set_result supports negative indexing like Python lists."""
    cur = aconn.cursor()
    await cur.execute("select 10; select 20; select 30")
    await cur.set_result(-1)
    assert (await cur.fetchone()) == (30,)
    await cur.set_result(-3)
    assert (await cur.fetchone()) == (10,)


async def test_set_result_returns_self_for_chaining(aconn):
    """set_result returns the cursor so calls can be chained."""
    cur = aconn.cursor()
    await cur.execute("select 42")
    result = await cur.set_result(0)
    assert result is cur


async def test_set_result_out_of_range_positive(aconn):
    """set_result raises IndexError for a too-large positive index."""
    cur = aconn.cursor()
    await cur.execute("select 1; select 2")
    with pytest.raises(IndexError):
        await cur.set_result(2)


async def test_set_result_out_of_range_negative(aconn):
    """set_result raises IndexError for a too-large negative index."""
    cur = aconn.cursor()
    await cur.execute("select 1; select 2")
    with pytest.raises(IndexError):
        await cur.set_result(-3)


async def test_set_result_rowcount(aconn):
    """set_result updates rowcount to match the selected result set."""
    cur = aconn.cursor()
    await cur.execute("select generate_series(1,5); select generate_series(1,2)")
    await cur.set_result(0)
    assert cur.rowcount == 5
    await cur.set_result(1)
    assert cur.rowcount == 2


async def test_set_result_after_executemany_returning(aconn):
    """set_result works across results produced by executemany with returning."""
    cur = aconn.cursor()
    await cur.executemany(
        "select %s::int",
        [(1,), (2,), (3,)],
        returning=True,
    )
    await cur.set_result(0)
    assert (await cur.fetchone()) == (1,)
    await cur.set_result(2)
    assert (await cur.fetchone()) == (3,)
