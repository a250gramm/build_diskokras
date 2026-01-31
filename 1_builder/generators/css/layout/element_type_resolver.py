#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Определитель типов элементов - определяет тип элемента из objects.json
"""

from typing import Dict, Any, Optional, Tuple


class ElementTypeResolver:
    """Определяет тип элемента из objects.json"""
    
    def __init__(self, sections_config: Dict[str, Any]):
        """
        Args:
            sections_config: Данные из objects.json (sections_config)
        """
        self.sections_config = sections_config or {}
    
    def find_child_recursive(self, data: Any, search_key: str) -> Optional[Any]:
        """
        Рекурсивно ищет дочерний элемент в структуре данных
        
        Args:
            data: Данные для поиска
            search_key: Ключ для поиска
            
        Returns:
            Найденное значение или None
        """
        if not isinstance(data, dict):
            return None
        
        # Ищем на текущем уровне
        if search_key in data:
            return data[search_key]
        
        # Ищем во вложенных структурах
        for value in data.values():
            if isinstance(value, dict):
                result = self.find_child_recursive(value, search_key)
                if result is not None:
                    return result
        
        return None
    
    def resolve_element_type(self, element_key: str) -> Tuple[Optional[str], bool, bool]:
        """
        Определяет тип элемента из objects.json
        
        Args:
            element_key: Ключ элемента (например, "header_nav", "logo")
            
        Returns:
            Кортеж (element_type, has_api, is_complex_structure)
        """
        element_type = None
        has_api = False
        is_complex_structure = False
        
        if element_key not in self.sections_config:
            return element_type, has_api, is_complex_structure
        
        element_data = self.sections_config[element_key]
        
        # Проверяем, есть ли структура с "if" (условные элементы)
        if isinstance(element_data, dict) and 'if' in element_data:
            # Для элементов с if берем тип из первого значения любого условия
            if_conditions = element_data['if']
            if if_conditions:
                # Берем первое значение из любого условия
                first_condition_value = next(iter(if_conditions.values()))
                if isinstance(first_condition_value, list) and len(first_condition_value) > 0:
                    element_type = first_condition_value[0]  # Первый элемент - тип
                elif isinstance(first_condition_value, dict):
                    # Если значение - словарь, это сложная структура
                    is_complex_structure = True
        elif isinstance(element_data, dict):
            # Это сложная структура (например, {"nav": {...}})
            is_complex_structure = True
        elif isinstance(element_data, list) and len(element_data) > 0:
            element_type = element_data[0]  # Первый элемент - тип
            # Проверяем, есть ли "api" в массиве
            has_api = len(element_data) > 2 and element_data[2] == 'api'
        
        return element_type, has_api, is_complex_structure
    
    def resolve_child_type(self, parent_key: str, child_key: str, 
                         tag_name: Optional[str] = None, 
                         class_name: Optional[str] = None) -> Optional[str]:
        """
        Определяет тип дочернего элемента
        
        Args:
            parent_key: Ключ родительского элемента
            child_key: Ключ дочернего элемента
            tag_name: Имя тега (опционально)
            class_name: Имя класса (опционально)
            
        Returns:
            Тип элемента или None
        """
        if parent_key not in self.sections_config:
            return None
        
        parent_data = self.sections_config[parent_key]
        
        # Если есть tag_name и class_name, ищем внутри конкретного div
        if tag_name and class_name:
            tag_with_class_key = f"{tag_name} {class_name}"
            tag_with_class_key_underscore = f"{tag_name}_{class_name}"
            
            div_data = None
            if isinstance(parent_data, dict):
                if tag_with_class_key in parent_data:
                    div_data = parent_data[tag_with_class_key]
                elif tag_with_class_key_underscore in parent_data:
                    div_data = parent_data[tag_with_class_key_underscore]
                else:
                    # Ключ в objects.json может быть с суффиксом " col:2,2,2" (например "div_field-paymet col:2,2,2")
                    for key in parent_data:
                        if key.startswith(tag_with_class_key_underscore) or key.startswith(tag_with_class_key.replace(' ', '_')):
                            div_data = parent_data[key]
                            break
            
            if div_data and isinstance(div_data, dict):
                # Точное совпадение дочернего ключа
                if child_key in div_data:
                    child_data = div_data[child_key]
                    if isinstance(child_data, list) and len(child_data) > 0:
                        return child_data[0]
                # Ключ в objects.json может быть "div_2-col:80%" при child_key "2-col"
                for key in div_data:
                    if key == child_key:
                        child_data = div_data[key]
                        if isinstance(child_data, list) and len(child_data) > 0:
                            return child_data[0]
                    if key.startswith(f"div_{child_key}") or key.startswith(f"div-{child_key}"):
                        child_data = div_data[key]
                        if isinstance(child_data, list) and len(child_data) > 0:
                            return child_data[0]
                        if isinstance(child_data, dict):
                            return 'text'
            
            # Пробуем найти div_field-paymet рекурсивно
            div_field_data = self.find_child_recursive(parent_data, f"div_{class_name}")
            if not div_field_data:
                div_field_data = self.find_child_recursive(parent_data, f"div-{class_name}")
            if not div_field_data and isinstance(parent_data, dict):
                for key in parent_data:
                    if key.startswith(f"div_{class_name}") or key.startswith(f"div-{class_name}"):
                        div_field_data = parent_data[key]
                        break
            
            if div_field_data and isinstance(div_field_data, dict):
                if child_key in div_field_data:
                    child_data = div_field_data[child_key]
                    if isinstance(child_data, list) and len(child_data) > 0:
                        return child_data[0]
                for key in div_field_data:
                    if key.startswith(f"div_{child_key}") or key.startswith(f"div-{child_key}"):
                        child_data = div_field_data[key]
                        if isinstance(child_data, list) and len(child_data) > 0:
                            return child_data[0]
                        if isinstance(child_data, dict):
                            return 'text'
        
        # Ищем child_key рекурсивно во всем parent_data
        child_data = self.find_child_recursive(parent_data, child_key)
        
        if child_data is not None:
            if isinstance(child_data, list) and len(child_data) > 0:
                return child_data[0]
            elif isinstance(child_data, dict):
                # Проверяем, является ли это меню (словарь со ссылками - массивы с 'a')
                is_menu = all(
                    isinstance(v, list) and len(v) >= 2 and v[0] == 'a'
                    for v in child_data.values()
                ) if child_data else False
                
                if is_menu:
                    return 'nav.menu'
        
        return None
    
    def build_selector_for_type(self, element_key: str, element_type: Optional[str], 
                               has_api: bool, is_complex_structure: bool) -> str:
        """
        Строит CSS селектор на основе типа элемента
        
        Args:
            element_key: Ключ элемента
            element_type: Тип элемента
            has_api: Есть ли API
            is_complex_structure: Является ли сложной структурой
            
        Returns:
            CSS селектор
        """
        # Если это сложная структура, селектор уже установлен
        if is_complex_structure:
            return f"[data-path='{element_key}']"
        
        # Если тип найден в objects.json, используем его
        if element_type:
            if element_type == 'img':
                return f"[data-path='{element_key}'] img"
            elif element_type == 'nav':
                return f"[data-path='{element_key}'] nav"
            elif element_type == 'icon':
                return f"[data-path='{element_key}'] icon"
            elif element_type == 'field' or element_type == 'input':
                return f"[data-path='{element_key}'] input"
            elif element_type == 'text':
                # Для text элементов с API используется span, без API - text
                tag = 'span' if has_api else 'text'
                return f"[data-path='{element_key}'] {tag}"
            elif element_type == 'a':
                return f"[data-path='{element_key}'] a"
            else:
                # Неизвестный тип - используем fallback
                return f"[data-path='{element_key}'] {element_type}"
        
        # Fallback: определяем по имени элемента
        if '_img' in element_key:
            return f"[data-path='{element_key}'] img"
        elif element_key.endswith('_nav'):
            return f"[data-path='{element_key}'] nav"
        elif element_key.endswith('_icon') or element_key.startswith('icon_'):
            return f"[data-path='{element_key}'] icon"
        elif element_key.endswith('_order') or element_key.endswith('_field'):
            return f"[data-path='{element_key}'] input"
        else:
            # По умолчанию для текстовых элементов
            return f"[data-path='{element_key}'] text"

