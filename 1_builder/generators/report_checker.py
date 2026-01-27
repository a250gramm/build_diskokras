#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report_checker.py - Проверка статуса report.json

Проверяет, нужно ли применять стили из report.json
Переключатель находится здесь: 1 = применять стили, 0 = не применять

ВАЖНО: Значение читается напрямую из файла при каждом вызове,
чтобы обойти кеширование модуля Python.
"""

import re
from pathlib import Path


def _get_report_enabled_value() -> int:
    """
    Читает значение REPORT_ENABLED напрямую из файла.
    Это обходит проблему кеширования модуля Python.
    
    Returns:
        0 или 1 - значение переключателя
    """
    # Получаем путь к этому файлу
    script_path = Path(__file__).resolve()
    
    try:
        # Читаем файл построчно
        with open(script_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Ищем последнюю строку, которая содержит "REPORT_ENABLED = " и НЕ является комментарием
        # Проходим по строкам с конца файла (где обычно объявляются переменные)
        for line in reversed(lines):
            stripped = line.strip()
            # Пропускаем пустые строки, комментарии и строки документации
            if not stripped or stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            
            # Ищем паттерн "REPORT_ENABLED = 0" или "REPORT_ENABLED = 1"
            match = re.search(r'^REPORT_ENABLED\s*=\s*(\d+)', stripped)
            if match:
                value = int(match.group(1))
                # Проверяем, что значение валидное (0 или 1)
                if value in (0, 1):
                    return value
        
        # Если не нашли, возвращаем 0 по умолчанию
        return 0
        
    except Exception as e:
        # В случае ошибки возвращаем 0 (выключено)
        print(f"⚠️ Ошибка чтения REPORT_ENABLED: {e}")
        return 0


def is_report_enabled() -> bool:
    """
    Проверяет, включены ли стили из report.json.
    Значение читается напрямую из файла при каждом вызове.
    
    Returns:
        True если REPORT_ENABLED = 1 (применять стили), False если 0 (не применять)
    """
    value = _get_report_enabled_value()
    return value == 1


# Переключатель для применения стилей из report.json
# 1 = применять стили
# 0 = не применять стили
# ВАЖНО: Эта переменная НЕ используется напрямую, значение читается через _get_report_enabled_value()
REPORT_ENABLED = 1


if __name__ == '__main__':
    # Тестирование
    status = is_report_enabled()
    current_value = _get_report_enabled_value()
    
    print(f"REPORT_ENABLED (прочитано из файла): {current_value}")
    print(f"Стили включены: {'✅ ДА' if status else '❌ НЕТ'}")

