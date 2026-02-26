-- Таблица clients (клиенты): id, имя, фамилия, отчество, дата рождения, номер телефона, role (обязательное).

CREATE TABLE IF NOT EXISTS "clients" (
    "id" UUID PRIMARY KEY,
    "first_name" VARCHAR(128),
    "last_name" VARCHAR(128),
    "patronymic" VARCHAR(128),
    "birth_date" DATE,
    "phone" VARCHAR(32),
    "role" VARCHAR(64) NOT NULL,
    "gos_num" VARCHAR(32)
);

COMMENT ON TABLE "clients" IS 'Клиенты';
COMMENT ON COLUMN "clients"."first_name" IS 'Имя';
COMMENT ON COLUMN "clients"."last_name" IS 'Фамилия';
COMMENT ON COLUMN "clients"."patronymic" IS 'Отчество';
COMMENT ON COLUMN "clients"."birth_date" IS 'Дата рождения';
COMMENT ON COLUMN "clients"."phone" IS 'Номер телефона';
COMMENT ON COLUMN "clients"."role" IS 'Роль (обязательное)';
COMMENT ON COLUMN "clients"."gos_num" IS 'Гос номер';
