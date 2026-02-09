<?php
/**
 * Принимает JSON с данными формы и перезаписывает файл form_{formClass}_db_paths.json в send_form_json/.
 */
header('Content-Type: application/json; charset=utf-8');

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);

if ($data === null || !is_array($data)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Invalid JSON']);
    exit;
}

$formClass = isset($data['_formClass']) ? preg_replace('/[^a-z0-9_]/i', '', $data['_formClass']) : 'form';
unset($data['_formClass']);

$dir = __DIR__ . '/../send_form_json';
if (!is_dir($dir)) {
    mkdir($dir, 0755, true);
}

$filename = 'form_' . $formClass . '_db_paths.json';
$path = $dir . '/' . $filename;

if (file_put_contents($path, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)) === false) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'Write failed']);
    exit;
}

echo json_encode(['ok' => true, 'file' => $filename]);
