#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSSLoader - Загрузка и работа с css.json
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json


class CSSLoader:
    """Загружает и предоставляет доступ к css.json"""
    
    def __init__(self, css_json_path: Path):
        """
        Args:
            css_json_path: Путь к css.json
        """
        self.css_json_path = css_json_path
        self.css_config: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Загружает css.json"""
        if not self.css_json_path or not self.css_json_path.exists():
            self.css_config = {}
            return
        
        try:
            with open(self.css_json_path, 'r', encoding='utf-8') as f:
                self.css_config = json.load(f)
        except Exception as e:
            print(f"⚠️  Ошибка загрузки css.json: {e}")
            self.css_config = {}
    
    def get_section_config(self, section_name: str) -> Optional[Dict[str, Any]]:
        """
        Получает конфигурацию CSS для секции
        
        Args:
            section_name: Имя секции (header, turn, body, footer)
            
        Returns:
            Конфигурация CSS для секции или None
        """
        return self.css_config.get(section_name)
    
    def get_column_widths(self, section_name: str, line_name: Optional[str] = None) -> List[int]:
        """
        Получает ширину колонок для секции
        
        Args:
            section_name: Имя секции
            line_name: Имя строки (для формата строки→колонки, например "row_1")
            
        Returns:
            Список ширин колонок для desktop
        """
        section_config = self.get_section_config(section_name)
        if not section_config:
            return []
        
        # Если указана строка, ищем ширину колонок внутри строки
        if line_name:
            line_config = section_config.get(line_name, {})
            if isinstance(line_config, dict):
                return line_config.get('desktop', [])
        
        # Иначе берем ширину колонок на верхнем уровне секции
        return section_config.get('desktop', [])
    
    def get_column_config(self, section_name: str, column_name: str) -> Optional[Dict[str, Any]]:
        """
        Получает конфигурацию CSS для колонки
        
        Args:
            section_name: Имя секции
            column_name: Имя колонки (column_1, column_2 и т.д.)
            
        Returns:
            Конфигурация CSS для колонки или None
        """
        section_config = self.get_section_config(section_name)
        if not section_config:
            return None
        
        return section_config.get(column_name)
    
    def get_line_config(self, section_name: str, line_name: str, column_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Получает конфигурацию CSS для строки
        
        Args:
            section_name: Имя секции
            line_name: Имя строки (row_1, row_2 и т.д.)
            column_name: Имя колонки (если строка внутри колонки)
            
        Returns:
            Конфигурация CSS для строки или None
        """
        section_config = self.get_section_config(section_name)
        if not section_config:
            return None
        
        # Если указана колонка, ищем строку внутри колонки
        if column_name:
            column_config = section_config.get(column_name, {})
            if isinstance(column_config, dict):
                return column_config.get(line_name)
        
        # Иначе ищем строку на верхнем уровне секции
        return section_config.get(line_name)
    
    def get_all_sections(self) -> Dict[str, Any]:
        """Возвращает всю конфигурацию css.json"""
        return self.css_config

