CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    order_date DATE NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('organic', 'paid search', 'referral')),
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    currency TEXT NOT NULL CHECK (currency = 'USD')
);

CREATE VIEW revenue_by_channel AS
SELECT channel, count(*)::int AS orders, sum(amount)::text AS revenue
FROM orders GROUP BY channel;
