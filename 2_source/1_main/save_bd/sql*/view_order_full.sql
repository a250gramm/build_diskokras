-- Представление «полный заказ»: одна строка на один order + один sub_order, цены собраны в JSON-массив.

DROP VIEW IF EXISTS public.order_full;

CREATE VIEW public.order_full AS
SELECT
    o.id AS order_id,
    so.id AS sub_order_id,
    so.revenu_100,
    so.revenu_fact,
    so.revenu_plan,
    so.stat_pay,
    so.page,
    COALESCE(
        (SELECT array_to_json(array_agg(row_to_json(t)))
         FROM (
             SELECT p2.id::text AS id, p2.servi_id AS servi_id, p2.price::text AS price
             FROM public.price p2
             WHERE p2.sub_order_id = so.id
         ) t), '[]'::json
    ) AS prices
FROM public."order" o
JOIN public.sub_order so ON so.order_id = o.id;

-- Пример: SELECT * FROM order_full WHERE order_id = 'a01351de-f420-41be-b9ea-d0d396e57a91';
