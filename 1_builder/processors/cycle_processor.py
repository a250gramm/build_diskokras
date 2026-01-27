#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Процессор циклов - обрабатывает циклы cycle
"""

import json
from typing import Any, Dict, Optional


class CycleProcessor:
    """Обрабатывает циклы cycle"""
    
    def process_cycle(self, cycle_data: Dict, bd_sources: Dict, template_processor, database_processor, cycle_key: str = 'cycle', original_cycle_key: str = None) -> str:
        """
        Обрабатывает цикл и генерирует контейнер с data-template
        
        Args:
            cycle_data: Данные цикла
            bd_sources: Источники БД
            template_processor: Процессор шаблонов для генерации атрибутов
            database_processor: Процессор БД для генерации span элементов
            cycle_key: Ключ цикла для определения колонок (cycle_col-2, cycle_col-3 и т.д.)
            original_cycle_key: Оригинальный ключ цикла (cycle_gr8, cycle_gr8 col:2,1,1 и т.д.)
            
        Returns:
            HTML строка с контейнером div и data-template
        """
        if not isinstance(cycle_data, dict):
            return ''
        
        html_parts = []
        
        # Генерируем span элементы для всех bd_sources
        if bd_sources:
            for api_name, bd_info in bd_sources.items():
                if api_name in cycle_data and isinstance(cycle_data[api_name], list):
                    bd_value = cycle_data[api_name]
                    bd_html = database_processor.generate_bd_element(api_name, bd_value, '')
                    if bd_html:
                        html_parts.append(bd_html)
        
        # Определяем классы для div[data-template]
        classes = []
        
        # Добавляем класс из оригинального ключа (например, gr8 из cycle_gr8)
        if original_cycle_key:
            from utils.element_utils import extract_col_info_from_key
            clean_key, _ = extract_col_info_from_key(original_cycle_key)
            if clean_key.startswith('cycle_'):
                base_class = clean_key.replace('cycle_', '')
                classes.append(base_class)
        
        # Добавляем класс колонок на основе cycle_key
        # cycle_col-2 -> класс _col-2, cycle_col-3 -> класс _col-3 и т.д.
        if cycle_key.startswith('cycle_col-'):
            col_num = cycle_key.replace('cycle_col-', '')
            classes.append(f'_col-{col_num}')
        
        class_attr = f' class="{" ".join(classes)}"' if classes else ''
        
        # Создаем контейнер с data-template для cycle
        # Передаем всю структуру cycle (включая сам cycle) в data-template
        cycle_template = {'cycle': cycle_data}
        template_attrs = template_processor.generate_template_attrs(cycle_template)
        
        if template_attrs:
            # Добавляем класс к div если есть
            if class_attr:
                # Вставляем класс в template_attrs
                if 'class=' in template_attrs:
                    # Если уже есть class, добавляем к нему
                    existing_classes = template_attrs.split('class="')[1].split('"')[0]
                    all_classes = f"{existing_classes} {' '.join(classes)}".strip()
                    template_attrs = template_attrs.replace(f'class="{existing_classes}"', f'class="{all_classes}"')
                else:
                    # Если нет class, добавляем перед data-template
                    template_attrs = f'{class_attr}{template_attrs}'
            html_parts.append(f'<div{template_attrs}></div>')
        else:
            # Если template_attrs пустой, все равно создаем контейнер с data-template
            # (для случая когда cycle содержит div_field-paymet с api: префиксами)
            template_json = json.dumps(cycle_template, ensure_ascii=False)
            # Используем одинарные кавычки для атрибута, чтобы не экранировать двойные кавычки в JSON
            html_parts.append(f"<div{class_attr} data-template='{template_json}'></div>")
        
        return ''.join(html_parts)
    
    def has_cycle_recursive(self, obj: Any) -> bool:
        """
        Рекурсивно проверяет наличие cycle в структуре
        
        Args:
            obj: Объект для проверки
            
        Returns:
            True если найден cycle
        """
        if not isinstance(obj, dict):
            return False
        # Проверяем cycle и cycle_col-N
        if 'cycle' in obj or any(k.startswith('cycle_col-') for k in obj.keys()):
            return True
        return any(self.has_cycle_recursive(v) for v in obj.values() if isinstance(v, dict))

