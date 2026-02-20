<?php
$include = json_decode(file_get_contents(__DIR__ . '/include.json'), true);
$c = $include['db_connection'] ?? [];
$port = isset($c['port']) ? ';port=' . $c['port'] : '';
$dsn = sprintf('pgsql:host=%s%s;dbname=%s', $c['host'] ?? 'localhost', $port, $c['database'] ?? '');
$pdo = new PDO($dsn, $c['username'] ?? '', $c['password'] ?? '');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$sql = 'CREATE TABLE IF NOT EXISTS "price" (
    "id" UUID PRIMARY KEY,
    "sub_order_id" UUID NOT NULL REFERENCES "sub_order"("id") ON DELETE CASCADE,
    "servi_id" VARCHAR(64) NOT NULL,
    "price" NUMERIC(12, 2) NOT NULL
)';
$pdo->exec($sql);
echo "OK: price table created\n";
