#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор стилей секций - генерирует CSS стили для секций из general.json
"""

from typing import Dict, Any, Callable
from processors.value_processor import process_css_value


class SectionCSSGenerator:
    """Генерирует стили секций из general.json"""
    
    def __init__(self, general_config: Dict[str, Any],
                 report_config: Dict[str, Any],
                 is_report_enabled: Callable[[], bool],
                 process_css_value_func: Callable):
        """
        Args:
            general_config: Конфигурация из general.json
            report_config: Конфигурация из report.json
            is_report_enabled: Функция проверки включен ли report
            process_css_value_func: Функция для обработки CSS значений
        """
        self.general_config = general_config or {}
        self.report_config = report_config or {}
        self.is_report_enabled = is_report_enabled
        self.process_css_value = process_css_value_func
    
    def generate(self) -> str:
        """
        Генерирует стили секций
        
        Returns:
            CSS строка со стилями секций
        """
        # Применяем стили section из general.json, если:
        # 1. Report выключен, ИЛИ
        # 2. Report включен, но в report_config нет стилей для section
        should_apply_section_styles = False
        if 'section' in self.general_config:
            if not self.is_report_enabled():
                should_apply_section_styles = True
            elif self.is_report_enabled() and (not self.report_config or 'section' not in self.report_config or 'bg-color' not in self.report_config.get('section', {})):
                # Report включен, но стилей section в report нет - применяем из general
                should_apply_section_styles = True
        
        if not should_apply_section_styles:
            return ''
        
        section_config = self.general_config['section']
        if not isinstance(section_config, dict) or 'bg-color' not in section_config:
            return ''
        
        css_parts = []
        bg_color_config = section_config['bg-color']
        
        # Поддержка нового формата объекта: {"header": "#ffffff", "turn": "#cccccc", ...}
        # Если ключ заканчивается на "*", значение игнорируется и используется "transparent"
        if isinstance(bg_color_config, dict):
            for section_type_key, color_value in bg_color_config.items():
                # Проверяем, есть ли звездочка в конце ключа
                if section_type_key.endswith('*'):
                    # Убираем звездочку из имени секции
                    section_type = section_type_key[:-1]
                    # Используем transparent вместо указанного значения
                    processed_value = "transparent"
                else:
                    # Используем имя секции как есть
                    section_type = section_type_key
                    # Обрабатываем значение через process_css_value для поддержки ссылок и модификаторов
                    processed_value = self.process_css_value(color_value, self.general_config, current_section='section')
                
                # Генерируем стили для всех селекторов с !important
                css_parts.append(f"section.section-{section_type} {{")
                css_parts.append(f"    background-color: {processed_value} !important;")
                css_parts.append("}\n")
                
                css_parts.append(f".section-{section_type} {{")
                css_parts.append(f"    background-color: {processed_value} !important;")
                css_parts.append("}\n")
                
                css_parts.append(f".layout.section-{section_type} {{")
                css_parts.append(f"    background-color: {processed_value} !important;")
                css_parts.append("}\n\n")
        
        # Поддержка формата массива значений: ["black", 10] - общий стиль для всех секций
        elif isinstance(bg_color_config, list) and len(bg_color_config) == 2:
            # Проверяем, что это формат [цвет, прозрачность]
            first_elem = bg_color_config[0]
            second_elem = bg_color_config[1]
            
            if isinstance(first_elem, str) and (isinstance(second_elem, (int, float)) or (isinstance(second_elem, str) and second_elem.isdigit())):
                # Это формат ["black", 10] - общий стиль для всех секций
                processed_value = self.process_css_value(bg_color_config, self.general_config, current_section='section')
                
                # Генерируем стили для общего селектора section с !important
                css_parts.append("section {")
                css_parts.append(f"    background-color: {processed_value} !important;")
                css_parts.append("}\n\n")
        
        # Поддержка старого формата массива строк: ["header: #ffffff", "turn: #cccccc", ...]
        elif isinstance(bg_color_config, list):
            for item in bg_color_config:
                if isinstance(item, str) and ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        section_type = parts[0].strip()
                        color_value = parts[1].strip()
                        
                        # Обрабатываем значение через process_css_value для поддержки ссылок и модификаторов
                        processed_value = self.process_css_value(color_value, self.general_config, current_section='section')
                        
                        # Генерируем стили для всех селекторов с !important
                        css_parts.append(f"section.section-{section_type} {{")
                        css_parts.append(f"    background-color: {processed_value} !important;")
                        css_parts.append("}\n")
                        
                        css_parts.append(f".section-{section_type} {{")
                        css_parts.append(f"    background-color: {processed_value} !important;")
                        css_parts.append("}\n")
                        
                        css_parts.append(f".layout.section-{section_type} {{")
                        css_parts.append(f"    background-color: {processed_value} !important;")
                        css_parts.append("}\n\n")
        
        return '\n'.join(css_parts)

