<?php
$include = json_decode(file_get_contents(__DIR__ . '/include.json'), true);
$c = $include['db_connection'] ?? [];
$dsn = sprintf('pgsql:host=%s;dbname=%s', $c['host'] ?? 'localhost', $c['database'] ?? '');
$pdo = new PDO($dsn, $c['username'] ?? '', $c['password'] ?? '');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
foreach (['revenu_100', 'revenu_fact', 'revenu_plan'] as $col) {
    $pdo->exec('ALTER TABLE "sub_order" ADD COLUMN IF NOT EXISTS "' . $col . '" NUMERIC(12, 2)');
}
echo "OK: sub_order columns added\n";
