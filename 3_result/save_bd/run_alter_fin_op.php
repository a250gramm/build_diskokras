<?php
$include = json_decode(file_get_contents(__DIR__ . '/include.json'), true);
$c = $include['db_connection'] ?? [];
$port = isset($c['port']) ? ';port=' . $c['port'] : '';
$dsn = sprintf('pgsql:host=%s%s;dbname=%s', $c['host'] ?? 'localhost', $port, $c['database'] ?? '');
$pdo = new PDO($dsn, $c['username'] ?? '', $c['password'] ?? '');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->exec('ALTER TABLE "fin_op" ADD COLUMN IF NOT EXISTS "id_wallet" VARCHAR(50)');
echo "OK: fin_op.id_wallet added\n";
