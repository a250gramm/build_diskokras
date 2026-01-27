#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Процессор циклов - обрабатывает циклы cycle
"""

import json
from typing import Any, Dict, Optional


class CycleProcessor:
    """Обрабатывает циклы cycle"""
    
    def process_cycle(self, cycle_data: Dict, bd_sources: Dict, template_processor, database_processor, cycle_key: str = 'cycle') -> str:
        """
        Обрабатывает цикл и генерирует контейнер с data-template
        
        Args:
            cycle_data: Данные цикла
            bd_sources: Источники БД
            template_processor: Процессор шаблонов для генерации атрибутов
            database_processor: Процессор БД для генерации span элементов
            cycle_key: Ключ цикла (cycle, cycle_col-2, cycle_col-3 и т.д.)
            
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
        
        # Определяем класс для div[data-template] на основе cycle_key
        # cycle_col-2 -> класс _col-2, cycle_col-3 -> класс _col-3 и т.д.
        col_class = ''
        if cycle_key.startswith('cycle_col-'):
            col_num = cycle_key.replace('cycle_col-', '')
            col_class = f' _col-{col_num}'
        
        # Создаем контейнер с data-template для cycle
        # Передаем всю структуру cycle (включая сам cycle) в data-template
        cycle_template = {'cycle': cycle_data}
        template_attrs = template_processor.generate_template_attrs(cycle_template)
        
        if template_attrs:
            # Добавляем класс к div если есть
            if col_class:
                # Вставляем класс в template_attrs перед закрывающей скобкой
                # template_attrs может быть вида: ' data-template="..."' или ' class="..." data-template="..."'
                if 'class=' in template_attrs:
                    # Если уже есть class, добавляем к нему
                    template_attrs = template_attrs.replace('class="', f'class="{col_class.lstrip()} ')
                else:
                    # Если нет class, добавляем перед data-template
                    template_attrs = f' class="{col_class.lstrip()}"{template_attrs}'
            html_parts.append(f'<div{template_attrs}></div>')
        else:
            # Если template_attrs пустой, все равно создаем контейнер с data-template
            # (для случая когда cycle содержит div_field-paymet с api: префиксами)
            template_json = json.dumps(cycle_template, ensure_ascii=False)
            # Используем одинарные кавычки для атрибута, чтобы не экранировать двойные кавычки в JSON
            class_attr = f' class="{col_class.lstrip()}"' if col_class else ''
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

