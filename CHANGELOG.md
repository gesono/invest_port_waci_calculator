# Changelog

## v1.1 – 6 October 2026
- Added `engine/waci.py`: the WACI calculation in plain Python, with a step-by-step explanation for learning, a CSV loader matching `docs/import_template.csv`, and a printed report.
- Added `tests/test_waci.py`: checks the Python results match the calculator and the Excel workbook (125.33 and 771.43 for the fictional example).

## v1.0 – 5 October 2026
- First public version of the browser calculator.
- Manual entry of fund name, amount, WACI (Scope 1+2 and Scope 1+2+3), $/€ label, data coverage and figure date.
- Separate results for each scope; coverage gate at 70%; weighted fund data coverage; date and plausibility flags.
- Paste/import from Excel or semicolon-separated text, with European number and date formats; duplicate fund names update the existing row.
- Companion Excel workbook (`docs/waci_sample_calculation.xlsx`) reproducing the calculation with fictional data.
