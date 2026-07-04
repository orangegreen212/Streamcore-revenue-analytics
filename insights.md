# Insights and recommendations

## The problem

MRR is still growing, but the growth rate has been dropping. First half of 2025 averaged about 4.2% MRR growth per month. Second half dropped to about 2.2%. ARR ended the year at $9.28M, up 34.9% year over year, but the trend line is clearly bending.

## What's driving it

New customer acquisition did not slow down. The drop in growth traces back almost entirely to churn.

| Period | Avg monthly churn |
|---|---|
| H1 2025 | 3.84% |
| H2 2025 | 4.37% |

Half a point of extra monthly churn across ~55-60k active customers adds up to real MRR loss every month.

Breaking it down by plan and segment shows where the increase actually happened:

| Cut | H1 2025 | H2 2025 | Change |
|---|---|---|---|
| Basic plan | 5.65% | 6.58% | +0.94pp (biggest jump) |
| Standard plan | 3.48% | 4.06% | +0.58pp |
| Premium plan | 1.96% | 2.14% | +0.18pp |
| Family plan | 1.70% | 2.01% | +0.31pp |
| Consumer segment | 4.29% | 4.89% | +0.60pp |
| SMB segment | 3.25% | 3.78% | +0.53pp |
| Enterprise segment | 2.11% | 2.28% | +0.16pp |

Country-level churn went up more or less evenly everywhere (+0.3 to +0.85pp), no single market stands out, so this doesn't look like a regional issue. It looks more like something specific to the entry-level plan or the Consumer segment - a price change, a competitor's offer, or a feature gap.

Cohort retention held up fine across signup months (roughly 57-60% still active at 12 months, consistently, from 2023 through 2024), so newer customers aren't lower quality. The churn increase is hitting the existing customer base, not new signups.

LTV by plan and segment:

| Segment x plan | Avg LTV |
|---|---|
| Enterprise + Family | $312 |
| SMB + Family | $297 |
| Consumer + Family | $284 |
| Enterprise + Premium | $262 |
| ... | ... |
| Consumer + Basic | $70 (lowest) |

Basic/Consumer is both the highest-churn group and the lowest-LTV group. It's also the largest group by volume (Basic is 45% of the customer base), so it has an outsized effect on the aggregate numbers even though each individual customer is low value.

## Recommendations

1. Look into why Basic-plan churn specifically went up in H2 2025 - check for a price change, a competitor promo, or something removed from the plan around mid-2025. Support tickets and cancellation reasons would help here (not something this dataset has).
2. Try a targeted retention offer for Consumer/Basic customers near renewal, instead of a blanket discount. Something like a "Standard Lite" nudge - Standard has less than half the churn rate of Basic for a small price step-up.
3. Shift some acquisition effort toward Family/Premium plans. Lower churn, 3-4x the LTV of Basic. Even a small mix shift helps blended retention without needing to fix the Basic problem directly.
4. Keep investing in Enterprise/SMB - churn there barely moved and LTV is the highest. These segments are only 8% and 22% of the customer base but disproportionately valuable.
5. Track churn by plan, not just company-wide. The overall churn number (4.2%) still looks manageable on its own, but it hides a much sharper issue in one specific segment. A company-wide-only dashboard would have missed this for another quarter or two.

## Forecast

Holt-Winters forecast puts MRR at roughly $862K by June 2026, up from $773K in December 2025 - still growing, just slower than the 2023-2024 pace. If Basic-plan churn gets back down to its H1 2025 level (5.65%), the model suggests recovering something like 1-1.5 points of monthly MRR growth, which compounds meaningfully over 6-12 months.
