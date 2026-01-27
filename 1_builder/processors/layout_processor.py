#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Процессор разметки - обрабатывает layout_html.json и генерирует структуру
"""

from typing import Dict, List
from .element_processor import ElementProcessor


class LayoutProcessor:
    """Обрабатывает разметку из layout_html.json и генерирует HTML структуру"""
    
    def __init__(self, html_config: Dict, section_name: str, 
                 element_processor: ElementProcessor, html_attrs: Dict = None):
        """
        Args:
            html_config: Конфиг разметки для секции из layout_html.json
            section_name: Реальное имя секции (header, turn)
            element_processor: Процессор элементов
            html_attrs: HTML атрибуты для групп из html.json
        """
        self.html_config = html_config
        self.section_name = section_name
        self.element_processor = element_processor
        self.html_attrs = html_attrs or {}
        # Контекст для отслеживания текущей позиции
        self.current_col = None
        self.current_row = None
    
    def generate_html(self) -> str:
        """
        Генерирует HTML структуру для секции
        
        Returns:
            HTML строка с полной структурой
        """
        html_parts = [f'<div class="layout section-{self.section_name}">']
        
        # Проверяем, есть ли колонки
        columns = self._get_columns()
        
        if columns:
            html_parts.append('<div class="column">')
            html_parts.append(self._generate_columns(columns))
            html_parts.append('</div>')
        else:
            # Если нет колонок, проверяем строки
            rows = self._get_rows()
            if rows:
                html_parts.append(self._generate_rows(rows))
        
            html_parts.append('</div>')
        
        result = ''.join(html_parts)
        # Отладка: проверяем наличие script тегов
        if 'type="application/json"' in result:
            print(f"   ✅ Script теги найдены в layout_processor для секции {self.section_name}")
        return result
    
    def _get_columns(self) -> List[str]:
        """Получает список колонок"""
        return sorted([k for k in self.html_config.keys() 
                      if k.startswith('col_') or k.startswith('column_')])
    
    def _get_rows(self) -> List[str]:
        """Получает список строк"""
        return sorted([k for k in self.html_config.keys() if k.startswith('row_')])
    
    def _generate_columns(self, columns: List[str]) -> str:
        """
        Генерирует HTML для колонок
        
        Args:
            columns: Список ключей колонок (col_1, col_2, etc)
            
        Returns:
            HTML строка
        """
        html_parts = []
        
        for col_key in columns:
            # Извлекаем номер колонки
            col_num = col_key.split('_')[1]
            self.current_col = col_num
            
            # Нормализуем имя класса к col_X
            col_class = col_key.replace('column_', 'col_')
            
            html_parts.append(f'<div class="{col_class}">')
            
            # Обрабатываем содержимое колонки
            col_config = self.html_config[col_key]
            
            # Ищем строки внутри колонки
            rows = sorted([k for k in col_config.keys() if k.startswith('row_')])
            
            if rows:
                html_parts.append(self._generate_rows_in_column(col_config, rows))
            
            html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def _generate_rows(self, rows: List[str]) -> str:
        """
        Генерирует HTML для строк (без колонок)
        
        Args:
            rows: Список ключей строк
            
        Returns:
            HTML строка
        """
        return self._generate_rows_in_column(self.html_config, rows)
    
    def _generate_rows_in_column(self, config: Dict, rows: List[str]) -> str:
        """
        Генерирует HTML для строк внутри колонки
        
        Args:
            config: Конфиг колонки или секции
            rows: Список ключей строк
            
        Returns:
            HTML строка
        """
        html_parts = []
        
        for row_key in rows:
            # Извлекаем номер ряда
            row_num = row_key.split('_')[1]
            self.current_row = row_num
            
            html_parts.append(f'<div class="row {row_key}">')
            
            # Обрабатываем содержимое строки
            row_config = config[row_key]
            
            # Ищем группы внутри строки
            groups = sorted([k for k in row_config.keys() if k.startswith('gr_')])
            
            if groups:
                html_parts.append(self._generate_groups(row_config, groups))
            
            html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def _generate_groups(self, row_config: Dict, groups: List[str]) -> str:
        """
        Генерирует HTML для групп внутри строки
        
        Args:
            row_config: Конфиг строки
            groups: Список ключей групп (gr_1, gr_2, etc)
            
        Returns:
            HTML строка
        """
        html_parts = []
        
        for group_key in groups:
            # Извлекаем номер группы (gr_1 -> 1)
            group_num = group_key.split('_')[1]
            
            # Формируем путь к группе для поиска атрибутов (например, "header.1.1.1")
            # Нужно найти номер колонки и ряда
            col_num = self._get_current_col_num()
            row_num = self._get_current_row_num()
            group_path = f"{self.section_name}.{col_num}.{row_num}.{group_num}"
            
            # Проверяем, есть ли HTML атрибуты для этой группы
            group_attrs = self.html_attrs.get(group_path, {})
            tag = group_attrs.get('tag', 'div')
            href = group_attrs.get('href', '')
            
            # Класс группы: {СЕКЦИЯ}-{КОЛОНКА}-{СТРОКА}-{ГРУППА}
            group_class = f"{self.section_name}-{col_num}-{row_num}-{group_num}"
            
            # Генерируем открывающий тег
            if tag == 'a' and href:
                html_parts.append(f'<a href="{href}" class="group {group_class}">')
            else:
                html_parts.append(f'<div class="group {group_class}">')
            
            # Обрабатываем элементы в группе
            elements = row_config[group_key]
            
            if isinstance(elements, list):
                for element_path in elements:
                    html_parts.append(self._generate_element(element_path))
            
            # Закрывающий тег
            if tag == 'a' and href:
                html_parts.append('</a>')
            else:
                html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def _get_current_col_num(self) -> str:
        """Получает номер текущей колонки"""
        return self.current_col or "1"
    
    def _get_current_row_num(self) -> str:
        """Получает номер текущего ряда"""
        return self.current_row or "1"
    
    def _generate_element(self, element_path: str) -> str:
        """
        Генерирует HTML для элемента с оберткой marking-item
        
        Args:
            element_path: Путь к элементу (например, "header.logo.title")
            
        Returns:
            HTML строка с оберткой и элементом
        """
        # Получаем HTML элемента
        element_html = self.element_processor.process_element(element_path)
        
        # Оборачиваем в marking-item
        return f'<div class="marking-item" data-path="{element_path}">{element_html}</div>'
