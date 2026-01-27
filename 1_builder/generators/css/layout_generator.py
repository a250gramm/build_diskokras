#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Layout Generator - Координатор для генерации CSS layout стилей
"""

from typing import Dict, Any
from pathlib import Path
from processors.value_processor import process_css_value, resolve_reference
from generators.css.layout.selector_parser import SelectorParser
from generators.css.layout.element_type_resolver import ElementTypeResolver
from generators.css.layout.responsive_generator import ResponsiveGenerator
from generators.css.layout.objects_css_processor import ObjectsCSSProcessor


class LayoutGenerator:
    """Координатор для генерации CSS layout стилей"""
    
    def __init__(self, css_config, general_config, report_config, default_config,
                 objects_css, report_objects_css, structure_analyzer, process_dict_fn, process_props_fn, 
                 process_props_important_fn, is_report_enabled_fn, sections_config=None):
        self.css_config = css_config
        self.general_config = general_config
        self.report_config = report_config
        self.default_config = default_config
        self.objects_css = objects_css
        self.report_objects_css = report_objects_css
        self.structure_analyzer = structure_analyzer
        self._process_dict_properties_with_important = process_dict_fn
        self._process_properties = process_props_fn
        self._process_properties_with_important = process_props_important_fn
        self._is_report_enabled = is_report_enabled_fn
        self.sections_config = sections_config or {}  # objects.json для определения типов элементов
        
        # Инициализируем специализированные модули
        self.selector_parser = SelectorParser()
        self.type_resolver = ElementTypeResolver(self.sections_config)
        self.responsive_gen = ResponsiveGenerator(
            self.general_config,
            self._process_property,
            self._add_css_property,
            self._normalize_array_value
        )
    
    def _normalize_array_value(self, value):
        """Нормализует массив значений: [10, 10, 10, "px"] -> ["10px", "10px", "10px"]"""
        if isinstance(value, list):
            # Формат [val1, val2, val3, unit]
            if len(value) == 4 and isinstance(value[3], str):
                unit = value[3]
                result = []
                for i in range(3):
                    val = value[i]
                    # Если значение уже содержит единицу или это специальное значение (auto, none), не добавляем unit
                    if isinstance(val, str) and (any(x in val for x in ['px', 'em', 'rem', '%', 'vh', 'vw']) or val.lower() in ['auto', 'none', 'inherit', 'initial', 'unset']):
                        result.append(str(val))
                    else:
                        result.append(f"{val}{unit}")
                return result
            # Формат [val1, val2, val3]
            elif len(value) == 3:
                return value
        return value
    
    def _process_property(self, prop_name, prop_value):
        """
        Обрабатывает CSS свойство: заменяет bg-color на background-color и обрабатывает значение
        """
        # Специальная обработка для border с массивом из 3 элементов
        if prop_name == 'border' and isinstance(prop_value, list) and len(prop_value) == 3:
            border_style = prop_value[0]  # "1px solid"
            border_flags_str = str(prop_value[1])  # "1 1 1 1"
            border_color_ref = prop_value[2]  # "black.100"
            
            # Разрешаем цвет с модификатором
            resolved_color = resolve_reference(border_color_ref, self.general_config, 'section')
            
            # Парсим флаги сторон
            border_flags = border_flags_str.split()
            
            # Если только один флаг, применяем ко всем сторонам
            if len(border_flags) == 1:
                if border_flags[0] == '1':
                    return 'border', f"{border_style} {resolved_color}"
            else:
                # Несколько флагов для разных сторон - возвращаем строку с разделителями |
                sides = ['top', 'right', 'bottom', 'left']
                border_props = []
                for i, flag in enumerate(border_flags):
                    if i < len(sides) and flag == '1':
                        border_props.append(f"border-{sides[i]}: {border_style} {resolved_color}")
                return 'border', ' | '.join(border_props)
        
        # Заменяем bg-color на background-color
        css_prop_name = prop_name.replace('bg-color', 'background-color')
        # Обрабатываем значение через process_css_value
        processed_value = process_css_value(prop_value, self.general_config)
        return css_prop_name, processed_value
    
    def _add_css_property(self, css_parts, indent, css_prop_name, processed_value):
        """
        Добавляет CSS свойство, обрабатывая border с разделителями |
        """
        # Обрабатываем border с разделителями | (несколько border-* свойств)
        if ' | ' in processed_value:
            # Разделяем на отдельные border свойства
            border_props = processed_value.split(' | ')
            for border_prop in border_props:
                css_parts.append(f"{indent}{border_prop} !important;")
        else:
            css_parts.append(f"{indent}{css_prop_name}: {processed_value} !important;")
    
    def generate(self) -> str:
        """Главный метод генерации"""
        return self._generate_layout_css()
    
    def _generate_layout_css(self) -> str:
        """Генерирует CSS из css.json"""
        css_parts = []
        # Получаем devices: если report включен - из report_config, иначе из general_config
        devices = {}
        device_settings = {}  # Дополнительные настройки для каждого устройства
        
        # Определяем, откуда брать device настройки
        config_to_use = None
        if self._is_report_enabled() and self.report_config and 'layout' in self.report_config:
            # Если report включен и есть device в report - используем его
            config_to_use = self.report_config.get('layout', {})
        elif self.general_config and 'layout' in self.general_config:
            # Иначе используем general_config
            config_to_use = self.general_config.get('layout', {})
        
        if config_to_use and 'device' in config_to_use:
            device_config = config_to_use['device']
            for device_name in ['desktop', 'tablet', 'mobile']:
                if device_name in device_config:
                    device_value = device_config[device_name]
                    # Новый формат: {"width": "1200px", "flex-wrap": "wrap", ...}
                    if isinstance(device_value, dict):
                        if 'width' in device_value:
                            devices[device_name] = device_value['width']
                        # Сохраняем дополнительные настройки (flex-wrap, full-width-columns)
                        device_settings[device_name] = {k: v for k, v in device_value.items() if k != 'width'}
                    # Старый формат: ["1200","px"] или "1200px"
                    elif isinstance(device_value, list) and len(device_value) >= 2:
                        devices[device_name] = device_value[0] + device_value[1]
                    elif isinstance(device_value, str):
                        devices[device_name] = device_value
        
        # Если не нашли в general_config, пробуем default_config
        if not devices:
            wrapper = self.default_config.get('wrapper', {})
            devices_config = self.default_config.get('devices', {})
            if not devices_config and wrapper:
                devices_config = {
                'desktop': wrapper.get('desktop', ['1200px']),
                'tablet': wrapper.get('tablet', ['768px']),
                'mobile': wrapper.get('mobile', ['320px'])
            }
            if devices_config:
                for device_name in ['desktop', 'tablet', 'mobile']:
                    if device_name in devices_config:
                        device_value = devices_config[device_name]
                        if isinstance(device_value, list) and len(device_value) >= 2:
                            devices[device_name] = device_value[0] + device_value[1]
                        elif isinstance(device_value, str):
                            devices[device_name] = device_value
        
        # Значения по умолчанию
        tablet_breakpoint = devices.get('tablet', '768px')
        mobile_breakpoint = devices.get('mobile', '320px')
        
        # Сначала обрабатываем простые секции (например, "header", "footer")
        for key, value in self.css_config.items():
            # Простые ключи без точек и пробелов - это стили для всей секции
            if '.' not in key and ' ' not in key:
                selector = self.selector_parser.parse_simple_selector(key)
                if selector:
                    if isinstance(value, dict):
                        # Обрабатываем суффиксы: -S-L-C означает layout + section + column
                        if key.endswith('-S-L-C'):
                            # Обрабатываем адаптивные массивы
                            value_props = {k: v for k, v in value.items()}
                            self.responsive_gen.generate_responsive_css(
                                selector, value_props, tablet_breakpoint,
                                mobile_breakpoint, css_parts
                            )
                            # Если нет массивов, генерируем обычные стили
                            if not self.responsive_gen.has_arrays(value_props):
                                css_parts.append(f"{selector} {{")
                                css_parts.append(self._process_dict_properties_with_important(value))
                                css_parts.append("}\n\n")
                        else:
                            css_parts.append(f"{selector} {{")
                            css_parts.append(self._process_dict_properties_with_important(value))
                            css_parts.append("}\n\n")
        
        # Затем обрабатываем составные селекторы (например, "header.nav", "turn.nav", "header.2.1.1", "header.2.1.1 .icon_burger")
        compound_selectors_processed = []
        for key, value in self.css_config.items():
            # Используем selector_parser для парсинга составных селекторов
            parsed_result = self.selector_parser.parse_compound_selector(key)
            if parsed_result:
                selector, element_part = parsed_result
                # Обрабатываем команду double
                if isinstance(value, dict):
                    selector = self.selector_parser.parse_double_selectors(value, selector)
                    value_props = {k: v for k, v in value.items() if k != 'double'}
                else:
                    value_props = value if isinstance(value, dict) else {}
                
                # Генерируем адаптивные стили
                if isinstance(value_props, dict) and value_props:
                    self.responsive_gen.generate_responsive_css(
                        selector, value_props, tablet_breakpoint,
                        mobile_breakpoint, css_parts
                    )
                    # Если нет массивов, генерируем обычные стили
                    if not self.responsive_gen.has_arrays(value_props):
                        css_parts.append(f"{selector} {{")
                        if isinstance(value, dict):
                            css_parts.append(self._process_dict_properties_with_important(value_props))
                        elif isinstance(value, list):
                            css_parts.append(self._process_properties_with_important(value))
                        css_parts.append("}\n\n")
                elif isinstance(value, list):
                    if value:
                        css_parts.append(f"{selector} {{")
                        css_parts.append(self._process_properties_with_important(value))
                        css_parts.append("}\n\n")
                
                compound_selectors_processed.append(key)
                continue
            
            # Проверяем, есть ли пробел в ключе (вложенный селектор) - старый код для совместимости
            if ' ' in key:
                # Формат "header.2.1.1 .icon_burger" (группа + элемент)
                main_parts = key.split(' ', 1)  # Разделяем только по первому пробелу
                group_part = main_parts[0]  # "header.2.1.1"
                element_part = main_parts[1]  # ".icon_burger"
                
                group_keys = group_part.split('.')
                if len(group_keys) == 4 and group_keys[1].isdigit() and group_keys[2].isdigit() and group_keys[3].isdigit():
                    section_name = group_keys[0]
                    col_num = group_keys[1]
                    row_num = group_keys[2]
                    gr_num = group_keys[3]
                    
                    # Преобразуем ".icon_burger" -> "[data-path='icon_burger']"
                    # Обрабатываем классы и теги (например, "header_nav.opened nav" -> "[data-path='header_nav'].opened nav")
                    element_clean = element_part.lstrip('.')
                    
                    # Проверяем, есть ли дополнительные селекторы (например, nav, .opened nav)
                    if ' ' in element_clean:
                        # Формат "header_nav nav" или "header_nav.opened nav"
                        element_first, *rest = element_clean.split(' ', 1)
                        tag_suffix = ' ' + rest[0] if rest else ''
                        
                        # Проверяем классы в первой части
                        if '.' in element_first:
                            element_name, *classes = element_first.split('.')
                            class_suffix = '.' + '.'.join(classes)
                            selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num} [data-path='{element_name}']{class_suffix}{tag_suffix}"
                        else:
                            selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num} [data-path='{element_first}']{tag_suffix}"
                    elif '.' in element_clean:
                        # Формат "header_nav.opened"
                        element_name, *classes = element_clean.split('.')
                        class_suffix = '.' + '.'.join(classes)
                        selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num} [data-path='{element_name}']{class_suffix}"
                    else:
                        # Формат "header_nav" - стили для div.marking-item
                        # Если нужно стилизовать внутренний тег, используй явно "header_nav nav"
                        selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num} [data-path='{element_clean}']"
                    
                    # Обрабатываем значение
                    if isinstance(value, dict):
                        # Проверяем наличие "double" для группировки селекторов
                        double_selectors = value.get('double', [])
                        if double_selectors and isinstance(double_selectors, list):
                            # Создаем список селекторов (текущий + все из double)
                            selectors = [selector]
                            for double_key in double_selectors:
                                double_parts = double_key.split('.')
                                if len(double_parts) == 4 and double_parts[1].isdigit() and double_parts[2].isdigit() and double_parts[3].isdigit():
                                    double_selector = f".group.{double_parts[0]}-{double_parts[1]}-{double_parts[2]}-{double_parts[3]}"
                                    selectors.append(double_selector)
                            selector = ',\n'.join(selectors)
                        
                        # Удаляем "double" из обработки свойств
                        value_props = {k: v for k, v in value.items() if k != 'double'}
                        
                        # Проверяем, содержит ли словарь массивы для разных устройств
                        # Исключаем border из проверки, так как border имеет формат ["1px solid", "1 1 1 1", "black.100"]
                        has_arrays = any(
                            isinstance(v, list) and (len(v) == 3 or (len(v) == 4 and isinstance(v[3], str)))
                            and k != 'border'  # border обрабатывается отдельно
                            for k, v in value_props.items()
                        )
                        
                        if has_arrays:
                            # Собираем свойства с массивами и без массивов отдельно
                            array_props = {}
                            normal_props = {}
                            
                            for prop_name, prop_value in value_props.items():
                                # border обрабатывается отдельно, не добавляем в array_props
                                if prop_name == 'border' and isinstance(prop_value, list) and len(prop_value) == 3:
                                    normal_props[prop_name] = prop_value
                                    continue
                                normalized = self._normalize_array_value(prop_value)
                                if isinstance(normalized, list) and len(normalized) == 3:
                                    array_props[prop_name] = normalized
                                else:
                                    normal_props[prop_name] = prop_value
                            
                            # Генерируем desktop стили (обычные свойства + desktop значения из массивов)
                            desktop_props = {k: v[0] for k, v in array_props.items()}
                            all_desktop_props = {**normal_props, **desktop_props}
                            
                            if all_desktop_props:
                                css_parts.append(f"{selector} {{")
                                for prop_name, prop_value in all_desktop_props.items():
                                    css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                                    self._add_css_property(css_parts, "    ", css_prop_name, processed_value)
                                    css_parts.append("}\n\n")
                                    
                            # Генерируем медиа-запросы для tablet
                            tablet_props = {k: v[1] for k, v in array_props.items()}
                            if tablet_props:
                                css_parts.append(f"@media (max-width: {tablet_breakpoint}) {{")
                                css_parts.append(f"    {selector} {{")
                                for prop_name, prop_value in tablet_props.items():
                                    css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                                    css_parts.append(f"        {css_prop_name}: {processed_value} !important;")
                                css_parts.append("    }")
                                css_parts.append("}\n\n")
                                    
                            # Генерируем медиа-запросы для mobile
                            mobile_props = {k: v[2] for k, v in array_props.items()}
                            if mobile_props:
                                css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{")
                                css_parts.append(f"    {selector} {{")
                                for prop_name, prop_value in mobile_props.items():
                                    css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                                    css_parts.append(f"        {css_prop_name}: {processed_value} !important;")
                                css_parts.append("    }")
                                css_parts.append("}\n\n")
                        else:
                            # Обычные стили без массивов
                            css_parts.append(f"{selector} {{")
                            css_parts.append(self._process_dict_properties_with_important(value))
                            css_parts.append("}\n\n")
                    
                    compound_selectors_processed.append(key)
                    continue
            
            if '.' in key:
                parts = key.split('.')
                
                # Формат "header.2.1.1" (секция.колонка.ряд.группа)
                if len(parts) == 4 and parts[1].isdigit() and parts[2].isdigit() and parts[3].isdigit():
                    section_name = parts[0]
                    col_num = parts[1]
                    row_num = parts[2]
                    gr_num = parts[3]
                    # Преобразуем "header.2.1.1" -> ".group.header-2-1-1"
                    selector = f".group.{section_name}-{col_num}-{row_num}-{gr_num}"
                    
                    if isinstance(value, dict):
                        # Проверяем наличие "double" для группировки селекторов
                        double_selectors = value.get('double', [])
                        if double_selectors and isinstance(double_selectors, list):
                            # Создаем список селекторов (текущий + все из double)
                            selectors = [selector]
                            for double_key in double_selectors:
                                double_parts = double_key.split('.')
                                if len(double_parts) == 4 and double_parts[1].isdigit() and double_parts[2].isdigit() and double_parts[3].isdigit():
                                    double_selector = f".group.{double_parts[0]}-{double_parts[1]}-{double_parts[2]}-{double_parts[3]}"
                                    selectors.append(double_selector)
                            selector = ',\n'.join(selectors)
                        
                        # Удаляем "double" из обработки свойств
                        value_props = {k: v for k, v in value.items() if k != 'double'}
                        
                        # Проверяем, содержит ли словарь массивы для разных устройств
                        has_arrays = any(isinstance(v, list) and (len(v) == 3 or (len(v) == 4 and isinstance(v[3], str))) for v in value_props.values())
                        
                        if has_arrays:
                            # Собираем обычные свойства и свойства с массивами отдельно
                            normal_props = {}
                            array_props = {}
                            
                            for prop_name, prop_value in value_props.items():
                                # Нормализуем значение
                                normalized_value = self._normalize_array_value(prop_value)
                                if isinstance(normalized_value, list) and len(normalized_value) == 3:
                                    array_props[prop_name] = normalized_value
                                else:
                                    normal_props[prop_name] = prop_value
                            
                            # Генерируем desktop стили (обычные свойства + desktop значения из массивов)
                            desktop_props = {k: v[0] for k, v in array_props.items()}
                            all_desktop_props = {**normal_props, **desktop_props}
                            
                            if all_desktop_props:
                                css_parts.append(f"{selector} {{")
                                for prop_name, prop_value in all_desktop_props.items():
                                    css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                                    self._add_css_property(css_parts, "    ", css_prop_name, processed_value)
                                css_parts.append("}\n\n")
                            
                            # Генерируем медиа-запросы для tablet
                            tablet_props = {k: v[1] for k, v in array_props.items()}
                            if tablet_props:
                                css_parts.append(f"@media (max-width: {tablet_breakpoint}) {{")
                                css_parts.append(f"    {selector} {{")
                                for prop_name, prop_value in tablet_props.items():
                                    css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                                    css_parts.append(f"        {css_prop_name}: {processed_value} !important;")
                                css_parts.append("    }")
                                css_parts.append("}\n\n")
                            
                            # Генерируем медиа-запросы для mobile
                            mobile_props = {k: v[2] for k, v in array_props.items()}
                            if mobile_props:
                                css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{")
                                css_parts.append(f"    {selector} {{")
                                for prop_name, prop_value in mobile_props.items():
                                    css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                                    css_parts.append(f"        {css_prop_name}: {processed_value} !important;")
                                css_parts.append("    }")
                                css_parts.append("}\n\n")
                        else:
                            # Обычные стили без массивов
                            css_parts.append(f"{selector} {{")
                            css_parts.append(self._process_dict_properties_with_important(value_props))
                            css_parts.append("}\n\n")
                    elif isinstance(value, list):
                        if value:
                            css_parts.append(f"{selector} {{")
                            css_parts.append(self._process_properties_with_important(value))
                            css_parts.append("}\n\n")
                    compound_selectors_processed.append(key)
                
                # Формат "header.nav" (секция.элемент)
                elif len(parts) == 2:
                    # Проверяем, не является ли это составным селектором типа "header.2.2.1 header_nav"
                    # Если первая часть содержит точки и цифры, пропускаем (обработано выше)
                    section_parts = parts[0].split('.')
                    if len(section_parts) > 1 and any(part.isdigit() for part in section_parts):
                        # Это составной селектор, уже обработан выше
                        continue
                    
                    section_name = parts[0]
                    selector_part = parts[1]
                    
                    # Определяем, это тег (nav, a, div) или класс
                    if selector_part in ['nav', 'a', 'img', 'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        # Это тег
                        selector = f".section-{section_name} {selector_part}"
                    else:
                        # Это класс
                        selector = f".section-{section_name} .{selector_part}"
                    
                    if isinstance(value, dict):
                        css_parts.append(f"{selector} {{")
                        css_parts.append(self._process_dict_properties_with_important(value))
                        css_parts.append("}\n\n")
                    elif isinstance(value, list):
                        if value:
                            css_parts.append(f"{selector} {{")
                            css_parts.append(self._process_properties_with_important(value))
                            css_parts.append("}\n\n")
                    compound_selectors_processed.append(key)
        
        for section_name, section_config in self.css_config.items():
            if not isinstance(section_config, dict) or section_name in ['column', 'row']:
                continue
            # Пропускаем составные селекторы (уже обработаны выше)
            if section_name in compound_selectors_processed or '.' in section_name:
                continue
            # Пропускаем -S-L-C селекторы (уже обработаны выше)
            if section_name.endswith('-S-L-C') or section_name.endswith('-S-L') or section_name.endswith('-S'):
                continue
            
            # Стили для .layout.section-{name}
            css_parts.append(f".layout.section-{section_name} {{")
            
            general_props = section_config.get('general', [])
            # Убираем gap из .layout, он будет применен к .column
            general_props_for_container = [p for p in general_props if not p.startswith('gap:')]
            css_parts.append(self._process_properties(general_props_for_container))
            css_parts.append("}\n\n")
            
            # Генерируем адаптивные стили для колонок используя responsive_generator
            desktop_columns = section_config.get('desktop', [])
            tablet_columns = section_config.get('tablet', [])
            mobile_columns = section_config.get('mobile', [])
            
            # Применяем desktop ширины колонок (inline в HTML, но для полноты добавляем и в CSS)
            if desktop_columns:
                for idx, width in enumerate(desktop_columns):
                    col_class = f"col_{idx + 1}"
                    css_parts.append(f".layout.section-{section_name} .{col_class} {{")
                    css_parts.append(f"    flex-basis: {width}%;")
                    css_parts.append("}\n")
            
            # Используем responsive_generator для генерации адаптивных стилей колонок
            section_column_config = {
                'desktop': desktop_columns,
                'tablet': tablet_columns,
                'mobile': mobile_columns
            }
            self.responsive_gen.generate_column_responsive_css(
                section_name, section_column_config, devices, device_settings, css_parts
            )
            
            # Проверяем, начинается ли секция со строк
            starts_with_rows = False
            if self.structure_analyzer:
                starts_with_rows = self.structure_analyzer.is_section_starts_with_rows(section_name)
            else:
                # Fallback: проверяем по структуре css_config
                has_row_1_desktop = isinstance(section_config.get('row_1'), dict) and 'desktop' in section_config.get('row_1', {})
                has_desktop_top = 'desktop' in section_config
                starts_with_rows = has_row_1_desktop and not has_desktop_top
            
            # Все генерации flex-стилей удалены
            
            # Генерируем стили для колонок и строк
            css_parts.append(self._generate_section_nested_css(section_name, section_config))
        
        # Генерируем стили для objects_css (индивидуальные стили элементов)
        if self.objects_css:
            # Используем ObjectsCSSProcessor для обработки objects_css
            objects_processor = ObjectsCSSProcessor(
                self.objects_css,
                self.sections_config,
                self.general_config,
                self._process_property,
                self._add_css_property,
                self._normalize_array_value,
                self._process_dict_properties_with_important,
                tablet_breakpoint,
                mobile_breakpoint
            )
            css_parts.append(objects_processor.generate_css())
        
        # Генерируем стили для report_objects_css (отладочные стили элементов)
        if self._is_report_enabled() and self.report_objects_css:
            # Используем ObjectsCSSProcessor для обработки report_objects_css
            report_objects_processor = ObjectsCSSProcessor(
                self.report_objects_css,
                self.sections_config,
                self.general_config,
                self._process_property,
                self._add_css_property,
                self._normalize_array_value,
                self._process_dict_properties_with_important,
                tablet_breakpoint,
                mobile_breakpoint
            )
            css_parts.append(report_objects_processor.generate_css())
        
        return '\n'.join(css_parts)
    

    def _generate_section_nested_css(self, section_name: str, section_config: Dict) -> str:
        """Генерирует CSS для вложенных элементов (column_X, row_X)"""
        css_parts = []
        
        for key, value in section_config.items():
            if key in ['general', 'desktop', 'tablet', 'mobile']:
                continue
            
            if isinstance(value, dict):
                # Преобразуем column_1 -> .col_1, row_1 -> .row.row_1
                if key.startswith('column_'):
                    col_class = key.replace('column_', 'col_')
                    selector = f".layout.section-{section_name} .{col_class}"
                else:
                    selector = f".layout.section-{section_name} .marking-{key.replace('_', '.')}"
                
                general_props = value.get('general', [])
                
                if general_props:
                    css_parts.append(f"{selector} {{")
                    css_parts.append(self._process_properties(general_props))
                    css_parts.append("}\n\n")
                
                # Рекурсивно обрабатываем вложенные элементы
                css_parts.append(self._generate_section_nested_css(section_name, value))
        
        return '\n'.join(css_parts)
