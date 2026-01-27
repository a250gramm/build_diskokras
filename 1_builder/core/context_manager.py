#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер контекста - управление контекстом для обработки элементов
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ProcessingContext:
    """Контекст обработки элементов"""
    current_page: str = ''
    section_name: str = ''
    icons: Dict[str, str] = field(default_factory=dict)
    if_values: Dict[str, Any] = field(default_factory=dict)
    function: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует контекст в словарь для обратной совместимости"""
        result = {
            'current_page': self.current_page,
            'section_name': self.section_name,
            'icons': self.icons,
            'if_values': self.if_values
        }
        if self.function:
            result['function'] = self.function
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingContext':
        """Создает контекст из словаря"""
        return cls(
            current_page=data.get('current_page', ''),
            section_name=data.get('section_name', ''),
            icons=data.get('icons', {}),
            if_values=data.get('if_values', {}),
            function=data.get('function')
        )


class ContextManager:
    """Управляет контекстом обработки"""
    
    def __init__(self):
        """Инициализация менеджера контекста"""
        self._contexts: Dict[str, ProcessingContext] = {}
    
    def create_context(self, section_name: str, current_page: str = '',
                      icons: Optional[Dict[str, str]] = None,
                      if_values: Optional[Dict[str, Any]] = None) -> ProcessingContext:
        """
        Создает новый контекст для секции
        
        Args:
            section_name: Имя секции
            current_page: Текущая страница
            icons: Словарь иконок
            if_values: Условные значения
            
        Returns:
            Созданный контекст
        """
        context = ProcessingContext(
            current_page=current_page,
            section_name=section_name,
            icons=icons or {},
            if_values=if_values or {}
        )
        
        # Сохраняем контекст по ключу секции
        key = f"{section_name}_{current_page}"
        self._contexts[key] = context
        
        return context
    
    def get_context(self, section_name: str, current_page: str = '') -> Optional[ProcessingContext]:
        """
        Получает контекст для секции
        
        Args:
            section_name: Имя секции
            current_page: Текущая страница
            
        Returns:
            Контекст или None если не найден
        """
        key = f"{section_name}_{current_page}"
        return self._contexts.get(key)
    
    def update_context(self, section_name: str, current_page: str = '',
                      **kwargs) -> Optional[ProcessingContext]:
        """
        Обновляет контекст для секции
        
        Args:
            section_name: Имя секции
            current_page: Текущая страница
            **kwargs: Поля для обновления
            
        Returns:
            Обновленный контекст или None если не найден
        """
        context = self.get_context(section_name, current_page)
        if context:
            for key, value in kwargs.items():
                if hasattr(context, key):
                    setattr(context, key, value)
        return context

