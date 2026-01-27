#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер селекторов - преобразует ключи из css.json в CSS селекторы
"""

from typing import Dict, Any, Optional, Tuple


class SelectorParser:
    """Парсит и преобразует селекторы из css.json в CSS селекторы"""
    
    def __init__(self):
        """Инициализация парсера"""
        pass
    
    def parse_simple_selector(self, key: str) -> Optional[str]:
        """
        Парсит простой селектор (без точек и пробелов)
        
        Args:
            key: Ключ из css.json (например, "header", "header-S", "header-S-L")
            
        Returns:
            CSS селектор или None
        """
        if '.' in key or ' ' in key:
            return None
        
        # Обрабатываем суффиксы
        if key.endswith('-S-L-C'):
            # main_action-S-L-C → .layout.section-main_action .column
            section_name = key[:-6]  # Убираем "-S-L-C"
            return f".layout.section-{section_name} .column"
        elif key.endswith('-S-L'):
            # header-S-L → .layout.section-header
            section_name = key[:-4]  # Убираем "-S-L"
            return f".layout.section-{section_name}"
        elif key.endswith('-S'):
            # header-S → section.section-header
            section_name = key[:-2]  # Убираем "-S"
            return f"section.section-{section_name}"
        else:
            # Обычный ключ без суффикса → .layout.section-{key}
            return f".layout.section-{key}"
    
    def parse_compound_selector(self, key: str) -> Optional[Tuple[str, Optional[str]]]:
        """
        Парсит составной селектор (с точками или пробелами)
        
        Args:
            key: Ключ из css.json (например, "header.2.1.1", "header.nav", "header.2.1.1 .icon_burger")
            
        Returns:
            Кортеж (selector, element_part) или None
        """
        # Проверяем, есть ли пробел в ключе (вложенный селектор)
        if ' ' in key:
            # Формат "header.2.1.1 .icon_burger" (группа + элемент)
            main_parts = key.split(' ', 1)  # Разделяем только по первому пробелу
            group_part = main_parts[0]  # "header.2.1.1"
            element_part = main_parts[1]  # ".icon_burger"
            
            group_keys = group_part.split('.')
            if len(group_keys) == 4 and group_keys[1].isdigit() and group_keys[2].isdigit() and group_keys[3].isdigit():
                section_name = group_keys[0]
                col_num = group_keys[1]
                row_num = group_keys[2]
                gr_num = group_keys[3]
                
                # Преобразуем ".icon_burger" -> "[data-path='icon_burger']"
                element_clean = element_part.lstrip('.')
                
                # Проверяем, есть ли дополнительные селекторы
                if ' ' in element_clean:
                    # Формат "header_nav nav" или "header_nav.opened nav"
                    element_first, *rest = element_clean.split(' ', 1)
                    tag_suffix = ' ' + rest[0] if rest else ''
                    
                    # Проверяем классы в первой части
                    if '.' in element_first:
                        element_name, *classes = element_first.split('.')
                        class_suffix = '.' + '.'.join(classes)
                        selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num} [data-path='{element_name}']{class_suffix}{tag_suffix}"
                    else:
                        selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num} [data-path='{element_first}']{tag_suffix}"
                elif '.' in element_clean:
                    # Формат "header_nav.opened"
                    element_name, *classes = element_clean.split('.')
                    class_suffix = '.' + '.'.join(classes)
                    selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num} [data-path='{element_name}']{class_suffix}"
                else:
                    # Формат "header_nav"
                    selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num} [data-path='{element_clean}']"
                
                return selector, element_part
        
        # Проверяем формат "header.2.1.1" (секция.колонка.ряд.группа)
        if '.' in key:
            parts = key.split('.')
            
            if len(parts) == 4 and parts[1].isdigit() and parts[2].isdigit() and parts[3].isdigit():
                section_name = parts[0]
                col_num = parts[1]
                row_num = parts[2]
                gr_num = parts[3]
                # Преобразуем "header.2.1.1" -> ".group.header-2-1-1"
                selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num}"
                return selector, None
            
            # Формат "header.nav" (секция.элемент)
            elif len(parts) == 2:
                # Проверяем, не является ли это составным селектором типа "header.2.2.1 header_nav"
                section_parts = parts[0].split('.')
                if len(section_parts) > 1 and any(part.isdigit() for part in section_parts):
                    # Это составной селектор, уже обработан выше
                    return None
                
                section_name = parts[0]
                selector_part = parts[1]
                
                # Определяем, это тег (nav, a, div) или класс
                if selector_part in ['nav', 'a', 'img', 'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    # Это тег
                    selector = f".section-{section_name} {selector_part}"
                else:
                    # Это класс
                    selector = f".section-{section_name} .{selector_part}"
                
                return selector, None
        
        return None
    
    def parse_double_selectors(self, value: Dict, base_selector: str) -> str:
        """
        Обрабатывает команду "double" для группировки селекторов
        
        Args:
            value: Значение из css.json
            base_selector: Базовый селектор
            
        Returns:
            Группированный селектор или базовый
        """
        if not isinstance(value, dict):
            return base_selector
        
        double_selectors = value.get('double', [])
        if double_selectors and isinstance(double_selectors, list):
            # Создаем список селекторов (текущий + все из double)
            selectors = [base_selector]
            for double_key in double_selectors:
                double_parts = double_key.split('.')
                if len(double_parts) == 4 and double_parts[1].isdigit() and double_parts[2].isdigit() and double_parts[3].isdigit():
                    double_selector = f".group.{double_parts[0]}-{double_parts[1]}-{double_parts[2]}-{double_parts[3]}"
                    selectors.append(double_selector)
            return ',\n'.join(selectors)
        
        return base_selector

