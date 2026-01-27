#!/usr:bin/env python3
# -*- coding: utf-8 -*-
"""
Элемент изображения
"""

from .base_element import BaseElement


class ImageElement(BaseElement):
    """Элемент изображения"""
    
    def render(self) -> str:
        """
        Генерирует HTML для изображения
        
        Формат 1: ["img", "logo.png"]
        Генерирует: <img src="../img/logo.png" alt="">
        
        Формат 2: ["img", "logo.png", "/url"]
        Генерирует: <a href="/url"><img src="../img/logo.png" alt=""></a>
        """
        if not isinstance(self.value, list) or len(self.value) < 2:
            return ''
        
        img_filename = self.value[1]
        img_tag = f'<img src="../img/{img_filename}" alt="">'
        
        # Если есть ссылка
        if len(self.value) > 2:
            url = self.value[2]
            return f'<a href="{url}">{img_tag}</a>'
        
        return img_tag
