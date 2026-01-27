#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Текстовый элемент
"""

from .base_element import BaseElement


class TextElement(BaseElement):
    """Текстовый элемент"""
    
    def render(self) -> str:
        """
        Генерирует HTML для текстового элемента
        
        Формат: ["text", "Текст", "api"]
        Формат с if: ["text", "if:modal_main_btn", "api"]
        Формат с fun: ["text", "fun:total_price"] → data-function-result="total_price"
        Генерирует: <span class="content-KEY" data-source="api" data-api-url="/php/real_date.php">Текст</span>
        Для элементов с API используем span вместо text для поддержки innerHTML
        """
        if not isinstance(self.value, list) or len(self.value) < 2:
            return ''
        
        text_raw = self.value[1]
        
        # Проверяем на функцию (fun:variable)
        function_attr = ''
        if isinstance(text_raw, str) and text_raw.startswith('fun:'):
            function_var = text_raw.split(':', 1)[1]
            function_attr = f' data-function-result="{function_var}"'
            text = '0'  # Placeholder, будет заменен JS
        else:
            # Резолвим text:, icon:, if:
            text = self.resolve_content(text_raw)
        
        css_class = self.get_css_class()
        data_source = self.get_data_source_attr()
        api_url_attr = self.get_api_url_attr()
        
        # Для элементов с API используем span для поддержки innerHTML
        # Иначе используем ключ элемента как тег (label -> <label>, suffix -> <suffix>)
        tag = 'span' if self.has_api_source() else self.key
        
        return f'<{tag} class="{css_class}"{data_source}{api_url_attr}{function_attr}>{text}</{tag}>'
    
    def get_api_url_attr(self) -> str:
        """
        Получает атрибут data-api-url если элемент имеет источник api
        
        Returns:
            ' data-api-url="/diskokras/php/KEY.php"' или ''
        """
        if self.has_api_source():
            # Путь к PHP скрипту на основе ключа элемента
            # Например, real_date -> /diskokras/php/real_date.php
            php_url = f'/diskokras/php/{self.key}.php'
            return f' data-api-url="{php_url}"'
        return ''
