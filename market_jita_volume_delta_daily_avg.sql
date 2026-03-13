DROP TABLE IF EXISTS market_jita_volume_delta_daily_avg;

CREATE TABLE market_jita_volume_delta_daily_avg AS
SELECT
    type_id,
    name,
    is_buy_order,
    ROUND(AVG(total_volume_delta), 0)   AS avg_daily_volume,
    ROUND(AVG(avg_price)::numeric, 2)   AS avg_price
FROM public.market_jita_volume_delta_daily
GROUP BY type_id, name, is_buy_order
ORDER BY avg_daily_volume DESC;
