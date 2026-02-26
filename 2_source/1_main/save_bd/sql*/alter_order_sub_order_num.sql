-- Порядковый номер в таблице "order" (1, 2, 3, …)
ALTER TABLE "order" ADD COLUMN "num" INTEGER;

UPDATE "order" SET num = sub.rn
FROM (SELECT id, row_number() OVER (ORDER BY id) AS rn FROM "order") sub
WHERE "order".id = sub.id;

CREATE SEQUENCE order_num_seq;
SELECT setval('order_num_seq', (SELECT COALESCE(MAX(num), 0) FROM "order"));

ALTER TABLE "order" ALTER COLUMN "num" SET DEFAULT nextval('order_num_seq');
ALTER TABLE "order" ALTER COLUMN "num" SET NOT NULL;


-- Порядковый номер в таблице "sub_order" (1, 2, 3, …)
ALTER TABLE "sub_order" ADD COLUMN "num" INTEGER;

UPDATE "sub_order" SET num = sub.rn
FROM (SELECT id, row_number() OVER (ORDER BY id) AS rn FROM "sub_order") sub
WHERE "sub_order".id = sub.id;

CREATE SEQUENCE sub_order_num_seq;
SELECT setval('sub_order_num_seq', (SELECT COALESCE(MAX(num), 0) FROM "sub_order"));

ALTER TABLE "sub_order" ALTER COLUMN "num" SET DEFAULT nextval('sub_order_num_seq');
ALTER TABLE "sub_order" ALTER COLUMN "num" SET NOT NULL;


-- Порядковый номер в таблице "price" (1, 2, 3, …)
ALTER TABLE "price" ADD COLUMN "num" INTEGER;

UPDATE "price" SET num = sub.rn
FROM (SELECT id, row_number() OVER (ORDER BY id) AS rn FROM "price") sub
WHERE "price".id = sub.id;

CREATE SEQUENCE price_num_seq;
SELECT setval('price_num_seq', (SELECT COALESCE(MAX(num), 0) FROM "price"));

ALTER TABLE "price" ALTER COLUMN "num" SET DEFAULT nextval('price_num_seq');
ALTER TABLE "price" ALTER COLUMN "num" SET NOT NULL;


-- Порядковый номер в таблице "fin_op" (1, 2, 3, …)
ALTER TABLE "fin_op" ADD COLUMN "num" INTEGER;

UPDATE "fin_op" SET num = sub.rn
FROM (SELECT id, row_number() OVER (ORDER BY id) AS rn FROM "fin_op") sub
WHERE "fin_op".id = sub.id;

CREATE SEQUENCE fin_op_num_seq;
SELECT setval('fin_op_num_seq', (SELECT COALESCE(MAX(num), 0) FROM "fin_op"));

ALTER TABLE "fin_op" ALTER COLUMN "num" SET DEFAULT nextval('fin_op_num_seq');
ALTER TABLE "fin_op" ALTER COLUMN "num" SET NOT NULL;
