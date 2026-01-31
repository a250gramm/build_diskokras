#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка сборки: исходники и логика выдачи (без записи в 3_result).
"""
import sys
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent
source_dir = project_root / '2_source'
result_dir = project_root / '3_result'

errors = []

# 1. JS: в 2_source/js/functions.js должен быть фикс (field-paymet без content-)
fix_marker = 'if (/^\\d/.test(match[1]))'
fix_else = 'className = match[1];'
functions_js = source_dir / 'js' / 'functions.js'
if functions_js.exists():
    text = functions_js.read_text(encoding='utf-8')
    if fix_marker not in text or fix_else not in text:
        errors.append(f"2_source/js/functions.js: нет фикса для div.field-paymet (ожидаются '{fix_marker}' и '{fix_else}')")
else:
    errors.append("2_source/js/functions.js не найден")

# 2. JS: симуляция объединения — итог должен содержать фикс
source_js_dir = source_dir / 'js'
if source_js_dir.exists():
    js_parts = []
    for js_file in sorted(source_js_dir.glob('*.js')):
        if js_file.is_file():
            js_parts.append(js_file.read_text(encoding='utf-8'))
    combined_js = '\n\n'.join(js_parts)
    if fix_marker not in combined_js or fix_else not in combined_js:
        errors.append("Объединённый JS из 2_source/js не содержит фикса field-paymet")
else:
    errors.append("2_source/js не найден")

# 3. CSS: в 3_result должен быть селектор для .content-2-col
css_file = result_dir / 'css' / 'style.css'
if css_file.exists():
    css_text = css_file.read_text(encoding='utf-8')
    if "div.field-paymet .content-2-col" not in css_text or "[data-path='main_btn']" not in css_text:
        errors.append("3_result/css/style.css: нет селектора [data-path='main_btn'] div.field-paymet .content-2-col")
else:
    errors.append("3_result/css/style.css не найден")

if errors:
    print("ПРОВЕРКА НЕ ПРОЙДЕНА:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("Проверка пройдена: исходники и результат согласованы (JS фикс + CSS селектор).")
sys.exit(0)
