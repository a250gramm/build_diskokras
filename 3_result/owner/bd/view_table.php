<?php
/**
 * Просмотр и удаление записей из таблиц order, sub_order, price, fin_op, wall, co_wor в PostgreSQL.
 */
header('Content-Type: text/html; charset=utf-8');

$includePath = __DIR__ . '/../../save_bd/include.json';
if (!is_file($includePath) && isset($_SERVER['DOCUMENT_ROOT'])) {
    $includePath = rtrim($_SERVER['DOCUMENT_ROOT'], '/') . '/save_bd/include.json';
}
if (!is_file($includePath)) {
    echo '<h1>Ошибка</h1><p>include.json не найден. Проверьте путь: ' . htmlspecialchars($includePath) . '</p>';
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

/** Режим: orders (заказы) | users (юзеры/co_wor) | views (представления) */
$modeRaw = $_GET['mode'] ?? 'orders';
if ($modeRaw === 'tables') { $modeRaw = 'orders'; }
$mode = in_array($modeRaw, ['orders', 'users', 'views'], true) ? $modeRaw : 'orders';

/** Ошибка добавления сотрудника/клиента/авто/гос номера (если была) */
$add_co_wor_error = null;
$add_clients_error = null;
$add_car_error = null;
$add_gos_num_error = null;

/** Таб:Заказы — все таблицы кроме co_wor, clients, car */
$tablesDisplayOrders = ['order', 'sub_order', 'price', 'fin_op', 'wall'];
/** Таб:Юзеры — co_wor, clients, car, gos_num */
$tablesDisplayUsers = ['co_wor', 'clients', 'car', 'gos_num'];
$tablesDisplay = ($mode === 'users') ? $tablesDisplayUsers : $tablesDisplayOrders;
/** Порядок удаления: fin_op ссылается на sub_order — сначала fin_op, потом sub_order, order */
$tablesDelete = ['price', 'fin_op', 'sub_order', 'order'];

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
    // 1. Удалить все заказы (кнопка «Удалить все заказы»). Таблицы wall и co_wor не затрагиваются.
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

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['add_co_wor'])) {
    try {
        $uuid = sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            random_int(0, 0xffff), random_int(0, 0xffff), random_int(0, 0xffff),
            random_int(0, 0x0fff) | 0x4000, random_int(0, 0x3fff) | 0x8000,
            random_int(0, 0xffff), random_int(0, 0xffff), random_int(0, 0xffff));
        $login = str_pad((string)random_int(0, 999999), 6, '0', STR_PAD_LEFT);
        $alnum = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
        $password = '';
        for ($i = 0; $i < 12; $i++) {
            $password .= $alnum[random_int(0, strlen($alnum) - 1)];
        }
        $phoneRaw = trim((string)($_POST['phone'] ?? ''));
        $phone = preg_replace('/\D/', '', $phoneRaw);
        if (strlen($phone) === 9) {
            $phone = '7' . $phone;
        } elseif (strlen($phone) > 11) {
            $phone = substr($phone, 0, 11);
        }
        $stmt = $pdo->prepare('INSERT INTO "co_wor" ("id", "first_name", "last_name", "patronymic", "birth_date", "phone", "login", "password") VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
        $stmt->execute([
            $uuid,
            trim((string)($_POST['first_name'] ?? '')),
            trim((string)($_POST['last_name'] ?? '')),
            trim((string)($_POST['patronymic'] ?? '')),
            trim((string)($_POST['birth_date'] ?? '')) ?: null,
            $phone,
            $login,
            $password
        ]);
        header('Location: view_table.php?mode=users');
        exit;
    } catch (PDOException $e) {
        $add_co_wor_error = $e->getMessage();
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['delete_co_wor']) && !empty($_POST['delete_co_wor_ids'])) {
    $ids = array_values(array_filter((array)$_POST['delete_co_wor_ids'], function ($id) {
        return is_string($id) && preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i', $id);
    }));
    if (!empty($ids)) {
        $placeholders = implode(',', array_fill(0, count($ids), '?'));
        $stmt = $pdo->prepare('DELETE FROM "co_wor" WHERE "id" IN (' . $placeholders . ')');
        $stmt->execute($ids);
    }
    header('Location: view_table.php?mode=users');
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['add_clients'])) {
    try {
        $uuid = sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            random_int(0, 0xffff), random_int(0, 0xffff), random_int(0, 0xffff),
            random_int(0, 0x0fff) | 0x4000, random_int(0, 0x3fff) | 0x8000,
            random_int(0, 0xffff), random_int(0, 0xffff), random_int(0, 0xffff));
        $phoneRaw = trim((string)($_POST['clients_phone'] ?? ''));
        $phone = preg_replace('/\D/', '', $phoneRaw);
        if (strlen($phone) === 9) {
            $phone = '7' . $phone;
        } elseif (strlen($phone) > 11) {
            $phone = substr($phone, 0, 11);
        }
        $role = (string)($_POST['clients_role'] ?? 'individual');
        if ($role !== 'individual' && $role !== 'legal') {
            $role = 'individual';
        }
        $stmt = $pdo->prepare('INSERT INTO "clients" ("id", "first_name", "last_name", "patronymic", "birth_date", "phone", "role", "comp_name") VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
        $stmt->execute([
            $uuid,
            trim((string)($_POST['clients_first_name'] ?? '')),
            trim((string)($_POST['clients_last_name'] ?? '')),
            trim((string)($_POST['clients_patronymic'] ?? '')),
            trim((string)($_POST['clients_birth_date'] ?? '')) ?: null,
            $phone,
            $role,
            trim((string)($_POST['clients_comp_name'] ?? '')) ?: null
        ]);
        header('Location: view_table.php?mode=users');
        exit;
    } catch (PDOException $e) {
        $add_clients_error = $e->getMessage();
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['delete_clients']) && !empty($_POST['delete_clients_ids'])) {
    $ids = array_values(array_filter((array)$_POST['delete_clients_ids'], function ($id) {
        return is_string($id) && preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i', $id);
    }));
    if (!empty($ids)) {
        $placeholders = implode(',', array_fill(0, count($ids), '?'));
        $stmt = $pdo->prepare('DELETE FROM "clients" WHERE "id" IN (' . $placeholders . ')');
        $stmt->execute($ids);
    }
    header('Location: view_table.php?mode=users');
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['add_car'])) {
    try {
        $uuid = sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            random_int(0, 0xffff), random_int(0, 0xffff), random_int(0, 0xffff),
            random_int(0, 0x0fff) | 0x4000, random_int(0, 0x3fff) | 0x8000,
            random_int(0, 0xffff), random_int(0, 0xffff), random_int(0, 0xffff));
        $id_client = trim((string)($_POST['car_id_client'] ?? ''));
        if (!preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i', $id_client)) {
            $id_client = null;
        }
        $id_gos_num = trim((string)($_POST['car_id_gos_num'] ?? ''));
        if ($id_gos_num !== '' && !preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i', $id_gos_num) && !ctype_digit($id_gos_num)) {
            $id_gos_num = null;
        } elseif ($id_gos_num === '') {
            $id_gos_num = null;
        }
        $stmt = $pdo->prepare('INSERT INTO "car" ("id", "id_client", "id_gos_num", "brand", "color") VALUES (?, ?, ?, ?, ?)');
        $stmt->execute([$uuid, $id_client ?: null, $id_gos_num, trim((string)($_POST['car_brand'] ?? '')), trim((string)($_POST['car_color'] ?? '')) ?: null]);
        header('Location: view_table.php?mode=users');
        exit;
    } catch (PDOException $e) {
        $add_car_error = $e->getMessage();
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['delete_car']) && !empty($_POST['delete_car_ids'])) {
    $ids = array_values(array_filter((array)$_POST['delete_car_ids'], function ($id) {
        return is_string($id) && preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i', $id);
    }));
    if (!empty($ids)) {
        $placeholders = implode(',', array_fill(0, count($ids), '?'));
        $stmt = $pdo->prepare('DELETE FROM "car" WHERE "id" IN (' . $placeholders . ')');
        $stmt->execute($ids);
    }
    header('Location: view_table.php?mode=users');
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['add_gos_num'])) {
    try {
        $plate = trim((string)($_POST['gos_num_plate'] ?? ''));
        $stmt = $pdo->prepare('INSERT INTO "gos_num" ("plate") VALUES (?)');
        $stmt->execute([$plate ?: null]);
        header('Location: view_table.php?mode=users');
        exit;
    } catch (PDOException $e) {
        $add_gos_num_error = $e->getMessage();
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['delete_gos_num']) && !empty($_POST['delete_gos_num_ids'])) {
    $ids = array_values(array_filter((array)$_POST['delete_gos_num_ids'], function ($id) {
        return is_string($id) && (preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i', $id) || ctype_digit($id));
    }));
    if (!empty($ids)) {
        $placeholders = implode(',', array_fill(0, count($ids), '?'));
        $stmt = $pdo->prepare('DELETE FROM "gos_num" WHERE "id" IN (' . $placeholders . ')');
        $stmt->execute($ids);
    }
    header('Location: view_table.php?mode=users');
    exit;
}

$data = [];
if ($mode === 'orders' || $mode === 'users') {
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
        .tbl-header-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
        .btn-add { padding: 6px 12px; background: #080; color: #fff; border: none; cursor: pointer; border-radius: 4px; font-size: 12px; }
        .btn-add:hover { background: #060; }
        .co_wor-form { margin: 12px 0; padding: 12px; background: #f5f5f5; border: 1px solid #ccc; border-radius: 4px; max-width: 400px; }
        .co_wor-form .form-row { margin-bottom: 8px; }
        .co_wor-form label { display: inline-block; min-width: 120px; font-size: 12px; }
        .co_wor-form input, .co_wor-form select { padding: 4px 8px; font-size: 12px; width: 200px; }
        .co_wor-form .btn-submit { padding: 6px 14px; background: #06c; color: #fff; border: none; cursor: pointer; border-radius: 4px; font-size: 12px; margin-top: 8px; }
        .co_wor-form .btn-submit:hover { background: #05a; }
        .co_wor-form .form-hint { font-size: 11px; color: #666; margin: 8px 0 0 0; }
        .co_wor-form .form-error { color: #c00; font-size: 12px; margin: 0 0 8px 0; }
    </style>
</head>
<body>
<div class="tabs">
    <a href="view_table.php?mode=orders"<?= $mode === 'orders' ? ' class="active"' : '' ?>>Таб:Заказы</a>
    <a href="view_table.php?mode=users"<?= $mode === 'users' ? ' class="active"' : '' ?>>Таб:Юзеры</a>
    <a href="view_table.php?mode=views"<?= $mode === 'views' ? ' class="active"' : '' ?>>Представления</a>
</div>

<?php if ($mode === 'orders'): ?>
<div class="header-row">
<form method="post" id="header-form">
    <input type="hidden" name="delete_all" value="1">
    <input type="hidden" name="only_new_data" id="only_new_data_val" value="0">
    <label class="cb-wrap"><input type="checkbox" id="only_new_data"> Только новые данные</label>
    <button type="submit" class="btn-delete">Удалить все заказы</button>
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

<?php if ($mode === 'orders' || $mode === 'users'): ?>
<?php foreach ($tablesDisplay as $t): ?>
<?php $cnt = count($data[$t] ?? []); $word = ($cnt === 1) ? 'запись' : (($cnt >= 2 && $cnt <= 4) ? 'записи' : 'записей'); ?>
<?php $staticLabel = ($t === 'wall') ? ' <span class="tbl-static">Статичная</span>' : ''; ?>
<div class="tbl-header-row">
    <h2 style="margin:0;"><?= htmlspecialchars($t) ?> <span class="tbl-count">(<?= $cnt ?> <?= $word ?>)</span><?= $staticLabel ?></h2>
    <?php if ($t === 'co_wor' && $mode === 'users'): ?>
    <button type="button" class="btn-add" id="btn_add_co_wor">Добавить сотрудника</button>
    <?php endif; ?>
    <?php if ($t === 'clients' && $mode === 'users'): ?>
    <button type="button" class="btn-add" id="btn_add_clients">Добавить клиента</button>
    <?php endif; ?>
    <?php if ($t === 'car' && $mode === 'users'): ?>
    <button type="button" class="btn-add" id="btn_add_car">Добавить авто</button>
    <?php endif; ?>
    <?php if ($t === 'gos_num' && $mode === 'users'): ?>
    <button type="button" class="btn-add" id="btn_add_gos_num">Добавить гос номер</button>
    <?php endif; ?>
</div>
<?php if ($t === 'co_wor'): ?>
<div id="co_wor_add_form" style="<?= $add_co_wor_error ? 'display:block;' : 'display:none;' ?>" class="co_wor-form">
    <?php if ($add_co_wor_error): ?>
    <p class="form-error">Ошибка при сохранении: <?= htmlspecialchars($add_co_wor_error) ?></p>
    <?php endif; ?>
    <form method="post">
        <input type="hidden" name="add_co_wor" value="1">
        <div class="form-row"><label for="co_wor_first_name">Имя</label><input type="text" id="co_wor_first_name" name="first_name"></div>
        <div class="form-row"><label for="co_wor_last_name">Фамилия</label><input type="text" id="co_wor_last_name" name="last_name"></div>
        <div class="form-row"><label for="co_wor_patronymic">Отчество</label><input type="text" id="co_wor_patronymic" name="patronymic"></div>
        <div class="form-row"><label for="co_wor_birth_date">Дата рождения</label><input type="date" id="co_wor_birth_date" name="birth_date"></div>
        <div class="form-row"><label for="co_wor_phone">Телефон</label><input type="text" id="co_wor_phone" name="phone" placeholder="+7 747 833 7318" maxlength="15" inputmode="numeric" autocomplete="tel" class="phone-mask-input"></div>
        <p class="form-hint">Логин (6 цифр) и пароль (12 символов) генерируются автоматически при сохранении.</p>
        <button type="submit" class="btn-submit">Сохранить</button>
    </form>
</div>
<?php endif; ?>
<?php if ($t === 'clients'): ?>
<div id="clients_add_form" style="<?= $add_clients_error ? 'display:block;' : 'display:none;' ?>" class="co_wor-form">
    <?php if ($add_clients_error): ?>
    <p class="form-error">Ошибка при сохранении: <?= htmlspecialchars($add_clients_error) ?></p>
    <?php endif; ?>
    <form method="post">
        <input type="hidden" name="add_clients" value="1">
        <div class="form-row"><label for="clients_role">Роль</label><select id="clients_role" name="clients_role"><option value="individual">individual</option><option value="legal">legal</option></select></div>
        <div id="clients_block_individual" class="clients-role-block">
            <div class="form-row"><label for="clients_first_name">Имя</label><input type="text" id="clients_first_name" name="clients_first_name"></div>
            <div class="form-row"><label for="clients_last_name">Фамилия</label><input type="text" id="clients_last_name" name="clients_last_name"></div>
            <div class="form-row"><label for="clients_patronymic">Отчество</label><input type="text" id="clients_patronymic" name="clients_patronymic"></div>
            <div class="form-row"><label for="clients_birth_date">Дата рождения</label><input type="date" id="clients_birth_date" name="clients_birth_date"></div>
        </div>
        <div id="clients_block_legal" class="clients-role-block" style="display:none;">
            <div class="form-row"><label for="clients_comp_name">Название компании</label><input type="text" id="clients_comp_name" name="clients_comp_name" placeholder="ООО Рога и копыта"></div>
        </div>
        <div class="form-row"><label for="clients_phone">Телефон</label><input type="text" id="clients_phone" name="clients_phone" placeholder="+7 747 833 7318" maxlength="15" inputmode="numeric" autocomplete="tel" class="phone-mask-input"></div>
        <button type="submit" class="btn-submit">Сохранить</button>
    </form>
</div>
<?php endif; ?>
<?php if ($t === 'car'): ?>
<div id="car_add_form" style="<?= $add_car_error ? 'display:block;' : 'display:none;' ?>" class="co_wor-form">
    <?php if ($add_car_error): ?>
    <p class="form-error">Ошибка при сохранении: <?= htmlspecialchars($add_car_error) ?></p>
    <?php endif; ?>
    <form method="post">
        <input type="hidden" name="add_car" value="1">
        <div class="form-row"><label for="car_id_client">Клиент</label><select id="car_id_client" name="car_id_client"><option value="">— выбрать —</option><?php foreach (($data['clients'] ?? []) as $c): ?><?php $clientLabel = ((string)($c['role'] ?? '') === 'legal') ? (trim((string)($c['comp_name'] ?? '')) ?: $c['id']) : (trim(($c['last_name'] ?? '') . ' ' . ($c['first_name'] ?? '')) ?: $c['id']); ?><option value="<?= htmlspecialchars($c['id']) ?>"><?= htmlspecialchars($clientLabel) ?></option><?php endforeach; ?></select></div>
        <div class="form-row"><label for="car_id_gos_num">Гос номер</label><select id="car_id_gos_num" name="car_id_gos_num"><option value="">— выбрать —</option><?php foreach (($data['gos_num'] ?? []) as $g): ?><option value="<?= htmlspecialchars($g['id'] ?? '') ?>"><?= htmlspecialchars((string)($g['plate'] ?? $g['id'] ?? '')) ?></option><?php endforeach; ?></select></div>
        <div class="form-row"><label for="car_brand">Марка авто</label><input type="text" id="car_brand" name="car_brand" placeholder="Toyota, Lada..."></div>
        <div class="form-row"><label for="car_color">Цвет</label><input type="text" id="car_color" name="car_color" placeholder="Чёрный, белый..."></div>
        <button type="submit" class="btn-submit">Сохранить</button>
    </form>
</div>
<?php endif; ?>
<?php if ($t === 'gos_num'): ?>
<div id="gos_num_add_form" style="<?= $add_gos_num_error ? 'display:block;' : 'display:none;' ?>" class="co_wor-form">
    <?php if ($add_gos_num_error): ?>
    <p class="form-error">Ошибка при сохранении: <?= htmlspecialchars($add_gos_num_error) ?></p>
    <?php endif; ?>
    <form method="post">
        <input type="hidden" name="add_gos_num" value="1">
        <div class="form-row"><label for="gos_num_plate">Гос номер (plate)</label><input type="text" id="gos_num_plate" name="gos_num_plate" placeholder="123ABC01"></div>
        <button type="submit" class="btn-submit">Сохранить</button>
    </form>
</div>
<?php endif; ?>
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
            // fin_op: порядок num, id, sub_order_id, остальное без изменений
            if ($t === 'fin_op') {
                $first = ['num', 'id', 'sub_order_id'];
                $rest = array_values(array_diff($cols, $first));
                $cols = array_merge($first, $rest);
            }
            // car: порядок id, id_client, id_gos_num, brand, color
            if ($t === 'car') {
                $first = ['id', 'id_client', 'id_gos_num', 'brand', 'color'];
                $rest = array_values(array_diff($cols, $first));
                $cols = array_merge($first, $rest);
            }
            $deleteFormAction = null;
            if ($t === 'co_wor' && $mode === 'users') {
                $cols = array_merge(['_cb'], $cols);
                $deleteFormAction = 'co_wor';
            } elseif ($t === 'clients' && $mode === 'users') {
                $cols = array_merge(['_cb'], $cols);
                $deleteFormAction = 'clients';
            } elseif ($t === 'car' && $mode === 'users') {
                $cols = array_merge(['_cb'], $cols);
                $deleteFormAction = 'car';
            } elseif ($t === 'gos_num' && $mode === 'users') {
                $cols = array_merge(['_cb'], $cols);
                $deleteFormAction = 'gos_num';
            }
            $deleteIdsName = $deleteFormAction === 'clients' ? 'delete_clients_ids[]' : ($deleteFormAction === 'car' ? 'delete_car_ids[]' : ($deleteFormAction === 'gos_num' ? 'delete_gos_num_ids[]' : 'delete_co_wor_ids[]'));
?>
<?php if ($deleteFormAction === 'co_wor'): ?>
<form method="post" class="co_wor-delete-form">
    <input type="hidden" name="delete_co_wor" value="1">
    <button type="submit" class="btn-delete" style="margin-bottom:8px;" onclick="return confirm('Удалить выбранных сотрудников?');">Удалить сотрудника</button>
<?php endif; ?>
<?php if ($deleteFormAction === 'clients'): ?>
<form method="post" class="clients-delete-form">
    <input type="hidden" name="delete_clients" value="1">
    <button type="submit" class="btn-delete" style="margin-bottom:8px;" onclick="return confirm('Удалить выбранных клиентов?');">Удалить клиента</button>
<?php endif; ?>
<?php if ($deleteFormAction === 'car'): ?>
<form method="post" class="car-delete-form">
    <input type="hidden" name="delete_car" value="1">
    <button type="submit" class="btn-delete" style="margin-bottom:8px;" onclick="return confirm('Удалить выбранные авто?');">Удалить авто</button>
<?php endif; ?>
<?php if ($deleteFormAction === 'gos_num'): ?>
<form method="post" class="gos_num-delete-form">
    <input type="hidden" name="delete_gos_num" value="1">
    <button type="submit" class="btn-delete" style="margin-bottom:8px;" onclick="return confirm('Удалить выбранные гос номера?');">Удалить гос номер</button>
<?php endif; ?>
<div class="table-wrapper">
<table>
<thead><tr><?php foreach ($cols as $col): ?><th><?= $col === '_cb' ? 'Удалить' : htmlspecialchars($col) ?></th><?php endforeach; ?></tr></thead>
<tbody>
<?php foreach ($rows as $row): ?>
<tr><?php foreach ($cols as $col): ?><?php if ($col === '_cb'): ?><td><input type="checkbox" name="<?= $deleteIdsName ?>" value="<?= htmlspecialchars($row['id']) ?>"></td><?php else: ?><td><?= htmlspecialchars((string)($row[$col] ?? '')) ?></td><?php endif; ?><?php endforeach; ?></tr>
<?php endforeach; ?>
</tbody>
</table>
</div>
<?php if ($deleteFormAction): ?>
</form>
<?php endif; ?>
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
                ? 'Удалить все заказы и сбросить balance в wall до 0? (wall, co_wor не затрагиваются)'
                : 'Удалить все заказы из order, sub_order, price, fin_op? (wall и co_wor не затрагиваются)';
            if (!confirm(msg)) return;
            var fd = new FormData();
            fd.append('delete_all', '1');
            fd.append('only_new_data', doReset ? '1' : '0');
            fetch(window.location.href, { method: 'POST', body: fd })
                .then(function(r) {
                    if (!r.ok) {
                        r.text().then(function(t) { alert('Ошибка: ' + (t || r.status)); });
                        return;
                    }
                    window.location.reload();
                })
                .catch(function(e) { alert('Ошибка: ' + e.message); });
        });
    }
})();
</script>
<script>
(function(){
    var btn = document.getElementById('btn_add_co_wor');
    var formBlock = document.getElementById('co_wor_add_form');
    if (btn && formBlock) {
        btn.addEventListener('click', function() {
            formBlock.style.display = formBlock.style.display === 'none' ? 'block' : 'none';
        });
    }
    var btnClients = document.getElementById('btn_add_clients');
    var formBlockClients = document.getElementById('clients_add_form');
    if (btnClients && formBlockClients) {
        btnClients.addEventListener('click', function() {
            formBlockClients.style.display = formBlockClients.style.display === 'none' ? 'block' : 'none';
        });
    }
    var clientsRole = document.getElementById('clients_role');
    var blockIndividual = document.getElementById('clients_block_individual');
    var blockLegal = document.getElementById('clients_block_legal');
    function toggleClientsBlocks() {
        if (!clientsRole || !blockIndividual || !blockLegal) return;
        if (clientsRole.value === 'legal') {
            blockIndividual.style.display = 'none';
            blockLegal.style.display = 'block';
        } else {
            blockIndividual.style.display = 'block';
            blockLegal.style.display = 'none';
        }
    }
    if (clientsRole) {
        clientsRole.addEventListener('change', toggleClientsBlocks);
        toggleClientsBlocks();
    }
    var deleteForm = document.querySelector('.co_wor-delete-form');
    if (deleteForm) {
        deleteForm.addEventListener('submit', function(e) {
            var checked = deleteForm.querySelectorAll('input[name="delete_co_wor_ids[]"]:checked');
            if (checked.length === 0) {
                e.preventDefault();
                alert('Выберите хотя бы одного сотрудника для удаления.');
            }
        });
    }
    var deleteFormClients = document.querySelector('.clients-delete-form');
    if (deleteFormClients) {
        deleteFormClients.addEventListener('submit', function(e) {
            var checked = deleteFormClients.querySelectorAll('input[name="delete_clients_ids[]"]:checked');
            if (checked.length === 0) {
                e.preventDefault();
                alert('Выберите хотя бы одного клиента для удаления.');
            }
        });
    }
    var btnCar = document.getElementById('btn_add_car');
    var formBlockCar = document.getElementById('car_add_form');
    if (btnCar && formBlockCar) {
        btnCar.addEventListener('click', function() {
            formBlockCar.style.display = formBlockCar.style.display === 'none' ? 'block' : 'none';
        });
    }
    var btnGosNum = document.getElementById('btn_add_gos_num');
    var formBlockGosNum = document.getElementById('gos_num_add_form');
    if (btnGosNum && formBlockGosNum) {
        btnGosNum.addEventListener('click', function() {
            formBlockGosNum.style.display = formBlockGosNum.style.display === 'none' ? 'block' : 'none';
        });
    }
    var deleteFormCar = document.querySelector('.car-delete-form');
    if (deleteFormCar) {
        deleteFormCar.addEventListener('submit', function(e) {
            var checked = deleteFormCar.querySelectorAll('input[name="delete_car_ids[]"]:checked');
            if (checked.length === 0) {
                e.preventDefault();
                alert('Выберите хотя бы одно авто для удаления.');
            }
        });
    }
    var deleteFormGosNum = document.querySelector('.gos_num-delete-form');
    if (deleteFormGosNum) {
        deleteFormGosNum.addEventListener('submit', function(e) {
            var checked = deleteFormGosNum.querySelectorAll('input[name="delete_gos_num_ids[]"]:checked');
            if (checked.length === 0) {
                e.preventDefault();
                alert('Выберите хотя бы один гос номер для удаления.');
            }
        });
    }
    document.querySelectorAll('.phone-mask-input').forEach(function(phoneInput) {
        function formatPhoneMask() {
            var v = phoneInput.value.replace(/\D/g, '');
            if (v.length === 0) {
                phoneInput.value = '';
                return;
            }
            var digits = (v.charAt(0) === '7') ? v.slice(1, 11) : v.slice(0, 10);
            if (digits.length === 0) {
                phoneInput.value = '';
                return;
            }
            var s = '+7 ' + digits.slice(0, 3);
            if (digits.length > 3) s += ' ' + digits.slice(3, 6);
            if (digits.length > 6) s += ' ' + digits.slice(6, 10);
            phoneInput.value = s;
        }
        phoneInput.addEventListener('focus', function() {
            if (this.value.replace(/\D/g, '').length === 0) this.value = '+7 ';
        });
        phoneInput.addEventListener('input', formatPhoneMask);
        phoneInput.addEventListener('paste', function(e) {
            e.preventDefault();
            var v = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
            if (v.charAt(0) === '7' && v.length >= 11) v = v.slice(1, 11);
            else if (v.length > 10) v = v.slice(0, 10);
            if (v.length === 0) { phoneInput.value = '+7 '; return; }
            phoneInput.value = '+7 ' + v.slice(0, 3) + (v.length > 3 ? ' ' + v.slice(3, 6) : '') + (v.length > 6 ? ' ' + v.slice(6, 10) : '');
        });
    });
})();
</script>
</body>
</html>
