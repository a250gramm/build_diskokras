#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Элемент иконки
"""

from .base_element import BaseElement


class IconElement(BaseElement):
    """Элемент иконки (SVG или текст)"""
    
    def render(self) -> str:
        """
        Генерирует HTML для иконки
        
        Формат: ["icon", "burger_svg"]
        Формат с if: ["icon", "if:icon_key"]
        Берет содержимое из icon.json по ключу
        Генерирует: <div class="content-KEY">...svg...</div>
        """
        if not isinstance(self.value, list) or len(self.value) < 2:
            return ''
        
        icon_key_raw = self.value[1]
        
        # Если это if:ключ, резолвим значение
        if isinstance(icon_key_raw, str) and icon_key_raw.startswith('if:'):
            icon_key = self.resolve_content(icon_key_raw)
        else:
            icon_key = icon_key_raw
        
        # Получаем иконки из контекста
        icons = self.context.get('icons', {})
        
        # Получаем содержимое иконки
        icon_content = icons.get(icon_key, '')
        
        if not icon_content:
            return ''
        
        css_class = self.get_css_class()
        data_source = self.get_data_source_attr()
        
        return f'<icon class="{css_class}"{data_source}>{icon_content}</icon>'

