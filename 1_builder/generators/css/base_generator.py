#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Generator - ПОЛНАЯ версия из css_generator_FULL_OLD.py
"""

from typing import Dict, Any
from pathlib import Path
from processors.value_processor import process_css_value


class BaseGenerator:
    """Генерирует базовые CSS стили (ПОЛНАЯ ЛОГИКА из старой версии)"""
    
    def __init__(self, general_config, process_dict_fn, process_props_important_fn):
        self.general_config = general_config
        self.tag_config = {}  # Будет установлено позже если нужно
        self._process_dict_properties_with_important = process_dict_fn
        self._process_properties_with_important = process_props_important_fn
    
    def generate(self) -> str:
        """Главный метод генерации"""
        return self._generate_general_css()
    
    def _generate_general_css(self) -> str:
        """Генерирует глобальные CSS стили из general.json
        Применяет стили ко всем страницам и секциям
        Использует !important для приоритета над специфичными селекторами
        Поддерживает формат объекта: {"property": "value"}
        """
        css_parts = []
        
        # html -> стили для html (нужно для работы min-height: 100% на body)
        if 'html' in self.general_config:
            html_config = self.general_config['html']
            if isinstance(html_config, dict):
                css_styles = {k: v for k, v in html_config.items() if k != 'device'}
                if css_styles:
                    css_parts.append("html {")
                    css_parts.append(self._process_dict_properties_with_important(css_styles, current_section='html'))
                    css_parts.append("}\n\n")
            elif isinstance(html_config, list):
                # Старый формат массива (для обратной совместимости)
                css_styles = [s for s in html_config if not s.startswith('device_')]
                if css_styles:
                    css_parts.append("html {")
                    css_parts.append(self._process_properties_with_important(css_styles))
                    css_parts.append("}\n\n")
        
        # page -> стили для body (глобальные стили для всех страниц)
        if 'page' in self.general_config:
            page_config = self.general_config['page']
            if isinstance(page_config, dict):
                # Формат объекта: {"background-color": "magenta", ...}
                css_styles = {k: v for k, v in page_config.items() if k != 'device'}
                if css_styles:
                    # Получаем breakpoints для медиа-запросов
                    tablet_breakpoint = '768px'
                    mobile_breakpoint = '320px'
                    if 'layout' in self.general_config and 'device' in self.general_config['layout']:
                        device_config = self.general_config['layout']['device']
                        if 'tablet' in device_config:
                            tablet_device = device_config['tablet']
                            if isinstance(tablet_device, dict) and 'width' in tablet_device:
                                tablet_breakpoint = tablet_device['width']
                            elif isinstance(tablet_device, list) and len(tablet_device) >= 2:
                                tablet_breakpoint = tablet_device[0] + tablet_device[1]
                        if 'mobile' in device_config:
                            mobile_device = device_config['mobile']
                            if isinstance(mobile_device, dict) and 'width' in mobile_device:
                                mobile_breakpoint = mobile_device['width']
                            elif isinstance(mobile_device, list) and len(mobile_device) >= 2:
                                mobile_breakpoint = mobile_device[0] + mobile_device[1]
                    
                    # Проверяем, есть ли массивы для медиа-запросов
                    def _normalize_array_value(value):
                        if isinstance(value, list) and len(value) == 4 and isinstance(value[3], str):
                            unit = value[3]
                            return [f"{value[0]}{unit}", f"{value[1]}{unit}", f"{value[2]}{unit}"]
                        elif isinstance(value, list) and len(value) == 3:
                            return value
                        return value
                    
                    has_arrays = any(isinstance(v, list) and (len(v) == 3 or (len(v) == 4 and isinstance(v[3], str))) for v in css_styles.values())
                    
                    if has_arrays:
                        # Разделяем свойства с массивами и без
                        array_props = {}
                        normal_props = {}
                        
                        for prop_name, prop_value in css_styles.items():
                            normalized = _normalize_array_value(prop_value)
                            if isinstance(normalized, list) and len(normalized) == 3:
                                array_props[prop_name] = normalized
                            else:
                                normal_props[prop_name] = prop_value
                        
                        # Генерируем desktop стили (обычные свойства + desktop значения из массивов)
                        desktop_props = {k: v[0] for k, v in array_props.items()}
                        all_desktop_props = {**normal_props, **desktop_props}
                        
                        if all_desktop_props:
                            css_parts.append("body {")
                            css_parts.append(self._process_dict_properties_with_important(all_desktop_props, current_section='page'))
                            css_parts.append("}\n\n")
                        
                        # Генерируем медиа-запросы для tablet
                        tablet_props = {k: v[1] for k, v in array_props.items()}
                        if tablet_props:
                            css_parts.append(f"@media (max-width: {tablet_breakpoint}) {{\n")
                            css_parts.append("    body {")
                            css_parts.append(self._process_dict_properties_with_important(tablet_props, indent="        ", current_section='page'))
                            css_parts.append("    }\n")
                            css_parts.append("}\n\n")
                        
                        # Генерируем медиа-запросы для mobile
                        mobile_props = {k: v[2] for k, v in array_props.items()}
                        if mobile_props:
                            css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{\n")
                            css_parts.append("    body {")
                            css_parts.append(self._process_dict_properties_with_important(mobile_props, indent="        ", current_section='page'))
                            css_parts.append("    }\n")
                            css_parts.append("}\n\n")
                    else:
                        # Обычные стили без массивов
                        css_parts.append("body {")
                        css_parts.append(self._process_dict_properties_with_important(css_styles, current_section='page'))
                        css_parts.append("}\n\n")
            elif isinstance(page_config, list):
                # Старый формат массива (для обратной совместимости)
                css_styles = [s for s in page_config if not s.startswith('device_')]
                if css_styles:
                    css_parts.append("body {")
                    css_parts.append(self._process_properties_with_important(css_styles))
                    css_parts.append("}\n\n")
        
        # section -> стили для section (глобальные стили для всех секций)
        # section должен занимать всю ширину, а .layout внутри ограничен по ширине
        # ПРИМЕЧАНИЕ: Стили для конкретных типов секций (header, turn, body, footer) 
        # генерируются ПОСЛЕ layout стилей, чтобы перекрыть их
        if 'section' in self.general_config:
            section_config = self.general_config['section']
            if isinstance(section_config, dict):
                # Пропускаем bg-color - он обрабатывается после layout
                # Старый формат объекта: {"background-color": "cyan", ...}
                css_styles = {k: v for k, v in section_config.items() if k != 'device' and k != 'bg-color'}
                if css_styles:
                    css_parts.append("section {")
                    css_parts.append(self._process_dict_properties_with_important(css_styles, current_section='section'))
                    css_parts.append("}\n\n")
            elif isinstance(section_config, list):
                # Старый формат массива (для обратной совместимости)
                css_styles = [s for s in section_config if not s.startswith('device_')]
                if css_styles:
                    css_parts.append("section {")
                    css_parts.append(self._process_properties_with_important(css_styles))
                    css_parts.append("}\n\n")
        
        # layout -> стили для .column (глобальные стили для всех layout)
        if 'layout' in self.general_config:
            layout_config = self.general_config['layout']
            if isinstance(layout_config, dict):
                # Формат объекта: {"background-color": "yellow", "device": {...}, "column": {...}}
                # Исключаем служебные ключи: device, column
                css_styles = {k: v for k, v in layout_config.items() if k not in ['device', 'column']}
                if css_styles:
                    css_parts.append(".column {")
                    css_parts.append(self._process_dict_properties_with_important(css_styles, current_section='layout'))
                    css_parts.append("}\n\n")
            elif isinstance(layout_config, list):
                # Старый формат массива (для обратной совместимости)
                css_styles = [s for s in layout_config if not s.startswith('device_')]
                if css_styles:
                    css_parts.append(".column {")
                    css_parts.append(self._process_properties_with_important(css_styles))
                    css_parts.append("}\n\n")
        
        # column -> стили для .column (глобальные стили для всех колонок)
        if 'column' in self.general_config:
            column_config = self.general_config['column']
            if isinstance(column_config, dict):
                css_parts.append(".column {")
                css_parts.append(self._process_dict_properties_with_important(column_config, current_section='column'))
                css_parts.append("}\n\n")
            elif isinstance(column_config, list):
                # Старый формат массива (для обратной совместимости)
                if column_config:
                    css_parts.append(".column {")
                    css_parts.append(self._process_properties_with_important(column_config))
                    css_parts.append("}\n\n")
        
        # row -> стили для .row (глобальные стили для всех рядов)
        if 'row' in self.general_config:
            row_config = self.general_config['row']
            if isinstance(row_config, dict):
                css_parts.append(".row {")
                css_parts.append(self._process_dict_properties_with_important(row_config, current_section='row'))
                css_parts.append("}\n\n")
            elif isinstance(row_config, list):
                # Старый формат массива (для обратной совместимости)
                if row_config:
                    css_parts.append(".row {")
                    css_parts.append(self._process_properties_with_important(row_config))
                    css_parts.append("}\n\n")
        
        # group -> стили для .group (глобальные стили для всех групп)
        if 'group' in self.general_config:
            group_config = self.general_config['group']
            if isinstance(group_config, dict):
                css_parts.append(".group {")
                css_parts.append(self._process_dict_properties_with_important(group_config, current_section='group'))
                css_parts.append("}\n\n")
            elif isinstance(group_config, list):
                # Старый формат массива (для обратной совместимости)
                if group_config:
                    css_parts.append(".group {")
                    css_parts.append(self._process_properties_with_important(group_config))
                    css_parts.append("}\n\n")
        
        # wrapper_content -> стили для .marking-item (обёртка контента)
        if 'wrapper_content' in self.general_config:
            wrapper_content_config = self.general_config['wrapper_content']
            if isinstance(wrapper_content_config, dict):
                css_parts.append(".marking-item {")
                css_parts.append(self._process_dict_properties_with_important(wrapper_content_config, current_section='wrapper_content'))
                css_parts.append("}\n\n")
            elif isinstance(wrapper_content_config, list):
                if wrapper_content_config:
                    css_parts.append(".marking-item {")
                    css_parts.append(self._process_properties_with_important(wrapper_content_config))
                    css_parts.append("}\n\n")
        
        # menu -> стили для .menu (для обратной совместимости)
        if 'menu' in self.general_config:
            menu_config = self.general_config['menu']
            if isinstance(menu_config, dict):
                css_parts.append(".menu {")
                css_parts.append(self._process_dict_properties_with_important(menu_config, current_section='menu'))
                css_parts.append("}\n\n")
            elif isinstance(menu_config, list):
                if menu_config:
                    css_parts.append(".menu {")
                    css_parts.append(self._process_properties_with_important(menu_config))
                    css_parts.append("}\n\n")
        
        # nav -> стили для nav (семантический тег навигации)
        if 'nav' in self.general_config:
            nav_config = self.general_config['nav']
            if isinstance(nav_config, dict):
                css_parts.append("nav {")
                css_parts.append(self._process_dict_properties_with_important(nav_config, current_section='nav'))
                css_parts.append("}\n\n")
                # Также применяем к .menu для обратной совместимости
                css_parts.append(".menu {")
                css_parts.append(self._process_dict_properties_with_important(nav_config, current_section='nav'))
                css_parts.append("}\n\n")
            elif isinstance(nav_config, list):
                if nav_config:
                    css_parts.append("nav {")
                    css_parts.append(self._process_properties_with_important(nav_config))
                    css_parts.append("}\n\n")
                    # Также применяем к .menu для обратной совместимости
                    css_parts.append(".menu {")
                    css_parts.append(self._process_properties_with_important(nav_config))
                    css_parts.append("}\n\n")
        
        # Стили из tag.json (перекрывают стили из general.json)
        if self.tag_config:
            css_parts.append("/* ===== СТИЛИ ТЕГОВ ИЗ TAG.JSON ===== */\n\n")
            for tag_name, tag_config in self.tag_config.items():
                if tag_name == 'text':
                    # text генерируется как <text class="content-*">
                    selector = 'text'
                elif tag_name == 'icon':
                    # icon генерируется как <icon class="content-*">
                    selector = 'icon'
                elif tag_name == 'icon svg':
                    # svg внутри icon
                    selector = 'icon svg'
                elif tag_name in ['a', 'img', 'input', 'button', 'form', 'label']:
                    # Для HTML тегов без точки (a, img, input, button, form, label)
                    selector = tag_name
                elif tag_name == 'nav':
                    selector = 'nav'
                elif tag_name == 'marking-item':
                    selector = '.marking-item'
                elif ' ' in tag_name or '>' in tag_name or ':' in tag_name or '[' in tag_name or '+' in tag_name or '~' in tag_name:
                    # Составные селекторы (например, "a > img", "a:has(img)", "a img")
                    # Используем как есть без добавления точки
                    selector = tag_name
                else:
                    # Для других классов
                    selector = f'.{tag_name}' if not tag_name.startswith('.') else tag_name
                
                if isinstance(tag_config, dict):
                    if tag_config:  # Проверяем, что не пустой словарь
                        # Проверяем, есть ли desktop/tablet/mobile для адаптивных стилей
                        desktop_config = tag_config.get('desktop', {})
                        tablet_config = tag_config.get('tablet', {})
                        mobile_config = tag_config.get('mobile', {})
                        
                        # Базовые стили (исключаем desktop/tablet/mobile)
                        base_config = {k: v for k, v in tag_config.items() if k not in ['desktop', 'tablet', 'mobile']}
                        
                        # Получаем breakpoints для медиа-запросов
                        tablet_breakpoint = '768px'
                        mobile_breakpoint = '320px'
                        if self.general_config and 'layout' in self.general_config:
                            device_config = self.general_config['layout'].get('device', {})
                            if 'tablet' in device_config:
                                tablet_device = device_config['tablet']
                                if isinstance(tablet_device, dict) and 'width' in tablet_device:
                                    tablet_breakpoint = tablet_device['width']
                                elif isinstance(tablet_device, list) and len(tablet_device) >= 2:
                                    tablet_breakpoint = tablet_device[0] + tablet_device[1]
                            if 'mobile' in device_config:
                                mobile_device = device_config['mobile']
                                if isinstance(mobile_device, dict) and 'width' in mobile_device:
                                    mobile_breakpoint = mobile_device['width']
                                elif isinstance(mobile_device, list) and len(mobile_device) >= 2:
                                    mobile_breakpoint = mobile_device[0] + mobile_device[1]
                        
                        # Нормализация массивов: [val1, val2, val3] или [val1, val2, val3, unit]
                        def _normalize_array_value(value):
                            if isinstance(value, list) and len(value) == 4 and isinstance(value[3], str):
                                unit = value[3]
                                return [f"{value[0]}{unit}", f"{value[1]}{unit}", f"{value[2]}{unit}"]
                            elif isinstance(value, list) and len(value) == 3:
                                return value
                            return value
                        
                        # Проверяем, есть ли массивы для адаптивных стилей в base_config
                        has_arrays = any(isinstance(v, list) and (len(v) == 3 or (len(v) == 4 and isinstance(v[3], str))) for v in base_config.values())
                        
                        if has_arrays:
                            # Разделяем свойства с массивами и без
                            array_props = {}
                            normal_props = {}
                            
                            for prop_name, prop_value in base_config.items():
                                normalized = _normalize_array_value(prop_value)
                                if isinstance(normalized, list) and len(normalized) == 3:
                                    array_props[prop_name] = normalized
                                else:
                                    normal_props[prop_name] = prop_value
                            
                            # Генерируем desktop стили (обычные свойства + desktop значения из массивов)
                            desktop_props = {k: v[0] for k, v in array_props.items()}
                            all_desktop_props = {**normal_props, **desktop_props}
                            
                            if all_desktop_props:
                                css_parts.append(f"{selector} {{")
                                css_parts.append(self._process_dict_properties_with_important(all_desktop_props, current_section=tag_name))
                                css_parts.append("}\n\n")
                            
                            # Генерируем медиа-запросы для tablet
                            tablet_props = {k: v[1] for k, v in array_props.items()}
                            if tablet_props:
                                css_parts.append(f"@media (max-width: {tablet_breakpoint}) {{\n")
                                css_parts.append(f"    {selector} {{\n")
                                css_parts.append(self._process_dict_properties_with_important(tablet_props, indent="        ", current_section=tag_name))
                                css_parts.append("    }\n")
                                css_parts.append("}\n\n")
                            
                            # Генерируем медиа-запросы для mobile
                            mobile_props = {k: v[2] for k, v in array_props.items()}
                            if mobile_props:
                                css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{\n")
                                css_parts.append(f"    {selector} {{\n")
                                css_parts.append(self._process_dict_properties_with_important(mobile_props, indent="        ", current_section=tag_name))
                                css_parts.append("    }\n")
                                css_parts.append("}\n\n")
                        elif base_config:
                            # Обычные стили без массивов
                            css_parts.append(f"{selector} {{")
                            css_parts.append(self._process_dict_properties_with_important(base_config, current_section=tag_name))
                            css_parts.append("}\n\n")
                        
                        # Desktop стили (если есть отдельная секция desktop)
                        if desktop_config:
                            css_parts.append(f"{selector} {{")
                            css_parts.append(self._process_dict_properties_with_important(desktop_config, current_section=tag_name))
                            css_parts.append("}\n\n")
                        
                        # Tablet стили (если есть отдельная секция tablet)
                        if tablet_config:
                            css_parts.append(f"@media (max-width: {tablet_breakpoint}) {{\n")
                            css_parts.append(f"    {selector} {{\n")
                            css_parts.append(self._process_dict_properties_with_important(tablet_config, current_section=tag_name, indent="        "))
                            css_parts.append("    }\n")
                            css_parts.append("}\n\n")
                        
                        # Mobile стили (если есть отдельная секция mobile)
                        if mobile_config:
                            css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{\n")
                            css_parts.append(f"    {selector} {{\n")
                            css_parts.append(self._process_dict_properties_with_important(mobile_config, current_section=tag_name, indent="        "))
                            css_parts.append("    }\n")
                            css_parts.append("}\n\n")
                elif isinstance(tag_config, list):
                    if tag_config:
                        css_parts.append(f"{selector} {{")
                        css_parts.append(self._process_properties_with_important(tag_config))
                        css_parts.append("}\n\n")
        
        # & -> стили для .col_* (внутренние колонки) - удобное короткое название
        if '&' in self.general_config:
            col_config = self.general_config['&']
            if isinstance(col_config, dict):
                css_parts.append("[class^='col_'] {")
                css_parts.append(self._process_dict_properties_with_important(col_config, current_section='&'))
                css_parts.append("}\n\n")
            elif isinstance(col_config, list):
                if col_config:
                    css_parts.append("[class^='col_'] {")
                    css_parts.append(self._process_properties_with_important(col_config))
                    css_parts.append("}\n\n")
        
        # col_in_row -> стили для .col_* (внутренние колонки)
        if 'col_in_row' in self.general_config:
            col_config = self.general_config['col_in_row']
            if isinstance(col_config, dict):
                css_parts.append("[class^='col_'] {")
                css_parts.append(self._process_dict_properties_with_important(col_config, current_section='col_in_row'))
                css_parts.append("}\n\n")
            elif isinstance(col_config, list):
                if col_config:
                    css_parts.append("[class^='col_'] {")
                    css_parts.append(self._process_properties_with_important(col_config))
                    css_parts.append("}\n\n")
        
        # col -> стили для .col_* (внутренние колонки) - для обратной совместимости
        if 'col' in self.general_config:
            col_config = self.general_config['col']
            if isinstance(col_config, dict):
                css_parts.append("[class^='col_'] {")
                css_parts.append(self._process_dict_properties_with_important(col_config, current_section='col'))
                css_parts.append("}\n\n")
            elif isinstance(col_config, list):
                if col_config:
                    css_parts.append("[class^='col_'] {")
                    css_parts.append(self._process_properties_with_important(col_config))
                    css_parts.append("}\n\n")
        
        # Составные селекторы (column.row, col.row и т.д.)
        for key, config in self.general_config.items():
            if '.' in key and isinstance(config, dict):
                # Преобразуем "column.row" -> ".column .row"
                selector = '.' + key.replace('.', ' .')
                css_parts.append(f"{selector} {{")
                css_parts.append(self._process_dict_properties_with_important(config, current_section=key))
                css_parts.append("}\n\n")
        
        return '\n'.join(css_parts)
    
    def _process_dict_properties_with_important(self, properties: dict, indent: str = "    ", current_section: str = None, config_for_refs: dict = None) -> str:
        """Обрабатывает словарь CSS свойств с добавлением !important
        Поддерживает формат: {"property": "value"} или {"property": ["value", "unit"]}
        Поддерживает ссылки: {"border": ["1px solid", "page.bg-color.darker-0.8"]}
        
        Args:
            properties: Словарь CSS свойств
            indent: Отступ для CSS
            current_section: Текущая секция для разрешения относительных ссылок
            config_for_refs: Конфиг для разрешения ссылок (если None, используется general_config)
        """
        css_lines = []
        # Используем переданный конфиг или general_config по умолчанию
        ref_config = config_for_refs if config_for_refs is not None else self.general_config
        
        for prop, value in properties.items():
            # Если свойство заканчивается на *, пропускаем его (не создаем CSS)
            if prop.endswith('*'):
                continue
            
            # Пропускаем служебные ключи конфигурации (не CSS свойства)
            if prop in ['desktop', 'tablet', 'mobile', 'general', 'device', 'double']:
                continue
            
            # Преобразуем сокращения
            # Сначала обрабатываем специальные случаи
            if prop == 'bg-clip':
                prop = 'background-clip'
            else:
                prop = prop.replace('bg-color', 'background-color')
                prop = prop.replace('bg', 'background-color')
            prop = prop.replace('radius', 'border-radius')
            prop = prop.replace('align', 'text-align')
            
            # Специальная обработка для border с массивом из 3 элементов: ["2px solid", "1", "yellow.150"]
            if prop == 'border' and isinstance(value, list) and len(value) == 3:
                border_style = value[0]  # "2px solid"
                border_flags_str = str(value[1])  # "1" или "1 1 0 1"
                border_color_ref = value[2]  # "yellow.150"
                
                # Разрешаем цвет с модификатором
                resolved_color = process_css_value(border_color_ref, ref_config, current_section)
                
                # Парсим флаги сторон
                border_flags = border_flags_str.split()  # "1" -> ["1"], "1 1 0 1" -> ["1", "1", "0", "1"]
                
                # Если только один флаг, применяем ко всем сторонам
                if len(border_flags) == 1:
                    if border_flags[0] == '1':
                        css_lines.append(f"{indent}border: {border_style} {resolved_color} !important;")
                else:
                    # Несколько флагов для разных сторон
                    sides = ['top', 'right', 'bottom', 'left']
                    for i, flag in enumerate(border_flags):
                        if i < len(sides) and flag == '1':
                            css_lines.append(f"{indent}border-{sides[i]}: {border_style} {resolved_color} !important;")
                continue
            
            # Обрабатываем значение с поддержкой ссылок и модификаторов
            css_value = process_css_value(value, ref_config, current_section)
            
            # Проверяем, является ли это border с несколькими сторонами (формат "border-top: ... | border-right: ...")
            if prop == 'border' and ' | ' in css_value:
                # Разбиваем на отдельные border-* свойства
                border_parts = css_value.split(' | ')
                for border_part in border_parts:
                    # border_part имеет формат "border-top: 2px solid #color"
                    css_lines.append(f"{indent}{border_part} !important;")
            else:
                # Обычное свойство
                css_lines.append(f"{indent}{prop}: {css_value} !important;")
        return '\n'.join(css_lines)
    
    def _process_properties_with_important(self, properties: list, indent: str = "    ") -> str:
        """Обрабатывает массив CSS свойств с добавлением !important"""
        css_lines = []
        for prop in properties:
            # Преобразуем сокращения
            prop = prop.replace('bg:', 'background-color:')
            prop = prop.replace('radius:', 'border-radius:')
            prop = prop.replace('align:', 'text-align:')
            # Добавляем !important если его еще нет
            if '!important' not in prop:
                prop = prop.rstrip(';') + ' !important'
            css_lines.append(f"{indent}{prop};")
        return '\n'.join(css_lines)
