#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Базовый класс элемента
"""

from typing import Any, Dict, Optional


class BaseElement:
    """Базовый класс для всех элементов"""
    
    def __init__(self, key: str, value: Any, context: Optional[Dict] = None):
        """
        Args:
            key: Ключ элемента в sections.json
            value: Значение элемента
            context: Контекст (current_page, section_name, etc)
        """
        self.key = key
        self.value = value
        self.context = context or {}
    
    def render(self) -> str:
        """
        Рендерит элемент в HTML
        
        Returns:
            HTML строка
        """
        raise NotImplementedError("Подклассы должны реализовать метод render()")
    
    def resolve_content(self, content_raw: str) -> str:
        """
        Резолвит содержимое с префиксами text:, icon:, if:
        
        Args:
            content_raw: Сырое содержимое (например, "text:Текст" или "if:modal_main_btn")
            
        Returns:
            Разрешённое содержимое (текст, SVG иконка или значение из if.json)
        """
        if not isinstance(content_raw, str) or ':' not in content_raw:
            return content_raw
        
        content_type, content_value = content_raw.split(':', 1)
        
        # Если text:Текст - возвращаем текст
        if content_type == 'text':
            return content_value
        
        # Если icon:ключ - берём иконку из icons
        elif content_type == 'icon':
            if self.context and 'icons' in self.context:
                icons = self.context['icons']
                if content_value in icons:
                    return icons[content_value]
                else:
                    return f'[Icon: {content_value} not found]'
            else:
                return f'[No icons loaded]'
        
        # Если if:ключ - берём значение из if_values
        elif content_type == 'if':
            if self.context and 'if_values' in self.context:
                if_values = self.context['if_values']
                current_page = self.context.get('current_page', '')
                page_url = f"/{current_page}"
                
                # Ищем ключ в if_values
                if content_value in if_values:
                    page_values = if_values[content_value]
                    if page_url in page_values:
                        result = page_values[page_url]
                        # Если результат - массив, берём первый элемент
                        if isinstance(result, list) and len(result) > 0:
                            result = result[0]
                        # Рекурсивно резолвим (может быть вложенный text: или icon:)
                        return self.resolve_content(result)
                    else:
                        return f'[No if value for page: {page_url}]'
                else:
                    return f'[If key not found: {content_value}]'
            else:
                return f'[No if_values loaded]'
        
        # Иначе возвращаем как есть
        return content_raw
    
    def get_css_class(self) -> str:
        """
        Получает CSS класс для элемента
        
        Returns:
            CSS класс (например, content-title)
        """
        return f"content-{self.key}"
    
    def has_api_source(self) -> bool:
        """
        Проверяет, имеет ли элемент источник api
        
        Returns:
            True если элемент получает данные из api
        """
        if isinstance(self.value, list) and len(self.value) > 2:
            return self.value[2] == 'api'
        return False
    
    def get_data_source_attr(self) -> str:
        """
        Получает атрибут data-source если есть
        
        Returns:
            ' data-source="api"' или ''
        """
        if self.has_api_source():
            return ' data-source="api"'
        return ''
