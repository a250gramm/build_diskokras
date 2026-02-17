<?php
/**
 * При клике «Отправить BD» — создаёт записи в PostgreSQL по конфигу shino2.json.
 * Формат: cycle: ["json","path"] — цикл по массиву; поля: ["create","uuid"], ["link","table.uuid"], ["json","path"]
 */
header('Content-Type: application/json; charset=utf-8');

$configName = $_GET['config'] ?? $_POST['config'] ?? '';
if ($configName === '') {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Missing config parameter']);
    exit;
}

$postData = json_decode(file_get_contents('php://input'), true) ?: [];
$replaceAll = !empty($postData['replace_all']);
unset($postData['replace_all']);

$saveBdDir = __DIR__ . '/../save_bd/';

$includePath = $saveBdDir . 'include.json';
if (!is_file($includePath)) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'include.json not found']);
    exit;
}

$configPath = $saveBdDir . $configName . '.json';
if (!is_file($configPath)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Config not found: ' . $configName]);
    exit;
}

$include = json_decode(file_get_contents($includePath), true);
$config = json_decode(file_get_contents($configPath), true);

if (!$include || !isset($include['db_connection'])) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'Invalid include.json']);
    exit;
}

$conn = $include['db_connection'];
if (($conn['driver'] ?? '') !== 'pgsql') {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'PostgreSQL required']);
    exit;
}

$dsn = sprintf(
    'pgsql:host=%s;dbname=%s',
    $conn['host'] ?? 'localhost',
    $conn['database'] ?? ''
);
$user = $conn['username'] ?? '';
$pass = $conn['password'] ?? '';

try {
    $pdo = new PDO($dsn, $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'DB connect: ' . $e->getMessage()]);
    exit;
}

if ($replaceAll) {
    foreach (['price', 'sub_order', 'order'] as $t) {
        $pdo->exec('DELETE FROM "' . $t . '"');
    }
}

$ctx = [];
$resultId = null;

function genUuid() {
    return sprintf(
        '%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
        random_int(0, 0xffff), random_int(0, 0xffff),
        random_int(0, 0xffff),
        random_int(0, 0x0fff) | 0x4000,
        random_int(0, 0x3fff) | 0x8000,
        random_int(0, 0xffff), random_int(0, 0xffff), random_int(0, 0xffff)
    );
}

function resolveRef($ref, $ctx) {
    $parts = explode('.', $ref);
    $val = $ctx;
    foreach ($parts as $p) {
        $val = $val[$p] ?? null;
        if ($val === null) return null;
    }
    return $val;
}

function resolveJsonPath($path, $postData, $item = null) {
    $parts = explode('.', $path);
    if ($item !== null && count($parts) >= 2) {
        return $item[$parts[1]] ?? null;
    }
    $val = $postData;
    foreach ($parts as $p) {
        $val = $val[$p] ?? null;
        if ($val === null) return null;
    }
    if (is_array($val) && count($parts) >= 2) {
        $field = $parts[1];
        $sum = 0;
        foreach ($val as $row) {
            if (isset($row[$field])) $sum += (float)$row[$field];
        }
        return $sum;
    }
    return $val;
}

try {
    foreach ($config as $table => $fields) {
        if (!is_array($fields)) continue;

        $cycleArrayKey = null;
        if (isset($fields['cycle'])) {
            $c = $fields['cycle'];
            if (is_array($c) && ($c[0] ?? '') === 'json' && isset($c[1])) {
                $path = $c[1];
                if (is_array($postData[$path] ?? null)) {
                    $cycleArrayKey = $path;
                }
            }
        }

        $rowsToInsert = $cycleArrayKey !== null ? ($postData[$cycleArrayKey] ?? []) : [null];
        if (!is_array($rowsToInsert)) $rowsToInsert = [null];

        foreach ($rowsToInsert as $idx => $rowItem) {
            $cols = [];
            $vals = [];

            foreach ($fields as $field => $type) {
                if ($field === 'cycle') continue;
                if (!is_array($type) || !isset($type[0])) continue;

                $action = $type[0];
                $arg = $type[1] ?? '';

                if ($action === 'create' && $arg === 'uuid') {
                    $val = genUuid();
                    $cols[] = $field;
                    $vals[] = $val;
                    if (!isset($ctx[$table])) $ctx[$table] = [];
                    $ctx[$table][$field] = $val;
                    $ctx[$table]['uuid'] = $val;
                    if ($table === 'order' && $field === 'id') $resultId = $val;
                } elseif ($action === 'link' && $arg !== '') {
                    $val = resolveRef($arg, $ctx);
                    if ($val !== null) {
                        $cols[] = $field;
                        $vals[] = $val;
                    }
                } elseif ($action === 'json' && $arg !== '') {
                    $val = resolveJsonPath($arg, $postData, $rowItem);
                    if ($val !== null) {
                        $cols[] = $field;
                        $vals[] = $val;
                    }
                }
            }

            if (!empty($cols)) {
                $placeholders = implode(', ', array_fill(0, count($cols), '?'));
                $stmt = $pdo->prepare('INSERT INTO "' . $table . '" (' . implode(', ', $cols) . ') VALUES (' . $placeholders . ')');
                $stmt->execute($vals);
            }

            if ($cycleArrayKey === null) break;
        }
    }
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'DB: ' . $e->getMessage()]);
    exit;
}

if ($resultId === null) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'No order id in config']);
    exit;
}

echo json_encode(['ok' => true, 'id' => $resultId]);
