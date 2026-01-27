#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoCSS - Автоматические правила для CSS
Автоматически добавляет display:flex и flex-direction на основе структуры
"""

from typing import List


def add_auto_flex_direction(properties: List[str], key_name: str) -> List[str]:
    """
    Автоматически добавляет flex-direction на основе имени ключа:
    - row_* → flex-direction:row
    - column_* → flex-direction:column
    - section_row → flex-direction:row (для секций с колонками)
    - section_column → flex-direction:column (для секций со строками)
    
    Также автоматически добавляет display:flex, если его нет.
    
    Args:
        properties: Список CSS свойств (например, ["width:100%", "align:left"])
        key_name: Имя ключа (например, "row_1", "column_1", "section_row")
        
    Returns:
        Обновленный список свойств с добавленными display:flex и flex-direction
    """
    if not properties:
        properties = []
    
    # Преобразуем в список строк, если нужно
    if not isinstance(properties, list):
        properties = list(properties)
    
    # Проверяем, есть ли уже flex-direction в свойствах
    has_flex_direction = any('flex-direction:' in str(p) for p in properties)
    has_display_flex = any('display:flex' in str(p) for p in properties)
    
    if not has_flex_direction:
        if key_name.startswith('row_') or key_name == 'section_row':
            # Добавляем flex-direction:row для строк
            if not has_display_flex:
                properties.insert(0, 'display:flex')
            # Убираем старые flex-direction, если есть
            properties = [p for p in properties if not str(p).startswith('flex-direction:')]
            properties.append('flex-direction:row')
        elif key_name.startswith('column_') or key_name == 'section_column':
            # Добавляем flex-direction:column для колонок
            if not has_display_flex:
                properties.insert(0, 'display:flex')
            # Убираем старые flex-direction, если есть
            properties = [p for p in properties if not str(p).startswith('flex-direction:')]
            properties.append('flex-direction:column')
    
    return properties


def determine_section_flex_direction(section_config: dict) -> str:
    """
    Определяет flex-direction для секции верхнего уровня на основе структуры:
    - Если есть column_* → flex-direction:row
    - Если есть row_* → flex-direction:column
    
    Args:
        section_config: Конфигурация секции из css.json
        
    Returns:
        'section_row' или 'section_column' или None
    """
    has_columns = any(k.startswith('column_') for k in section_config.keys())
    has_rows = any(k.startswith('row_') for k in section_config.keys())
    
    if has_columns and not has_rows:
        return 'section_row'
    elif has_rows and not has_columns:
        return 'section_column'
    
    return None

