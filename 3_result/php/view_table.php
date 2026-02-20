<?php
/**
 * Просмотр и удаление записей из таблиц order, sub_order, price, fin_op, wall в PostgreSQL.
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

$port = isset($conn['port']) ? ';port=' . $conn['port'] : '';
$dsn = sprintf('pgsql:host=%s%s;dbname=%s', $conn['host'] ?? 'localhost', $port, $conn['database'] ?? '');
$user = $conn['username'] ?? '';
$pass = $conn['password'] ?? '';

try {
    $pdo = new PDO($dsn, $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo '<h1>Ошибка</h1><p>' . htmlspecialchars($e->getMessage()) . '</p>';
    exit;
}

/** Порядок вывода: order → sub_order → price → fin_op → wall (статичный) */
$tablesDisplay = ['order', 'sub_order', 'price', 'fin_op', 'wall'];
/** Порядок удаления: сначала дочерние, затем родители */
$tablesDelete = ['price', 'sub_order', 'order', 'fin_op'];

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['delete_all'])) {
    // 1. Сначала: удалить все записи (функции кнопки «Удалить все записи»)
    foreach ($tablesDelete as $t) {
        $pdo->exec('DELETE FROM "' . $t . '"');
    }
    // 2. Потом: если галочка «Только новые данные» — ещё «Обновить баланс» (по fin_op; после удаления fin_op пустая → балансы 0)
    if (isset($_POST['only_new_data']) && (string)$_POST['only_new_data'] === '1') {
        $pdo->exec('UPDATE "wall" SET "balance" = 0');
        $rows = $pdo->query('SELECT id_wallet, SUM(money) AS s FROM "fin_op" WHERE id_wallet IS NOT NULL AND id_wallet != \'\' GROUP BY id_wallet')->fetchAll(PDO::FETCH_ASSOC);
        $stmt = $pdo->prepare('UPDATE "wall" SET "balance" = ? WHERE id = ?');
        foreach ($rows as $r) {
            $stmt->execute([(float)$r['s'], $r['id_wallet']]);
        }
    }
    header('Location: view_table.php');
    exit;
}
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['reset_balance'])) {
    $pdo->exec('UPDATE "wall" SET "balance" = 0');
    header('Location: view_table.php');
    exit;
}
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['update_balance'])) {
    $pdo->exec('UPDATE "wall" SET "balance" = 0');
    $rows = $pdo->query('SELECT id_wallet, SUM(money) AS s FROM "fin_op" WHERE id_wallet IS NOT NULL AND id_wallet != \'\' GROUP BY id_wallet')->fetchAll(PDO::FETCH_ASSOC);
    $stmt = $pdo->prepare('UPDATE "wall" SET "balance" = ? WHERE id = ?');
    foreach ($rows as $r) {
        $stmt->execute([(float)$r['s'], $r['id_wallet']]);
    }
    header('Location: view_table.php');
    exit;
}

$data = [];
foreach ($tablesDisplay as $t) {
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
        body { font-family: sans-serif; margin: 16px; font-size: 13px; }
        .btn-delete { padding: 6px 12px; background: #c00; color: #fff; border: none; cursor: pointer; border-radius: 4px; font-size: 12px; margin-bottom: 12px; }
        .btn-delete:hover { background: #a00; }
        .btn-reset { padding: 6px 12px; background: #06c; color: #fff; border: none; cursor: pointer; border-radius: 4px; font-size: 12px; margin-bottom: 12px; }
        .btn-reset:hover { background: #05a; }
        .btn-update { padding: 6px 12px; background: #080; color: #fff; border: none; cursor: pointer; border-radius: 4px; font-size: 12px; margin-bottom: 12px; }
        .btn-update:hover { background: #060; }
        h2 { margin-top: 16px; margin-bottom: 6px; font-size: 14px; }
        table { border-collapse: collapse; margin-bottom: 12px; font-size: 12px; }
        th, td { border: 1px solid #999; padding: 4px 8px; text-align: left; }
        th { background: #eee; font-size: 11px; font-weight: 600; }
        .empty { color: #999; font-style: italic; font-size: 12px; }
        .tbl-count { font-size: 0.85em; font-weight: normal; color: #666; }
        .tbl-static { font-size: 0.8em; font-weight: normal; color: #888; background: #eee; padding: 2px 6px; border-radius: 3px; margin-left: 4px; }
        .header-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 4px; }
        .header-hint { font-size: 11px; color: #888; margin-bottom: 12px; }
        .cb-wrap label { cursor: pointer; user-select: none; font-size: 12px; }
    </style>
</head>
<body>
<div class="header-row">
<form method="post" id="header-form">
    <input type="hidden" name="delete_all" value="1">
    <input type="hidden" name="only_new_data" id="only_new_data_val" value="0">
    <label class="cb-wrap"><input type="checkbox" id="only_new_data"> Только новые данные</label>
    <button type="submit" class="btn-delete">Удалить все записи</button>
</form>
<form method="post" style="margin:0;display:inline-block;">
    <button type="submit" name="reset_balance" value="1" class="btn-reset" onclick="return confirm('Обнулить balance во всех кошельках wall?');">Обнулить баланс</button>
</form>
<form method="post" style="margin:0;display:inline-block;">
    <button type="submit" name="update_balance" value="1" class="btn-update" onclick="return confirm('Обновить balance в wall по сумме всех fin_op?');">Обновить баланс</button>
</form>
</div>
<p class="header-hint">Функции выше действуют только на данные, которые сбрасывают balance в wall до 0.</p>

<?php foreach ($tablesDisplay as $t): ?>
<?php $cnt = count($data[$t] ?? []); $word = ($cnt === 1) ? 'запись' : (($cnt >= 2 && $cnt <= 4) ? 'записи' : 'записей'); ?>
<?php $staticLabel = ($t === 'wall') ? ' <span class="tbl-static">Статичная</span>' : ''; ?>
<h2><?= htmlspecialchars($t) ?> <span class="tbl-count">(<?= $cnt ?> <?= $word ?>)</span><?= $staticLabel ?></h2>
<?php $rows = $data[$t] ?? []; ?>
<?php if (empty($rows)): ?>
<p class="empty">Нет данных</p>
<?php else: ?>
<?php $cols = array_diff(array_keys($rows[0]), ['created_at', 'updated_at']); ?>
<table>
<thead><tr><?php foreach ($cols as $col): ?><th><?= htmlspecialchars($col) ?></th><?php endforeach; ?></tr></thead>
<tbody>
<?php foreach ($rows as $row): ?>
<tr><?php foreach ($cols as $col): ?><td><?= htmlspecialchars((string)($row[$col] ?? '')) ?></td><?php endforeach; ?></tr>
<?php endforeach; ?>
</tbody>
</table>
<?php endif; ?>
<?php endforeach; ?>
<script>
(function(){
    var key = 'save_bd_only_new_data';
    var cb = document.getElementById('only_new_data');
    var hid = document.getElementById('only_new_data_val');
    var form = document.getElementById('header-form');
    if (cb) {
        cb.checked = localStorage.getItem(key) === '1';
        hid.value = cb.checked ? '1' : '0';
        cb.addEventListener('change', function(){
            localStorage.setItem(key, cb.checked ? '1' : '0');
            hid.value = cb.checked ? '1' : '0';
        });
    }
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var doReset = cb && cb.checked;
            var msg = doReset
                ? 'Удалить все записи и сбросить balance в wall до 0?'
                : 'Удалить все записи из order, sub_order, price, fin_op? (wall не затрагивается)';
            if (!confirm(msg)) return;
            var fd = new FormData();
            fd.append('delete_all', '1');
            fd.append('only_new_data', doReset ? '1' : '0');
            fetch(window.location.href, { method: 'POST', body: fd })
                .then(function() { window.location.href = window.location.pathname; });
        });
    }
})();
</script>
</body>
</html>
