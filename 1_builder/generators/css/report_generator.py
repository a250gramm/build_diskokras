#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Generator - ПОЛНАЯ версия из css_generator_FULL_OLD.py
"""

from typing import Dict, Any
from pathlib import Path


class ReportGenerator:
    """Генерирует отладочные CSS стили (ПОЛНАЯ ЛОГИКА из старой версии)"""
    
    def __init__(self, report_config, general_config, css_config, structure_analyzer,
                 process_dict_fn, process_props_important_fn, is_report_enabled_fn):
        self.report_config = report_config
        self.general_config = general_config
        self.css_config = css_config
        self.structure_analyzer = structure_analyzer
        self._process_dict_properties_with_important = process_dict_fn
        self._process_properties_with_important = process_props_important_fn
        self._is_report_enabled = is_report_enabled_fn
    
    def generate(self) -> str:
        """Главный метод генерации"""
        return self._generate_report_css()
    
    def _generate_report_css(self) -> str:
        """Генерирует CSS из report.json по названиям элементов
        Поддерживает формат объектов: {"page": {"bg-color": "magenta", ...}}
        """
        css_parts = []
        
        # Получаем device_settings для использования gap и flex-wrap из device настроек
        device_settings = {}
        config_to_use = None
        if self._is_report_enabled() and self.report_config and 'layout' in self.report_config:
            config_to_use = self.report_config.get('layout', {})
        elif self.general_config and 'layout' in self.general_config:
            config_to_use = self.general_config.get('layout', {})
        
        if config_to_use and 'device' in config_to_use:
            device_config = config_to_use['device']
            for device_name in ['desktop', 'tablet', 'mobile']:
                if device_name in device_config:
                    device_value = device_config[device_name]
                    if isinstance(device_value, dict):
                        device_settings[device_name] = {k: v for k, v in device_value.items() if k != 'width'}
        
        # Объединяем general_config и report_config для разрешения ссылок
        # Сначала general_config (базовые значения), потом report_config (переопределения)
        merged_config = {**self.general_config, **self.report_config}
        
        # html -> стили для html (корневой элемент)
        if 'html' in self.report_config:
            html_config = self.report_config['html']
            if isinstance(html_config, dict):
                css_parts.append("html {")
                css_parts.append(self._process_dict_properties_with_important(html_config, current_section='html', config_for_refs=merged_config))
                css_parts.append("}\n\n")
            elif isinstance(html_config, list):
                # Старый формат массива (для обратной совместимости)
                if html_config:
                    css_parts.append("html {")
                    css_parts.append(self._process_properties_with_important(html_config))
                    css_parts.append("}\n\n")
        
        # page -> стили для body
        if 'page' in self.report_config:
            page_config = self.report_config['page']
            if isinstance(page_config, dict):
                css_parts.append("body {")
                css_parts.append(self._process_dict_properties_with_important(page_config, current_section='page', config_for_refs=merged_config))
                css_parts.append("}\n\n")
            elif isinstance(page_config, list):
                # Старый формат массива (для обратной совместимости)
                if page_config:
                    css_parts.append("body {")
                    css_parts.append(self._process_properties_with_important(page_config))
                    css_parts.append("}\n\n")
        
        # section -> стили для section
        if 'section' in self.report_config:
            section_config = self.report_config['section']
            if isinstance(section_config, dict):
                css_parts.append("section {")
                css_parts.append(self._process_dict_properties_with_important(section_config, current_section='section', config_for_refs=merged_config))
                css_parts.append("}\n\n")
            elif isinstance(section_config, list):
                # Старый формат массива (для обратной совместимости)
                if section_config:
                    css_parts.append("section {")
                    css_parts.append(self._process_properties_with_important(section_config))
                    css_parts.append("}\n\n")
        
        # layout -> стили для .layout
        # РЕФАКТОРИНГ: определяем структуру секций и генерируем только нужные селекторы
        if 'layout' in self.report_config:
            layout_config = self.report_config['layout']
            if isinstance(layout_config, dict):
                # Сначала применяем базовые стили layout к .layout (исключаем device)
                layout_config_filtered_base = {k: v for k, v in layout_config.items() if k != 'device'}
                if layout_config_filtered_base:
                    css_parts.append(".layout {")
                    css_parts.append(self._process_dict_properties_with_important(layout_config_filtered_base, current_section='layout', config_for_refs=merged_config))
                    css_parts.append("}\n\n")
                
                # ВОЗВРАЩАЕМ СТАРУЮ ЛОГИКУ:
                # Для секций с колонками - стили layout к .column
                # Для секций со строками - стили layout к .layout (без margin для центрирования)
                
                for section_name, section_data in self.css_config.items():
                    if not isinstance(section_data, dict) or section_name in ['column', 'row']:
                        continue
                    
                    # Определяем тип секции
                    if self.structure_analyzer:
                        starts_with_rows = self.structure_analyzer.is_section_starts_with_rows(section_name)
                    else:
                        has_desktop_top = 'desktop' in section_data
                        has_row_1_desktop = isinstance(section_data.get('row_1'), dict) and 'desktop' in section_data.get('row_1', {})
                        starts_with_rows = has_row_1_desktop and not has_desktop_top
                    
                    if starts_with_rows:
                        # Для секций со строками (body): стили layout к .layout, исключаем margin и device
                        layout_config_filtered = {k: v for k, v in layout_config.items() if k != 'margin' and k != 'device'}
                        css_parts.append(f".layout.section-{section_name} {{")
                        css_parts.append(self._process_dict_properties_with_important(layout_config_filtered, current_section='layout', config_for_refs=merged_config))
                        css_parts.append("}\n\n")
                    else:
                        # Для секций с колонками (header, turn, footer): стили layout к .layout (как для body), исключаем device
                        layout_config_filtered = {k: v for k, v in layout_config.items() if k != 'device'}
                        css_parts.append(f".layout.section-{section_name} {{")
                        css_parts.append(self._process_dict_properties_with_important(layout_config_filtered, current_section='layout', config_for_refs=merged_config))
                        css_parts.append("}\n\n")
            elif isinstance(layout_config, list):
                # Старый формат массива (для обратной совместимости)
                if layout_config:
                    # ВОЗВРАЩАЕМ СТАРУЮ ЛОГИКУ
                    for section_name, section_data in self.css_config.items():
                        if not isinstance(section_data, dict) or section_name in ['column', 'row']:
                            continue
                        
                        if self.structure_analyzer:
                            starts_with_rows = self.structure_analyzer.is_section_starts_with_rows(section_name)
                        else:
                            has_desktop_top = 'desktop' in section_data
                            has_row_1_desktop = isinstance(section_data.get('row_1'), dict) and 'desktop' in section_data.get('row_1', {})
                            starts_with_rows = has_row_1_desktop and not has_desktop_top
                        
                        if starts_with_rows:
                            # Для секций со строками: стили layout к .layout, исключаем margin
                            layout_config_filtered = [p for p in layout_config if not p.startswith('margin:')]
                            css_parts.append(f".layout.section-{section_name} {{")
                            css_parts.append(self._process_properties_with_important(layout_config_filtered))
                            css_parts.append("}\n\n")
                        else:
                            # Для секций с колонками: стили layout к .layout (как для body)
                            css_parts.append(f".layout.section-{section_name} {{")
                            css_parts.append(self._process_properties_with_important(layout_config))
                            css_parts.append("}\n\n")
        
        # column -> стили для .column
        # ЕДИНООБРАЗНО для всех секций: применяем ко ВСЕМ .column независимо от вложенности
        # CSS автоматически найдет все вложенные .column элементы
        if 'column' in self.report_config:
            column_config = self.report_config['column']
            if isinstance(column_config, dict):
                # Применяем ЕДИНООБРАЗНО для всех секций: .layout.section-{name} .column (любой уровень вложенности)
                for section_name, section_data in self.css_config.items():
                    if not isinstance(section_data, dict) or section_name in ['column', 'row']:
                        continue
                    
                    # Для секций с колонками (header, turn, footer) исключаем padding/margin из column стилей,
                    # так как они уже применены в layout стилях
                    column_config_filtered = column_config.copy()
                    if self.structure_analyzer:
                        starts_with_rows = self.structure_analyzer.is_section_starts_with_rows(section_name)
                    else:
                        has_desktop_top = 'desktop' in section_data
                        has_row_1_desktop = isinstance(section_data.get('row_1'), dict) and 'desktop' in section_data.get('row_1', {})
                        starts_with_rows = has_row_1_desktop and not has_desktop_top
                    
                    # НЕ исключаем padding/margin из column, так как они нужны для корректного отображения border
                    # Если у column есть border, то padding предотвращает выход границ за пределы родителя
                    # ИСКЛЮЧАЕМ flex-wrap и gap из базовых стилей, так как они должны определяться динамически
                    # flex-wrap - на основе конфигурации колонок, gap - из device_settings
                    column_config_filtered_no_flex = {k: v for k, v in column_config_filtered.items() if k not in ['flex-wrap', 'gap']}
                    
                    css_parts.append(f".layout.section-{section_name} .column {{")
                    css_parts.append(self._process_dict_properties_with_important(column_config_filtered_no_flex, config_for_refs=merged_config))
                    # Добавляем gap и flex-wrap из desktop device_settings (если есть)
                    desktop_column_config = device_settings.get('desktop', {})
                    if desktop_column_config.get('gap'):
                        gap_value = desktop_column_config['gap']
                        css_parts.append(f"    gap: {gap_value} !important;\n")
                    if desktop_column_config.get('flex-wrap'):
                        flex_wrap_value = desktop_column_config['flex-wrap']
                        css_parts.append(f"    flex-wrap: {flex_wrap_value} !important;\n")
                    css_parts.append("}\n\n")
            elif isinstance(column_config, list):
                # Старый формат массива (для обратной совместимости)
                if column_config:
                    for section_name, section_data in self.css_config.items():
                        if not isinstance(section_data, dict) or section_name in ['column', 'row']:
                            continue
                        # ИСКЛЮЧАЕМ flex-wrap и gap из базовых стилей, так как они должны определяться динамически
                        column_config_no_flex = [prop for prop in column_config if not prop.startswith('flex-wrap:') and not prop.startswith('gap:')]
                        css_parts.append(f".layout.section-{section_name} .column {{")
                        css_parts.append("box-sizing: border-box !important;")
                        css_parts.append(self._process_properties_with_important(column_config_no_flex))
                        # Добавляем gap и flex-wrap из desktop device_settings (если есть)
                        desktop_column_config = device_settings.get('desktop', {})
                        if desktop_column_config.get('gap'):
                            gap_value = desktop_column_config['gap']
                            css_parts.append(f"    gap: {gap_value} !important;\n")
                        if desktop_column_config.get('flex-wrap'):
                            flex_wrap_value = desktop_column_config['flex-wrap']
                            css_parts.append(f"    flex-wrap: {flex_wrap_value} !important;\n")
                        css_parts.append("}\n\n")
        
        # row -> стили для .row
        # ЕДИНООБРАЗНО для всех секций: применяем ко ВСЕМ .row независимо от вложенности
        # CSS автоматически найдет все вложенные .row элементы
        if 'row' in self.report_config:
            row_config = self.report_config['row']
            if isinstance(row_config, dict):
                # Сначала применяем базовые стили к .row
                css_parts.append(".row {")
                css_parts.append(self._process_dict_properties_with_important(row_config, config_for_refs=merged_config))
                css_parts.append("}\n\n")
                
                # Собираем все селекторы для объединения в один CSS блок
                selectors = []
                for section_name, section_data in self.css_config.items():
                    if not isinstance(section_data, dict) or section_name in ['column', 'row']:
                        continue
                    selectors.append(f".layout.section-{section_name} .row")
                
                # Объединяем все селекторы в один блок
                if selectors:
                    css_parts.append(",\n".join(selectors) + " {")
                    css_parts.append(self._process_dict_properties_with_important(row_config, config_for_refs=merged_config))
                    css_parts.append("}\n\n")
            elif isinstance(row_config, list):
                # Старый формат массива (для обратной совместимости)
                if row_config:
                    # Собираем все селекторы для объединения в один CSS блок
                    selectors = []
                    for section_name, section_data in self.css_config.items():
                        if not isinstance(section_data, dict) or section_name in ['column', 'row']:
                            continue
                        selectors.append(f".layout.section-{section_name} .row")
                    
                    # Объединяем все селекторы в один блок
                    if selectors:
                        css_parts.append(",\n".join(selectors) + " {")
                        css_parts.append(self._process_properties_with_important(row_config))
                        css_parts.append("}\n\n")
        
        # a -> стили для тега a (ссылки) из css_report/tag.json
        if 'a' in self.report_config:
            a_config = self.report_config['a']
            if isinstance(a_config, dict):
                css_parts.append("a {")
                css_parts.append(self._process_dict_properties_with_important(a_config, config_for_refs=merged_config))
                css_parts.append("}\n\n")
            elif isinstance(a_config, list):
                if a_config:
                    css_parts.append("a {")
                    css_parts.append(self._process_properties_with_important(a_config))
                    css_parts.append("}\n\n")
        
        # text -> стили для текстовых элементов [class^="content-"] из css_report/tag.json
        if 'text' in self.report_config:
            text_config = self.report_config['text']
            if isinstance(text_config, dict):
                css_parts.append("[class^=\"content-\"] {")
                css_parts.append(self._process_dict_properties_with_important(text_config, config_for_refs=merged_config))
                css_parts.append("}\n\n")
            elif isinstance(text_config, list):
                if text_config:
                    css_parts.append("[class^=\"content-\"] {")
                    css_parts.append(self._process_properties_with_important(text_config))
                    css_parts.append("}\n\n")
        
        # img -> стили для тега img из css_report/tag.json
        if 'img' in self.report_config:
            img_config = self.report_config['img']
            if isinstance(img_config, dict):
                if img_config:  # Проверяем, что не пустой словарь
                    css_parts.append("img {")
                    css_parts.append(self._process_dict_properties_with_important(img_config, config_for_refs=merged_config))
                    css_parts.append("}\n\n")
            elif isinstance(img_config, list):
                if img_config:
                    css_parts.append("img {")
                    css_parts.append(self._process_properties_with_important(img_config))
                    css_parts.append("}\n\n")
        
        # nav -> стили для тега nav из css_report/tag.json
        if 'nav' in self.report_config:
            nav_config = self.report_config['nav']
            if isinstance(nav_config, dict):
                if nav_config:  # Проверяем, что не пустой словарь
                    css_parts.append("nav {")
                    css_parts.append(self._process_dict_properties_with_important(nav_config, config_for_refs=merged_config))
                    css_parts.append("}\n\n")
            elif isinstance(nav_config, list):
                if nav_config:
                    css_parts.append("nav {")
                    css_parts.append(self._process_properties_with_important(nav_config))
                    css_parts.append("}\n\n")
        
        # icon -> стили для тега icon из css_report/tag.json
        if 'icon' in self.report_config:
            icon_config = self.report_config['icon']
            if isinstance(icon_config, dict):
                if icon_config:  # Проверяем, что не пустой словарь
                    css_parts.append("icon[class^=\"content-\"] {")
                    css_parts.append(self._process_dict_properties_with_important(icon_config, config_for_refs=merged_config))
                    css_parts.append("}\n\n")
            elif isinstance(icon_config, list):
                if icon_config:
                    css_parts.append("icon[class^=\"content-\"] {")
                    css_parts.append(self._process_properties_with_important(icon_config))
                    css_parts.append("}\n\n")
        
        # icon svg -> стили для svg внутри icon из css_report/tag.json
        if 'icon svg' in self.report_config:
            icon_svg_config = self.report_config['icon svg']
            if isinstance(icon_svg_config, dict):
                if icon_svg_config:
                    css_parts.append("icon[class^=\"content-\"] svg {")
                    css_parts.append(self._process_dict_properties_with_important(icon_svg_config, config_for_refs=merged_config))
                    css_parts.append("}\n\n")
            elif isinstance(icon_svg_config, list):
                if icon_svg_config:
                    css_parts.append("icon[class^=\"content-\"] svg {")
                    css_parts.append(self._process_properties_with_important(icon_svg_config))
                    css_parts.append("}\n\n")
        
        # Обработка всех остальных ключей из report_config как селекторов (например, "a > img", "a:has(img)")
        special_keys = {'html', 'page', 'section', 'layout', 'column', 'row', 'group', 'col_in_row', 'a', 'text', 'img', 'nav', 'icon', 'icon svg', 'wrapper_content', 'menu'}
        for key, value in self.report_config.items():
            if key not in special_keys:
                # Это составной селектор или другой селектор
                if isinstance(value, dict):
                    if value:  # Проверяем, что не пустой словарь
                        css_parts.append(f"{key} {{")
                        css_parts.append(self._process_dict_properties_with_important(value, config_for_refs=merged_config))
                        css_parts.append("}\n\n")
                elif isinstance(value, list):
                    if value:
                        css_parts.append(f"{key} {{")
                        css_parts.append(self._process_properties_with_important(value))
                        css_parts.append("}\n\n")
        
        # col_in_row -> стили для .col_* (внутренние колонки) - отладочные стили
        if 'col_in_row' in self.report_config:
            col_in_row_config = self.report_config['col_in_row']
            if isinstance(col_in_row_config, dict):
                css_parts.append("[class^='col_'] {")
                css_parts.append(self._process_dict_properties_with_important(col_in_row_config, config_for_refs=merged_config))
                css_parts.append("}\n\n")
            elif isinstance(col_in_row_config, list):
                if col_in_row_config:
                    css_parts.append("[class^='col_'] {")
                    css_parts.append(self._process_properties_with_important(col_in_row_config))
                    css_parts.append("}\n\n")
        
        # group -> стили для .group (группы элементов) - отладочные стили
        if 'group' in self.report_config:
            group_config = self.report_config['group']
            if isinstance(group_config, dict):
                css_parts.append(".group {")
                css_parts.append(self._process_dict_properties_with_important(group_config, config_for_refs=merged_config))
                css_parts.append("}\n\n")
            elif isinstance(group_config, list):
                # Старый формат массива (для обратной совместимости)
                if group_config:
                    css_parts.append(".group {")
                    css_parts.append(self._process_properties_with_important(group_config))
                    css_parts.append("}\n\n")
        
        return '\n'.join(css_parts)
    
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

