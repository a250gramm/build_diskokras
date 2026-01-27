#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер конфигураций
"""

from typing import Dict, Any, List


class ConfigManager:
    """Управляет всеми конфигурациями сборки"""
    
    def __init__(self, configs: Dict[str, Any]):
        """
        Args:
            configs: Словарь с конфигами от ConfigLoader
        """
        self.pages = configs.get('pages', {})
        self.sections = configs.get('sections', {})  # Теперь это плоский словарь всех элементов
        self.html = configs.get('html', {})
        self.css = configs.get('css', {})
        self.general = configs.get('general', {})
        self.tag = configs.get('tag', {})
        self.report = configs.get('report', {})
        self.config = configs.get('config', {})
        self.html_attrs = configs.get('html_attrs', {})  # HTML атрибуты для групп
        self.icons = configs.get('icons', {})  # SVG иконки из icon.json
        self.if_values = configs.get('if_values', {})  # Условные значения из if.json
        self.objects_fun = configs.get('objects_fun', {})  # Функции для объектов (sum, avg, etc)
        
        # Создаем список имен секций из html (layout_html.json)
        self._create_section_list()
    
    def _create_section_list(self):
        """Создает список секций из html конфигурации"""
        # В новом формате секции определяются в layout_html.json
        self.section_names = list(self.html.keys())
    
    def get_section_name(self, sec_key: str) -> str:
        """
        Получает реальное имя секции (для обратной совместимости)
        
        Args:
            sec_key: имя секции
            
        Returns:
            Реальное имя секции
        """
        return sec_key
    
    def get_sec_key(self, section_name: str) -> str:
        """
        Получает ключ секции (для обратной совместимости)
        
        Args:
            section_name: Реальное имя секции
            
        Returns:
            Ключ секции
        """
        return section_name
    
    def get_page_sections(self, page_name: str) -> List[str]:
        """
        Получает список секций для страницы
        
        Args:
            page_name: Имя страницы
            
        Returns:
            Список sec_X ключей
        """
        page_data = self.pages.get(page_name, {})
        return page_data.get('section', [])
    
    def get_page_seo(self, page_name: str) -> List[str]:
        """
        Получает SEO данные для страницы
        
        Args:
            page_name: Имя страницы
            
        Returns:
            [title, description, keywords]
        """
        page_data = self.pages.get(page_name, {})
        return page_data.get('seo', ['', '', ''])
    
    def validate(self):
        """
        Проверяет, что все необходимые конфиги загружены
        
        Raises:
            ValidationError: Если есть ошибки валидации
        """
        from core.validator import ConfigValidator
        
        # Создаем словарь конфигов для валидатора
        configs = {
            'pages': self.pages,
            'sections': self.sections,
            'html': self.html,
            'css': self.css,
            'general': self.general,
            'tag': self.tag,
            'report': self.report,
            'config': self.config,
            'html_attrs': self.html_attrs,
            'icons': self.icons,
            'if_values': self.if_values,
            'objects_fun': self.objects_fun
        }
        
        # Валидируем конфигурации
        validator = ConfigValidator()
        validator.validate_all(configs)

