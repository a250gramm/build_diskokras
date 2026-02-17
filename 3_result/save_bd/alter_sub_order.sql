-- Добавить колонки в sub_order (из shino2.json)
ALTER TABLE "sub_order" ADD COLUMN IF NOT EXISTS "revenu_100" NUMERIC(12, 2);
ALTER TABLE "sub_order" ADD COLUMN IF NOT EXISTS "revenu_fact" NUMERIC(12, 2);
ALTER TABLE "sub_order" ADD COLUMN IF NOT EXISTS "revenu_plan" NUMERIC(12, 2);
