<?php
/**
 * Возвращает данные таблицы из PostgreSQL в формате JSON.
 * GET: ?table=wall
 */
header('Content-Type: application/json; charset=utf-8');

$table = $_GET['table'] ?? '';
if ($table === '' || !preg_match('/^[a-z0-9_]+$/', $table)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid table']);
    exit;
}

$includePath = __DIR__ . '/../save_bd/include.json';
if (!is_file($includePath)) {
    http_response_code(500);
    echo json_encode(['error' => 'include.json not found']);
    exit;
}

$include = json_decode(file_get_contents($includePath), true);
if (!$include || !isset($include['db_connection'])) {
    http_response_code(500);
    echo json_encode(['error' => 'Invalid include.json']);
    exit;
}

$conn = $include['db_connection'];
if (($conn['driver'] ?? '') !== 'pgsql') {
    http_response_code(500);
    echo json_encode(['error' => 'PostgreSQL required']);
    exit;
}

$port = isset($conn['port']) ? ';port=' . $conn['port'] : '';
$dsn = sprintf('pgsql:host=%s%s;dbname=%s', $conn['host'] ?? 'localhost', $port, $conn['database'] ?? '');
$user = $conn['username'] ?? '';
$pass = $conn['password'] ?? '';

try {
    $pdo = new PDO($dsn, $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $stmt = $pdo->query('SELECT * FROM "' . $table . '" ORDER BY 1');
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($rows, JSON_UNESCAPED_UNICODE);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
