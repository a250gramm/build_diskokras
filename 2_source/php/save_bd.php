<?php
/**
 * При клике «Отправить BD» — создаёт записи в PostgreSQL по конфигу shino2.json.
 * Формат: cycle: ["json","path"] или cycle:json-<path> — цикл по массиву;
 * search:json-<path> — найти строку (path = массив.поле для id) и UPDATE; поля: ["up","sum","json.path"] — прибавить к balance;
 * row_1, row_2... — фиксированное число строк;
 * поля: ["create","uuid"], ["link","table.uuid"], ["json","path"], ["text","значение"]
 */
header('Content-Type: application/json; charset=utf-8');

// Если PHP упадёт с фатальной ошибкой — вернуть JSON с текстом (иначе 500 с пустым телом)
register_shutdown_function(function() {
    $err = error_get_last();
    if ($err && in_array($err['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR], true)) {
        if (!headers_sent()) {
            header('Content-Type: application/json; charset=utf-8');
            http_response_code(500);
        }
        echo json_encode(['ok' => false, 'error' => 'PHP: ' . $err['message'] . ' (файл ' . basename($err['file']) . ':' . $err['line'] . ')']);
    }
});

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
if (!is_file($includePath) && isset($_SERVER['DOCUMENT_ROOT'])) {
    $saveBdDir = rtrim($_SERVER['DOCUMENT_ROOT'], '/') . '/save_bd/';
    $includePath = $saveBdDir . 'include.json';
}
if (!is_file($includePath)) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'include.json не найден. Путь: ' . $saveBdDir]);
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

$port = isset($conn['port']) ? ';port=' . $conn['port'] : '';
$dsn = sprintf(
    'pgsql:host=%s%s;dbname=%s',
    $conn['host'] ?? 'localhost',
    $port,
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

// Порядок удаления: сначала таблицы со ссылками на другие (fin_op → sub_order), потом sub_order, order
if ($replaceAll) {
    foreach (['price', 'fin_op', 'sub_order', 'order'] as $t) {
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

        $searchKey = null;
        $searchFields = null;
        foreach (array_keys($fields) as $k) {
            if (preg_match('/^search:json-(.+)$/', $k, $m)) {
                $searchKey = $m[1];
                $searchFields = $fields[$k];
                break;
            }
        }

        if ($searchKey !== null && is_array($searchFields)) {
            $pathParts = explode('.', $searchKey, 2);
            $arrKey = $pathParts[0];
            $idField = $pathParts[1] ?? 'id';
            $items = $postData[$arrKey] ?? [];
            if (!is_array($items)) $items = [];
            if ($items && !isset($items[0]) && isset($items[$idField])) {
                $items = [$items];
            }
            foreach ($items as $item) {
                $rowId = is_array($item) ? ($item[$idField] ?? null) : null;
                if ($rowId === null) continue;
                foreach ($searchFields as $field => $type) {
                    if (!is_array($type) || ($type[0] ?? '') !== 'up') continue;
                    $op = $type[1] ?? '';
                    $path = isset($type[2]) ? preg_replace('/^json\./', '', $type[2]) : '';
                    if ($op === 'sum' && $path !== '') {
                        $pathFirst = explode('.', $path, 2)[0];
                        $useItem = ($pathFirst === $arrKey) ? $item : null;
                        $addVal = (float) resolveJsonPath($path, $postData, $useItem);
                        $stmt = $pdo->prepare('UPDATE "' . $table . '" SET "' . $field . '" = "' . $field . '" + ? WHERE id = ?');
                        $stmt->execute([$addVal, $rowId]);
                    }
                }
            }
            continue;
        }

        $cycleArrayKey = null;
        $rowKeys = [];
        $cycleFields = null;

        foreach (array_keys($fields) as $k) {
            if (preg_match('/^cycle:json-(.+)$/', $k, $m)) {
                $path = $m[1];
                if (is_array($postData[$path] ?? null)) {
                    $cycleArrayKey = $path;
                    $cycleFields = $fields[$k];
                }
                break;
            }
        }

        if ($cycleFields === null && isset($fields['cycle'])) {
            $c = $fields['cycle'];
            if (is_array($c) && ($c[0] ?? '') === 'json' && isset($c[1])) {
                $path = $c[1];
                if (is_array($postData[$path] ?? null)) {
                    $cycleArrayKey = $path;
                    $cycleFields = $fields;
                }
            }
        }

        if ($cycleFields === null) {
            foreach (array_keys($fields) as $k) {
                if (preg_match('/^row_\d+$/', $k)) {
                    $rowKeys[] = $k;
                }
            }
            usort($rowKeys, function ($a, $b) {
                return (int) substr($a, 4) - (int) substr($b, 4);
            });
        }

        if ($cycleFields !== null) {
            $fields = $cycleFields;
        }

        if (!empty($rowKeys)) {
            foreach ($rowKeys as $rk) {
                $rowFields = $fields[$rk] ?? [];
                if (!is_array($rowFields)) continue;
                $cols = [];
                $vals = [];
                foreach ($rowFields as $field => $type) {
                    if (!is_array($type) || !isset($type[0])) continue;
                    $action = $type[0];
                    $arg = $type[1] ?? '';
                    if ($action === 'create' && $arg === 'uuid') {
                        $val = genUuid();
                        $cols[] = $field;
                        $vals[] = $val;
                        if (!isset($ctx[$table . '_' . $rk])) $ctx[$table . '_' . $rk] = [];
                        $ctx[$table . '_' . $rk][$field] = $val;
                        $ctx[$table . '_' . $rk]['uuid'] = $val;
                        if ($table === 'order' && $field === 'id') $resultId = $val;
                    } elseif ($action === 'link' && $arg !== '') {
                        $val = resolveRef($arg, $ctx);
                        if ($val !== null) {
                            $cols[] = $field;
                            $vals[] = $val;
                        }
                    } elseif ($action === 'json' && $arg !== '') {
                        $val = resolveJsonPath($arg, $postData, null);
                        if ($val !== null) {
                            $cols[] = $field;
                            $vals[] = $val;
                        }
                    } elseif ($action === 'text') {
                        $cols[] = $field;
                        $vals[] = $arg;
                    }
                }
                if (!empty($cols)) {
                    $placeholders = implode(', ', array_fill(0, count($cols), '?'));
                    $stmt = $pdo->prepare('INSERT INTO "' . $table . '" (' . implode(', ', $cols) . ') VALUES (' . $placeholders . ')');
                    $stmt->execute($vals);
                }
            }
            continue;
        }

        $rowsToInsert = $cycleArrayKey !== null ? ($postData[$cycleArrayKey] ?? []) : [null];
        if (!is_array($rowsToInsert)) $rowsToInsert = [null];

        foreach ($rowsToInsert as $idx => $rowItem) {
            $cols = [];
            $vals = [];

            foreach ($fields as $field => $type) {
                if ($field === 'cycle' || preg_match('/^cycle:/', $field)) continue;
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
                } elseif ($action === 'text') {
                    $cols[] = $field;
                    $vals[] = $arg;
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
