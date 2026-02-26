-- Таблица co_wor (сотрудники): id, имя, фамилия, отчество, дата рождения, телефон, логин, пароль.

CREATE TABLE IF NOT EXISTS "co_wor" (
    "id" UUID PRIMARY KEY,
    "first_name" VARCHAR(128),
    "last_name" VARCHAR(128),
    "patronymic" VARCHAR(128),
    "birth_date" DATE,
    "phone" VARCHAR(32),
    "login" VARCHAR(64),
    "password" VARCHAR(256)
);

COMMENT ON TABLE "co_wor" IS 'Сотрудники';
COMMENT ON COLUMN "co_wor"."first_name" IS 'Имя';
COMMENT ON COLUMN "co_wor"."last_name" IS 'Фамилия';
COMMENT ON COLUMN "co_wor"."patronymic" IS 'Отчество';
COMMENT ON COLUMN "co_wor"."birth_date" IS 'Дата рождения';
COMMENT ON COLUMN "co_wor"."phone" IS 'Телефон';
COMMENT ON COLUMN "co_wor"."login" IS 'Логин';
COMMENT ON COLUMN "co_wor"."password" IS 'Пароль';
