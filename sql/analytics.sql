-- Re-runnable analytical views over the accepted records in schema.sql.
-- Views always reflect the current contents of the source tables.

CREATE OR REPLACE VIEW daily_transaction_summary AS
SELECT
    transaction_date,
    transaction_type,
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT account_id) AS account_count,
    SUM(amount) AS total_amount_zar,
    AVG(amount) AS average_amount_zar
FROM transactions
GROUP BY transaction_date, transaction_type;

CREATE OR REPLACE VIEW branch_transaction_summary AS
SELECT
    b.branch_id,
    b.branch_name,
    b.city,
    b.province,
    COUNT(t.transaction_id) AS transaction_count,
    COALESCE(SUM(t.amount), 0) AS total_amount_zar,
    MIN(t.transaction_date) AS first_transaction_date,
    MAX(t.transaction_date) AS last_transaction_date
FROM branches AS b
LEFT JOIN transactions AS t ON t.branch_id = b.branch_id
GROUP BY b.branch_id, b.branch_name, b.city, b.province;

CREATE OR REPLACE VIEW monthly_customer_growth AS
WITH monthly_signups AS (
    SELECT
        DATE_TRUNC('month', join_date)::DATE AS signup_month,
        COUNT(*) AS new_customer_count
    FROM customers
    GROUP BY DATE_TRUNC('month', join_date)::DATE
)
SELECT
    signup_month,
    new_customer_count,
    SUM(new_customer_count) OVER (
        ORDER BY signup_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_customer_count
FROM monthly_signups;

CREATE OR REPLACE VIEW customer_province_summary AS
SELECT
    province,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0), 2)
        AS customer_percentage
FROM customers
GROUP BY province;

CREATE OR REPLACE VIEW monthly_payment_summary AS
SELECT
    DATE_TRUNC('month', payment_date)::DATE AS payment_month,
    status,
    COUNT(*) AS payment_count,
    SUM(amount) AS total_amount_zar,
    AVG(amount) AS average_amount_zar
FROM payments
GROUP BY DATE_TRUNC('month', payment_date)::DATE, status;
