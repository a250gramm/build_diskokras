#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
value_processor.py - Обработка значений CSS с поддержкой ссылок и модификаторов
"""

import re
from typing import Any, Dict, Optional
from colorsys import rgb_to_hls, hls_to_rgb

# Глобальная переменная для библиотеки цветов
_colors_config: Dict[str, str] = {}


def init_colors(colors_config: Dict[str, str]):
    """
    Инициализирует библиотеку цветов из color.json
    
    Args:
        colors_config: Словарь с цветами из library/color.json
    """
    global _colors_config
    _colors_config = colors_config or {}


def process_css_value(value: Any, general_config: Dict, current_section: str = None) -> str:
    """
    Обрабатывает CSS значение, поддерживая:
    - Строки: "magenta"
    - Массивы: ["100", "vh"] -> "100vh"
    - Ссылки: "page.bg-color.darker-0.8" или "page.bg-color.darker-80" -> вычисленное значение
    
    Args:
        value: Значение для обработки (строка, массив, или ссылка)
        general_config: Конфигурация из general.json
        current_section: Текущая секция (page, section, layout) для разрешения относительных ссылок
        
    Returns:
        Обработанное CSS значение
    """
    # Если это массив
    if isinstance(value, list):
        if len(value) == 4:
            # Формат: [10, 10, 5, "px"] -> "10px" (берем первое значение + единицу)
            # Или [10, 10, 5, "px"] для gap/margin/padding с одним значением
            val = str(value[0])
            unit = str(value[3]).strip("'\"")
            return f"{val}{unit}"
        elif len(value) == 3:
            # Формат для border: ["2px solid", "1 1 0 1", "section.bg-color.100"]
            # где "1 1 0 1" - флаги для сторон (top right bottom left): 1=включить, 0=выключить
            val_str = str(value[0])  # "2px solid"
            sides_flags = str(value[1])  # "1 1 0 1"
            color_ref = str(value[2])  # "section.bg-color.100"
            
            # Разрешаем ссылку на цвет
            resolved_color = resolve_reference(color_ref, general_config, current_section)
            
            # Парсим флаги сторон
            flags = sides_flags.split()
            if len(flags) == 4:
                top, right, bottom, left = flags
                # Генерируем border для каждой стороны
                borders = []
                if top == '1':
                    borders.append(f"border-top: {val_str} {resolved_color}")
                if right == '1':
                    borders.append(f"border-right: {val_str} {resolved_color}")
                if bottom == '1':
                    borders.append(f"border-bottom: {val_str} {resolved_color}")
                if left == '1':
                    borders.append(f"border-left: {val_str} {resolved_color}")
                
                # Возвращаем как строку с разделителями (будет обработано в css_generator)
                return " | ".join(borders) if borders else f"border: {val_str} {resolved_color}"
            else:
                # Если формат флагов неправильный, используем как обычный border
                return f"{val_str} {resolved_color}"
        elif len(value) == 2:
            # Формат: ["1px solid", "page.bg-color.darker-80"] или ["100", "vh"] или ["1px solid", "black"]
            # Или ["yellow", "50"] или ["yellow", 50] - цвет с прозрачностью (50 = 50% непрозрачности)
            # Или ["transparent", 100] или ["transparent", "100"] - прозрачный фон
            val_str = str(value[0])
            second_raw = value[1]
            
            # Если первый элемент - transparent, возвращаем transparent независимо от второго
            if val_str.lower() == 'transparent':
                return 'transparent'
            
            # Проверяем, является ли второй элемент числом (int или float)
            is_number = isinstance(second_raw, (int, float))
            second = str(second_raw)
            
            # Проверяем, является ли второй элемент ссылкой
            if not is_number and ('.' in second or second.startswith('#')):
                # Это ссылка или hex-цвет
                resolved_value = resolve_reference(second, general_config, current_section)
                # Объединяем: "1px solid" + resolved_value
                return f"{val_str} {resolved_value}"
            elif not is_number and second in ['px', 'vh', 'vw', '%', 'em', 'rem', 'pt', 'pc', 'in', 'cm', 'mm', 'ex', 'ch']:
                # Это единица измерения
                unit = second
                if ' ' in val_str:
                    # "10 0" + "px" -> "10px 0px"
                    # "0 auto" + "px" -> "0px auto" (auto без единицы)
                    parts = val_str.split()
                    result_parts = []
                    for part in parts:
                        if part.lower() == 'auto':
                            result_parts.append('auto')
                        else:
                            result_parts.append(f"{part}{unit}")
                    return ' '.join(result_parts)
                else:
                    # "100" + "vh" -> "100vh"
                    return f"{val_str}{unit}"
            elif is_number or re.match(r'^\d+$', second):
                # Это число (int/float) или строка с числом - проверяем, может быть это прозрачность для цвета
                opacity_value = int(float(second_raw)) if is_number else int(second)
                if 0 <= opacity_value <= 100:
                    # Проверяем, является ли первый элемент цветом (без единиц измерения и не содержит пробелов)
                    if ' ' not in val_str and val_str not in ['px', 'vh', 'vw', '%', 'em', 'rem', 'pt', 'pc', 'in', 'cm', 'mm', 'ex', 'ch']:
                        # Проверяем, является ли это цветом
                        rgb = color_to_rgb(val_str)
                        if rgb is not None:
                            # Это цвет с прозрачностью
                            # Преобразуем процент в alpha: 100 -> 1.0, 50 -> 0.5, 0 -> 0.0
                            alpha = opacity_value / 100.0
                            r, g, b = rgb
                            return f"rgba({r}, {g}, {b}, {alpha})"
                
                # Если не цвет, то это просто значение
                return f"{val_str} {second}"
            else:
                # Это просто значение (например, "black", "solid", "dotted")
                # Объединяем: "1px solid" + " " + "black" = "1px solid black"
                return f"{val_str} {second}"
        else:
            # Неизвестный формат массива
            return str(value)
    
    # Если это строка
    if isinstance(value, str):
        # Проверяем, является ли это ссылкой
        if '.' in value or value.startswith('#'):
            return resolve_reference(value, general_config, current_section)
        else:
            return value
    
    # Остальные типы
    return str(value)


def resolve_reference(ref: str, general_config: Dict, current_section: str = None) -> str:
    """
    Разрешает ссылку вида "page.bg-color.darker-0.8" или "page.bg-color.darker-80"
    
    Args:
        ref: Ссылка (например, "page.bg-color.darker-0.8", "page.bg-color.darker-80" или "#ff00ff")
        general_config: Конфигурация из general.json
        current_section: Текущая секция для относительных ссылок
        
    Returns:
        Вычисленное значение
    """
    # Если это hex-цвет, возвращаем как есть
    if ref.startswith('#'):
        return ref
    
    # Парсим ссылку: "page.bg-color.darker-0.8"
    parts = ref.split('.')
    
    if len(parts) < 2:
        # Не ссылка, возвращаем как есть
        return ref
    
    # Первая часть - секция (page, section, layout) или цвет (yellow, red и т.д.)
    section_name = parts[0]
    
    # Вторая часть - свойство (bg-color, border и т.д.) или модификатор (150, darker-80 и т.д.)
    property_name = parts[1]
    
    # Остальные части - модификаторы (darker-0.8, darker-80, lighter-0.2, lighter-20 и т.д.)
    modifiers = parts[2:] if len(parts) > 2 else []
    
    # Получаем значение из конфига
    if section_name not in general_config:
        # Если секция не найдена, возможно это прямой цвет с модификатором (например, "yellow.150")
        # Проверяем, является ли первая часть названием цвета
        if color_to_rgb(section_name) is not None:
            # Это цвет с модификатором
            # Если только 2 части (yellow.150), то property_name - это модификатор
            if len(parts) == 2:
                modifiers = [property_name]
            else:
                # Если больше частей, то property_name - это свойство, а модификаторы уже в modifiers
                modifiers = [property_name] + modifiers
            
            # Применяем модификаторы к цвету
            result = section_name
            for modifier in modifiers:
                result = apply_modifier(result, modifier)
            return result
        return ref  # Секция не найдена
    
    section_config = general_config[section_name]
    if not isinstance(section_config, dict):
        return ref  # Неправильный формат
    
    # Получаем значение свойства
    if property_name not in section_config:
        return ref  # Свойство не найдено
    
    base_value = section_config[property_name]
    
    # Если это массив, берем первое значение
    if isinstance(base_value, list):
        base_value = base_value[0] if base_value else ""
    
    base_value = str(base_value)
    
    # Применяем модификаторы
    result = base_value
    for modifier in modifiers:
        result = apply_modifier(result, modifier)
    
    return result


def apply_modifier(value: str, modifier: str) -> str:
    """
    Применяет модификатор к значению
    
    Args:
        value: Исходное значение (например, "magenta" или "#ff00ff")
        modifier: Модификатор в новом формате:
                  - "100" = исходный цвет (без изменений)
                  - "90" = осветлить на 10% (100 - 90 = 10%)
                  - "110" = затемнить на 10% (110 - 100 = 10%)
                  Или в старом формате (для обратной совместимости):
                  - "darker-0.8", "darker-80", "lighter-0.2", "lighter-20"
        
    Returns:
        Модифицированное значение
    """
    # Проверяем, является ли модификатор просто числом (новый формат)
    if re.match(r'^\d+$', modifier):
        # Новый формат: просто число
        brightness = int(modifier)
        
        # 100 = исходный цвет
        if brightness == 100:
            rgb = color_to_rgb(value)
            if rgb is None:
                return value
            return rgb_to_hex(rgb)
        
        # Конвертируем значение в RGB
        rgb = color_to_rgb(value)
        if rgb is None:
            return value  # Не удалось распознать цвет
        
        # Вычисляем процент изменения
        if brightness < 100:
            # Осветление: 90 -> осветлить на 10%
            lighten_percent = (100 - brightness) / 100.0
            rgb = lighten_color(rgb, lighten_percent)
        else:
            # Затемнение: 110 -> затемнить на 10%
            darken_percent = (brightness - 100) / 100.0
            rgb = darken_color(rgb, darken_percent)
        
        # Конвертируем обратно в hex
        return rgb_to_hex(rgb)
    
    # Старый формат: "darker-0.8" или "darker-80" (для обратной совместимости)
    match = re.match(r'^(\w+)-([\d.]+)$', modifier)
    if not match:
        return value  # Неизвестный формат модификатора
    
    mod_type = match.group(1)
    mod_value_raw = float(match.group(2))
    
    # Нормализуем значение: если >= 1, то это проценты (80 -> 0.8), иначе коэффициент (0.8 -> 0.8)
    if mod_value_raw >= 1.0:
        mod_value = mod_value_raw / 100.0  # Проценты в коэффициент
    else:
        mod_value = mod_value_raw  # Уже коэффициент
    
    # Ограничиваем диапазон 0.0-1.0
    mod_value = max(0.0, min(1.0, mod_value))
    
    # Конвертируем значение в RGB
    rgb = color_to_rgb(value)
    if rgb is None:
        return value  # Не удалось распознать цвет
    
    # Применяем модификатор
    if mod_type == 'darker':
        rgb = darken_color(rgb, mod_value)
    elif mod_type == 'lighter':
        rgb = lighten_color(rgb, mod_value)
    else:
        return value  # Неизвестный тип модификатора
    
    # Конвертируем обратно в hex
    return rgb_to_hex(rgb)


def color_to_rgb(color_str: str) -> Optional[tuple]:
    """
    Конвертирует строку цвета в RGB кортеж (0-255)
    
    Args:
        color_str: Цвет в виде строки ("magenta", "#ff00ff", "rgb(255,0,255)" и т.д.)
        
    Returns:
        Кортеж (r, g, b) или None если не удалось распознать
    """
    color_str = color_str.strip().lower()
    
    # Hex формат: #ff00ff или ff00ff
    if color_str.startswith('#'):
        color_str = color_str[1:]
    
    if len(color_str) == 6 and all(c in '0123456789abcdef' for c in color_str):
        r = int(color_str[0:2], 16)
        g = int(color_str[2:4], 16)
        b = int(color_str[4:6], 16)
        return (r, g, b)
    
    # Короткий формат hex: #fff -> #ffffff
    if len(color_str) == 3 and all(c in '0123456789abcdef' for c in color_str):
        r = int(color_str[0] + color_str[0], 16)
        g = int(color_str[1] + color_str[1], 16)
        b = int(color_str[2] + color_str[2], 16)
        return (r, g, b)
    
    # Сначала проверяем библиотеку цветов из color.json
    # Поддерживаем формат gray_1, gray_2 и т.д. для доступа к элементам массива
    if _colors_config:
        # Проверяем формат color_name_index (например, gray_1, gray_2)
        if '_' in color_str:
            parts = color_str.rsplit('_', 1)  # Разделяем по последнему подчеркиванию
            if len(parts) == 2 and parts[1].isdigit():
                base_color = parts[0]  # "gray"
                index = int(parts[1]) - 1  # "1" -> индекс 0, "2" -> индекс 1
                
                # Проверяем, есть ли массив с таким именем
                if base_color in _colors_config:
                    color_value = _colors_config[base_color]
                    if isinstance(color_value, list) and 0 <= index < len(color_value):
                        hex_color = color_value[index]
                        # Конвертируем hex в RGB
                        if isinstance(hex_color, str) and hex_color.startswith('#'):
                            hex_color = hex_color[1:]
                        if len(hex_color) == 6 and all(c in '0123456789abcdef' for c in hex_color.lower()):
                            r = int(hex_color[0:2], 16)
                            g = int(hex_color[2:4], 16)
                            b = int(hex_color[4:6], 16)
                            return (r, g, b)
                        elif len(hex_color) == 3 and all(c in '0123456789abcdef' for c in hex_color.lower()):
                            # Короткий формат #fff -> #ffffff
                            r = int(hex_color[0] + hex_color[0], 16)
                            g = int(hex_color[1] + hex_color[1], 16)
                            b = int(hex_color[2] + hex_color[2], 16)
                            return (r, g, b)
        
        # Обычная проверка цвета (не массив)
        if color_str in _colors_config:
            hex_color = _colors_config[color_str]
            # Если это массив, берем первый элемент
            if isinstance(hex_color, list) and len(hex_color) > 0:
                hex_color = hex_color[0]
            # Конвертируем hex в RGB
            if isinstance(hex_color, str) and hex_color.startswith('#'):
                hex_color = hex_color[1:]
            if len(hex_color) == 6 and all(c in '0123456789abcdef' for c in hex_color.lower()):
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b)
            elif len(hex_color) == 3 and all(c in '0123456789abcdef' for c in hex_color.lower()):
                # Короткий формат #fff -> #ffffff
                r = int(hex_color[0] + hex_color[0], 16)
                g = int(hex_color[1] + hex_color[1], 16)
                b = int(hex_color[2] + hex_color[2], 16)
                return (r, g, b)
    
    # Fallback: старые именованные цвета (для обратной совместимости)
    named_colors = {
        'magenta': (255, 0, 255),
        'cyan': (0, 255, 255),
        'yellow': (255, 255, 0),
        'red': (255, 0, 0),
        'green': (0, 128, 0),
        'lime': (0, 255, 0),  # Ярко-зеленый (lime)
        'blue': (0, 0, 255),
        'black': (0, 0, 0),
        'white': (255, 255, 255),
    }
    
    if color_str in named_colors:
        return named_colors[color_str]
    
    return None


def darken_color(rgb: tuple, factor: float) -> tuple:
    """
    Затемняет цвет
    
    Args:
        rgb: RGB кортеж (0-255)
        factor: Коэффициент затемнения (0.0 - 1.0)
        
    Returns:
        Новый RGB кортеж
    """
    r, g, b = rgb
    # Конвертируем в 0-1 диапазон
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    
    # Конвертируем в HLS
    h, l, s = rgb_to_hls(r_norm, g_norm, b_norm)
    
    # Уменьшаем яркость
    l = max(0.0, l * (1.0 - factor))
    
    # Конвертируем обратно в RGB
    r_new, g_new, b_new = hls_to_rgb(h, l, s)
    
    # Конвертируем в 0-255 диапазон
    return (int(r_new * 255), int(g_new * 255), int(b_new * 255))


def lighten_color(rgb: tuple, factor: float) -> tuple:
    """
    Осветляет цвет
    
    Args:
        rgb: RGB кортеж (0-255)
        factor: Коэффициент осветления (0.0 - 1.0)
        
    Returns:
        Новый RGB кортеж
    """
    r, g, b = rgb
    # Конвертируем в 0-1 диапазон
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    
    # Конвертируем в HLS
    h, l, s = rgb_to_hls(r_norm, g_norm, b_norm)
    
    # Увеличиваем яркость
    l = min(1.0, l + (1.0 - l) * factor)
    
    # Конвертируем обратно в RGB
    r_new, g_new, b_new = hls_to_rgb(h, l, s)
    
    # Конвертируем в 0-255 диапазон
    return (int(r_new * 255), int(g_new * 255), int(b_new * 255))


def rgb_to_hex(rgb: tuple) -> str:
    """
    Конвертирует RGB кортеж в hex строку
    
    Args:
        rgb: RGB кортеж (0-255)
        
    Returns:
        Hex строка вида "#ff00ff"
    """
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"

