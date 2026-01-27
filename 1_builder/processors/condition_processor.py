#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Процессор условий - обрабатывает условия if в элементах
"""

from typing import Any, Dict, Optional


class ConditionProcessor:
    """Обрабатывает условия if в элементах"""
    
    def __init__(self, context: Dict):
        """
        Args:
            context: Контекст с current_page и другими данными
        """
        self.context = context or {}
    
    def process_if(self, data: Any) -> Optional[Any]:
        """
        Обрабатывает условие if в данных элемента
        
        Args:
            data: Данные элемента (может содержать ключ 'if')
            
        Returns:
            Обработанные данные или None если условие не выполнено
        """
        if not isinstance(data, dict) or 'if' not in data:
            return data
        
        current_page = self.context.get('current_page', '')
        if_conditions = data['if']
        
        # Ищем подходящее условие
        # Проверяем по URL (например, "/shino" для страницы "shino")
        page_url = f"/{current_page}"
        
        if page_url in if_conditions:
            return if_conditions[page_url]
        
        # Если условие не выполнено, возвращаем None
        return None
    
    def find_matching_condition(self, if_conditions: Dict, page_url: str) -> Optional[Any]:
        """
        Находит подходящее условие для страницы
        
        Args:
            if_conditions: Словарь условий if
            page_url: URL страницы (например, "/shino")
            
        Returns:
            Значение условия или None
        """
        return if_conditions.get(page_url)

