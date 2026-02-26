-- Представление 1_poss_point: те же столбцы, что в 1_sub_order (одна строка на order + sub_order).

DROP VIEW IF EXISTS public."1_poss_point";

CREATE VIEW public."1_poss_point" AS
SELECT
    row_number() OVER (ORDER BY so.id) AS num,
    o.id AS order_id,
    so.id AS sub_order_id,
    so.revenu_100,
    so.revenu_fact,
    so.revenu_plan,
    round((so.revenu_fact / NULLIF(so.revenu_100, 0)) * 100, 2) AS pay_percent,
    so.stat_pay,
    so.stat_ready,
    so.page,
    COALESCE(
        (SELECT array_to_json(array_agg(row_to_json(t)))
         FROM (
             SELECT p2.id::text AS id, p2.servi_id AS servi_id, p2.price::text AS price, p2.name AS name
             FROM public.price p2
             WHERE p2.sub_order_id = so.id
         ) t), '[]'::json
    ) AS prices
FROM public."order" o
JOIN public.sub_order so ON so.order_id = o.id;
