#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file_ignore.py - Функции для определения, нужно ли игнорировать файлы при сборке
"""

from pathlib import Path


def should_ignore_file(file_path: Path) -> bool:
    """
    Проверяет, нужно ли игнорировать файл при сборке.
    Файлы с звездочкой (*) в имени игнорируются.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        True если файл нужно игнорировать, False если нужно загружать
        
    Examples:
        >>> should_ignore_file(Path("default.json"))
        False
        >>> should_ignore_file(Path("default*.json"))
        True
        >>> should_ignore_file(Path("config*.json"))
        True
    """
    return '*' in file_path.name


def find_file_without_asterisk(directory: Path, base_name: str, extension: str = '.json') -> Path:
    """
    Ищет файл в директории, игнорируя файлы со звездочкой.
    Сначала ищет файл без звездочки, если не найден - возвращает путь с base_name.
    
    Args:
        directory: Директория для поиска
        base_name: Базовое имя файла (без расширения)
        extension: Расширение файла (по умолчанию .json)
        
    Returns:
        Путь к файлу (может не существовать, если файл не найден)
        
    Examples:
        >>> find_file_without_asterisk(Path("/css"), "default", ".json")
        Path("/css/default.json")  # если default.json существует
    """
    # Сначала проверяем точное совпадение
    exact_file = directory / f"{base_name}{extension}"
    if exact_file.exists() and not should_ignore_file(exact_file):
        return exact_file
    
    # Ищем все файлы с таким базовым именем
    pattern = f"{base_name}*{extension}"
    matching_files = list(directory.glob(pattern))
    
    # Фильтруем файлы без звездочки
    valid_files = [f for f in matching_files if not should_ignore_file(f)]
    
    if valid_files:
        # Возвращаем первый найденный файл без звездочки
        return valid_files[0]
    
    # Если не найден, возвращаем путь к ожидаемому файлу
    return directory / f"{base_name}{extension}"

