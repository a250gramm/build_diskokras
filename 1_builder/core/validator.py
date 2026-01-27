#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Валидатор конфигураций - проверяет корректность конфигурационных файлов
"""

from typing import Dict, Any, List, Optional
from core.exceptions import ValidationError, ConfigurationError


class ConfigValidator:
    """Валидирует конфигурации сборки"""
    
    def __init__(self):
        """Инициализация валидатора"""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self, configs: Dict[str, Any]) -> bool:
        """
        Валидирует все конфигурации
        
        Args:
            configs: Словарь с конфигурациями
            
        Returns:
            True если все конфигурации валидны
            
        Raises:
            ValidationError: Если есть критические ошибки
        """
        self.errors.clear()
        self.warnings.clear()
        
        # Проверяем обязательные конфигурации
        self._validate_required_configs(configs)
        
        # Валидируем каждую конфигурацию
        if 'pages' in configs:
            self._validate_pages(configs['pages'])
        
        if 'sections' in configs:
            self._validate_sections(configs['sections'])
        
        if 'html' in configs:
            self._validate_html(configs['html'])
        
        if 'css' in configs:
            self._validate_css(configs['css'])
        
        # Если есть ошибки, выбрасываем исключение
        if self.errors:
            error_msg = "Ошибки валидации:\n" + "\n".join(f"  - {e}" for e in self.errors)
            raise ValidationError(error_msg)
        
        # Выводим предупреждения
        if self.warnings:
            for warning in self.warnings:
                print(f"⚠️  Предупреждение: {warning}")
        
        return True
    
    def _validate_required_configs(self, configs: Dict[str, Any]) -> None:
        """Проверяет наличие обязательных конфигураций"""
        required = ['pages', 'sections', 'html']
        missing = [key for key in required if key not in configs or not configs[key]]
        
        if missing:
            self.errors.append(f"Отсутствуют обязательные конфигурации: {', '.join(missing)}")
    
    def _validate_pages(self, pages: Dict[str, Any]) -> None:
        """Валидирует конфигурацию страниц"""
        if not isinstance(pages, dict):
            self.errors.append("pages должен быть словарем")
            return
        
        if not pages:
            self.warnings.append("pages пуст - нет страниц для генерации")
            return
        
        for page_name, page_data in pages.items():
            if not isinstance(page_data, dict):
                self.errors.append(f"Данные страницы '{page_name}' должны быть словарем")
                continue
            
            # Проверяем наличие секций
            if 'section' not in page_data:
                self.warnings.append(f"Страница '{page_name}' не имеет секций")
            elif not isinstance(page_data['section'], list):
                self.errors.append(f"Секции страницы '{page_name}' должны быть списком")
    
    def _validate_sections(self, sections: Dict[str, Any]) -> None:
        """Валидирует конфигурацию секций (objects.json)"""
        if not isinstance(sections, dict):
            self.errors.append("sections должен быть словарем")
            return
        
        if not sections:
            self.warnings.append("sections пуст - нет элементов для генерации")
    
    def _validate_html(self, html: Dict[str, Any]) -> None:
        """Валидирует конфигурацию HTML (layout_html.json)"""
        if not isinstance(html, dict):
            self.errors.append("html должен быть словарем")
            return
        
        if not html:
            self.warnings.append("html пуст - нет разметки для генерации")
    
    def _validate_css(self, css: Dict[str, Any]) -> None:
        """Валидирует конфигурацию CSS"""
        if not isinstance(css, dict):
            self.errors.append("css должен быть словарем")
            return
    
    def get_errors(self) -> List[str]:
        """Возвращает список ошибок"""
        return self.errors.copy()
    
    def get_warnings(self) -> List[str]:
        """Возвращает список предупреждений"""
        return self.warnings.copy()

