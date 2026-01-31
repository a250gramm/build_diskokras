#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Процессор objects_css - обрабатывает индивидуальные стили элементов из objects_css.json
"""

from typing import Dict, Any, List, Callable, Optional, Tuple
from generators.css.layout.element_type_resolver import ElementTypeResolver
from generators.css.layout.responsive_generator import ResponsiveGenerator


class ObjectsCSSProcessor:
    """Обрабатывает стили из objects_css.json"""
    
    def __init__(self, objects_css: Dict[str, Any], sections_config: Dict[str, Any],
                 general_config: Dict, process_property_fn: Callable,
                 add_css_property_fn: Callable, normalize_array_fn: Callable,
                 process_dict_properties_fn: Callable, tablet_breakpoint: str,
                 mobile_breakpoint: str):
        """
        Args:
            objects_css: Стили из objects_css.json
            sections_config: Данные из objects.json
            general_config: Общая конфигурация
            process_property_fn: Функция обработки свойств
            add_css_property_fn: Функция добавления CSS свойств
            normalize_array_fn: Функция нормализации массивов
            process_dict_properties_fn: Функция обработки словаря свойств
            tablet_breakpoint: Брейкпоинт для планшета
            mobile_breakpoint: Брейкпоинт для мобильного
        """
        self.objects_css = objects_css
        self.sections_config = sections_config
        self.general_config = general_config
        self._process_property = process_property_fn
        self._add_css_property = add_css_property_fn
        self._normalize_array_value = normalize_array_fn
        self._process_dict_properties_with_important = process_dict_properties_fn
        self.tablet_breakpoint = tablet_breakpoint
        self.mobile_breakpoint = mobile_breakpoint
        
        # Инициализируем вспомогательные классы
        self.type_resolver = ElementTypeResolver(sections_config)
        self.responsive_gen = ResponsiveGenerator(
            general_config, process_property_fn, add_css_property_fn, normalize_array_fn
        )
    
    def flatten_objects_css(self) -> Dict[str, Any]:
        """
        Разворачивает группы в objects_css
        
        Returns:
            Плоский словарь стилей
        """
        flat_objects_css = {}
        for key, value in self.objects_css.items():
            # Если значение - словарь, и все его значения тоже словари - это группа
            if isinstance(value, dict) and all(
                isinstance(v, dict) for v in value.values()
            ):
                # Это группа - разворачиваем её
                for nested_key, nested_value in value.items():
                    flat_objects_css[nested_key] = nested_value
            else:
                # Это обычный элемент (не группа)
                flat_objects_css[key] = value
        return flat_objects_css
    
    def parse_composite_selector(self, element_key: str) -> Optional[Tuple[str, str, List[str], Optional[str]]]:
        """
        Парсит составной селектор с пробелами (например, "turn_menu nav a")
        
        Args:
            element_key: Ключ элемента (например, "turn_menu nav a")
            
        Returns:
            Кортеж (data_path_key, nested_selectors, nested_parts, additional_classes) или None
        """
        if ' ' not in element_key:
            return None
        
        # Извлекаем классы (например, .opened) из последней части
        additional_classes = ''
        if '.' in element_key and element_key.count('.') > element_key.count(' '):
            parts_with_classes = element_key.rsplit('.', 1)
            if len(parts_with_classes) == 2:
                element_key_without_class = parts_with_classes[0]
                additional_classes = '.' + parts_with_classes[1]
                element_key = element_key_without_class
        
        # Разделяем ключ: "turn_menu nav a" -> ["turn_menu", "nav", "a"]
        parts = element_key.split(' ')
        data_path_key = parts[0]  # "turn_menu"
        nested_parts = parts[1:]  # ["nav", "a"]
        
        # Парсим вложенные части
        nested_selectors = self._parse_nested_parts(data_path_key, nested_parts)
        
        # Добавляем дополнительные классы
        if additional_classes and nested_selectors:
            if ' ' in nested_selectors:
                last_space_idx = nested_selectors.rfind(' ')
                nested_selectors = nested_selectors[:last_space_idx + 1] + nested_selectors[last_space_idx + 1:] + additional_classes
            else:
                nested_selectors = nested_selectors + additional_classes
        
        return data_path_key, nested_selectors, nested_parts, additional_classes
    
    def _parse_nested_parts(self, data_path_key: str, nested_parts: List[str]) -> str:
        """
        Парсит вложенные части селектора
        
        Args:
            data_path_key: Ключ родительского элемента
            nested_parts: Список вложенных частей
            
        Returns:
            CSS селектор для вложенных частей
        """
        html_tags = ['div', 'span', 'section', 'article', 'aside', 'header', 'footer', 'main', 'nav']
        
        if len(nested_parts) == 2 and nested_parts[0] in html_tags:
            # Формат "tag classname": "div 1" -> div.1
            tag_name = nested_parts[0]
            class_name = nested_parts[1]
            return f"{tag_name}.{class_name}"
        
        elif len(nested_parts) == 1:
            # Проверяем, может ли это быть тег с подчеркиванием
            nested_key = nested_parts[0]
            
            # Проверяем, является ли это cycle элементом (cycle_gr8 -> .gr8)
            if nested_key.startswith('cycle_'):
                class_name = nested_key.replace('cycle_', '')
                return f".{class_name}"
            elif nested_key == 'cycle':
                return ".cycle"
            
            # Проверяем, является ли это ссылкой с классом (a_gr2 -> a.gr2)
            if nested_key.startswith('a_'):
                class_name_from_suffix = nested_key[2:]
                return f"a.{class_name_from_suffix}"
            
            # Проверяем другие HTML-теги
            for tag in html_tags:
                if nested_key.startswith(tag + '_') or nested_key.startswith(tag + '-'):
                    suffix = nested_key[len(tag):]
                    if suffix.startswith('_') or suffix.startswith('-'):
                        class_name_from_suffix = suffix[1:]
                        # Поддержка :has() для состояний (например div_field-paymet:has(input:checked))
                        if ':has(' in class_name_from_suffix:
                            base_class, pseudo = class_name_from_suffix.split(':has(', 1)
                            return f"{tag}.{base_class}:has({pseudo}"
                        return f"{tag}.{class_name_from_suffix}"
            
            # Если это не тег с классом, определяем тип из objects.json
            child_type = self.type_resolver.resolve_child_type(data_path_key, nested_key)
            if child_type:
                if child_type == 'text':
                    return f".content-{nested_key}"
                elif child_type == 'nav.menu':
                    return 'nav.menu'
                else:
                    return child_type
            else:
                return nested_key
        
        elif len(nested_parts) == 2:
            # Формат "div_2 burger" -> div.2 icon
            first_part = nested_parts[0]
            child_key = nested_parts[1]
            tag_name = None
            class_name = None
            
            for tag in html_tags:
                if first_part.startswith(tag + '_') or first_part.startswith(tag + '-'):
                    tag_name = tag
                    suffix = first_part[len(tag):]
                    if suffix.startswith('_') or suffix.startswith('-'):
                        class_name = suffix[1:]
                    break
            
            if tag_name and class_name:
                child_type = self.type_resolver.resolve_child_type(data_path_key, child_key, tag_name, class_name)
                if child_type:
                    if child_type == 'text':
                        return f"{tag_name}.{class_name} .content-{child_key}"
                    else:
                        return f"{tag_name}.{class_name} {child_type}"
                else:
                    # Проверяем, является ли child_key HTML тегом
                    html_tags_full = html_tags + ['a', 'img', 'input', 'button', 'form', 'label']
                    if child_key not in html_tags_full:
                        return f"{tag_name}.{class_name} .content-{child_key}"
                    else:
                        return f"{tag_name}.{class_name} {child_key}"
        
        elif len(nested_parts) == 3 and nested_parts[0] in html_tags:
            # Формат "tag classname element": "div 2 burger" -> div.2 icon
            tag_name = nested_parts[0]
            class_name = nested_parts[1]
            child_key = nested_parts[2]
            
            child_type = self.type_resolver.resolve_child_type(data_path_key, child_key, tag_name, class_name)
            if child_type:
                if child_type == 'text':
                    return f"{tag_name}.{class_name} .content-{child_key}"
                else:
                    return f"{tag_name}.{class_name} {child_type}"
            else:
                return f"{tag_name}.{class_name} {child_key}"
        
        # Множественные вложенные части: "nav a" -> "nav a"
        return ' '.join(nested_parts)
    
    def generate_css(self) -> str:
        """
        Генерирует CSS из objects_css
        
        Returns:
            CSS строка
        """
        css_parts = []
        
        if not self.objects_css:
            return ''
        
        flat_objects_css = self.flatten_objects_css()
        
        for element_key, element_styles in flat_objects_css.items():
            # Пропускаем правила, которые заканчиваются на * (отключенные правила)
            if element_key.endswith('*') or (' ' in element_key and element_key.split()[-1].endswith('*')):
                continue
            
            # Проверяем, есть ли пробел в ключе (составной селектор)
            composite_result = self.parse_composite_selector(element_key)
            
            if composite_result:
                data_path_key, nested_selectors, nested_parts, additional_classes = composite_result
                selector = f"[data-path='{data_path_key}'] {nested_selectors}"
                
                # Обрабатываем стили
                if isinstance(element_styles, dict):
                    value_props = {k: v for k, v in element_styles.items()}
                    self.responsive_gen.generate_responsive_css(
                        selector, value_props, self.tablet_breakpoint,
                        self.mobile_breakpoint, css_parts
                    )
                    
                    # Если нет массивов, генерируем обычные стили
                    if not self.responsive_gen.has_arrays(value_props):
                        css_parts.append(f"{selector} {{")
                        css_parts.append(self._process_dict_properties_with_important(element_styles))
                        css_parts.append("}\n\n")
                continue
            
            # Простой селектор - определяем тип элемента
            element_type, has_api, is_complex_structure = self.type_resolver.resolve_element_type(element_key)
            selector = self.type_resolver.build_selector_for_type(
                element_key, element_type, has_api, is_complex_structure
            )
            
            # Генерируем стили
            if isinstance(element_styles, dict):
                value_props = {k: v for k, v in element_styles.items()}
                self.responsive_gen.generate_responsive_css(
                    selector, value_props, self.tablet_breakpoint,
                    self.mobile_breakpoint, css_parts
                )
                
                # Если нет массивов, генерируем обычные стили
                if not self.responsive_gen.has_arrays(value_props):
                    css_parts.append(f"{selector} {{")
                    for prop_name, prop_value in element_styles.items():
                        css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                        self._add_css_property(css_parts, "    ", css_prop_name, processed_value)
                    css_parts.append("}\n\n")
        
        return '\n'.join(css_parts)

