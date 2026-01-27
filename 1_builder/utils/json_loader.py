#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSONLoader - Базовый класс для загрузки JSON файлов
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import json


class JSONLoader:
    """Базовый класс для загрузки JSON конфигураций"""
    
    @staticmethod
    def load(file_path: Path, default: Any = None) -> Any:
        """
        Загружает JSON файл
        
        Args:
            file_path: Путь к JSON файлу
            default: Значение по умолчанию, если файл не найден
            
        Returns:
            Загруженные данные или default
        """
        if default is None:
            default = {}
        
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON {file_path}: {e}")
            return default
        except Exception as e:
            print(f"❌ Ошибка загрузки {file_path}: {e}")
            return default
    
    @staticmethod
    def load_required(file_path: Path, error_message: str = None) -> Any:
        """
        Загружает обязательный JSON файл (вызывает ошибку если не найден)
        
        Args:
            file_path: Путь к JSON файлу
            error_message: Сообщение об ошибке
            
        Returns:
            Загруженные данные
            
        Raises:
            FileNotFoundError: Если файл не найден
        """
        if not file_path.exists():
            msg = error_message or f"Обязательный файл не найден: {file_path}"
            raise FileNotFoundError(msg)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON {file_path}: {e}")
        except Exception as e:
            raise IOError(f"Ошибка загрузки {file_path}: {e}")


class ConfigValidator:
    """Валидация конфигурационных файлов"""
    
    @staticmethod
    def validate_pages(pages_data: Dict[str, Any]) -> bool:
        """Валидирует pages.json"""
        if not isinstance(pages_data, dict):
            return False
        
        for page_name, page_config in pages_data.items():
            if not isinstance(page_config, dict):
                return False
            if 'section' not in page_config:
                return False
            if not isinstance(page_config['section'], list):
                return False
        
        return True
    
    @staticmethod
    def validate_sections(sections_data: Dict[str, Any]) -> bool:
        """Валидирует sections.json"""
        return isinstance(sections_data, dict)
    
    @staticmethod
    def validate_forms(forms_data: List[Dict[str, Any]]) -> bool:
        """Валидирует forms.json"""
        if not isinstance(forms_data, list):
            return False
        
        for form in forms_data:
            if not isinstance(form, dict):
                return False
            if 'filter' not in form:
                return False
        
        return True

