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

/** Режим: tables | views */
$mode = isset($_GET['mode']) && $_GET['mode'] === 'views' ? 'views' : 'tables';

/** Порядок вывода: order → sub_order → price → fin_op → wall (статичный) */
$tablesDisplay = ['order', 'sub_order', 'price', 'fin_op', 'wall'];
/** Порядок удаления: сначала дочерние, затем родители */
$tablesDelete = ['price', 'sub_order', 'order', 'fin_op'];

/** Список представлений из БД (для mode=views) */
$viewsList = [];
if ($mode === 'views') {
    try {
        $viewsList = $pdo->query("SELECT table_name FROM information_schema.views WHERE table_schema = 'public' ORDER BY table_name")->fetchAll(PDO::FETCH_COLUMN);
    } catch (PDOException $e) {
        $viewsList = [];
    }
}

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
if ($mode === 'tables') {
    foreach ($tablesDisplay as $t) {
        try {
            $rows = $pdo->query('SELECT * FROM "' . $t . '" ORDER BY 1')->fetchAll(PDO::FETCH_ASSOC);
            $data[$t] = $rows;
        } catch (PDOException $e) {
            $data[$t] = [];
        }
    }
}

$dataViews = [];
if ($mode === 'views') {
    foreach ($viewsList as $v) {
        try {
            $rows = $pdo->query('SELECT * FROM "' . $v . '" ORDER BY 1')->fetchAll(PDO::FETCH_ASSOC);
            $dataViews[$v] = $rows;
        } catch (PDOException $e) {
            $dataViews[$v] = [];
        }
    }
}

/**
 * Для представлений: если значение — JSON-массив объектов, вернуть HTML вложенной таблицы; иначе текст.
 */
function render_view_cell($val) {
    if ($val === null || $val === '') return '';
    $arr = null;
    if (is_string($val)) {
        $arr = json_decode($val, true);
    } elseif (is_array($val)) {
        $arr = $val;
    }
    if (is_array($arr) && !empty($arr) && isset($arr[0]) && is_array($arr[0])) {
        $innerCols = array_keys($arr[0]);
        $html = '<table class="nested-tbl"><thead><tr>';
        foreach ($innerCols as $c) {
            $html .= '<th>' . htmlspecialchars($c) . '</th>';
        }
        $html .= '</tr></thead><tbody>';
        foreach ($arr as $item) {
            $html .= '<tr>';
            foreach ($innerCols as $c) {
                $html .= '<td>' . htmlspecialchars((string)($item[$c] ?? '')) . '</td>';
            }
            $html .= '</tr>';
        }
        $html .= '</tbody></table>';
        return $html;
    }
    if (is_string($val)) return htmlspecialchars($val);
    return htmlspecialchars(json_encode($val, JSON_UNESCAPED_UNICODE));
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
        .tabs { display: flex; gap: 0; margin-bottom: 16px; border-bottom: 1px solid #999; }
        .tabs a { padding: 8px 16px; text-decoration: none; color: #06c; background: #f5f5f5; border: 1px solid #999; border-bottom: none; margin-right: 2px; border-radius: 4px 4px 0 0; font-size: 13px; }
        .tabs a:hover { background: #eee; }
        .tabs a.active { background: #fff; color: #000; font-weight: 600; margin-bottom: -1px; padding-bottom: 9px; }
        .tbl-view-label { font-size: 0.8em; font-weight: normal; color: #06c; background: #e8f4ff; padding: 2px 6px; border-radius: 3px; margin-left: 4px; }
        .nested-tbl { font-size: 11px; margin: 0; border: 1px solid #ccc; background: #fafafa; }
        .nested-tbl th, .nested-tbl td { border: 1px solid #ddd; padding: 2px 6px; }
        .nested-tbl th { background: #e8e8e8; }
        .table-wrapper { overflow-x: auto; margin-bottom: 12px; -webkit-overflow-scrolling: touch; }
        .table-wrapper table { margin-bottom: 0; min-width: min-content; }
    </style>
</head>
<body>
<div class="tabs">
    <a href="view_table.php?mode=tables"<?= $mode === 'tables' ? ' class="active"' : '' ?>>Таблицы</a>
    <a href="view_table.php?mode=views"<?= $mode === 'views' ? ' class="active"' : '' ?>>Представления</a>
</div>

<?php if ($mode === 'tables'): ?>
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
<?php endif; ?>

<?php if ($mode === 'tables'): ?>
<?php foreach ($tablesDisplay as $t): ?>
<?php $cnt = count($data[$t] ?? []); $word = ($cnt === 1) ? 'запись' : (($cnt >= 2 && $cnt <= 4) ? 'записи' : 'записей'); ?>
<?php $staticLabel = ($t === 'wall') ? ' <span class="tbl-static">Статичная</span>' : ''; ?>
<h2><?= htmlspecialchars($t) ?> <span class="tbl-count">(<?= $cnt ?> <?= $word ?>)</span><?= $staticLabel ?></h2>
<?php $rows = $data[$t] ?? []; ?>
<?php if (empty($rows)): ?>
<p class="empty">Нет данных</p>
<?php else: ?>
<?php
            $cols = array_diff(array_keys($rows[0]), ['created_at', 'updated_at']);
            $cols = array_values($cols);
            if (in_array('num', $cols, true)) {
                $cols = array_merge(['num'], array_values(array_diff($cols, ['num'])));
            }
?>
<div class="table-wrapper">
<table>
<thead><tr><?php foreach ($cols as $col): ?><th><?= htmlspecialchars($col) ?></th><?php endforeach; ?></tr></thead>
<tbody>
<?php foreach ($rows as $row): ?>
<tr><?php foreach ($cols as $col): ?><td><?= htmlspecialchars((string)($row[$col] ?? '')) ?></td><?php endforeach; ?></tr>
<?php endforeach; ?>
</tbody>
</table>
</div>
<?php endif; ?>
<?php endforeach; ?>
<?php endif; ?>

<?php if ($mode === 'views'): ?>
<?php if (empty($viewsList)): ?>
<p class="empty">В схеме public нет представлений.</p>
<?php else: ?>
<?php foreach ($viewsList as $v): ?>
<?php $cnt = count($dataViews[$v] ?? []); $word = ($cnt === 1) ? 'запись' : (($cnt >= 2 && $cnt <= 4) ? 'записи' : 'записей'); ?>
<h2><?= htmlspecialchars($v) ?> <span class="tbl-count">(<?= $cnt ?> <?= $word ?>)</span> <span class="tbl-view-label">Представление</span></h2>
<?php $rows = $dataViews[$v] ?? []; ?>
<?php if (empty($rows)): ?>
<p class="empty">Нет данных</p>
<?php else: ?>
<?php $cols = array_keys($rows[0]); ?>
<div class="table-wrapper">
<table>
<thead><tr><?php foreach ($cols as $col): ?><th><?= htmlspecialchars($col) ?></th><?php endforeach; ?></tr></thead>
<tbody>
<?php foreach ($rows as $row): ?>
<tr><?php foreach ($cols as $col): ?><td><?php echo render_view_cell($row[$col] ?? null); ?></td><?php endforeach; ?></tr>
<?php endforeach; ?>
</tbody>
</table>
</div>
<?php endif; ?>
<?php endforeach; ?>
<?php endif; ?>
<?php endif; ?>

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
