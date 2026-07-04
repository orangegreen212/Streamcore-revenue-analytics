"""
Generates synthetic subscription data for StreamCore, a fictional SaaS company.
Creates 36 months of customer signups, plans, churn and revenue.
"""
import numpy as np
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

np.random.seed(42)

START_MONTH = date(2023, 1, 1)
END_MONTH = date(2025, 12, 1)
N_MONTHS = (END_MONTH.year - START_MONTH.year) * 12 + (END_MONTH.month - START_MONTH.month) + 1

COUNTRIES = {
    "United States": 1.00, "United Kingdom": 0.85, "Germany": 0.80,
    "Canada": 0.90, "France": 0.75, "Brazil": 0.45, "India": 0.30,
    "Australia": 0.88, "Mexico": 0.40, "Netherlands": 0.82
}
COUNTRY_WEIGHTS = {"United States": 0.32, "United Kingdom": 0.12, "Germany": 0.10,
                   "Canada": 0.08, "France": 0.07, "Brazil": 0.09, "India": 0.10,
                   "Australia": 0.05, "Mexico": 0.04, "Netherlands": 0.03}

PLANS = {
    "Basic":    {"price": 9.99,  "weight": 0.45, "churn_base": 0.055},
    "Standard": {"price": 15.99, "weight": 0.35, "churn_base": 0.035},
    "Premium":  {"price": 22.99, "weight": 0.15, "churn_base": 0.020},
    "Family":   {"price": 27.99, "weight": 0.05, "churn_base": 0.018},
}

SEGMENTS = ["Consumer", "SMB", "Enterprise"]
SEGMENT_WEIGHTS = [0.70, 0.22, 0.08]


def month_range(start, n):
    return [start + relativedelta(months=i) for i in range(n)]


months = month_range(START_MONTH, N_MONTHS)

# new customers per month, with seasonality and a slowdown in the last 2 quarters
base_new = 1800
growth_rate = 0.028
seasonal = {1: 1.15, 2: 0.95, 3: 1.0, 4: 0.98, 5: 0.95, 6: 0.92,
            7: 0.90, 8: 0.93, 9: 1.05, 10: 1.08, 11: 1.20, 12: 1.35}

new_customers_by_month = []
val = base_new
for i, m in enumerate(months):
    val_this = val * seasonal[m.month]
    months_from_end = N_MONTHS - i
    if months_from_end <= 6:
        slowdown = 0.80 - (0.03 * (6 - months_from_end))
        val_this *= slowdown
    new_customers_by_month.append(int(val_this))
    val *= (1 + growth_rate)

# generate customers
countries_list = list(COUNTRY_WEIGHTS.keys())
countries_p = list(COUNTRY_WEIGHTS.values())
plans_list = list(PLANS.keys())
plans_p = [PLANS[p]["weight"] for p in plans_list]

customers = []
cust_id = 100000
for m, n_new in zip(months, new_customers_by_month):
    countries_choice = np.random.choice(countries_list, size=n_new, p=countries_p)
    plans_choice = np.random.choice(plans_list, size=n_new, p=plans_p)
    segments_choice = np.random.choice(SEGMENTS, size=n_new, p=SEGMENT_WEIGHTS)
    for i in range(n_new):
        cust_id += 1
        customers.append({
            "customer_id": cust_id,
            "signup_date": m,
            "signup_cohort": m.strftime("%Y-%m"),
            "country": countries_choice[i],
            "initial_plan": plans_choice[i],
            "segment": segments_choice[i],
        })

customers_df = pd.DataFrame(customers)

# simulate month by month subscription life for each customer
SEGMENT_CHURN_MULT = {"Consumer": 1.15, "SMB": 0.90, "Enterprise": 0.55}
PLAN_ORDER = ["Basic", "Standard", "Premium", "Family"]


def tenure_churn_multiplier(tenure_months):
    if tenure_months == 0:
        return 1.6
    elif tenure_months <= 3:
        return 1.3
    elif tenure_months <= 6:
        return 1.05
    elif tenure_months <= 12:
        return 0.85
    else:
        return 0.65


subscription_records = []

for c in customers_df.to_dict("records"):
    signup_idx = months.index(c["signup_date"])
    current_plan = c["initial_plan"]
    tenure = 0
    country_mult = COUNTRIES[c["country"]]
    seg_mult = SEGMENT_CHURN_MULT[c["segment"]]

    for m_idx in range(signup_idx, N_MONTHS):
        m = months[m_idx]
        base_churn = PLANS[current_plan]["churn_base"]
        churn_prob = base_churn * seg_mult * tenure_churn_multiplier(tenure)

        months_from_end = N_MONTHS - m_idx
        if months_from_end <= 6:
            churn_prob *= 1.20
        churn_prob = min(churn_prob, 0.35)

        will_churn = np.random.random() < churn_prob
        price = PLANS[current_plan]["price"] * country_mult

        subscription_records.append({
            "customer_id": c["customer_id"],
            "month": m.strftime("%Y-%m"),
            "month_date": m,
            "plan": current_plan,
            "segment": c["segment"],
            "country": c["country"],
            "mrr": round(price, 2),
            "tenure_months": tenure,
            "event_type": "new" if tenure == 0 else "recurring",
            "is_churned_this_month": will_churn,
        })

        if will_churn:
            break

        # occasional plan upgrade or downgrade every 6 months
        if tenure > 0 and tenure % 6 == 0:
            r = np.random.random()
            idx_plan = PLAN_ORDER.index(current_plan)
            if r < 0.08 and idx_plan < len(PLAN_ORDER) - 1:
                current_plan = PLAN_ORDER[idx_plan + 1]
            elif r > 0.96 and idx_plan > 0:
                current_plan = PLAN_ORDER[idx_plan - 1]

        tenure += 1

subs_df = pd.DataFrame(subscription_records)

customers_df.to_csv("customers.csv", index=False)
subs_df.to_csv("subscriptions_monthly.csv", index=False)

print(f"customers: {customers_df.shape}")
print(f"subscriptions: {subs_df.shape}")
