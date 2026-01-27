#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для работы с элементами
"""

import re
from typing import Dict, Optional, Tuple


def parse_element_path(path: str) -> Dict[str, str]:
    """
    Парсит путь к элементу
    
    Args:
        path: Путь к элементу (например, "logo_img" или "header.nav")
        
    Returns:
        Словарь с частями пути
    """
    if '.' not in path:
        return {'key': path, 'parts': [path]}
    
    parts = path.split('.')
    return {'key': parts[-1], 'parts': parts}


def extract_class_from_key(key: str) -> str:
    """
    Извлекает класс из ключа
    
    Args:
        key: Ключ элемента (например, "div_gr1" или "nav_menu1")
        
    Returns:
        Класс (например, "gr1" или "menu1")
    """
    # Убираем числовой префикс (например "1.div_gr5" → "div_gr5")
    numeric_prefix_match = re.match(r'^(\d+)\.(.+)$', key)
    if numeric_prefix_match:
        key = numeric_prefix_match.group(2)
    
    # Проверяем формат с суффиксом (div_1, nav_menu1, div-1)
    html_tags = ['div', 'span', 'section', 'article', 'aside', 'header', 'footer', 'main', 'nav', 'form']
    
    for tag in html_tags:
        if key.startswith(tag):
            if key == tag:
                return ''
            suffix = key[len(tag):]
            if suffix.startswith('_') or suffix.startswith('-'):
                return suffix[1:]  # Убираем префикс _ или -
    
    return key


def normalize_numeric_prefix(key: str) -> str:
    """
    Убирает числовой префикс из ключа
    
    Args:
        key: Ключ с префиксом (например, "1.div_gr5")
        
    Returns:
        Ключ без префикса (например, "div_gr5")
    """
    numeric_prefix_match = re.match(r'^(\d+)\.(.+)$', key)
    if numeric_prefix_match:
        potential_key = numeric_prefix_match.group(2)
        # Проверяем начинается ли с HTML тега
        html_tags = ['div', 'span', 'section', 'article', 'aside', 'header', 'footer', 'main', 'nav', 'form']
        if any(potential_key.startswith(tag) for tag in html_tags):
            return potential_key
    return key


def parse_html_tag(key: str) -> Optional[Tuple[str, str, Optional[Dict[str, any]]]]:
    """
    Парсит HTML тег из ключа, включая синтаксис col:
    
    Args:
        key: Ключ элемента (например, "div_gr1", "nav_menu1", "div wrapper", "div_field-paymet col:2,2,2")
        
    Returns:
        Кортеж (tag_name, class_name, col_info) или None если это не HTML тег
        col_info может быть None если синтаксис col: не найден
    """
    html_tags = ['div', 'span', 'section', 'article', 'aside', 'header', 'footer', 'main', 'nav', 'form']
    tag_name = None
    class_name = None
    
    # Извлекаем информацию о col: синтаксисе
    clean_key, col_info = extract_col_info_from_key(key)
    
    # Убираем числовой префикс
    clean_key = normalize_numeric_prefix(clean_key)
    
    # Проверяем формат "tag classname" (с пробелом)
    if ' ' in clean_key:
        parts = clean_key.split(' ', 1)
        if parts[0] in html_tags:
            return (parts[0], parts[1], col_info)
    
    # Проверяем формат с суффиксом (div_1, nav_menu1, div-1)
    for tag in html_tags:
        if clean_key.startswith(tag):
            if clean_key == tag:
                return (tag, None, col_info)
            if clean_key[len(tag):][0] in ['_', '-']:
                tag_name = tag
                suffix = clean_key[len(tag):]
                if suffix.startswith('_') or suffix.startswith('-'):
                    class_name = suffix[1:]  # Убираем префикс _ или -
                return (tag_name, class_name, col_info)
    
    # Точное совпадение
    if clean_key in html_tags:
        return (clean_key, None, col_info)
    
    return None


def is_link_key(key: str) -> bool:
    """
    Проверяет, является ли ключ ссылкой (начинается с a_)
    
    Args:
        key: Ключ элемента
        
    Returns:
        True если ключ начинается с a_
    """
    return key.startswith('a_')


def extract_link_info(key: str, value: Dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Извлекает информацию о ссылке из ключа и значения
    
    Args:
        key: Ключ элемента (например, "a_gr2")
        value: Значение элемента (может содержать "in" для href)
        
    Returns:
        Кортеж (href, class_name)
    """
    if not is_link_key(key):
        return (None, None)
    
    # Убираем префикс "a_" - получаем класс
    link_class = key[2:]  # Все после "a_"
    
    # Если значение - словарь, ищем "in" для href
    if isinstance(value, dict):
        if 'in' in value and isinstance(value['in'], list) and len(value['in']) > 0:
            link_href = value['in'][0]  # Берем первый элемент из массива
        else:
            link_href = '/'  # По умолчанию
    else:
        link_href = '/'  # По умолчанию
    
    return (link_href, link_class)


def is_menu_dict(value: Dict) -> bool:
    """
    Проверяет, является ли словарь меню (все значения - массивы со ссылками)
    
    Args:
        value: Словарь для проверки
        
    Returns:
        True если это меню
    """
    if not isinstance(value, dict) or len(value) == 0:
        return False
    
    return all(
        isinstance(v, list) and len(v) >= 2 and v[0] == 'a' 
        for v in value.values() 
        if not isinstance(v, dict)
    )


def parse_col_syntax(key: str) -> Optional[Dict[str, any]]:
    """
    Парсит синтаксис col: из ключа элемента
    
    Args:
        key: Ключ элемента (например, "div_field-paymet col:2,2,2" или "div_1-col:20%")
        
    Returns:
        Словарь с информацией о колонках:
        - type: "adaptive" (col:2,1,1) или "percentage" (col:20%)
        - desktop: количество колонок для desktop или процент
        - tablet: количество колонок для tablet (только для adaptive)
        - mobile: количество колонок для mobile (только для adaptive)
        - original_key: ключ без col: синтаксиса
        Или None если синтаксис col: не найден
    """
    # Ищем паттерн " col:X,Y,Z" или " col:X%" в конце ключа
    col_pattern = r'\s+col:([^\s]+)'
    match = re.search(col_pattern, key)
    
    if not match:
        return None
    
    col_value = match.group(1)
    original_key = re.sub(col_pattern, '', key)
    
    # Проверяем формат col:20% (процентная ширина)
    if '%' in col_value:
        percentage = col_value.replace('%', '')
        try:
            percent_value = float(percentage)
            return {
                'type': 'percentage',
                'percentage': percent_value,
                'original_key': original_key
            }
        except ValueError:
            return None
    
    # Проверяем формат col:2,1,1 (адаптивные колонки)
    if ',' in col_value:
        parts = col_value.split(',')
        if len(parts) == 3:
            try:
                desktop = int(parts[0].strip())
                tablet = int(parts[1].strip())
                mobile = int(parts[2].strip())
                return {
                    'type': 'adaptive',
                    'desktop': desktop,
                    'tablet': tablet,
                    'mobile': mobile,
                    'original_key': original_key
                }
            except ValueError:
                return None
        elif len(parts) == 1:
            # col:2 (одинаковое количество колонок для всех устройств)
            try:
                cols = int(parts[0].strip())
                return {
                    'type': 'adaptive',
                    'desktop': cols,
                    'tablet': cols,
                    'mobile': cols,
                    'original_key': original_key
                }
            except ValueError:
                return None
    
    # Просто число без запятых - одинаковое количество колонок
    try:
        cols = int(col_value)
        return {
            'type': 'adaptive',
            'desktop': cols,
            'tablet': cols,
            'mobile': cols,
            'original_key': original_key
        }
    except ValueError:
        return None


def extract_col_info_from_key(key: str) -> Tuple[str, Optional[Dict[str, any]]]:
    """
    Извлекает информацию о col: синтаксисе из ключа и возвращает очищенный ключ
    
    Args:
        key: Ключ элемента (например, "div_field-paymet col:2,2,2")
        
    Returns:
        Кортеж (очищенный_ключ, col_info) где col_info может быть None
    """
    col_info = parse_col_syntax(key)
    if col_info:
        return (col_info['original_key'], col_info)
    return (key, None)

