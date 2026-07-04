"""
Revenue analysis for StreamCore.
Builds cohort retention, LTV, MRR waterfall, churn trend and a simple forecast.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.holtwinters import ExponentialSmoothing

plt.rcParams["figure.dpi"] = 110
sns.set_style("whitegrid")

customers = pd.read_csv("customers.csv")
subs = pd.read_csv("subscriptions_monthly.csv")
subs["month_date"] = pd.to_datetime(subs["month_date"])

# monthly MRR and growth rate
monthly = subs.groupby("month").agg(mrr=("mrr", "sum"),
                                     active=("customer_id", "nunique")).reset_index()
monthly["mom_growth"] = monthly["mrr"].pct_change() * 100

fig, ax1 = plt.subplots(figsize=(11, 5))
ax1.bar(monthly["month"], monthly["mrr"] / 1000, color="#3b6fd6", alpha=0.85)
ax1.set_ylabel("MRR ($K)", color="#3b6fd6")
ax1.set_xticks(range(0, len(monthly), 3))
ax1.set_xticklabels(monthly["month"][::3], rotation=45, ha="right")

ax2 = ax1.twinx()
ax2.plot(monthly["month"], monthly["mom_growth"], color="#d63b3b", marker="o", markersize=3)
ax2.set_ylabel("MoM growth (%)", color="#d63b3b")
ax2.axhline(0, color="gray", linewidth=0.6)

plt.title("MRR growth is slowing down")
fig.tight_layout()
plt.savefig("chart_mrr_growth.png", bbox_inches="tight")
plt.close()

# churn rate over time
churn = subs.groupby("month").agg(
    churned=("is_churned_this_month", "sum"),
    active=("customer_id", "nunique")
).reset_index()
churn["churn_pct"] = 100 * churn["churned"] / churn["active"]

fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(churn["month"], churn["churn_pct"], color="#d63b3b", marker="o", markersize=3)
ax.fill_between(churn["month"], churn["churn_pct"], alpha=0.15, color="#d63b3b")
ax.set_xticks(range(0, len(churn), 3))
ax.set_xticklabels(churn["month"][::3], rotation=45, ha="right")
ax.set_ylabel("Churn rate (%)")
ax.set_title("Churn rate went up in the last two quarters")
ax.axvspan(len(churn) - 6, len(churn) - 1, color="orange", alpha=0.12)
plt.tight_layout()
plt.savefig("chart_churn_trend.png", bbox_inches="tight")
plt.close()

# cohort retention heatmap
cohort_data = subs.merge(customers[["customer_id", "signup_cohort"]], on="customer_id")
cohort_sizes = customers.groupby("signup_cohort")["customer_id"].count()

pivot = cohort_data.groupby(["signup_cohort", "tenure_months"])["customer_id"].nunique().unstack(fill_value=0)
retention_pct = pivot.divide(cohort_sizes, axis=0) * 100
retention_pct = retention_pct.loc[:, :12]
valid_cohorts = [c for c in retention_pct.index if c <= "2024-12"]
retention_pct = retention_pct.loc[valid_cohorts]
retention_sample = retention_pct.loc[retention_pct.index[::2]]

fig, ax = plt.subplots(figsize=(11, 8))
sns.heatmap(retention_sample, annot=True, fmt=".0f", cmap="YlGnBu", cbar_kws={"label": "% retained"}, ax=ax)
ax.set_title("Cohort retention by month since signup")
ax.set_xlabel("Months since signup")
ax.set_ylabel("Signup cohort")
plt.tight_layout()
plt.savefig("chart_cohort_heatmap.png", bbox_inches="tight")
plt.close()

# LTV by segment and plan
cust_life = subs.groupby("customer_id").agg(
    lifetime_months=("tenure_months", "max"),
    avg_mrr=("mrr", "mean")
).reset_index()
cust_life["lifetime_months"] += 1
cust_life = cust_life.merge(customers[["customer_id", "segment", "initial_plan"]], on="customer_id")
cust_life["ltv"] = cust_life["avg_mrr"] * cust_life["lifetime_months"]

ltv_summary = cust_life.groupby(["segment", "initial_plan"])["ltv"].mean().reset_index()
ltv_pivot = ltv_summary.pivot(index="initial_plan", columns="segment", values="ltv")
ltv_pivot = ltv_pivot.reindex(["Basic", "Standard", "Premium", "Family"])

fig, ax = plt.subplots(figsize=(9, 5.5))
ltv_pivot.plot(kind="bar", ax=ax, color=["#8ab4f8", "#f6b26b", "#6aa84f"])
ax.set_ylabel("Estimated LTV ($)")
ax.set_title("LTV by plan and segment")
ax.set_xlabel("Plan")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("chart_ltv_by_segment.png", bbox_inches="tight")
plt.close()

# MRR movement (new, expansion, contraction, churn)
subs_sorted = subs.sort_values(["customer_id", "month"])
subs_sorted["prev_mrr"] = subs_sorted.groupby("customer_id")["mrr"].shift(1)


def classify(row):
    if pd.isna(row["prev_mrr"]):
        return "New"
    elif row["mrr"] > row["prev_mrr"]:
        return "Expansion"
    elif row["mrr"] < row["prev_mrr"]:
        return "Contraction"
    else:
        return "Retained"


subs_sorted["movement"] = subs_sorted.apply(classify, axis=1)
subs_sorted["delta"] = subs_sorted["mrr"] - subs_sorted["prev_mrr"].fillna(0)

churned_rows = subs_sorted[subs_sorted["is_churned_this_month"] == True].copy()
churn_by_month = churned_rows.groupby("month")["mrr"].sum().reset_index()
churn_by_month.columns = ["month", "churned_mrr"]

movement_by_month = subs_sorted[subs_sorted["movement"] != "Retained"].groupby(
    ["month", "movement"])["delta"].sum().unstack(fill_value=0)

last12 = sorted(subs["month"].unique())[-12:]
movement_last12 = movement_by_month.loc[movement_by_month.index.isin(last12)]
churn_last12 = churn_by_month[churn_by_month["month"].isin(last12)].set_index("month")["churned_mrr"]

waterfall_df = pd.DataFrame({
    "New": movement_last12.get("New", 0),
    "Expansion": movement_last12.get("Expansion", 0),
    "Contraction": movement_last12.get("Contraction", 0),
    "Churn": -churn_last12.reindex(movement_last12.index, fill_value=0)
})

fig, ax = plt.subplots(figsize=(12, 5.5))
waterfall_df[["New", "Expansion"]].plot(kind="bar", stacked=True, ax=ax, color=["#4a86e8", "#6aa84f"], width=0.7)
waterfall_df[["Contraction", "Churn"]].plot(kind="bar", stacked=True, ax=ax, color=["#f6b26b", "#cc4125"], width=0.7)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_ylabel("MRR movement ($)")
ax.set_title("MRR bridge, last 12 months")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("chart_mrr_waterfall.png", bbox_inches="tight")
plt.close()

# forecast next 6 months
ts = monthly.set_index(pd.to_datetime(monthly["month"]))["mrr"]
model = ExponentialSmoothing(ts, trend="add", seasonal="add", seasonal_periods=12).fit()
forecast = model.forecast(6)

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(ts.index, ts.values / 1000, label="Actual", color="#3b6fd6")
ax.plot(forecast.index, forecast.values / 1000, label="Forecast", color="#d63b3b", linestyle="--", marker="o")
ax.fill_between(forecast.index, forecast.values / 1000 * 0.93, forecast.values / 1000 * 1.07,
                 color="#d63b3b", alpha=0.15)
ax.set_ylabel("MRR ($K)")
ax.set_title("MRR forecast, next 6 months")
ax.legend()
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("chart_forecast.png", bbox_inches="tight")
plt.close()

print("MRR growth last 6 months:", round(monthly["mom_growth"].iloc[-6:].mean(), 2))
print("MRR growth prior 6 months:", round(monthly["mom_growth"].iloc[-12:-6].mean(), 2))
print("Churn last 6 months:", round(churn["churn_pct"].iloc[-6:].mean(), 2))
print("Churn prior 6 months:", round(churn["churn_pct"].iloc[-12:-6].mean(), 2))
