#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Элемент ссылки
"""

from .base_element import BaseElement


class LinkElement(BaseElement):
    """Элемент ссылки"""
    
    def render(self) -> str:
        """
        Генерирует HTML для ссылки
        
        Формат с текстом: ["a", "text:Шиномонтаж", "/shino"]
        Формат с иконкой: ["a", "icon:cart", "/cart"]
        Формат модального: ["a", "text:Текст", "modal", "form"]
        
        Генерирует: <a href="/url">Текст</a> или <a href="/url"><svg>...</svg></a>
        """
        if not isinstance(self.value, list) or len(self.value) < 3:
            return ''
        
        link_content = self.value[1]
        url = self.value[2]
        
        # Резолвим контент (text:, icon:, if:)
        content_html = self.resolve_content(link_content)
        
        # Проверяем модальное окно
        if len(self.value) > 3 and url == 'modal':
            modal_id = self.value[3]
            return f'<a href="modal" class="btn" data-modal="{modal_id}">{content_html}</a>'
        
        # Обычная ссылка
        return f'<a href="{url}" class="btn">{content_html}</a>'
