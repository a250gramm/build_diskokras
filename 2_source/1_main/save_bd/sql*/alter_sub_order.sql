-- Добавить колонки в sub_order (из shino2.json)
ALTER TABLE "sub_order" ADD COLUMN IF NOT EXISTS "revenu_100" NUMERIC(12, 2);
ALTER TABLE "sub_order" ADD COLUMN IF NOT EXISTS "revenu_fact" NUMERIC(12, 2);
ALTER TABLE "sub_order" ADD COLUMN IF NOT EXISTS "revenu_plan" NUMERIC(12, 2);
-- Статус оплаты: full | part | none
ALTER TABLE "sub_order" ADD COLUMN IF NOT EXISTS "stat_pay" TEXT;

-- Статус готовности подзаказа (stat_ready):
--   creat   — создан
--   in_prog — в работе
--   over    — завершён
--   accept  — принят
ALTER TABLE "sub_order" ADD COLUMN "stat_ready" TEXT
  CHECK ("stat_ready" IS NULL OR "stat_ready" IN ('creat', 'in_prog', 'over', 'accept'));
COMMENT ON COLUMN "sub_order"."stat_ready" IS 'Статус готовности: creat — создан, in_prog — в работе, over — завершён, accept — принят';
