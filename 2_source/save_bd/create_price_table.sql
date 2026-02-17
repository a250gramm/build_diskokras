-- Таблица price (из shino2.json)
CREATE TABLE IF NOT EXISTS "price" (
    "id" UUID PRIMARY KEY,
    "sub_order_id" UUID NOT NULL REFERENCES "sub_order"("id") ON DELETE CASCADE,
    "servi_id" VARCHAR(64) NOT NULL,
    "price" NUMERIC(12, 2) NOT NULL
);
