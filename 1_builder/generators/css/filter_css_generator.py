#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор фильтрованных CSS стилей - генерирует CSS из filter.json
"""

from typing import Dict, Any, Callable


class FilterCSSGenerator:
    """Генерирует фильтрованные CSS стили из filter.json"""
    
    def __init__(self, filter_config: Dict[str, Any],
                 default_config: Dict[str, Any],
                 process_properties: Callable,
                 process_media_properties: Callable):
        """
        Args:
            filter_config: Конфигурация из filter.json
            default_config: Конфигурация из default.json (для devices)
            process_properties: Функция для обработки CSS свойств
            process_media_properties: Функция для обработки media свойств
        """
        self.filter_config = filter_config or {}
        self.default_config = default_config or {}
        self.process_properties = process_properties
        self.process_media_properties = process_media_properties
    
    def generate(self) -> str:
        """
        Генерирует фильтрованные стили
        
        Returns:
            CSS строка с фильтрованными стилями
        """
        if not self.filter_config:
            return ''
        
        css_parts = []
        
        # Получаем devices из wrapper или используем значения по умолчанию
        wrapper = self.default_config.get('wrapper', {})
        devices = self.default_config.get('devices', {})
        if not devices and wrapper:
            # Если devices нет, но есть wrapper, используем его
            devices = {
                'desktop': wrapper.get('desktop', ['1200px']),
                'tablet': wrapper.get('tablet', ['768px']),
                'mobile': wrapper.get('mobile', ['320px'])
            }
        tablet_breakpoint = devices.get('tablet', ['768px'])[0] if devices else '768px'
        mobile_breakpoint = devices.get('mobile', ['320px'])[0] if devices else '320px'
        
        for class_name, class_config in self.filter_config.items():
            filter_conditions = class_config.get('filter', [])
            if not filter_conditions:
                continue
            
            # Генерируем селекторы для каждого условия
            for condition in filter_conditions:
                # condition может быть "header.menu" -> генерируем .header-menu
                selector = f".{condition.replace('.', '-')}"
                
                general_props = class_config.get('general', [])
                if general_props:
                    css_parts.append(f"{selector} {{")
                    css_parts.append(self.process_properties(general_props))
                    css_parts.append("}\n\n")
                
                # Media свойства
                media_props = class_config.get('media', [])
                if media_props:
                    # Desktop
                    css_parts.append(self.process_media_properties(media_props, 0))
                    
                    # Tablet
                    if len(media_props) > 1:
                        css_parts.append(f"@media (max-width: {tablet_breakpoint}) {{")
                        css_parts.append(f"    {selector} {{")
                        css_parts.append(self.process_media_properties(media_props, 1, indent="        "))
                        css_parts.append("    }")
                        css_parts.append("}\n\n")
                    
                    # Mobile
                    if len(media_props) > 2:
                        css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{")
                        css_parts.append(f"    {selector} {{")
                        css_parts.append(self.process_media_properties(media_props, 2, indent="        "))
                        css_parts.append("    }")
                        css_parts.append("}\n\n")
                
                # Theme стили
                for theme_key in ['theme_light', 'theme_dark']:
                    if theme_key in class_config:
                        theme_props = class_config[theme_key]
                        static_props = theme_props.get('static', [])
                        hover_props = theme_props.get('hover', [])
                        
                        if static_props:
                            css_parts.append(f"{selector} {{")
                            css_parts.append(self.process_properties(static_props))
                            css_parts.append("}\n\n")
                        
                        if hover_props:
                            css_parts.append(f"{selector}:hover {{")
                            css_parts.append(self.process_properties(hover_props))
                            css_parts.append("}\n\n")
        
        return '\n'.join(css_parts)

