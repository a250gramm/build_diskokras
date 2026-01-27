<?php
header('Content-Type: text/plain; charset=utf-8');

// Получаем текущее время
$hour = (int)date('H');
$minute = (int)date('i');
$second = (int)date('s');

// Форматируем часы и минуты
$time_main = sprintf('%02d:%02d', $hour, $minute);

// Форматируем секунды
$time_seconds = sprintf('%02d', $second);

// Размер секунд в процентах (можно изменить здесь)
$seconds_font_size = 80; // 70% от основного размера

// Возвращаем в формате JSON для удобной обработки в JavaScript
echo json_encode([
    'main' => $time_main,
    'seconds' => $time_seconds,
    'secondsSize' => $seconds_font_size // размер секунд в процентах
]);
?>

