#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConfigValidator - Валидация конфигурационных файлов
"""

from typing import Dict, List, Any


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

