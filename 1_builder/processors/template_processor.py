#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Процессор шаблонов - генерирует шаблоны с data-template атрибутами
"""

import json
from typing import Any, Dict, Optional


class TemplateProcessor:
    """Генерирует шаблоны с data-template атрибутами"""
    
    def is_template(self, element_dict: Dict, bd_sources: Dict) -> bool:
        """
        Проверяет, является ли элемент шаблоном
        
        Шаблоном считается элемент который:
        1. Содержит источники БД (api1, api2, ...) НАПРЯМУЮ
        2. И содержит дочерний элемент с api: префиксами
        3. ИЛИ содержит cycle (может быть вложен в div_gr и т.д.)
        4. ИЛИ если в родителе есть bd_sources, то дочерний элемент с api: префиксами - это шаблон
        
        Args:
            element_dict: Словарь с элементами
            bd_sources: Источники БД из родителя
            
        Returns:
            True если элемент является шаблоном
        """
        has_bd_direct = any(
            isinstance(v, list) and len(v) >= 2 and v[0] == 'bd'
            for v in element_dict.values()
        )
        
        has_api_prefix_direct = any(
            isinstance(v, list) and len(v) >= 2 and 
            isinstance(v[1], str) and 'api' in v[1] and ':' in v[1]
            for v in element_dict.values()
        )
        
        # Проверяем наличие cycle рекурсивно
        has_cycle = self._has_cycle_recursive(element_dict)
        
        # Если в родителе есть bd_sources И элемент содержит api: префиксы - это шаблон
        # Если есть cycle, но нет api: префиксов на первом уровне - это контейнер для шаблона
        is_template = False
        if bd_sources and has_api_prefix_direct:
            is_template = True
        elif has_bd_direct and has_api_prefix_direct:
            is_template = True
        # НЕ помечаем как шаблон, если есть только cycle без api: префиксов на первом уровне
        
        return is_template
    
    def generate_template_attrs(self, element_dict: Dict) -> str:
        """
        Генерирует data-template атрибуты для шаблона
        
        Args:
            element_dict: Словарь с элементами шаблона
            
        Returns:
            Строка с data-template атрибутами или пустая строка
        """
        def has_direct_api_prefix(value: Any) -> bool:
            """Проверяет наличие api: префиксов ТОЛЬКО на первом уровне (не рекурсивно)"""
            if isinstance(value, list) and len(value) >= 2:
                if isinstance(value[1], str) and 'api' in value[1] and ':' in value[1]:
                    return True
            return False
        
        # Проверяем только прямые значения (не рекурсивно в дочерних словарях)
        has_api = False
        for v in element_dict.values():
            if has_direct_api_prefix(v):
                has_api = True
                break
        
        # Если не нашли на первом уровне, ищем рекурсивно (для cycle внутри div_gr)
        if not has_api:
            def has_api_recursive(obj):
                if isinstance(obj, list):
                    return has_direct_api_prefix(obj)
                if isinstance(obj, dict):
                    for v in obj.values():
                        if has_api_recursive(v):
                            return True
                return False
            has_api = has_api_recursive(element_dict)
        
        # Также проверяем наличие источников БД (api1, api2, ...)
        has_bd_source = any(
            isinstance(v, list) and len(v) >= 2 and v[0] == 'bd'
            for v in element_dict.values()
        )
        
        # Проверяем наличие cycle (может быть вложен в div_gr и т.д.)
        has_cycle = self._has_cycle_recursive(element_dict)
        
        if has_api or has_bd_source or has_cycle:
            # Генерируем JSON с шаблоном для JavaScript
            template_json = json.dumps(element_dict, ensure_ascii=False)
            # Используем одинарные кавычки для атрибута, чтобы не экранировать двойные кавычки в JSON
            return f" data-template='{template_json}'"
        
        return ''
    
    def _has_cycle_recursive(self, obj: Any) -> bool:
        """
        Рекурсивно проверяет наличие cycle в структуре
        
        Args:
            obj: Объект для проверки
            
        Returns:
            True если найден cycle
        """
        if not isinstance(obj, dict):
            return False
        if 'cycle' in obj:
            return True
        return any(self._has_cycle_recursive(v) for v in obj.values() if isinstance(v, dict))
    
    def has_api_prefixes(self, element_dict: Dict) -> bool:
        """
        Проверяет наличие api: префиксов в элементе
        
        Args:
            element_dict: Словарь с элементами
            
        Returns:
            True если найдены api: префиксы
        """
        def has_direct_api_prefix(value: Any) -> bool:
            if isinstance(value, list) and len(value) >= 2:
                if isinstance(value[1], str) and 'api' in value[1] and ':' in value[1]:
                    return True
            return False
        
        # Проверяем на первом уровне
        for v in element_dict.values():
            if has_direct_api_prefix(v):
                return True
        
        # Проверяем рекурсивно
        def has_api_recursive(obj):
            if isinstance(obj, list):
                return has_direct_api_prefix(obj)
            if isinstance(obj, dict):
                for v in obj.values():
                    if has_api_recursive(v):
                        return True
            return False
        
        return has_api_recursive(element_dict)

