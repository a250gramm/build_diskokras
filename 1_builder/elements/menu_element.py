#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Элемент меню/навигации
"""

from typing import Dict
from .base_element import BaseElement
from utils.path_utils import PathUtils


class MenuElement(BaseElement):
    """Элемент меню (nav)"""
    
    def render(self) -> str:
        """
        Генерирует HTML для меню
        
        Формат: {
            "main": ["a", "Главная", "/index"],
            "about": ["a", "О нас", "/about"]
        }
        
        Генерирует: <nav class="menu nav-menu">
            <a href="index.html" class="btn">Главная</a>
            <a href="about.html" class="btn">О нас</a>
        </nav>
        """
        if not isinstance(self.value, dict):
            return ''
        
        links = []
        for item_key, item_value in self.value.items():
            if isinstance(item_value, list) and len(item_value) >= 3 and item_value[0] == 'a':
                # Формат может быть разным:
                # ["a", "text", "url"] - простой формат (3 элемента)
                # ["a", "parent", "text", "url"] - со вторым параметром родителя (4 элемента)
                # ["a", "parent", "text", "modal", "form"] - модальное окно (5 элементов)
                
                text = ""
                url = ""
                modal_id = ""

                if len(item_value) == 3:
                    # Простой формат: ["a", "text", "url"]
                    text = item_value[1]
                    url = item_value[2]
                elif len(item_value) == 4:
                    # Формат: ["a", "text", "modal", "form"] или ["a", "text", "url", "extra"]
                    text = item_value[1]  # Второй элемент - текст
                    url = item_value[2]   # Третий элемент - url/modal
                    if url == 'modal':
                        modal_id = item_value[3]  # Четвертый элемент - modal_id
                elif len(item_value) >= 5:
                    # Формат с родителем: ["a", "parent", "text", "modal", "form"]
                    text = item_value[2]  # Третий элемент - текст
                    url = item_value[3]   # Четвертый элемент - url/modal
                    if url == 'modal':
                        modal_id = item_value[4]  # Пятый элемент - modal_id
                
                # Проверяем модальное окно
                if url == 'modal':
                    # Это модальное окно
                    links.append(f'<a href="modal" class="btn" data-modal="{modal_id}">{text}</a>')
                else:
                    # Внутренний путь страницы → имя файла для file:// и статики
                    if url.startswith('/') and '//' not in url:
                        url = PathUtils.page_path_to_name(url)
                    links.append(f'<a href="{url}" class="btn">{text}</a>')
        
        if not links:
            return ''
        
        # Добавляем класс на основе ключа элемента (например, nav_menu1 -> menu1)
        key_class = self.key.replace('nav_', '').replace('menu_', '')
        return f'<nav class="menu nav-menu {key_class}">{"".join(links)}</nav>'
