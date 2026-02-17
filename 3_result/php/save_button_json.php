<?php
/**
 * Принимает JSON с данными button_json (servi, pay_met, calc и т.д.) и сохраняет в tmp/.
 */
header('Content-Type: application/json; charset=utf-8');

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);

if ($data === null || !is_array($data)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Invalid JSON']);
    exit;
}

$tmpDir = __DIR__ . '/../data/tmp';
if (!is_dir($tmpDir)) {
    @mkdir($tmpDir, 0755, true);
}

$filename = 'shino_' . date('Y-m-d_H-i-s') . '_' . uniqid() . '.json';
$path = $tmpDir . '/' . $filename;

if (file_put_contents($path, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)) === false) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'Write failed']);
    exit;
}

echo json_encode(['ok' => true, 'file' => $filename]);
