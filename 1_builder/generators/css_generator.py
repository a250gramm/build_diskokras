#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSSGenerator - Генерация CSS стилей
"""

from typing import Dict, Any
from pathlib import Path
from css.layout.default import get_default_css, get_component_css, get_alignment_css, get_modal_css, get_section_styles_css
from generators.report_checker import is_report_enabled
from processors.value_processor import process_css_value
from utils.layout_structure_analyzer import LayoutStructureAnalyzer
from generators.css.layout_generator import LayoutGenerator
from generators.css.report_generator import ReportGenerator
from generators.css.base_generator import BaseGenerator
from generators.css.conditional_css_generator import ConditionalCSSGenerator
from generators.css.filter_css_generator import FilterCSSGenerator
from generators.css.section_css_generator import SectionCSSGenerator
from processors.value_processor import init_colors


class CSSGenerator:
    """Генерирует CSS из css.json, default.json, general.json, if.json, filter.json"""
    
    def __init__(self, configs: Dict[str, Any]):
        """
        Args:
            configs: Словарь с конфигами (css, default, general, if, filter, report, config, html)
        """
        self.css_config = configs['css']
        self.default_config = configs['default']
        self.general_config = configs.get('general', {})
        self.tag_config = configs.get('tag', {})
        self.objects_css = configs.get('objects_css', {})
        self.report_objects_css = configs.get('report_objects_css', {})
        self.if_config = configs.get('if', {})
        self.filter_config = configs.get('filter', {})
        self.report_config = configs.get('report', {})
        self.app_config = configs.get('config', {})
        self.map_config = configs.get('map', {})
        self.html_config = configs.get('html', {})
        self.sections_config = configs.get('sections', {})  # objects.json
        self.colors_config = configs.get('colors', {})  # library/color.json
        self.div_column_config = configs.get('div_column', {})  # default/div_column.json
        self.source_dir = None  # Будет установлен при генерации
        
        # Инициализируем библиотеку цветов
        init_colors(self.colors_config)
        
        # Инициализируем анализатор структуры разметки
        self.structure_analyzer = LayoutStructureAnalyzer(self.html_config) if self.html_config else None
        
        # Инициализируем генераторы модулей
        self.base_generator = BaseGenerator(
            self.general_config,
            self._process_dict_properties_with_important,
            self._process_properties_with_important
        )
        self.base_generator.tag_config = self.tag_config  # Передаём tag_config
        
        self.layout_generator = LayoutGenerator(
            self.css_config,
            self.general_config,
            self.report_config,
            self.default_config,
            self.objects_css,
            self.report_objects_css,
            self.structure_analyzer,
            self._process_dict_properties_with_important,
            self._process_properties,
            self._process_properties_with_important,
            self._is_report_enabled,
            self.sections_config  # objects.json для определения типов элементов
        )
        
        self.report_generator = ReportGenerator(
            self.report_config,
            self.general_config,
            self.css_config,
            self.structure_analyzer,
            self._process_dict_properties_with_important,
            self._process_properties_with_important,
            self._is_report_enabled
        )
        
        # Инициализируем новые генераторы
        self.conditional_generator = ConditionalCSSGenerator(
            self.if_config,
            self._process_media_properties
        )
        
        self.filter_generator = FilterCSSGenerator(
            self.filter_config,
            self.default_config,
            self._process_properties,
            self._process_media_properties
        )
        
        self.section_generator = SectionCSSGenerator(
            self.general_config,
            self.report_config,
            self._is_report_enabled,
            process_css_value
        )
    
    def generate(self, source_dir: Path = None) -> str:
        """
        Генерирует весь CSS
        
        Args:
            source_dir: Путь к директории sourse (для default.json)
            
        Returns:
            Полный CSS код
        """
        self.source_dir = source_dir
        
        css_parts = ["/* CSS стили для diskokras - сгенерировано автоматически */\n"]
        
        # Базовые стили из default.json 
        # Если report включен - используем report_config для device, иначе general_config
        config_for_default = self.general_config
        if self._is_report_enabled() and self.report_config and 'layout' in self.report_config:
            config_for_default = self.report_config
        css_parts.append(get_default_css(source_dir, config_for_default))
        css_parts.append("\n")
        
        # Стили компонентов из default.json
        css_parts.append(get_component_css(source_dir))
        css_parts.append("\n")
        
        # Стили выравнивания из default.json
        css_parts.append(get_alignment_css(source_dir))
        css_parts.append("\n")
        
        # Стили модальных окон из default.json
        css_parts.append(get_modal_css(source_dir))
        css_parts.append("\n")
        
        # Глобальные стили из general.json
        if self.general_config:
            css_parts.append("/* ===== ГЛОБАЛЬНЫЕ СТИЛИ (general) ===== */\n\n")
            css_parts.append(self.base_generator.generate())
            css_parts.append("\n")
        
        # Стили из report.json (если включено в config.json и файл существует)
        # ВАЖНО: генерируем ДО layout, чтобы медиа-запросы из layout перекрывали базовые стили
        if self._is_report_enabled() and self.report_config:
            css_parts.append("/* ===== ОТЛАДОЧНЫЕ СТИЛИ (report) ===== */\n\n")
            css_parts.append(self.report_generator.generate())
            css_parts.append("\n")
        
        # Обрабатываем составные селекторы из css.json (например, "header.nav", "turn.nav", "turn.column_3.row_1.group_1")
        # ВАЖНО: генерируем ПОСЛЕ report, чтобы специфичные селекторы перекрывали базовые стили из report
        css_parts.append("/* ===== СОСТАВНЫЕ СЕЛЕКТОРЫ ИЗ CSS.JSON ===== */\n\n")
        for key, value in self.css_config.items():
            # Пропускаем ключи с пробелами (они обрабатываются в layout_generator.py)
            if ' ' in key:
                continue
            
            if '.' in key:
                # Это составной селектор
                parts = key.split('.')
                
                # Пропускаем ключи формата "header.2.2.1" (группы, обрабатываются в layout_generator.py)
                if len(parts) == 4 and parts[1].isdigit() and parts[2].isdigit() and parts[3].isdigit():
                    continue
                
                if len(parts) == 2:
                    # Простой селектор: "header.nav" -> ".section-header .nav" или ".section-header nav"
                    section_name = parts[0]
                    selector_part = parts[1]
                    # Определяем, это тег (nav, a, div) или класс
                    if selector_part in ['nav', 'a', 'img', 'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        # Это тег
                        selector = f".section-{section_name} {selector_part}"
                    else:
                        # Это класс
                        selector = f".section-{section_name} .{selector_part}"
                elif len(parts) >= 3:
                    # Глубокий селектор: "turn.column_3.row_1.group_1" -> ".section-turn .col_3 .row_1 .group-turn-1"
                    section_name = parts[0]
                    selector_parts = [f".section-{section_name}"]
                    
                    for i, part in enumerate(parts[1:], 1):
                        if part.startswith('column_'):
                            # column_3 -> .col_3
                            col_num = part.replace('column_', '')
                            selector_parts.append(f".col_{col_num}")
                        elif part.startswith('row_'):
                            # row_1 -> .row_1
                            selector_parts.append(f".{part}")
                        elif part.startswith('group_') or part == 'group':
                            # group_1 -> .group-{section}-1
                            group_num = part.replace('group_', '').replace('group', '1') if part != 'group' else '1'
                            selector_parts.append(f".group-{section_name}-{group_num}")
                        else:
                            # Обычный класс или тег
                            if part in ['nav', 'a', 'img', 'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                selector_parts.append(part)
                            else:
                                selector_parts.append(f".{part}")
                    
                    selector = ' '.join(selector_parts)
                else:
                    continue
                
                if isinstance(value, dict):
                    css_parts.append(f"{selector} {{")
                    css_parts.append(self._process_dict_properties_with_important(value))
                    css_parts.append("}\n\n")
                elif isinstance(value, list):
                    if value:
                        css_parts.append(f"{selector} {{")
                        css_parts.append(self._process_properties_with_important(value))
                        css_parts.append("}\n\n")
        css_parts.append("\n")
        
        # Layout стили из css.json
        css_parts.append("/* ===== LAYOUT СТИЛИ ===== */\n\n")
        css_parts.append(self.layout_generator.generate())
        css_parts.append("\n")
        
        # Стили для section из general.json (после layout, чтобы перекрыть их)
        section_styles = self.section_generator.generate()
        if section_styles:
            css_parts.append("/* ===== СТИЛИ СЕКЦИЙ ИЗ GENERAL.JSON (перекрывают layout) ===== */\n\n")
            css_parts.append(section_styles)
            css_parts.append("\n")
        
        # Стили для section из default.json (после layout, чтобы перекрыть их)
        section_styles = get_section_styles_css(source_dir, self.general_config)
        if section_styles:
            css_parts.append("/* ===== СТИЛИ СЕКЦИЙ ИЗ DEFAULT.JSON ===== */\n\n")
            css_parts.append(section_styles)
            css_parts.append("\n")
        
        # Стили из if.json
        if_css = self.conditional_generator.generate()
        if if_css:
            css_parts.append("/* ===== УСЛОВНЫЕ СТИЛИ (if) ===== */\n\n")
            css_parts.append(if_css)
            css_parts.append("\n")
        
        # Стили из filter.json
        filter_css = self.filter_generator.generate()
        if filter_css:
            css_parts.append("/* ===== ФИЛЬТРОВАННЫЕ СТИЛИ (filter) ===== */\n\n")
            css_parts.append(filter_css)
            css_parts.append("\n")
        
        # Стили для колонок из div_column.json
        div_column_css = self._generate_div_column_css()
        if div_column_css:
            css_parts.append("/* ===== СТИЛИ ДЛЯ КОЛОНОК (div_column) ===== */\n\n")
            css_parts.append(div_column_css)
            css_parts.append("\n")
        
        # Стили для col: синтаксиса из objects.json
        col_syntax_css = self._generate_col_syntax_css()
        if col_syntax_css:
            css_parts.append("/* ===== СТИЛИ ДЛЯ COL: СИНТАКСИСА ===== */\n\n")
            css_parts.append(col_syntax_css)
            css_parts.append("\n")
        
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
    
    def _process_properties(self, properties: list, indent: str = "    ") -> str:
        """Обрабатывает массив CSS свойств"""
        css_lines = []
        for prop in properties:
            # Преобразуем сокращения
            prop = prop.replace('bg:', 'background-color:')
            prop = prop.replace('radius:', 'border-radius:')
            prop = prop.replace('align:', 'text-align:')
            css_lines.append(f"{indent}{prop};")
        return '\n'.join(css_lines)
    
    def _process_media_properties(self, media_props: list, device_index: int = 0, indent: str = "    ") -> str:
        """Обрабатывает media свойства для разных устройств"""
        css_lines = []
        for prop in media_props:
            if ':' in prop:
                prop_name, prop_values = prop.split(':', 1)
                values = [v.strip() for v in prop_values.split(',')]
                if device_index < len(values):
                    value = values[device_index]
                    # Преобразуем сокращения
                    prop_name = prop_name.replace('bg', 'background-color')
                    prop_name = prop_name.replace('radius', 'border-radius')
                    css_lines.append(f"{indent}{prop_name}: {value};")
        return '\n'.join(css_lines)
    
    def _generate_div_column_css(self) -> str:
        """
        Генерирует CSS для колонок из div_column.json
        Применяет стили из col-1, col-2, etc к классам с суффиксом _col-1, _col-2, etc
        """
        if not self.div_column_config:
            return ''
        
        css_parts = []
        
        # Получаем брейкпоинты
        devices = self._get_devices()
        tablet_breakpoint = devices.get('tablet', '768px')
        mobile_breakpoint = devices.get('mobile', '320px')
        
        # Обрабатываем desktop (базовые стили)
        desktop_config = self.div_column_config.get('desktop', {})
        for col_key, col_styles in desktop_config.items():
            if col_key.startswith('col-'):
                # Генерируем селектор для классов с суффиксом _col-N
                # Например, col-2 → [class*='_col-2']
                selector = f"[class*='_{col_key}']"
                css_parts.append(f"{selector} {{")
                css_parts.append(self._process_dict_properties_with_important(col_styles))
                css_parts.append("}\n")
                
                # Добавляем более специфичный селектор для перекрытия правил типа [data-path='main_btn'] div.gr7
                # [data-path] div[class*='_col-2'] имеет такую же специфичность (0,2,1) как [data-path] div.gr7
                # и идет позже в CSS, поэтому перекрывает его
                specific_selector = f"[data-path] div[class*='_{col_key}']"
                css_parts.append(f"{specific_selector} {{")
                css_parts.append(self._process_dict_properties_with_important(col_styles))
                css_parts.append("}\n")
                
                # Также применяем grid к div[data-template] внутри элементов с _col-N
                # Это нужно для cycle, который генерирует элементы внутри data-template
                template_selector = f"{selector} > div[data-template]"
                css_parts.append(f"{template_selector} {{")
                css_parts.append(self._process_dict_properties_with_important(col_styles))
                css_parts.append("}\n")
                
                # Добавляем селектор для div[data-template] который САМ имеет класс _col-N
                # Это нужно для cycle_col-N, который создает div[data-template] с классом _col-N
                template_with_class = f"div[data-template][class*='_{col_key}']"
                css_parts.append(f"{template_with_class} {{")
                css_parts.append(self._process_dict_properties_with_important(col_styles))
                css_parts.append("}\n")
                
                # Добавляем стили для дочерних элементов div[data-template] с классом _col-N
                # чтобы они правильно размещались в grid колонках
                child_selector_template = f"{template_with_class} > div"
                css_parts.append(f"{child_selector_template} {{")
                css_parts.append("    box-sizing: border-box !important;\n")
                css_parts.append("    min-width: 0 !important;\n")
                css_parts.append("    width: auto !important;\n")
                css_parts.append("    max-width: none !important;\n")
                css_parts.append("}\n")
                
                # Добавляем еще более специфичный селектор для гарантированного применения
                # div[class*='_col-2'] > div[data-template] с явным указанием display: grid
                very_specific = f"div{selector} > div[data-template]"
                css_parts.append(f"{very_specific} {{")
                css_parts.append(self._process_dict_properties_with_important(col_styles))
                css_parts.append("}\n")
                
                # Добавляем стили для дочерних элементов внутри div[data-template]
                # чтобы они правильно размещались в grid колонках
                # Важно: НЕ добавляем width, чтобы grid сам управлял размерами
                child_selector = f"{template_selector} > div"
                css_parts.append(f"{child_selector} {{")
                css_parts.append("    box-sizing: border-box !important;\n")
                css_parts.append("    min-width: 0 !important;\n")  # Позволяет grid сжимать элементы
                css_parts.append("    width: auto !important;\n")  # Явно указываем auto, чтобы grid управлял
                css_parts.append("    max-width: none !important;\n")  # Убираем ограничения
                css_parts.append("}\n")
        
        # Обрабатываем tablet (медиа-запрос)
        tablet_config = self.div_column_config.get('tablet', {})
        if tablet_config:
            # Tablet: от mobile_breakpoint + 1px до tablet_breakpoint
            mobile_breakpoint_num = int(mobile_breakpoint.replace('px', ''))
            tablet_breakpoint_num = int(tablet_breakpoint.replace('px', ''))
            css_parts.append(f"@media (max-width: {tablet_breakpoint}) and (min-width: {mobile_breakpoint_num + 1}px) {{")
            for selector_key, selector_styles in tablet_config.items():
                # Селектор может быть "col-2, col-3" или просто "col-2"
                selectors = [f"[class*='_{s.strip()}']" for s in selector_key.split(',')]
                selector = ', '.join(selectors)
                css_parts.append(f"    {selector} {{")
                css_parts.append(self._process_dict_properties_with_important(selector_styles, indent="        "))
                css_parts.append("    }")
            css_parts.append("}\n")
        
        # Обрабатываем mobile (медиа-запрос)
        mobile_config = self.div_column_config.get('mobile', {})
        if mobile_config:
            css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{")
            for selector_key, selector_styles in mobile_config.items():
                # Селектор может быть "col-2, col-3" или просто "col-2"
                selectors = [f"[class*='_{s.strip()}']" for s in selector_key.split(',')]
                selector = ', '.join(selectors)
                css_parts.append(f"    {selector} {{")
                css_parts.append(self._process_dict_properties_with_important(selector_styles, indent="        "))
                css_parts.append("    }")
            css_parts.append("}\n")
        
        return '\n'.join(css_parts)
    
    def _generate_col_syntax_css(self) -> str:
        """
        Генерирует CSS стили для элементов с col: синтаксисом из objects.json
        Сканирует sections_config и генерирует стили для элементов с col:2,1,1 и col:20%
        """
        if not self.sections_config:
            return ''
        
        from utils.element_utils import parse_col_syntax, parse_html_tag
        
        css_parts = []
        devices = self._get_devices()
        tablet_breakpoint = devices.get('tablet', '768px')
        mobile_breakpoint = devices.get('mobile', '320px')
        
        # Собираем информацию о всех элементах с col: синтаксисом
        col_elements = []  # Список элементов с col: синтаксисом
        parent_child_map = {}  # {parent_path: [child_percentages]}
        
        def scan_dict(data: Dict, path: str = '', parent_col_info: Dict = None, parent_path: str = ''):
            """Рекурсивно сканирует словарь и собирает элементы с col: синтаксисом"""
            for key, value in data.items():
                if key == 'if':
                    continue
                
                # Проверяем, есть ли col: синтаксис в ключе
                col_info = parse_col_syntax(key)
                current_col_info = col_info if col_info else parent_col_info
                
                # Парсим HTML тег для получения информации об элементе
                tag_info = parse_html_tag(key)
                full_path = f"{path}.{key}" if path else key
                
                if tag_info:
                    tag_name, class_name, _ = tag_info
                    
                    # Используем data-path для селектора
                    last_part = full_path.split('.')[-1]
                    if class_name:
                        # Для элементов с классом используем более специфичный селектор
                        selector = f"[data-path*='{last_part}'] {tag_name}.{class_name}"
                    else:
                        selector = f"[data-path*='{last_part}'] {tag_name}"
                    
                    # Если есть col: синтаксис, сохраняем информацию
                    if col_info:
                        element_data = {
                            'col_info': col_info,
                            'selector': selector,
                            'full_path': full_path,
                            'tag_name': tag_name,
                            'class_name': class_name,
                            'parent_path': parent_path
                        }
                        col_elements.append(element_data)
                        
                        # Если это процентная колонка, сохраняем информацию о родителе
                        if col_info['type'] == 'percentage' and parent_path:
                            if parent_path not in parent_child_map:
                                parent_child_map[parent_path] = []
                            parent_child_map[parent_path].append(col_info['percentage'])
                
                # Обрабатываем cycle элементы отдельно
                elif (key == 'cycle' or key.startswith('cycle_')) and col_info:
                    # Для cycle элементов используем селектор по классу
                    clean_key = col_info['original_key']
                    last_part = full_path.split('.')[-1]
                    if clean_key.startswith('cycle_'):
                        class_name = clean_key.replace('cycle_', '')
                        selector = f"[data-path*='{last_part}'] .{class_name}"
                    else:
                        selector = f"[data-path*='{last_part}'] .cycle"
                    
                    element_data = {
                        'col_info': col_info,
                        'selector': selector,
                        'full_path': full_path,
                        'tag_name': 'div',
                        'class_name': class_name if clean_key.startswith('cycle_') else 'cycle',
                        'parent_path': parent_path
                    }
                    col_elements.append(element_data)
                
                # Рекурсивно обрабатываем вложенные словари
                if isinstance(value, dict):
                    new_path = f"{path}.{key}" if path else key
                    # Если текущий элемент имеет adaptive col: синтаксис, он становится родителем
                    new_parent_path = new_path if col_info and col_info['type'] == 'adaptive' else parent_path
                    scan_dict(value, new_path, current_col_info, new_parent_path)
        
        # Сканируем все секции
        for section_name, section_data in self.sections_config.items():
            if isinstance(section_data, dict):
                scan_dict(section_data, section_name)
        
        # Получаем базовые стили из div_column.json
        base_styles = self.div_column_config.get('base', {})
        columns_config = self.div_column_config.get('columns', {})
        
        # Сначала обрабатываем родительские элементы с процентными дочерними элементами
        processed_parents = set()
        
        # Генерируем CSS для каждого элемента
        for element in col_elements:
            col_info = element['col_info']
            selector = element['selector']
            
            if col_info['type'] == 'adaptive':
                # Адаптивные колонки: col:2,1,1
                desktop_cols = col_info['desktop']
                tablet_cols = col_info['tablet']
                mobile_cols = col_info['mobile']
                
                # Desktop стили
                grid_template = columns_config.get(str(desktop_cols), f"repeat({desktop_cols}, 1fr)")
                css_parts.append(f"{selector} {{")
                if base_styles.get('display'):
                    css_parts.append(f"    display: {base_styles['display']} !important;")
                else:
                    css_parts.append("    display: grid !important;")
                css_parts.append(f"    grid-template-columns: {grid_template} !important;")
                if base_styles.get('gap'):
                    gap_value = base_styles['gap']
                    if isinstance(gap_value, list) and len(gap_value) >= 2:
                        gap_str = f"{gap_value[0]}{gap_value[1] if len(gap_value) > 1 else 'px'}"
                        css_parts.append(f"    gap: {gap_str} !important;")
                css_parts.append("    box-sizing: border-box !important;")
                css_parts.append("}\n")
                
                # Tablet стили (если отличается от desktop)
                if tablet_cols != desktop_cols:
                    grid_template_tablet = columns_config.get(str(tablet_cols), f"repeat({tablet_cols}, 1fr)")
                    css_parts.append(f"@media (max-width: {tablet_breakpoint}) {{")
                    css_parts.append(f"    {selector} {{")
                    css_parts.append(f"        grid-template-columns: {grid_template_tablet} !important;")
                    css_parts.append("    }")
                    css_parts.append("}\n")
                
                # Mobile стили (если отличается от tablet)
                if mobile_cols != tablet_cols:
                    grid_template_mobile = columns_config.get(str(mobile_cols), f"repeat({mobile_cols}, 1fr)")
                    css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{")
                    css_parts.append(f"    {selector} {{")
                    css_parts.append(f"        grid-template-columns: {grid_template_mobile} !important;")
                    css_parts.append("    }")
                    css_parts.append("}\n")
            
            elif col_info['type'] == 'percentage':
                # Процентная ширина: col:20%
                # Это используется для дочерних элементов внутри grid контейнера
                percent = col_info['percentage']
                css_parts.append(f"{selector} {{")
                css_parts.append(f"    width: {percent}% !important;")
                css_parts.append(f"    max-width: {percent}% !important;")
                css_parts.append("    box-sizing: border-box !important;")
                css_parts.append("}\n")
                
                # Если у родителя есть дочерние элементы с процентами, обновляем grid-template-columns
                parent_path = element.get('parent_path', '')
                if parent_path and parent_path in parent_child_map and parent_path not in processed_parents:
                    processed_parents.add(parent_path)
                    # Находим родительский элемент
                    parent_element = next((e for e in col_elements if e['full_path'] == parent_path and e['col_info']['type'] == 'adaptive'), None)
                    if parent_element:
                        # Генерируем grid-template-columns на основе процентов дочерних элементов
                        percentages = parent_child_map[parent_path]
                        grid_template = ' '.join([f"{p}%" for p in percentages])
                        parent_selector = parent_element['selector']
                        css_parts.append(f"{parent_selector} {{")
                        css_parts.append(f"    grid-template-columns: {grid_template} !important;")
                        css_parts.append("}\n")
        
        return '\n'.join(css_parts)
    
    def _get_devices(self):
        """Получает настройки устройств из конфига"""
        devices = {}
        if self.general_config and 'layout' in self.general_config and 'device' in self.general_config['layout']:
            device_config = self.general_config['layout']['device']
            for device_name in ['desktop', 'tablet', 'mobile']:
                if device_name in device_config:
                    device_value = device_config[device_name]
                    if isinstance(device_value, dict) and 'width' in device_value:
                        devices[device_name] = device_value['width']
                    elif isinstance(device_value, list) and len(device_value) >= 2:
                        devices[device_name] = device_value[0] + device_value[1]
                    elif isinstance(device_value, str):
                        devices[device_name] = device_value
        if not devices and self.default_config:
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
        return devices
    
    def _is_report_enabled(self) -> bool:
        """
        Проверяет, включен ли репорт.
        Использует report_checker для проверки переключателя REPORT_ENABLED
        """
        return is_report_enabled()
    
    def save(self, css_content: str, css_file: Path) -> None:
        """
        Сохраняет CSS в файл
        
        Args:
            css_content: Содержимое CSS
            css_file: Путь к файлу CSS
        """
        # Убеждаемся, что директория существует
        css_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Удаляем старый файл (если существует)
        if css_file.exists():
            css_file.unlink()
        
        # Записываем новое содержимое через open() для гарантии полной записи
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        # Проверяем, что файл записан правильно
        if not css_file.exists():
            raise IOError(f"Файл не был создан: {css_file}")
        
        # Финальная проверка содержимого
        saved_content = css_file.read_text(encoding='utf-8')
        if saved_content != css_content:
            raise IOError(f"Файл не записан правильно! Размеры: ожидалось {len(css_content)}, записано {len(saved_content)}")

