# Methodology

This page explains exactly how the calculator turns fund-level figures into a portfolio figure, and what it deliberately does not do.

## 1. The metric

**Weighted average carbon intensity (WACI)** measures a portfolio's exposure to carbon-intensive companies. For a single fund, it is the holdings-weighted average of each company's greenhouse gas emissions divided by its revenue, expressed in **tonnes of CO2e per $1m (or €1m) of revenue**. This is the definition recommended by the TCFD and used on most fund factsheets.

The calculator does not compute company-level WACI itself. It takes each fund's **published** WACI and combines them.

## 2. Portfolio WACI

For each scope separately:

```
Portfolio WACI = Σ ( wᵢ × WACIᵢ )        over funds i that have a figure

wᵢ = amountᵢ / Σ amount of funds that have a figure
```

Because WACI is a weighted average, the portfolio WACI is the value-weighted average of the funds' WACIs.

### Worked example (fictional funds, Scope 1+2)

| Fund | Amount (€) | WACI | Rescaled share | Contribution |
|---|---|---|---|---|
| Global Equity | 10,000 | 95.0 | 44.4% | 42.22 |
| Europe Equity | 6,000 | 80.0 | 26.7% | 21.33 |
| Emerging Markets | 4,000 | 260.0 | 17.8% | 46.22 |
| Clean Energy | 2,500 | 140.0 | 11.1% | 15.56 |
| Bond Fund | 2,000 | – | excluded | – |
| **Total** | **24,500** | | **100%** | **125.33** |

Coverage = 22,500 ÷ 24,500 = **91.8%**.

## 3. Rescaling for coverage

Funds without a figure are left out and the remaining shares are rescaled to 100%. This is the standard treatment for intensity metrics: a missing fund is not assumed to have zero emissions, nor is any value estimated for it.

The excluded share is always reported as **portfolio coverage**:

```
Portfolio coverage = value of funds with a figure / total portfolio value
```

| Coverage | Label |
|---|---|
| 70% or more | Result shown normally |
| Below 70% | *Indicative only* |

## 4. Scopes are never combined

Scope 1+2 and Scope 1+2+3 are calculated in separate sections. Scope 3 figures are typically several times larger than Scope 1+2, so blending them would distort the result. A fund can contribute to both sections if it publishes both figures.

## 5. Currency of the WACI denominator

Funds publish WACI per **$1m** or per **€1m** of revenue. In v1:

- each figure is labelled with its denominator;
- **no currency conversion is applied**;
- if one section mixes $- and €-denominated figures, the result is flagged as mixed and approximate. With EUR/USD around 1.15, the same portfolio reads roughly 15% different depending on the denominator.

Allocations are entered in one currency (EUR or USD), as shown by the user's bank or broker, so no conversion is needed for weights either.

## 6. Fund data coverage

Each fund's WACI is itself based on the share of its holdings that have emissions data. Where the fund reports this (often called "coverage"), it can be entered and is shown per fund, together with a value-weighted average:

```
Weighted data coverage = Σ ( amountᵢ × coverageᵢ ) / Σ amountᵢ     over funds with a reported coverage
```

Funds reporting coverage below 70% are flagged.

## 7. Dates

Every figure carries the date it refers to. The results show the date range of the figures used; figures older than 12 months, or without a date, are flagged. Where a factsheet gives both a data date and a holdings date, the holdings date is the better choice, since that is the portfolio the WACI describes.

## 8. Limitations

- **Fund-level aggregation, not PCAF.** The calculator combines figures already published by funds. It does not attribute company emissions bottom-up as in the PCAF Global GHG Accounting and Reporting Standard.
- **Each fund's own coverage gaps are inherited.** A fund's WACI already excludes its holdings without data.
- **Methodologies differ between fund managers and data providers.** Figures from different sources may not be perfectly comparable even within the same scope.
- **No currency conversion in v1.** See section 5.
- **Not investment advice.**

## 9. Glossary

| Term | Meaning |
|---|---|
| Scope 1 | Direct emissions from a company's own operations |
| Scope 2 | Indirect emissions from purchased electricity, heat and steam |
| Scope 3 | All other indirect emissions in the value chain |
| tCO2e | Tonnes of CO2 equivalent |
| SFDR PAI 3 | "GHG intensity of investee companies" under the EU Sustainable Finance Disclosure Regulation: Scope 1+2+3 per €1m of revenue |
