# Portfolio WACI Calculator

A free, browser-based calculator that works out the **weighted average carbon intensity (WACI)** of a fund portfolio from the figures funds already publish.

You enter each fund, how much you hold, and the WACI from its factsheet or monthly report. The calculator combines them into a portfolio figure and shows how complete and current the data is. Nothing you type leaves your browser.

**Live demo:** https://gesono.github.io/invest_port_waci_calculator/

> The demo opens with fictional example funds. Replace them with your own.

---

## What it does

| Feature | Detail |
|---|---|
| Portfolio WACI | Sum of (each fund's rescaled share × its WACI) |
| Separate scopes | Scope 1+2 and Scope 1+2+3 get their own results and are never combined |
| Coverage | Share of the portfolio's value that has a figure; below 70% the result is marked *indicative only* |
| Data coverage | Each fund's own reported coverage, plus a value-weighted portfolio average |
| Date checks | Every figure carries its date; figures older than 12 months or undated are flagged |
| Currency label | Each WACI is marked per $1m or per €1m of revenue; mixing the two is flagged (no conversion in v1) |
| Gaps | Funds without a figure are listed, never estimated |
| Import | Paste rows from Excel or semicolon-separated text; handles European number and date formats |
| Privacy | Runs entirely in the browser; data is kept only in your browser's local storage |

## How to use it

1. Open the live demo, or open `index.html` locally in any browser.
2. Choose the currency your amounts are in (EUR or USD).
3. For each fund, enter its name, the amount you hold, and its WACI for Scope 1+2 and/or Scope 1+2+3.
4. Mark whether the fund reports WACI per $1m or €1m of revenue, and add its data coverage and figure date if available.
5. Read the results. Each scope section shows the portfolio WACI, coverage, data coverage, date range and each fund's contribution.

Not sure where to find a fund's WACI? See [docs/how-to-find-waci.md](docs/how-to-find-waci.md).

## Check the maths yourself

[docs/waci_sample_calculation.xlsx](docs/waci_sample_calculation.xlsx) is a formula-driven Excel workbook that reproduces the calculator step by step, using the same fictional example. Change the inputs and every result updates.

Expected results for the example:

| | Scope 1+2 | Scope 1+2+3 |
|---|---|---|
| Portfolio WACI (tCO2e/$1m revenue) | 125.33 | 771.43 |
| Portfolio coverage | 91.8% | 57.1% (indicative only) |

The full method is in [docs/methodology.md](docs/methodology.md).

## Python version

[engine/waci.py](engine/waci.py) is the same calculation in plain Python (standard library only, no installs). It is written for learning: the file opens with a full explanation of the method, and every step in the code is labelled to match the Excel workbook's columns.

```bash
python engine/waci.py                           # run the fictional example
python engine/waci.py docs/import_template.csv  # run your own funds from a CSV
python tests/test_waci.py                       # check it matches 125.33 and 771.43
```

The CSV uses the same semicolon-separated layout as the calculator's paste/import feature, including European number formats.

## Project structure

```
portfolio-waci-calculator/
├── index.html                      the calculator (single self-contained page)
├── engine/
│   └── waci.py                     the same calculation in Python, fully explained
├── tests/
│   └── test_waci.py                checks Python results match the calculator and Excel
├── docs/
│   ├── methodology.md              how the calculation works and its limits
│   ├── how-to-find-waci.md         where fund managers publish WACI
│   ├── waci_sample_calculation.xlsx  worked example in Excel
│   └── import_template.csv         template for the paste/import feature
├── data/
│   └── README.md                   why no fund data is stored in this repo
├── CHANGELOG.md
├── LICENSE                         MIT (code only)
└── .gitignore
```

## Data and licensing

This repository contains **code and fictional example data only**. Carbon metrics shown on fund factsheets are often licensed from third-party providers (for example MSCI ESG Research), whose terms typically allow internal use only and prohibit redistribution. The calculator therefore ships no real fund figures: users enter figures they have access to themselves.

The MIT licence applies to the code in this repository, not to any data a user enters.

## Roadmap

- **v1 (current):** manual entry, Scope 1+2 and 1+2+3 sections, coverage and date checks
- **Next:** optional ISIN field; export results to CSV/PDF; benchmark reference line
- **Later:** a Python engine that reads headline figures from fund documents (SFDR periodic reports, EET files) and calculates holdings-based WACI from company-reported emissions

## Disclaimer

For information only, not investment advice. The calculator aggregates fund-level figures as published; it is not a company-by-company PCAF calculation, and its accuracy depends on the figures entered.

## Licence

[MIT](LICENSE)
