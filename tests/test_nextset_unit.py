"""
Pass-to-pass regression tests for cursor result-set navigation.

Tests nextset() from _cursor_base.py via AST extraction against a minimal
mock cursor — no DB connection required.  These tests exercise the cursor
result-set navigation area and must continue to pass after set_result() is
added.

_results and _select_current_result are BaseCursor contract attributes
(declared in _cursor_base.py), not arbitrary internal names — any correct
psycopg implementation uses them.
"""
import ast
import os
import pytest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TESTS_DIR)
_PKG_DIR = os.path.join(_REPO_ROOT, 'psycopg', 'psycopg')

CURSOR_BASE = os.path.join(_PKG_DIR, '_cursor_base.py')


class _MockResult:
    """Stands in for a real PGresult object."""


class _MockCursor:
    """Minimal cursor stub mirroring BaseCursor's navigation attributes."""

    def __init__(self, n):
        self._results = [_MockResult() for _ in range(n)]
        self._iresult = 0

    def _select_current_result(self, i):
        self._iresult = i


def _extract_fn(path, name):
    with open(path) as fh:
        src = fh.read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            node.returns = None
            for arg in node.args.args:
                arg.annotation = None
            mod = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(mod)
            ns: dict = {}
            exec(compile(mod, path, 'exec'), ns)
            return ns[name]
    return None


@pytest.fixture(scope='module')
def nextset_fn():
    fn = _extract_fn(CURSOR_BASE, 'nextset')
    if fn is None:
        pytest.fail("nextset not found in _cursor_base.py")
    return fn


def test_nextset_returns_true_when_next_exists(nextset_fn):
    cur = _MockCursor(3)
    result = nextset_fn(cur)
    assert result is True


def test_nextset_advances_iresult(nextset_fn):
    cur = _MockCursor(3)
    nextset_fn(cur)
    assert cur._iresult == 1


def test_nextset_returns_falsy_at_last_result(nextset_fn):
    cur = _MockCursor(1)
    result = nextset_fn(cur)
    assert not result


def test_nextset_does_not_advance_past_last(nextset_fn):
    cur = _MockCursor(2)
    nextset_fn(cur)
    nextset_fn(cur)
    assert cur._iresult == 1


def test_nextset_single_result_stays_at_zero(nextset_fn):
    cur = _MockCursor(1)
    nextset_fn(cur)
    assert cur._iresult == 0


def test_nextset_sequential_advance(nextset_fn):
    cur = _MockCursor(3)
    assert nextset_fn(cur) is True
    assert cur._iresult == 1
    assert nextset_fn(cur) is True
    assert cur._iresult == 2
    assert not nextset_fn(cur)
    assert cur._iresult == 2
