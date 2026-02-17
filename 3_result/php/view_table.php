<?php
/**
 * Просмотр и удаление записей из таблиц order, sub_order, price в PostgreSQL.
 */
header('Content-Type: text/html; charset=utf-8');

$includePath = __DIR__ . '/../save_bd/include.json';
if (!is_file($includePath)) {
    echo '<h1>Ошибка</h1><p>include.json не найден.</p>';
    exit;
}

$include = json_decode(file_get_contents($includePath), true);
if (!$include || !isset($include['db_connection'])) {
    echo '<h1>Ошибка</h1><p>Неверный include.json.</p>';
    exit;
}

$conn = $include['db_connection'];
if (($conn['driver'] ?? '') !== 'pgsql') {
    echo '<h1>Ошибка</h1><p>PostgreSQL требуется.</p>';
    exit;
}

$dsn = sprintf('pgsql:host=%s;dbname=%s', $conn['host'] ?? 'localhost', $conn['database'] ?? '');
$user = $conn['username'] ?? '';
$pass = $conn['password'] ?? '';

try {
    $pdo = new PDO($dsn, $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo '<h1>Ошибка</h1><p>' . htmlspecialchars($e->getMessage()) . '</p>';
    exit;
}

$tables = ['price', 'sub_order', 'order', 'fin_op'];
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['delete_all'])) {
    foreach ($tables as $t) {
        $pdo->exec('DELETE FROM "' . $t . '"');
    }
    header('Location: view_table.php');
    exit;
}

$data = [];
foreach ($tables as $t) {
    try {
        $rows = $pdo->query('SELECT * FROM "' . $t . '" ORDER BY 1')->fetchAll(PDO::FETCH_ASSOC);
        $data[$t] = $rows;
    } catch (PDOException $e) {
        $data[$t] = [];
    }
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Просмотр заказов</title>
    <style>
        body { font-family: sans-serif; margin: 40px; }
        .btn-delete { padding: 12px 24px; background: #c00; color: #fff; border: none; cursor: pointer; border-radius: 4px; font-size: 16px; margin-bottom: 24px; }
        .btn-delete:hover { background: #a00; }
        h2 { margin-top: 32px; margin-bottom: 12px; }
        table { border-collapse: collapse; margin-bottom: 24px; }
        th, td { border: 1px solid #999; padding: 8px 12px; text-align: left; }
        th { background: #eee; }
        .empty { color: #999; font-style: italic; }
        .tbl-count { font-size: 0.75em; font-weight: normal; color: #666; }
        .header-row { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; margin-bottom: 24px; }
        .cb-wrap label { cursor: pointer; user-select: none; }
    </style>
</head>
<body>
<div class="header-row">
    <label class="cb-wrap"><input type="checkbox" id="only_new_data" name="only_new_data"> Только новые данные</label>
    <form method="post" onsubmit="return confirm('Удалить все записи из order, sub_order, price, fin_op?');" style="margin:0">
        <button type="submit" name="delete_all" value="1" class="btn-delete">Удалить все записи</button>
    </form>
</div>

<?php foreach (['order', 'sub_order', 'price', 'fin_op'] as $t): ?>
<?php $cnt = count($data[$t] ?? []); $word = ($cnt === 1) ? 'запись' : (($cnt >= 2 && $cnt <= 4) ? 'записи' : 'записей'); ?>
<h2><?= htmlspecialchars($t) ?> <span class="tbl-count">(<?= $cnt ?> <?= $word ?>)</span></h2>
<?php $rows = $data[$t] ?? []; ?>
<?php if (empty($rows)): ?>
<p class="empty">Нет данных</p>
<?php else: ?>
<table>
<thead><tr><?php foreach (array_keys($rows[0]) as $col): ?><th><?= htmlspecialchars($col) ?></th><?php endforeach; ?></tr></thead>
<tbody>
<?php foreach ($rows as $row): ?>
<tr><?php foreach ($row as $v): ?><td><?= htmlspecialchars((string)$v) ?></td><?php endforeach; ?></tr>
<?php endforeach; ?>
</tbody>
</table>
<?php endif; ?>
<?php endforeach; ?>
<script>
(function(){
    var key = 'save_bd_only_new_data';
    var cb = document.getElementById('only_new_data');
    if (cb) {
        cb.checked = localStorage.getItem(key) === '1';
        cb.addEventListener('change', function(){ localStorage.setItem(key, cb.checked ? '1' : '0'); });
    }
})();
</script>
</body>
</html>
