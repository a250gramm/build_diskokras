-- Добавить колонку id_wallet в fin_op
ALTER TABLE "fin_op" ADD COLUMN IF NOT EXISTS "id_wallet" VARCHAR(50);
