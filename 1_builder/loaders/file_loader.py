#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузчик JSON файлов и CSS переменных
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Загружает JSON файл
    
    Args:
        file_path: Путь к JSON файлу
        
    Returns:
        Словарь с данными или None если файл не найден
    """
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON {file_path}: {e}")
        return None
    except Exception as e:
        print(f"❌ Ошибка чтения файла {file_path}: {e}")
        return None


def load_json_safe(file_path: Path, default: Dict = None) -> Dict[str, Any]:
    """
    Загружает JSON файл с дефолтным значением
    
    Args:
        file_path: Путь к JSON файлу
        default: Значение по умолчанию если файл не найден
        
    Returns:
        Словарь с данными или default
    """
    if default is None:
        default = {}
    
    result = load_json(file_path)
    return result if result is not None else default


def load_css_variables(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Загружает CSS переменные из файла color.css
    
    Args:
        file_path: Путь к CSS файлу
        
    Returns:
        Словарь с цветами в формате, совместимом с color.json
    """
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Парсим CSS переменные из :root { ... }
        colors = {}
        gray_array = []
        
        # Паттерн для поиска CSS переменных: --name: value;
        # Поддерживаем подчеркивание и тире: --gray_1 или --gray-1
        pattern = r'--([\w_-]+):\s*([^;]+);'
        matches = re.findall(pattern, content)
        
        for var_name, var_value in matches:
            # Убираем пробелы из значения
            var_value = var_value.strip()
            
            # Обрабатываем gray_1, gray_2 (с подчеркиванием) или gray-1, gray-2 (с тире) - собираем в массив
            # Проверяем оба формата
            gray_match = None
            if var_name.startswith('gray_') and var_name[5:].isdigit():
                # Формат: gray_1, gray_2
                index = int(var_name[5:]) - 1  # gray_1 -> индекс 0
                gray_match = index
            elif var_name.startswith('gray-') and var_name[5:].isdigit():
                # Формат: gray-1, gray-2 (старый формат для обратной совместимости)
                index = int(var_name[5:]) - 1  # gray-1 -> индекс 0
                gray_match = index
            
            if gray_match is not None:
                # Расширяем массив если нужно
                while len(gray_array) <= gray_match:
                    gray_array.append(None)
                gray_array[gray_match] = var_value
            else:
                # Обычные переменные
                # Преобразуем kebab-case в snake_case для совместимости
                key = var_name.replace('-', '_')
                colors[key] = var_value
        
        # Добавляем массив gray если он был собран
        if gray_array:
            # Убираем None значения в конце
            while gray_array and gray_array[-1] is None:
                gray_array.pop()
            if gray_array:
                colors['gray'] = gray_array
        
        return colors if colors else None
        
    except Exception as e:
        print(f"❌ Ошибка чтения CSS файла {file_path}: {e}")
        return None


def load_css_variables_safe(file_path: Path, default: Dict = None) -> Dict[str, Any]:
    """
    Загружает CSS переменные с дефолтным значением
    
    Args:
        file_path: Путь к CSS файлу
        default: Значение по умолчанию если файл не найден
        
    Returns:
        Словарь с данными или default
    """
    if default is None:
        default = {}
    
    result = load_css_variables(file_path)
    return result if result is not None else default

