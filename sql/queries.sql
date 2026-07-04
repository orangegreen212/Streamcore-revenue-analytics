-- StreamCore revenue analysis
-- Tables: customers, subscriptions_monthly

-- 1. Monthly revenue overview: MRR, ARR, active customers, growth rate
WITH monthly AS (
    SELECT
        month,
        SUM(mrr) AS mrr,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM subscriptions_monthly
    GROUP BY month
)
SELECT
    month,
    ROUND(mrr, 0) AS mrr,
    ROUND(mrr * 12, 0) AS arr,
    active_customers,
    ROUND(mrr / active_customers, 2) AS arpu,
    ROUND(100.0 * (mrr - LAG(mrr) OVER (ORDER BY month)) / LAG(mrr) OVER (ORDER BY month), 2) AS mrr_growth_pct
FROM monthly
ORDER BY month;


-- 2. Revenue by plan (last month)
SELECT
    plan,
    COUNT(DISTINCT customer_id) AS customers,
    ROUND(SUM(mrr), 0) AS mrr,
    ROUND(100.0 * SUM(mrr) / SUM(SUM(mrr)) OVER (), 1) AS pct_of_mrr
FROM subscriptions_monthly
WHERE month = (SELECT MAX(month) FROM subscriptions_monthly)
GROUP BY plan
ORDER BY mrr DESC;


-- 3. Revenue by country (last month)
SELECT
    country,
    COUNT(DISTINCT customer_id) AS customers,
    ROUND(SUM(mrr), 0) AS mrr,
    ROUND(100.0 * SUM(mrr) / SUM(SUM(mrr)) OVER (), 1) AS pct_of_mrr
FROM subscriptions_monthly
WHERE month = (SELECT MAX(month) FROM subscriptions_monthly)
GROUP BY country
ORDER BY mrr DESC;


-- 4. Revenue by segment (last month)
SELECT
    segment,
    COUNT(DISTINCT customer_id) AS customers,
    ROUND(SUM(mrr), 0) AS mrr,
    ROUND(AVG(mrr), 2) AS arpu
FROM subscriptions_monthly
WHERE month = (SELECT MAX(month) FROM subscriptions_monthly)
GROUP BY segment
ORDER BY mrr DESC;


-- 5. MRR movement (new / expansion / contraction / churn)
WITH cust_month AS (
    SELECT
        customer_id,
        month,
        mrr,
        LAG(mrr) OVER (PARTITION BY customer_id ORDER BY month) AS prev_mrr
    FROM subscriptions_monthly
),
classified AS (
    SELECT
        month,
        CASE
            WHEN prev_mrr IS NULL THEN 'New'
            WHEN mrr > prev_mrr THEN 'Expansion'
            WHEN mrr < prev_mrr THEN 'Contraction'
            ELSE 'Retained'
        END AS movement_type,
        mrr - COALESCE(prev_mrr, 0) AS mrr_delta
    FROM cust_month
),
churned AS (
    SELECT
        s2.month,
        'Churn' AS movement_type,
        -SUM(s1.mrr) AS mrr_delta
    FROM subscriptions_monthly s1
    LEFT JOIN subscriptions_monthly s2
        ON s2.customer_id = s1.customer_id
        AND s2.month = (SELECT MIN(month) FROM subscriptions_monthly WHERE month > s1.month)
    WHERE s1.is_churned_this_month = 1
    GROUP BY s2.month
)
SELECT movement_type, month, ROUND(SUM(mrr_delta), 0) AS mrr_delta
FROM classified
GROUP BY movement_type, month
HAVING movement_type != 'Retained'
ORDER BY month, movement_type;


-- 6. Cohort retention by month since signup
WITH cohort_size AS (
    SELECT signup_cohort, COUNT(*) AS cohort_customers
    FROM customers
    GROUP BY signup_cohort
),
activity AS (
    SELECT
        c.signup_cohort,
        s.tenure_months,
        COUNT(DISTINCT s.customer_id) AS active_customers
    FROM subscriptions_monthly s
    JOIN customers c ON c.customer_id = s.customer_id
    GROUP BY c.signup_cohort, s.tenure_months
)
SELECT
    a.signup_cohort,
    a.tenure_months,
    a.active_customers,
    cs.cohort_customers,
    ROUND(100.0 * a.active_customers / cs.cohort_customers, 1) AS retention_pct
FROM activity a
JOIN cohort_size cs ON cs.signup_cohort = a.signup_cohort
WHERE a.tenure_months <= 12
ORDER BY a.signup_cohort, a.tenure_months;


-- 7. Customer lifetime value by segment and plan
WITH customer_lifetime AS (
    SELECT
        customer_id,
        MAX(tenure_months) + 1 AS lifetime_months,
        AVG(mrr) AS avg_mrr
    FROM subscriptions_monthly
    GROUP BY customer_id
)
SELECT
    c.segment,
    c.initial_plan,
    COUNT(*) AS customers,
    ROUND(AVG(cl.lifetime_months), 1) AS avg_lifetime_months,
    ROUND(AVG(cl.avg_mrr), 2) AS avg_mrr,
    ROUND(AVG(cl.avg_mrr) * AVG(cl.lifetime_months), 2) AS estimated_ltv
FROM customer_lifetime cl
JOIN customers c ON c.customer_id = cl.customer_id
GROUP BY c.segment, c.initial_plan
ORDER BY estimated_ltv DESC;


-- 8. Top customers by lifetime revenue
SELECT
    s.customer_id,
    c.segment,
    c.country,
    c.initial_plan,
    COUNT(*) AS months_active,
    ROUND(SUM(s.mrr), 2) AS lifetime_revenue
FROM subscriptions_monthly s
JOIN customers c ON c.customer_id = s.customer_id
GROUP BY s.customer_id
ORDER BY lifetime_revenue DESC
LIMIT 20;


-- 9. Churn rate by month
SELECT
    month,
    SUM(CASE WHEN is_churned_this_month = 1 THEN 1 ELSE 0 END) AS churned_customers,
    COUNT(DISTINCT customer_id) AS active_customers,
    ROUND(100.0 * SUM(CASE WHEN is_churned_this_month = 1 THEN 1 ELSE 0 END) / COUNT(DISTINCT customer_id), 2) AS churn_pct
FROM subscriptions_monthly
GROUP BY month
ORDER BY month;
