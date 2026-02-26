-- Таблица car (автомобили): id, id клиента, id гос номера (из gos_num), марка авто.

CREATE TABLE IF NOT EXISTS "car" (
    "id" UUID PRIMARY KEY,
    "id_client" UUID REFERENCES "clients"("id"),
    "id_gos_num" UUID REFERENCES "gos_num"("id"),
    "brand" VARCHAR(128),
    "color" VARCHAR(64)
);

COMMENT ON TABLE "car" IS 'Автомобили';
COMMENT ON COLUMN "car"."id_client" IS 'Клиент';
COMMENT ON COLUMN "car"."id_gos_num" IS 'Гос номер (из таблицы gos_num)';
COMMENT ON COLUMN "car"."brand" IS 'Марка авто';
COMMENT ON COLUMN "car"."color" IS 'Цвет';
