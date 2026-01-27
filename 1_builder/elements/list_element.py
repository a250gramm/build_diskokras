#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Элемент списка
"""

from .base_element import BaseElement


class ListElement(BaseElement):
    """Элемент списка"""
    
    def render(self) -> str:
        """
        Генерирует HTML для списка
        
        Формат: ["list"]
        Генерирует: пустую строку (список генерируется динамически на клиенте)
        """
        # Списки рендерятся на клиенте, поэтому возвращаем пустую строку
        return ''
