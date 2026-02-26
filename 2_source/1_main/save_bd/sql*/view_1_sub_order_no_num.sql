-- Пересоздать представление 1_sub_order БЕЗ столбца num (удалить num из вывода)
DROP VIEW IF EXISTS public."1_sub_order";

CREATE VIEW public."1_sub_order" AS
SELECT
    o.id AS order_id,
    so.id AS sub_order_id,
    so.revenu_100,
    so.revenu_fact,
    so.revenu_plan,
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
