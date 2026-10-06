"""
waci.py — Portfolio Weighted Average Carbon Intensity (WACI), explained step by step
====================================================================================

This script is the Python twin of the browser calculator (index.html) and the
Excel workbook (docs/waci_sample_calculation.xlsx). All three follow the same
rules and give the same results for the same inputs, so you can learn the
method in whichever format you prefer and cross-check one against another.

It uses only the Python standard library: no pandas, no installs needed.

Run it
------
    python engine/waci.py                          # the fictional example
    python engine/waci.py docs/import_template.csv # your own funds from a CSV file

What is WACI?
-------------
Weighted Average Carbon Intensity measures how exposed a portfolio is to
carbon-intensive companies. For ONE company:

    carbon intensity = greenhouse gas emissions (tCO2e) / revenue ($m or €m)

For ONE fund, the fund manager (or its data provider, e.g. MSCI) takes the
weighted average of that intensity across the fund's holdings and publishes it
on the factsheet, typically as "tCO2e per $1m of revenue". The TCFD recommends
this metric, and SFDR PAI indicator 3 is a Scope 1+2+3 version of it in €.

This script does NOT recalculate each fund from company data. It takes the
figure each fund PUBLISHES and combines those figures into one PORTFOLIO
figure. Because WACI is itself a weighted average, the portfolio WACI is simply
the value-weighted average of the funds' WACIs.

The method in six steps
-----------------------
The step numbers below are used in the comments throughout the code, and match
the columns of the 'WACI calculation' tab in the Excel workbook.

  STEP 1  Add up the whole portfolio.
          total value = sum of all fund amounts

  STEP 2  Keep only the funds that publish a figure for this scope.
          Funds with no figure are NOT given zero, and NOT estimated.
          They are left out and reported as a gap.
          included value = sum of amounts of funds with a figure
                                                  (Excel columns I and J / N and O)

  STEP 3  Measure how much of the portfolio has data.
          coverage = included value / total value
          70% or more -> result is shown normally
          below 70%   -> result is marked "indicative only"

  STEP 4  Rescale each included fund's share so the shares add up to 100%.
          share(i) = amount(i) / included value       (Excel column K / P)

  STEP 5  Weight each fund's WACI by its share.
          contribution(i) = share(i) x WACI(i)        (Excel column L / Q)

  STEP 6  Add up the contributions. This is the portfolio WACI.
          portfolio WACI = sum of contributions

Steps 2-6 are done twice, once for Scope 1+2 and once for Scope 1+2+3, and the
two are NEVER combined. Scope 3 figures are usually several times larger than
Scope 1+2, so blending them would make the number meaningless.

Quality checks reported alongside the result
--------------------------------------------
  * Currency of the denominator: funds publish WACI per $1m OR per €1m of
    revenue. Version 1 does no currency conversion. If a scope mixes the two,
    the result is flagged as approximate.
  * Fund data coverage: the share of each fund's OWN holdings its WACI is based
    on, as the fund reports it. Shown as a value-weighted average.
  * Figure dates: the oldest date used, plus flags for figures older than
    12 months or with no date at all.

Limitations
-----------
This is fund-level aggregation of published figures, not a bottom-up PCAF
calculation. Each fund's own data gaps and methodology are inherited as is.
For information and education only; not investment advice.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Settings. Kept as named constants so the rules are visible and easy to change.
# ---------------------------------------------------------------------------
COVERAGE_THRESHOLD = 0.70      # below this, a portfolio result is "indicative only"
LOW_FUND_DATA_COVERAGE = 0.70  # a fund reporting less than this is flagged
STALE_AFTER_DAYS = 365         # figures older than ~12 months are flagged

SCOPES = {
    # key       : (label shown in the report, attribute name on Fund)
    "scope_12":  ("Scope 1+2", "waci_scope_12"),
    "scope_123": ("Scope 1+2+3", "waci_scope_123"),
}


# ---------------------------------------------------------------------------
# The input: one Fund per holding
# ---------------------------------------------------------------------------
@dataclass
class Fund:
    """One holding in the portfolio, with the figures exactly as the fund publishes them.

    name            Fund name, as you want it to appear in the report.
    amount          How much you hold, in your portfolio currency (EUR or USD).
    waci_scope_12   Published Scope 1+2 WACI, or None if the fund doesn't publish one.
    waci_scope_123  Published Scope 1+2+3 WACI, or None.
    denominator     "USD" if the WACI is per $1m of revenue, "EUR" if per €1m.
                    This is a label only; no conversion is applied.
    data_coverage   Share of the fund's holdings its WACI is based on, as a
                    fraction (0.98 = 98%), or None if not reported.
    figure_date     Date the figure refers to, or None.
    """
    name: str
    amount: float
    waci_scope_12: float | None = None
    waci_scope_123: float | None = None
    denominator: str = "USD"
    data_coverage: float | None = None
    figure_date: date | None = None


# ---------------------------------------------------------------------------
# The output: everything we work out for one scope
# ---------------------------------------------------------------------------
@dataclass
class Contribution:
    """One fund's line in the working table (the Excel 'working' columns)."""
    name: str
    amount: float
    waci: float
    share: float          # STEP 4 result
    contribution: float   # STEP 5 result


@dataclass
class ScopeResult:
    """The results for one scope (Scope 1+2 or Scope 1+2+3)."""
    label: str
    total_value: float                 # STEP 1
    included_value: float              # STEP 2
    coverage: float                    # STEP 3
    portfolio_waci: float | None       # STEP 6 (None if no fund has a figure)
    cross_check: float | None          # the same answer, worked out a second way
    lines: list[Contribution] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    denominator_note: str = ""
    weighted_data_coverage: float | None = None
    oldest_date: date | None = None
    flags: list[str] = field(default_factory=list)

    @property
    def coverage_label(self) -> str:
        if self.portfolio_waci is None:
            return "No figures"
        if self.coverage >= COVERAGE_THRESHOLD:
            return f"OK ({COVERAGE_THRESHOLD:.0%} or more)"
        return f"Indicative only (below {COVERAGE_THRESHOLD:.0%})"


# ---------------------------------------------------------------------------
# The calculation
# ---------------------------------------------------------------------------
def calculate_scope(funds: list[Fund], scope: str, today: date | None = None) -> ScopeResult:
    """Run steps 1-6 for one scope and attach the quality checks."""
    label, attribute = SCOPES[scope]
    today = today or date.today()

    # STEP 1 - Add up the whole portfolio.
    # Every fund counts here, including those with no carbon figure, because
    # coverage (step 3) must show how much of YOUR money the result describes.
    total_value = sum(f.amount for f in funds if f.amount > 0)

    # STEP 2 - Keep only the funds that publish a figure for this scope.
    # getattr(f, attribute) reads f.waci_scope_12 or f.waci_scope_123.
    # A missing figure (None) or zero means "no figure": the fund is excluded,
    # never treated as zero emissions and never estimated.
    with_figure = [f for f in funds if f.amount > 0 and (getattr(f, attribute) or 0) > 0]
    excluded = [f.name for f in funds if f not in with_figure]
    included_value = sum(f.amount for f in with_figure)

    # STEP 3 - Coverage: how much of the portfolio has data.
    coverage = included_value / total_value if total_value > 0 else 0.0

    result = ScopeResult(label=label, total_value=total_value, included_value=included_value,
                         coverage=coverage, portfolio_waci=None, cross_check=None, excluded=excluded)
    if not with_figure:
        return result  # nothing to average

    # STEP 4 and STEP 5 - Rescale each share to the included value, then
    # weight each fund's WACI by that share.
    # Dividing by included_value (not total_value) is the "rescaling": the
    # shares of the included funds now add up to exactly 100%.
    for f in with_figure:
        waci = getattr(f, attribute)
        share = f.amount / included_value          # STEP 4
        contribution = share * waci                # STEP 5
        result.lines.append(Contribution(f.name, f.amount, waci, share, contribution))

    # STEP 6 - The portfolio WACI is the sum of the contributions.
    result.portfolio_waci = sum(line.contribution for line in result.lines)

    # CROSS-CHECK - The same number, worked out a second way:
    #   sum(amount x WACI) / sum(amount)
    # This is what Excel's SUMPRODUCT does. If the two disagree, something is wrong.
    result.cross_check = sum(f.amount * getattr(f, attribute) for f in with_figure) / included_value

    # QUALITY CHECK 1 - Currency of the WACI denominator (label only, no conversion).
    denominators = {f.denominator for f in with_figure}
    if len(denominators) > 1:
        result.denominator_note = "Mixed $ and € - approximate"
        result.flags.append("Funds mix per-$1m and per-€1m figures; no conversion applied.")
    else:
        result.denominator_note = "All per €1m revenue" if denominators == {"EUR"} else "All per $1m revenue"

    # QUALITY CHECK 2 - Fund data coverage, weighted by value.
    # Only funds that REPORT a coverage figure enter this average.
    reported = [f for f in with_figure if f.data_coverage is not None]
    if reported:
        reported_value = sum(f.amount for f in reported)
        result.weighted_data_coverage = sum(f.amount * f.data_coverage for f in reported) / reported_value
    for f in reported:
        if f.data_coverage < LOW_FUND_DATA_COVERAGE:
            result.flags.append(f"{f.name}: fund data coverage only {f.data_coverage:.0%}.")

    # QUALITY CHECK 3 - Dates: oldest figure, stale figures, undated figures.
    dated = [f for f in with_figure if f.figure_date]
    if dated:
        result.oldest_date = min(f.figure_date for f in dated)
    for f in dated:
        if (today - f.figure_date).days > STALE_AFTER_DAYS:
            result.flags.append(f"{f.name}: figure dated {f.figure_date:%d %b %Y} is over 12 months old.")
    for f in with_figure:
        if not f.figure_date:
            result.flags.append(f"{f.name}: figure has no date.")

    return result


def calculate_portfolio(funds: list[Fund], today: date | None = None) -> dict[str, ScopeResult]:
    """Run the calculation for both scopes, kept strictly separate."""
    return {scope: calculate_scope(funds, scope, today) for scope in SCOPES}


# ---------------------------------------------------------------------------
# Reading your own funds from a CSV (same format as docs/import_template.csv)
# ---------------------------------------------------------------------------
def _number(text: str) -> float | None:
    """Turn '1 234,5', '1234.5' or '' into a number (or None).

    Handles European formats: spaces as thousand separators and a comma as the
    decimal mark, as used on Finnish and other European factsheets.
    """
    text = (text or "").strip().replace("\u00a0", "").replace(" ", "").replace("%", "")
    if not text:
        return None
    if "," in text and "." in text:      # e.g. 1.234,5 -> 1234.5
        text = text.replace(".", "").replace(",", ".")
    else:                                # e.g. 58,4 -> 58.4
        text = text.replace(",", ".")
    return float(text)


def load_funds_from_csv(path: str | Path) -> list[Fund]:
    """Read a semicolon-separated file laid out like docs/import_template.csv.

    Columns, in order: fund name; amount; WACI Scope 1+2; WACI Scope 1+2+3;
    WACI per (USD/EUR); data coverage %; figure date (YYYY-MM-DD).
    """
    funds = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle, delimiter=";")
        next(reader, None)  # skip the header row
        for row in reader:
            if not row or not row[0].strip():
                continue
            row += [""] * (7 - len(row))  # pad short rows
            coverage = _number(row[5])
            funds.append(Fund(
                name=row[0].strip(),
                amount=_number(row[1]) or 0.0,
                waci_scope_12=_number(row[2]),
                waci_scope_123=_number(row[3]),
                denominator=(row[4].strip().upper() or "USD"),
                data_coverage=coverage / 100 if coverage is not None else None,  # 98 -> 0.98
                figure_date=date.fromisoformat(row[6].strip()) if row[6].strip() else None,
            ))
    return funds


# ---------------------------------------------------------------------------
# The fictional example (identical to the calculator and the Excel workbook)
# ---------------------------------------------------------------------------
EXAMPLE_FUNDS = [
    Fund("Example Global Equity Fund",    10_000,  95.0,  620.0, "USD", 0.99, date(2026, 8, 31)),
    Fund("Example Europe Equity Fund",     6_000,  80.0,  None,  "USD", 1.00, date(2026, 8, 31)),
    Fund("Example Emerging Markets Fund",  4_000, 260.0, 1150.0, "USD", 0.95, date(2026, 7, 31)),
    Fund("Example Clean Energy Fund",      2_500, 140.0,  None,  "USD", 0.92, date(2026, 6, 30)),
    Fund("Example Bond Fund",              2_000,  None,  None,  "USD", None, None),
]
# Expected results:  Scope 1+2   -> WACI 125.33, coverage 91.8%
#                    Scope 1+2+3 -> WACI 771.43, coverage 57.1% (indicative only)


# ---------------------------------------------------------------------------
# A readable report
# ---------------------------------------------------------------------------
def print_report(results: dict[str, ScopeResult], currency: str = "EUR") -> None:
    for r in results.values():
        print("=" * 78)
        print(f"WACI {r.label}")
        print("=" * 78)
        if r.portfolio_waci is None:
            print("No funds have a figure for this scope.\n")
            continue

        # The working table: one line per included fund (steps 4 and 5).
        print(f"{'Fund':<32}{'Amount':>12}{'WACI':>9}{'Share':>9}{'Contribution':>14}")
        for line in r.lines:
            print(f"{line.name[:31]:<32}{line.amount:>12,.2f}{line.waci:>9.1f}"
                  f"{line.share:>9.1%}{line.contribution:>14.2f}")
        print(f"{'Total':<32}{r.included_value:>12,.2f}{'':>9}"
              f"{sum(l.share for l in r.lines):>9.1%}{r.portfolio_waci:>14.2f}")
        print()

        print(f"  Step 1  Total portfolio value     {r.total_value:,.2f} {currency}")
        print(f"  Step 2  Value with a figure       {r.included_value:,.2f} {currency}")
        print(f"  Step 3  Portfolio coverage        {r.coverage:.1%}  -> {r.coverage_label}")
        print(f"  Step 6  PORTFOLIO WACI            {r.portfolio_waci:.2f} tCO2e per $/€1m revenue")
        print(f"          Cross-check (SUMPRODUCT)  {r.cross_check:.2f}")
        print(f"          WACI currency             {r.denominator_note}")
        wdc = f"{r.weighted_data_coverage:.1%}" if r.weighted_data_coverage is not None else "Not reported"
        print(f"          Fund data coverage        {wdc} (value-weighted)")
        print(f"          Oldest figure date        {r.oldest_date:%d %b %Y}" if r.oldest_date
              else "          Oldest figure date        No dates")
        if r.excluded:
            print(f"          Not included (gaps)       {', '.join(r.excluded)}")
        for flag in r.flags:
            print(f"  ! {flag}")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        portfolio = load_funds_from_csv(sys.argv[1])
        print(f"Loaded {len(portfolio)} funds from {sys.argv[1]}\n")
    else:
        portfolio = EXAMPLE_FUNDS
        print("Using the fictional example funds (pass a CSV path to use your own).\n")
    print_report(calculate_portfolio(portfolio))
