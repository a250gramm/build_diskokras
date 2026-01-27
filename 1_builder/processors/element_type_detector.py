#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детектор типов элементов - определяет тип элемента
"""

from typing import Any, Dict, Optional
from utils.element_utils import is_menu_dict, is_link_key


class ElementTypeDetector:
    """Определяет тип элемента"""
    
    def detect_type(self, key: str, value: Any) -> str:
        """
        Определяет тип элемента
        
        Args:
            key: Ключ элемента
            value: Значение элемента
            
        Returns:
            Тип элемента: 'menu', 'button', 'form', 'link', 'complex', 'simple'
        """
        if isinstance(value, list) and len(value) > 0:
            element_type = value[0]
            if element_type in ['text', 'a', 'img', 'icon', 'field', 'input', 'button', 'list']:
                return 'simple'
        
        if isinstance(value, dict):
            if is_menu_dict(value):
                return 'menu'
            
            # Проверяем, есть ли вложенный nav или menu
            has_nav = 'nav' in value and isinstance(value['nav'], dict)
            has_menu = 'menu' in value and isinstance(value['menu'], dict)
            
            if has_nav or has_menu:
                nav_children = value.get('nav', {})
                menu_children = value.get('menu', {})
                
                nav_is_menu = all(
                    isinstance(v, list) and len(v) >= 2 and v[0] == 'a' 
                    for v in nav_children.values()
                ) if has_nav else False
                
                menu_is_menu = all(
                    isinstance(v, list) and len(v) >= 2 and v[0] == 'a' 
                    for v in menu_children.values()
                ) if has_menu else False
                
                if nav_is_menu or menu_is_menu:
                    return 'menu'
            
            # Проверяем, это кнопка с модалкой?
            other_keys = [k for k in value.keys() if k not in ['nav', 'menu', 'if']]
            if len(value) == 1 and len(other_keys) == 1:
                nested_value = value[other_keys[0]]
                if isinstance(nested_value, list) and len(nested_value) >= 4 and nested_value[0] == 'button':
                    if isinstance(nested_value[3], dict):
                        return 'button_modal'
            
            # Проверяем наличие HTML-тегов
            html_tags = ['div', 'span', 'section', 'article', 'aside', 'header', 'footer', 'main', 'nav', 'form']
            has_html_tags = any(k in html_tags for k in other_keys)
            if has_html_tags:
                return 'complex'
            
            return 'complex'
        
        return 'simple'
    
    def is_menu(self, value: Dict) -> bool:
        """
        Проверяет, является ли элемент меню
        
        Args:
            value: Значение элемента
            
        Returns:
            True если это меню
        """
        return is_menu_dict(value)
    
    def is_link(self, key: str) -> bool:
        """
        Проверяет, является ли ключ ссылкой (a_)
        
        Args:
            key: Ключ элемента
            
        Returns:
            True если это ссылка
        """
        return is_link_key(key)
    
    def is_html_tag(self, key: str) -> Optional[tuple]:
        """
        Проверяет, является ли ключ HTML тегом
        
        Args:
            key: Ключ элемента
            
        Returns:
            Кортеж (tag_name, class_name) или None
        """
        from utils.element_utils import parse_html_tag
        result = parse_html_tag(key)
        if result:
            # Возвращаем только первые два значения (tag_name, class_name)
            return (result[0], result[1])
        return None

