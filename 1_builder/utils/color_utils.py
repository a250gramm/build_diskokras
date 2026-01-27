#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для работы с цветами
"""

from typing import Tuple, Optional


# Базовая палитра цветов
COLOR_MAP = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'yellow': (255, 255, 0),
    'cyan': (0, 255, 255),
    'magenta': (255, 0, 255),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'gray': (128, 128, 128),
    'orange': (255, 165, 0),
    'purple': (128, 0, 128),
    'pink': (255, 192, 203),
    'brown': (165, 42, 42),
    'transparent': None,
}


def parse_color(color_name: str) -> Optional[Tuple[int, int, int]]:
    """
    Парсит название цвета в RGB
    
    Args:
        color_name: Название цвета (red, yellow, etc) или hex (#ff0000)
        
    Returns:
        Tuple (r, g, b) или None для transparent
    """
    color_name = color_name.lower().strip()
    
    # Проверяем базовую палитру
    if color_name in COLOR_MAP:
        return COLOR_MAP[color_name]
    
    # Проверяем hex формат
    if color_name.startswith('#'):
        hex_color = color_name.lstrip('#')
        if len(hex_color) == 6:
            try:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b)
            except ValueError:
                pass
    
    return None


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Конвертирует RGB в HEX
    
    Args:
        r, g, b: Компоненты цвета (0-255)
        
    Returns:
        HEX строка (#rrggbb)
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_rgba(r: int, g: int, b: int, opacity: float) -> str:
    """
    Конвертирует RGB + opacity в rgba()
    
    Args:
        r, g, b: Компоненты цвета (0-255)
        opacity: Непрозрачность (0-100)
        
    Returns:
        rgba() строка
    """
    alpha = opacity / 100.0
    return f"rgba({r}, {g}, {b}, {alpha})"


def color_to_css(color_name: str, opacity: int = 100) -> str:
    """
    Конвертирует название цвета и непрозрачность в CSS значение
    
    Args:
        color_name: Название цвета или hex
        opacity: Непрозрачность (0-100)
        
    Returns:
        CSS цвет (hex или rgba или transparent)
    """
    # Специальный случай - transparent
    if color_name.lower() == 'transparent':
        return 'transparent'
    
    rgb = parse_color(color_name)
    if rgb is None:
        return color_name  # Возвращаем как есть
    
    r, g, b = rgb
    
    # Если полная непрозрачность - используем hex
    if opacity == 100:
        return rgb_to_hex(r, g, b)
    
    # Иначе rgba
    return rgb_to_rgba(r, g, b, opacity)


def adjust_brightness(r: int, g: int, b: int, factor: float) -> Tuple[int, int, int]:
    """
    Регулирует яркость цвета
    
    Args:
        r, g, b: Компоненты цвета (0-255)
        factor: Множитель (>1 = светлее, <1 = темнее)
        
    Returns:
        Tuple (r, g, b) с измененной яркостью
    """
    r = min(255, max(0, int(r * factor)))
    g = min(255, max(0, int(g * factor)))
    b = min(255, max(0, int(b * factor)))
    return (r, g, b)


def darken_color(color_name: str, amount: int) -> str:
    """
    Затемняет цвет
    
    Args:
        color_name: Название цвета
        amount: Процент затемнения (0-100)
        
    Returns:
        HEX строка затемненного цвета
    """
    rgb = parse_color(color_name)
    if rgb is None:
        return color_name
    
    r, g, b = rgb
    factor = 1.0 - (amount / 100.0)
    r, g, b = adjust_brightness(r, g, b, factor)
    return rgb_to_hex(r, g, b)


def lighten_color(color_name: str, amount: int) -> str:
    """
    Осветляет цвет
    
    Args:
        color_name: Название цвета
        amount: Процент осветления (0-100)
        
    Returns:
        HEX строка осветленного цвета
    """
    rgb = parse_color(color_name)
    if rgb is None:
        return color_name
    
    r, g, b = rgb
    # Осветление = движение к белому (255, 255, 255)
    factor = 1.0 + (amount / 100.0)
    r = min(255, r + int((255 - r) * (amount / 100.0)))
    g = min(255, g + int((255 - g) * (amount / 100.0)))
    b = min(255, b + int((255 - b) * (amount / 100.0)))
    return rgb_to_hex(r, g, b)

