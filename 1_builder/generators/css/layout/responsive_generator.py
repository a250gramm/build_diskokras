#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор адаптивных стилей - генерирует медиа-запросы для desktop/tablet/mobile
"""

from typing import Dict, Any, List, Callable, Tuple


class ResponsiveGenerator:
    """Генерирует адаптивные CSS стили с медиа-запросами"""
    
    def __init__(self, general_config: Dict, process_property_fn: Callable, 
                 add_css_property_fn: Callable, normalize_array_fn: Callable):
        """
        Args:
            general_config: Общая конфигурация
            process_property_fn: Функция обработки свойств
            add_css_property_fn: Функция добавления CSS свойств
            normalize_array_fn: Функция нормализации массивов
        """
        self.general_config = general_config
        self._process_property = process_property_fn
        self._add_css_property = add_css_property_fn
        self._normalize_array_value = normalize_array_fn
    
    def normalize_array_value(self, value: Any) -> Any:
        """Нормализует массив значений: [10, 10, 10, "px"] -> ["10px", "10px", "10px"]"""
        return self._normalize_array_value(value)
    
    def split_properties_by_arrays(self, value_props: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, List]]:
        """
        Разделяет свойства на обычные и с массивами для адаптивности
        
        Args:
            value_props: Словарь свойств
            
        Returns:
            Кортеж (normal_props, array_props)
        """
        array_props = {}
        normal_props = {}
        
        for prop_name, prop_value in value_props.items():
            # border обрабатывается отдельно
            if prop_name == 'border' and isinstance(prop_value, list) and len(prop_value) == 3:
                normal_props[prop_name] = prop_value
                continue
            
            normalized = self._normalize_array_value(prop_value)
            if isinstance(normalized, list) and len(normalized) == 3:
                array_props[prop_name] = normalized
            else:
                normal_props[prop_name] = prop_value
        
        return normal_props, array_props
    
    def has_arrays(self, value_props: Dict[str, Any]) -> bool:
        """
        Проверяет, содержит ли словарь массивы для разных устройств
        
        Args:
            value_props: Словарь свойств
            
        Returns:
            True если есть массивы
        """
        return any(
            isinstance(v, list) and (len(v) == 3 or (len(v) == 4 and isinstance(v[3], str)))
            and k != 'border'  # border обрабатывается отдельно
            for k, v in value_props.items()
        )
    
    def generate_responsive_css(self, selector: str, value_props: Dict[str, Any],
                               tablet_breakpoint: str, mobile_breakpoint: str,
                               css_parts: List[str]) -> None:
        """
        Генерирует адаптивные CSS стили с медиа-запросами
        
        Args:
            selector: CSS селектор
            value_props: Словарь свойств
            tablet_breakpoint: Брейкпоинт для планшета
            mobile_breakpoint: Брейкпоинт для мобильного
            css_parts: Список для добавления CSS
        """
        if not self.has_arrays(value_props):
            # Обычные стили без массивов
            return
        
        normal_props, array_props = self.split_properties_by_arrays(value_props)
        
        # Desktop стили
        desktop_props = {k: v[0] for k, v in array_props.items()}
        all_desktop_props = {**normal_props, **desktop_props}
        
        if all_desktop_props:
            css_parts.append(f"{selector} {{")
            for prop_name, prop_value in all_desktop_props.items():
                css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                self._add_css_property(css_parts, "    ", css_prop_name, processed_value)
            css_parts.append("}\n\n")
        
        # Tablet стили
        tablet_props = {k: v[1] for k, v in array_props.items()}
        if tablet_props:
            css_parts.append(f"@media (max-width: {tablet_breakpoint}) {{")
            css_parts.append(f"    {selector} {{")
            for prop_name, prop_value in tablet_props.items():
                css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                css_parts.append(f"        {css_prop_name}: {processed_value} !important;")
            css_parts.append("    }")
            css_parts.append("}\n\n")
        
        # Mobile стили
        mobile_props = {k: v[2] for k, v in array_props.items()}
        if mobile_props:
            css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{")
            css_parts.append(f"    {selector} {{")
            for prop_name, prop_value in mobile_props.items():
                css_prop_name, processed_value = self._process_property(prop_name, prop_value)
                css_parts.append(f"        {css_prop_name}: {processed_value} !important;")
            css_parts.append("    }")
            css_parts.append("}\n\n")
    
    def generate_column_responsive_css(self, section_name: str, section_config: Dict[str, Any],
                                      devices: Dict[str, str], device_settings: Dict[str, Dict],
                                      css_parts: List[str]) -> None:
        """
        Генерирует адаптивные стили для колонок
        
        Args:
            section_name: Имя секции
            section_config: Конфигурация секции
            devices: Словарь устройств
            device_settings: Настройки устройств
            css_parts: Список для добавления CSS
        """
        tablet_breakpoint = devices.get('tablet', '768px')
        mobile_breakpoint = devices.get('mobile', '320px')
        
        desktop_columns = section_config.get('desktop', [])
        tablet_columns = section_config.get('tablet', [])
        mobile_columns = section_config.get('mobile', [])
        
        # Применяем desktop ширины колонок
        if desktop_columns:
            for idx, width in enumerate(desktop_columns):
                col_class = f"col_{idx + 1}"
                css_parts.append(f".layout.section-{section_name} .{col_class} {{")
                css_parts.append(f"    flex-basis: {width}%;")
                css_parts.append("}\n")
        
        # Генерируем медиа-запрос для tablet
        if tablet_columns and tablet_breakpoint:
            try:
                tablet_value = int(tablet_breakpoint.replace('px', ''))
                tablet_max = f"{tablet_value}px"
            except:
                tablet_max = tablet_breakpoint
            
            tablet_column_config = device_settings.get('tablet', {})
            
            # Проверяем, есть ли gap в layout_css.json для этой секции (-S-L-C)
            has_custom_gap = False
            column_config_key = f"{section_name}-S-L-C"
            # Это будет проверено в основном генераторе
            
            css_parts.append(f"@media (max-width: {tablet_max}) {{")
            column_styles = []
            
            sum_tablet_widths = sum(tablet_columns) if tablet_columns else 0
            if len(tablet_columns) == 1 and tablet_columns[0] == 100:
                column_styles.append("flex-wrap: wrap !important;")
            elif len(tablet_columns) > 1 and sum_tablet_widths == 100:
                column_styles.append("flex-wrap: nowrap !important;")
            elif tablet_column_config.get('flex-wrap'):
                column_styles.append(f"flex-wrap: {tablet_column_config['flex-wrap']} !important;")
            
            if tablet_column_config.get('gap') and not has_custom_gap:
                gap_value = tablet_column_config['gap']
                column_styles.append(f"gap: {gap_value} !important;")
            
            column_styles.append("padding: 0px !important;")
            
            if column_styles:
                css_parts.append(f"    .layout.section-{section_name} .column {{")
                for style in column_styles:
                    css_parts.append(f"        {style}")
                css_parts.append(f"    }}")
            
            # Применяем стили для всех колонок
            num_desktop_cols = len(desktop_columns) if desktop_columns else 0
            for idx in range(num_desktop_cols):
                col_class = f"col_{idx + 1}"
                if idx < len(tablet_columns):
                    width = tablet_columns[idx]
                elif len(tablet_columns) > 0:
                    width = tablet_columns[-1]
                else:
                    width = None
                
                if width is not None:
                    css_parts.append(f"    .layout.section-{section_name} .{col_class} {{")
                    css_parts.append(f"        flex-basis: {width}% !important;")
                    css_parts.append("    }")
                else:
                    css_parts.append(f"    .layout.section-{section_name} .{col_class} {{")
                    css_parts.append(f"        display: none !important;")
                    css_parts.append("    }")
            
            css_parts.append("}\n\n")
        
        # Генерируем медиа-запрос для mobile (аналогично tablet)
        if mobile_columns and mobile_breakpoint:
            mobile_column_config = device_settings.get('mobile', {})
            
            has_custom_gap = False
            column_config_key = f"{section_name}-S-L-C"
            
            css_parts.append(f"@media (max-width: {mobile_breakpoint}) {{")
            column_styles = []
            
            sum_mobile_widths = sum(mobile_columns) if mobile_columns else 0
            if len(mobile_columns) == 1 and mobile_columns[0] == 100:
                column_styles.append("flex-wrap: wrap !important;")
            elif len(mobile_columns) > 1 and sum_mobile_widths == 100:
                column_styles.append("flex-wrap: nowrap !important;")
            elif mobile_column_config.get('flex-wrap'):
                column_styles.append(f"flex-wrap: {mobile_column_config['flex-wrap']} !important;")
            
            if mobile_column_config.get('gap') and not has_custom_gap:
                gap_value = mobile_column_config['gap']
                column_styles.append(f"gap: {gap_value} !important;")
            
            column_styles.append("padding: 0px !important;")
            
            if column_styles:
                css_parts.append(f"    .layout.section-{section_name} .column {{")
                for style in column_styles:
                    css_parts.append(f"        {style}")
                css_parts.append(f"    }}")
            
            num_desktop_cols = len(desktop_columns) if desktop_columns else 0
            for idx in range(num_desktop_cols):
                col_class = f"col_{idx + 1}"
                if idx < len(mobile_columns):
                    width = mobile_columns[idx]
                elif len(mobile_columns) > 0:
                    width = mobile_columns[-1]
                else:
                    width = None
                
                if width is not None:
                    css_parts.append(f"    .layout.section-{section_name} .{col_class} {{")
                    css_parts.append(f"        flex-basis: {width}% !important;")
                    css_parts.append("    }")
                else:
                    css_parts.append(f"    .layout.section-{section_name} .{col_class} {{")
                    css_parts.append(f"        display: none !important;")
                    css_parts.append("    }")
            
            css_parts.append("}\n\n")

