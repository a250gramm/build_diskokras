#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTMLLoader - Загрузка и работа с html.json
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json


class HTMLLoader:
    """Загружает и предоставляет доступ к html.json"""
    
    def __init__(self, html_json_path: Path):
        """
        Args:
            html_json_path: Путь к html.json
        """
        self.html_json_path = html_json_path
        self.html_config: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Загружает html.json"""
        if not self.html_json_path or not self.html_json_path.exists():
            self.html_config = {}
            return
        
        try:
            with open(self.html_json_path, 'r', encoding='utf-8') as f:
                self.html_config = json.load(f)
        except Exception as e:
            print(f"⚠️  Ошибка загрузки html.json: {e}")
            self.html_config = {}
    
    def get_section_marking(self, section_name: str) -> Optional[Dict[str, Any]]:
        """
        Получает разметку для секции
        
        Args:
            section_name: Имя секции (header, turn, body, footer)
            
        Returns:
            Разметка секции или None
        """
        return self.html_config.get(section_name)
    
    def has_section(self, section_name: str) -> bool:
        """Проверяет, есть ли разметка для секции"""
        return section_name in self.html_config
    
    def get_all_sections(self) -> Dict[str, Any]:
        """Возвращает всю конфигурацию html.json"""
        return self.html_config

