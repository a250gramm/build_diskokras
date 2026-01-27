#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Процессор команды double - обрабатывает команду ["double"] для копирования структур
"""

from typing import Any, Dict, Optional


class DoubleProcessor:
    """Обрабатывает команду double (копирование структур из предыдущих условий)"""
    
    def process_double(self, data: Any, all_conditions: Dict) -> Any:
        """
        Рекурсивно обрабатывает команду ["double"] в структуре данных
        
        Args:
            data: Данные для обработки
            all_conditions: Все условия if для поиска оригинальных структур
            
        Returns:
            Обработанные данные с замененными ["double"]
        """
        # Если это список с командой ["double"]
        if isinstance(data, list) and len(data) == 1 and data[0] == 'double':
            return data  # Вернём как есть, обработаем на уровне _process_complex_element
        
        # Если это список с вложенным объектом (например, кнопка с модалкой)
        if isinstance(data, list):
            processed_list = []
            for item in data:
                if isinstance(item, dict):
                    # Обрабатываем словарь внутри массива
                    processed_dict = {}
                    for key, value in item.items():
                        # Проверяем команду ["double"]
                        if isinstance(value, list) and len(value) == 1 and value[0] == 'double':
                            # Ищем оригинальную структуру в предыдущих условиях
                            original = self._find_original_structure(key, all_conditions)
                            if original:
                                processed_dict[key] = original
                            else:
                                processed_dict[key] = value
                        elif isinstance(value, dict):
                            # Рекурсивно обрабатываем вложенные структуры
                            processed_dict[key] = self._process_double_in_dict(value, all_conditions)
                        else:
                            processed_dict[key] = value
                    processed_list.append(processed_dict)
                else:
                    processed_list.append(item)
            return processed_list
        
        # Если это словарь
        if isinstance(data, dict):
            return self._process_double_in_dict(data, all_conditions)
        
        return data
    
    def _process_double_in_dict(self, data: Dict, all_conditions: Dict) -> Dict:
        """
        Обрабатывает ["double"] в словаре
        
        Args:
            data: Словарь для обработки
            all_conditions: Все условия if
            
        Returns:
            Обработанный словарь
        """
        processed = {}
        for key, value in data.items():
            # Проверяем команду ["double"]
            if isinstance(value, list) and len(value) == 1 and value[0] == 'double':
                # Ищем оригинальную структуру
                original = self._find_original_structure(key, all_conditions)
                if original:
                    processed[key] = original
                else:
                    processed[key] = value
            elif isinstance(value, dict):
                # Рекурсивно обрабатываем
                processed[key] = self._process_double_in_dict(value, all_conditions)
            else:
                processed[key] = value
        return processed
    
    def _find_original_structure(self, key: str, all_conditions: Dict) -> Optional[Any]:
        """
        Ищет оригинальную структуру по ключу в предыдущих условиях
        
        Args:
            key: Ключ для поиска (например, "div_gr4")
            all_conditions: Все условия if
            
        Returns:
            Оригинальная структура или None
        """
        # Проходим по всем условиям в порядке их определения
        for condition_key, condition_value in all_conditions.items():
            # Если это список (например, кнопка с модалкой)
            if isinstance(condition_value, list):
                for idx, item in enumerate(condition_value):
                    if isinstance(item, dict):
                        # Ищем ключ в словаре напрямую
                        if key in item:
                            found = item[key]
                            # Если найденное значение не ["double"], возвращаем его
                            if not (isinstance(found, list) and len(found) == 1 and found[0] == 'double'):
                                return found
                        # Рекурсивный поиск в глубине словаря
                        result = self._find_in_nested_dict(key, item)
                        if result:
                            return result
            # Если это словарь
            elif isinstance(condition_value, dict):
                if key in condition_value:
                    found = condition_value[key]
                    if not (isinstance(found, list) and len(found) == 1 and found[0] == 'double'):
                        return found
                # Рекурсивный поиск в глубине
                result = self._find_in_nested_dict(key, condition_value)
                if result:
                    return result
        
        return None
    
    def _find_in_nested_dict(self, key: str, data: Dict) -> Optional[Any]:
        """
        Рекурсивный поиск ключа в вложенных словарях
        
        Args:
            key: Ключ для поиска
            data: Словарь для поиска
            
        Returns:
            Найденное значение или None
        """
        for k, v in data.items():
            if k == key:
                # Проверяем что это не ["double"]
                if not (isinstance(v, list) and len(v) == 1 and v[0] == 'double'):
                    return v
            elif isinstance(v, dict):
                result = self._find_in_nested_dict(key, v)
                if result:
                    return result
            elif isinstance(v, list):
                # Проверяем список - может быть словарь внутри
                for item in v:
                    if isinstance(item, dict):
                        result = self._find_in_nested_dict(key, item)
                        if result:
                            return result
        return None

