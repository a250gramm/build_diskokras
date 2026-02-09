#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Фабрика элементов
"""

from typing import Any, Dict, Optional
from .base_element import BaseElement
from .text_element import TextElement
from .link_element import LinkElement
from .image_element import ImageElement
from .menu_element import MenuElement
from .field_element import FieldElement
from .list_element import ListElement
from .icon_element import IconElement
from .button_element import ButtonElement


class ElementFactory:
    """Фабрика для создания элементов"""
    
    @staticmethod
    def create(key: str, value: Any, context: Optional[Dict] = None) -> Optional[BaseElement]:
        """
        Создает элемент по типу
        
        Args:
            key: Ключ элемента
            value: Значение элемента
            context: Контекст
            
        Returns:
            Экземпляр элемента или None
        """
        # Определяем тип элемента
        if isinstance(value, list) and len(value) > 0:
            element_type = value[0]
            
            if element_type == 'text':
                return TextElement(key, value, context)
            elif element_type == 'a':
                return LinkElement(key, value, context)
            elif element_type == 'img':
                return ImageElement(key, value, context)
            elif element_type == 'icon':
                return IconElement(key, value, context)
            elif element_type == 'field' or element_type == 'input':
                return FieldElement(key, value, context)
            elif element_type == 'button' or element_type == 'button_json':
                return ButtonElement(key, value, context)
            elif element_type == 'list':
                return ListElement(key, value, context)
        
        # Если это словарь, проверяем специальные случаи
        if isinstance(value, dict):
            # Проверяем, это меню (содержит только ссылки)
            if all(isinstance(v, list) and len(v) > 0 and v[0] == 'a' for v in value.values()):
                return MenuElement(key, value, context)
        
        return None

