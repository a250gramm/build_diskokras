#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор условных CSS стилей - генерирует CSS из if.json
"""

from typing import Dict, Any, Callable


class ConditionalCSSGenerator:
    """Генерирует условные CSS стили из if.json"""
    
    def __init__(self, if_config: Dict[str, Any], 
                 process_media_properties: Callable):
        """
        Args:
            if_config: Конфигурация из if.json
            process_media_properties: Функция для обработки media свойств
        """
        self.if_config = if_config or {}
        self.process_media_properties = process_media_properties
    
    def generate(self) -> str:
        """
        Генерирует условные стили
        
        Returns:
            CSS строка с условными стилями
        """
        if not self.if_config:
            return ''
        
        css_parts = []
        
        for class_name, class_config in self.if_config.items():
            if_conditions = class_config.get('if', [])
            if not if_conditions:
                continue
            
            # Генерируем стили для каждого условия
            for condition in if_conditions:
                # condition может быть "turn.info:text" -> генерируем .content-info
                parts = condition.split('.')
                if len(parts) >= 2:
                    element_name = parts[-1]
                    selector = f".content-{element_name}"
                    
                    # Генерируем стили из свойств класса
                    for prop_key, prop_value in class_config.items():
                        if prop_key == 'if':
                            continue
                        
                        if isinstance(prop_value, dict):
                            media_props = prop_value.get('media', [])
                            if media_props:
                                css_parts.append(f"{selector} {{")
                                css_parts.append(self.process_media_properties(media_props, 0))
                                css_parts.append("}\n\n")
        
        return '\n'.join(css_parts)

