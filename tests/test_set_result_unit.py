"""
Fail-to-pass behavioral tests for set_result().

The evaluator patches source files without reinstalling the package, so we
load set_result() from the patched source via AST extraction and exercise it
against a minimal mock cursor — no DB connection required.
"""
import ast
import asyncio
import os
import pytest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TESTS_DIR)
_PKG_DIR = os.path.join(_REPO_ROOT, 'psycopg', 'psycopg')

CURSOR_SYNC = os.path.join(_PKG_DIR, 'cursor.py')
CURSOR_ASYNC = os.path.join(_PKG_DIR, 'cursor_async.py')


class _MockResult:
    """Stands in for a real PGresult object."""


class _MockCursor:
    """Minimal cursor stub that mirrors the BaseCursor contract.

    _results (list of result objects) and _select_current_result(i) are
    declared in BaseCursor.__slots__ and BaseCursor._select_current_result()
    in _cursor_base.py.  They are the established internal API that
    set_result() is expected to call — not arbitrary implementation details.
    Any correct psycopg implementation of set_result() must use them.
    """

    def __init__(self, n):
        self._results = [_MockResult() for _ in range(n)]
        self._iresult = 0

    def _select_current_result(self, i):
        self._iresult = i


def _extract_fn(path, is_async):
    """Parse the source at *path* and return the set_result function object.

    Strips type annotations so Self/other typing names don't need to be in
    scope when the extracted snippet is exec'd.
    """
    with open(path) as fh:
        src = fh.read()
    tree = ast.parse(src)
    cls = ast.AsyncFunctionDef if is_async else ast.FunctionDef
    for node in ast.walk(tree):
        if isinstance(node, cls) and node.name == 'set_result':
            node.returns = None
            for arg in node.args.args:
                arg.annotation = None
            mod = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(mod)
            ns: dict = {}
            exec(compile(mod, path, 'exec'), ns)
            return ns['set_result']
    return None


@pytest.fixture(scope='module')
def sync_fn():
    fn = _extract_fn(CURSOR_SYNC, is_async=False)
    if fn is None:
        pytest.fail("set_result not found in cursor.py — [sol] not applied")
    return fn


@pytest.fixture(scope='module')
def async_fn():
    fn = _extract_fn(CURSOR_ASYNC, is_async=True)
    if fn is None:
        pytest.fail("set_result not found in cursor_async.py — [sol] not applied")
    return fn


# ── sync Cursor ────────────────────────────────────────────────────────────


def test_sync_selects_first_result(sync_fn):
    cur = _MockCursor(3)
    sync_fn(cur, 0)
    assert cur._iresult == 0


def test_sync_selects_middle_result(sync_fn):
    cur = _MockCursor(3)
    sync_fn(cur, 1)
    assert cur._iresult == 1


def test_sync_selects_last_result(sync_fn):
    cur = _MockCursor(3)
    sync_fn(cur, 2)
    assert cur._iresult == 2


def test_sync_negative_index_last(sync_fn):
    cur = _MockCursor(3)
    sync_fn(cur, -1)
    assert cur._iresult == 2


def test_sync_negative_index_first(sync_fn):
    cur = _MockCursor(3)
    sync_fn(cur, -3)
    assert cur._iresult == 0


def test_sync_out_of_range_raises(sync_fn):
    cur = _MockCursor(2)
    with pytest.raises(IndexError):
        sync_fn(cur, 2)


def test_sync_negative_out_of_range_raises(sync_fn):
    cur = _MockCursor(2)
    with pytest.raises(IndexError):
        sync_fn(cur, -3)


def test_sync_empty_results_raises(sync_fn):
    cur = _MockCursor(0)
    with pytest.raises(IndexError):
        sync_fn(cur, 0)


def test_sync_returns_self(sync_fn):
    cur = _MockCursor(2)
    assert sync_fn(cur, 0) is cur


# ── async Cursor ───────────────────────────────────────────────────────────


def test_async_selects_result(async_fn):
    cur = _MockCursor(3)
    asyncio.run(async_fn(cur, 1))
    assert cur._iresult == 1


def test_async_negative_index(async_fn):
    cur = _MockCursor(3)
    asyncio.run(async_fn(cur, -1))
    assert cur._iresult == 2


def test_async_out_of_range_raises(async_fn):
    cur = _MockCursor(2)
    with pytest.raises(IndexError):
        asyncio.run(async_fn(cur, 5))


def test_async_returns_self(async_fn):
    cur = _MockCursor(2)
    assert asyncio.run(async_fn(cur, 0)) is cur
