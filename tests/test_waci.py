"""
Checks that the Python engine gives the same answers as the browser calculator
and the Excel workbook for the fictional example.

Run with:   python tests/test_waci.py      (or: pytest)
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from waci import EXAMPLE_FUNDS, Fund, calculate_portfolio  # noqa: E402

TODAY = date(2026, 10, 6)  # fixed, so the date checks don't change over time


def test_scope_12_matches_excel():
    r = calculate_portfolio(EXAMPLE_FUNDS, TODAY)["scope_12"]
    assert round(r.portfolio_waci, 2) == 125.33
    assert round(r.coverage, 3) == 0.918
    assert r.coverage_label.startswith("OK")
    assert r.excluded == ["Example Bond Fund"]


def test_scope_123_is_indicative_only():
    r = calculate_portfolio(EXAMPLE_FUNDS, TODAY)["scope_123"]
    assert round(r.portfolio_waci, 2) == 771.43
    assert round(r.coverage, 3) == 0.571
    assert r.coverage_label.startswith("Indicative only")


def test_cross_check_agrees():
    for r in calculate_portfolio(EXAMPLE_FUNDS, TODAY).values():
        assert abs(r.portfolio_waci - r.cross_check) < 1e-9


def test_shares_add_up_to_100_percent():
    for r in calculate_portfolio(EXAMPLE_FUNDS, TODAY).values():
        assert abs(sum(line.share for line in r.lines) - 1) < 1e-9


def test_mixed_currency_is_flagged():
    funds = [Fund("A", 100, 50, denominator="USD"), Fund("B", 100, 60, denominator="EUR")]
    r = calculate_portfolio(funds, TODAY)["scope_12"]
    assert r.denominator_note.startswith("Mixed")


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
            print("passed:", name)
