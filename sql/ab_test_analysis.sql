-- PostgreSQL reference queries for A/B test funnel analysis.
-- events(user_id, experiment_group, event_name, event_time, revenue)

-- User-level funnel flags: each user counted once per stage.
WITH user_funnel AS (
  SELECT user_id, experiment_group,
    MAX((event_name='landing_page')::int) AS landed,
    MAX((event_name='add_to_cart')::int) AS added_to_cart,
    MAX((event_name='checkout')::int) AS checked_out,
    MAX((event_name='purchase')::int) AS purchased,
    SUM(CASE WHEN event_name='purchase' THEN revenue ELSE 0 END) AS revenue
  FROM events
  GROUP BY user_id, experiment_group
)
SELECT experiment_group,
       COUNT(*) AS users,
       SUM(landed) AS landing_users,
       SUM(added_to_cart) AS cart_users,
       SUM(checked_out) AS checkout_users,
       SUM(purchased) AS purchasers,
       SUM(purchased)::numeric / NULLIF(COUNT(*),0) AS conversion_rate,
       SUM(revenue) AS revenue
FROM user_funnel
GROUP BY experiment_group;

-- Conversion count and non-conversion count for a 2x2 test table.
WITH user_outcome AS (
 SELECT user_id, experiment_group,
        MAX((event_name='purchase')::int) AS converted
 FROM events GROUP BY user_id, experiment_group
)
SELECT experiment_group, converted, COUNT(*) AS users
FROM user_outcome GROUP BY experiment_group, converted
ORDER BY experiment_group, converted;
