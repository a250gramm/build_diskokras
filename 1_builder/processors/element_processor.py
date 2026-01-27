#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Процессор элементов - координатор для обработки элементов из objects.json
"""

from pathlib import Path
from typing import Any, Dict, Optional

from elements.factory import ElementFactory
from processors.condition_processor import ConditionProcessor
from processors.double_processor import DoubleProcessor
from processors.template_processor import TemplateProcessor
from processors.database_processor import DatabaseProcessor
from processors.cycle_processor import CycleProcessor
from processors.element_type_detector import ElementTypeDetector
from utils.element_utils import (
    parse_html_tag, extract_link_info
)


class ElementProcessor:
    """Координатор для обработки элементов из objects.json"""
    
    def __init__(self, section_data: Dict, context: Optional[Dict] = None, 
                 functions_config: Optional[Dict] = None, source_dir: Optional[Path] = None):
        """
        Args:
            section_data: Данные секции из objects.json
            context: Контекст (current_page, section_name)
            functions_config: Конфигурация функций из objects_fun.json
            source_dir: Путь к исходникам (для загрузки JSON из bd/)
        """
        self.section_data = section_data
        self.context = context or {}
        self.functions_config = functions_config or {}
        
        # Инициализируем специализированные процессоры
        self.condition_processor = ConditionProcessor(context)
        self.double_processor = DoubleProcessor()
        self.template_processor = TemplateProcessor()
        self.database_processor = DatabaseProcessor(source_dir)
        self.cycle_processor = CycleProcessor()
        self.type_detector = ElementTypeDetector()
    
    def get_element_data(self, path: str) -> Optional[Any]:
        """
        Получает данные элемента по пути
        
        Args:
            path: Путь к элементу (например, "logo" или "header.nav")
            
        Returns:
            Данные элемента или None
        """
        # В новом формате все данные в корне section_data, ключ - это просто имя элемента
        if '.' not in path:
            return self.section_data.get(path)
        
        # Если путь составной (со старым форматом), разбираем
        keys = path.split('.')
        data = self.section_data
        
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        
        return data
    
    def process_element(self, path: str) -> str:
        """
        Обрабатывает элемент по пути и возвращает HTML
        
        Args:
            path: Путь к элементу
            
        Returns:
            HTML строка элемента
        """
        element_data = self.get_element_data(path)
        
        if element_data is None:
            return ''
        
        # 1. Обрабатываем условия "if"
        original_data = element_data  # Сохраняем для обработки double
        element_data = self.condition_processor.process_if(element_data)
        if element_data is None:
            return ''
        
        # 2. Обрабатываем команду "double" если есть условия if
        if isinstance(original_data, dict) and 'if' in original_data:
            if_conditions = original_data.get('if', {})
            element_data = self.double_processor.process_double(element_data, if_conditions)
        
        # Получаем ключ элемента (последняя часть пути)
        key = path.split('.')[-1]
        
        # 3. Если это nav/menu элемент с форматом ["nav"], собираем детей
        if isinstance(element_data, list) and len(element_data) == 1 and element_data[0] in ['nav', 'menu']:
            children = self._collect_children(key)
            if children:
                element_data = children
        
        # 4. Определяем тип элемента
        element_type = self.type_detector.detect_type(key, element_data)
        
        # 5. Обрабатываем в зависимости от типа
        if element_type == 'menu':
            # Это меню - обрабатываем напрямую
            element = ElementFactory.create(key, element_data, self.context)
            if element:
                return element.render()
        
        elif element_type == 'button_modal':
            # Кнопка с модалкой
            other_keys = [k for k in element_data.keys() if k not in ['nav', 'menu', 'if']]
            if other_keys:
                nested_key = other_keys[0]
                nested_value = element_data[nested_key]
                if isinstance(nested_value, list) and len(nested_value) >= 4:
                    if isinstance(nested_value[3], dict):
                        # Обрабатываем модалку
                        modal_html = self._process_complex_element(nested_value[3], f"{path}.{nested_key}.modal")
                        # Создаем кнопку
                        button_element = ElementFactory.create(nested_key, nested_value, self.context)
                        if button_element:
                            return button_element.render() + modal_html
        
        elif element_type == 'complex':
            # Сложная структура - обрабатываем рекурсивно
            return self._process_complex_element(element_data, path)
        
        # 6. Проверяем, есть ли модалка в 4-м параметре (для кнопок)
        modal_html = ''
        if isinstance(element_data, list) and len(element_data) >= 4:
            if isinstance(element_data[3], dict):
                modal_html = self._process_complex_element(element_data[3], f"{path}.modal")
        
        # 7. Создаем элемент через фабрику
        element = ElementFactory.create(key, element_data, self.context)
        
        if element:
            html = element.render()
            if modal_html:
                return html + modal_html
            return html
        
        # 8. Если это сложная структура, обрабатываем рекурсивно
        if isinstance(element_data, dict):
            return self._process_complex_element(element_data, path)
        
        return ''
    
    def _process_complex_element(self, data: Dict, base_path: str, parent_bd_sources: Optional[Dict] = None) -> str:
        """
        Обрабатывает сложный элемент (словарь с подэлементами)
        
        Args:
            data: Словарь с подэлементами
            base_path: Базовый путь
            parent_bd_sources: Источники БД из родительского элемента
            
        Returns:
            HTML строка всех подэлементов
        """
        html_parts = []
        
        # Собираем информацию о базах данных
        bd_sources = self.database_processor.collect_bd_sources(data, parent_bd_sources)
        
        for key, value in data.items():
            if key == 'if':
                continue
            
            # Обрабатываем ключ "cycle" или "cycle_col-N" или "cycle_gr8 col:2,1,1"
            from utils.element_utils import parse_col_syntax, extract_col_info_from_key
            
            is_cycle = key == 'cycle' or key.startswith('cycle_col-') or key.startswith('cycle_')
            if is_cycle and isinstance(value, dict):
                # Извлекаем col: информацию из ключа
                clean_key, col_info = extract_col_info_from_key(key)
                
                # Определяем cycle_key для cycle_processor
                if clean_key.startswith('cycle_col-'):
                    cycle_key = clean_key
                elif clean_key.startswith('cycle_'):
                    # Для cycle_gr8 col:2,1,1 создаем cycle_key на основе col_info
                    if col_info and col_info['type'] == 'adaptive':
                        desktop_cols = col_info['desktop']
                        cycle_key = f"cycle_col-{desktop_cols}"
                    else:
                        cycle_key = clean_key
                else:
                    cycle_key = clean_key
                
                # Собираем bd_sources из самого cycle (api1, api2 могут быть внутри cycle)
                cycle_bd_sources = self.database_processor.collect_bd_sources(value, bd_sources)
                cycle_html = self.cycle_processor.process_cycle(value, cycle_bd_sources, self.template_processor, self.database_processor, cycle_key=cycle_key)
                html_parts.append(cycle_html)
                continue
            
            # Проверяем, является ли ключ ссылкой
            link_href, link_class = extract_link_info(key, value if isinstance(value, dict) else {})
            is_link = link_href is not None
            
            if is_link:
                class_attr = f' class="{link_class}"' if link_class else ''
                html_parts.append(f'<a href="{link_href}"{class_attr}>')
            
            # Парсим HTML тег
            tag_info = parse_html_tag(key)
            
            if tag_info:
                tag_name, class_name, col_info = tag_info
                
                # Формируем атрибуты класса
                classes = []
                if class_name:
                    classes.append(class_name)
                
                # Обрабатываем col: синтаксис
                if col_info:
                    if col_info['type'] == 'adaptive':
                        # Добавляем класс _col-N для адаптивных колонок
                        desktop_cols = col_info['desktop']
                        classes.append(f"_col-{desktop_cols}")
                    elif col_info['type'] == 'percentage':
                        # Для процентных колонок добавляем класс с процентом
                        percent = int(col_info['percentage'])
                        classes.append(f"_col-{percent}pct")
                
                attrs = f' class="{" ".join(classes)}"' if classes else ''
                
                # Добавляем data-col атрибут для CSS генерации
                if col_info:
                    if col_info['type'] == 'adaptive':
                        attrs += f' data-col-desktop="{col_info["desktop"]}"'
                        attrs += f' data-col-tablet="{col_info["tablet"]}"'
                        attrs += f' data-col-mobile="{col_info["mobile"]}"'
                    elif col_info['type'] == 'percentage':
                        attrs += f' data-col-percent="{col_info["percentage"]}"'
                
                # Для модальных окон добавляем также id
                if class_name and class_name.startswith('modal'):
                    attrs += f' id="{class_name}"'
                
                sub_path = f"{base_path}.{key}"
                
                if isinstance(value, dict):
                    # Проверяем является ли это шаблоном
                    is_template = self.template_processor.is_template(value, bd_sources)
                    
                    if is_template:
                        # Это шаблон - генерируем только контейнер с data-template
                        template_attrs = self.template_processor.generate_template_attrs(value)
                        html_parts.append(f"<{tag_name}{attrs}{template_attrs}></{tag_name}>")
                    else:
                        # Обычная обработка
                        inner_html = self._process_complex_element(value, sub_path, bd_sources)
                        if inner_html:
                            html_parts.append(f"<{tag_name}{attrs}>{inner_html}</{tag_name}>")
                else:
                    sub_html = self.process_element(sub_path)
                    if sub_html:
                        html_parts.append(f"<{tag_name}{attrs}>{sub_html}</{tag_name}>")
            
            elif is_link:
                # Это ссылка - обрабатываем содержимое
                sub_path = f"{base_path}.{key}"
                if isinstance(value, dict):
                    # Удаляем "in" из данных для обработки содержимого
                    value_without_in = {k: v for k, v in value.items() if k != 'in'}
                    inner_html = self._process_complex_element(value_without_in, sub_path, bd_sources)
                    if inner_html:
                        html_parts.append(inner_html)
                else:
                    sub_html = self.process_element(sub_path)
                    if sub_html:
                        html_parts.append(sub_html)
            
            else:
                # Обрабатываем значение
                if isinstance(value, list):
                    # Проверяем формат ["bd", "table_name", ...] для базы данных
                    if len(value) >= 2 and value[0] == 'bd':
                        bd_html = self.database_processor.generate_bd_element(key, value, base_path)
                        html_parts.append(bd_html)
                    else:
                        # Обычный элемент
                        sub_path = f"{base_path}.{key}"
                        function_info = self._get_function_info(sub_path)
                        
                        element_context = self.context.copy()
                        if function_info:
                            element_context['function'] = function_info
                        
                        element = ElementFactory.create(key, value, element_context)
                        if element:
                            sub_html = element.render()
                            if sub_html:
                                html_parts.append(sub_html)
                
                elif isinstance(value, dict):
                    # Проверяем является ли это шаблоном
                    is_template = self.template_processor.is_template(value, bd_sources)
                    
                    if is_template:
                        # Это шаблон - генерируем только контейнер с data-template
                        template_attrs = self.template_processor.generate_template_attrs(value)
                        # Определяем тег контейнера (div по умолчанию)
                        tag_name = 'div'
                        class_name = key
                        if key.startswith('div'):
                            if '_' in key:
                                class_name = key.split('_', 1)[1]
                            elif '-' in key:
                                class_name = key.split('-', 1)[1]
                        
                        html_parts.append(f'<{tag_name}{template_attrs}></{tag_name}>')
                    else:
                        # Обычная обработка
                        sub_html = self._process_complex_element(value, f"{base_path}.{key}", bd_sources)
                        if sub_html:
                            html_parts.append(sub_html)
                else:
                    # Иначе пытаемся обработать через путь
                    sub_path = f"{base_path}.{key}"
                    sub_html = self.process_element(sub_path)
                    if sub_html:
                        html_parts.append(sub_html)
            
            # Закрываем ссылку, если она была открыта
            if is_link:
                html_parts.append('</a>')
        
        result = ''.join(html_parts)
        # Отладка: проверяем наличие script тегов
        if 'type="application/json"' in result:
            print(f"   ✅ Script теги найдены в результате для {base_path}")
        return result
    
    def _collect_children(self, parent_key: str) -> Optional[Dict]:
        """
        Собирает дочерние элементы по 2-му параметру (родитель)
        
        Args:
            parent_key: Ключ родительского элемента (например, "header_nav", "turn_nav")
            
        Returns:
            Словарь дочерних элементов для MenuElement или None
        """
        children = {}
        
        for key, value in self.section_data.items():
            if isinstance(value, list) and len(value) >= 2:
                # 2-й параметр = родитель
                if value[1] == parent_key:
                    children[key] = value
        
        return children if children else None
    
    def _get_function_info(self, element_path: str) -> Optional[Dict]:
        """
        Получает информацию о функции для элемента из functions_config
        
        Args:
            element_path: Путь к элементу
            
        Returns:
            Словарь {"fun": "sum", "result": "total_price"} или None
        """
        if not self.functions_config:
            return None
        
        # Преобразуем путь: "main_btn.form_form2.div_field" → "main_btn form_form2 div_field"
        path_parts = element_path.split('.')
        search_path = ' '.join(path_parts)
        
        # Ищем этот путь в functions_config по окончанию
        for function_name, function_data in self.functions_config.items():
            # function_data это словарь с одним ключом = путь к элементу
            for element_path_key, func_config in function_data.items():
                # Разбиваем ключ конфигурации на части
                config_parts = element_path_key.split(' ')
                
                # Проверяем что все части из config присутствуют в path в правильном порядке
                match = True
                path_idx = 0
                last_match_idx = -1
                
                for config_part in config_parts:
                    # Ищем эту часть в path_parts начиная с path_idx
                    found = False
                    while path_idx < len(path_parts):
                        path_part = path_parts[path_idx]
                        
                        # Убираем числовой префикс из config_part если есть
                        config_part_clean = config_part
                        if '.' in config_part:
                            parts = config_part.split('.', 1)
                            if parts[0].isdigit():
                                config_part_clean = parts[1]
                        
                        # Сравниваем
                        if path_part == config_part or path_part == config_part_clean:
                            found = True
                            last_match_idx = path_idx
                            path_idx += 1
                            break
                        path_idx += 1
                    
                    if not found:
                        match = False
                        break
                
                # Проверяем что последняя совпавшая часть - это конец пути
                if match and last_match_idx == len(path_parts) - 1:
                    return {
                        'fun': func_config.get('fun', ''),
                        'result': func_config.get('result', ''),
                        'format': func_config.get('format', 'number')
                    }
        
        return None
