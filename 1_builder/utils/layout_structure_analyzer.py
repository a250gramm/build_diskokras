#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LayoutStructureAnalyzer - Анализ структуры разметки из layout_html.json
Определяет, начинается ли секция с колонок или строк
"""

from typing import Dict, Any, Optional


class LayoutStructureAnalyzer:
    """Анализирует структуру разметки из layout_html.json"""
    
    def __init__(self, html_config: Dict[str, Any]):
        """
        Args:
            html_config: Конфигурация из layout_html.json
        """
        self.html_config = html_config
    
    def is_section_starts_with_rows(self, section_name: str) -> bool:
        """
        Определяет, начинается ли секция со строк (row_X) или с колонок (column_X)
        
        Args:
            section_name: Имя секции (header, turn, body, footer)
            
        Returns:
            True если секция начинается со строк, False если с колонок
        """
        section_data = self.html_config.get(section_name, {})
        
        if not isinstance(section_data, dict):
            return False
        
        # Получаем все ключи верхнего уровня
        top_level_keys = list(section_data.keys())
        
        if not top_level_keys:
            return False
        
        # Проверяем первый ключ - если начинается с row_*, значит секция начинается со строк
        first_key = top_level_keys[0]
        
        if first_key.startswith('row_'):
            return True
        elif first_key.startswith('column_'):
            return False
        
        # Если первый ключ не row_ и не column_, проверяем все ключи
        has_rows = any(k.startswith('row_') for k in top_level_keys)
        has_columns = any(k.startswith('column_') for k in top_level_keys)
        
        # Если есть и строки, и колонки, проверяем порядок
        if has_rows and has_columns:
            # Находим первый ключ row_ и column_
            first_row_key = next((k for k in top_level_keys if k.startswith('row_')), None)
            first_column_key = next((k for k in top_level_keys if k.startswith('column_')), None)
            
            if first_row_key and first_column_key:
                # Определяем, какой ключ идет раньше в словаре
                row_index = top_level_keys.index(first_row_key)
                column_index = top_level_keys.index(first_column_key)
                return row_index < column_index
            elif first_row_key:
                return True
            else:
                return False
        
        # Если есть только строки
        if has_rows:
            return True
        
        # Если есть только колонки (или ничего)
        return False
    
    def is_section_starts_with_columns(self, section_name: str) -> bool:
        """
        Определяет, начинается ли секция с колонок
        
        Args:
            section_name: Имя секции
            
        Returns:
            True если секция начинается с колонок, False если со строк
        """
        return not self.is_section_starts_with_rows(section_name)
    
    def get_section_structure_type(self, section_name: str) -> Optional[str]:
        """
        Возвращает тип структуры секции
        
        Args:
            section_name: Имя секции
            
        Returns:
            'rows' если начинается со строк, 'columns' если с колонок, None если неопределено
        """
        if self.is_section_starts_with_rows(section_name):
            return 'rows'
        elif self.is_section_starts_with_columns(section_name):
            return 'columns'
        return None
    
    def get_all_sections_structure(self) -> Dict[str, str]:
        """
        Возвращает структуру всех секций
        
        Returns:
            Словарь {section_name: 'rows' | 'columns'}
        """
        result = {}
        for section_name in self.html_config.keys():
            structure_type = self.get_section_structure_type(section_name)
            if structure_type:
                result[section_name] = structure_type
        return result

