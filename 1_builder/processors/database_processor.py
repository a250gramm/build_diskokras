#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Процессор базы данных - обрабатывает загрузку и встраивание данных из БД
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class DatabaseProcessor:
    """Обрабатывает загрузку и встраивание данных из БД"""
    
    def __init__(self, source_dir: Optional[Path] = None):
        """
        Args:
            source_dir: Путь к исходникам (для загрузки JSON из bd/)
        """
        self.source_dir = source_dir
        self.bd_cache: Dict[str, List] = {}  # Кэш загруженных JSON файлов
    
    def load_bd_json(self, table_name: str) -> Optional[List]:
        """
        Загружает JSON файл из source_dir/bd/
        
        Args:
            table_name: Имя таблицы (имя JSON файла без расширения)
            
        Returns:
            Список данных или None если файл не найден
        """
        if not self.source_dir:
            return None
        
        # Проверяем кэш
        if table_name in self.bd_cache:
            return self.bd_cache[table_name]
        
        # Путь к JSON файлу
        json_path = self.source_dir / 'bd' / f'{table_name}.json'
        
        if not json_path.exists():
            return None
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.bd_cache[table_name] = data
                return data
        except Exception as e:
            print(f"⚠️ Ошибка загрузки {json_path}: {e}")
            return None
    
    def generate_bd_element(self, key: str, value: List, base_path: str = '') -> str:
        """
        Генерирует HTML для элемента БД
        
        Args:
            key: Ключ элемента (имя источника api1, api2, ...)
            value: Массив с данными БД ["bd", "table_name", ...]
            base_path: Базовый путь для отладки
            
        Returns:
            HTML строка с span и script тегом
        """
        if len(value) < 2 or value[0] != 'bd':
            return ''
        
        table_name = value[1]
        link_attr = ''
        if len(value) >= 3 and isinstance(value[2], str) and value[2].startswith('link:'):
            link_attr = f' data-bd-link="{value[2]}"'
        
        # Используем ключ как имя источника (api1, api2, ...)
        api_name = key
        
        # Загружаем JSON данные если source_dir указан
        json_data = None
        if self.source_dir:
            json_data = self.load_bd_json(table_name)
            if json_data:
                print(f"   ✅ Загружены данные для {table_name}: {len(json_data)} записей")
            else:
                print(f"   ⚠️ Не удалось загрузить данные для {table_name}")
        
        # Генерируем span с data-атрибутами (скрытый элемент для JavaScript)
        bd_html = f'<span data-bd-api="{api_name}" data-bd-source="{table_name}" data-bd-url="../bd/{table_name}.json"{link_attr} style="display:none;"></span>'
        
        html_parts = [bd_html]
        
        # Если данные загружены, встраиваем их в script тег
        if json_data is not None:
            json_str = json.dumps(json_data, ensure_ascii=False)
            script_html = f'<script type="application/json" data-bd-api="{api_name}" data-bd-source="{table_name}">{json_str}</script>'
            html_parts.append(script_html)
            print(f"   ✅ Встроен script тег для {table_name} (длина: {len(script_html)} символов)")
        
        return ''.join(html_parts)
    
    def collect_bd_sources(self, data: Dict, parent_bd_sources: Optional[Dict] = None) -> Dict:
        """
        Собирает информацию о базах данных (api1, api2, ...) в текущем уровне
        
        Args:
            data: Словарь с элементами
            parent_bd_sources: Источники БД из родительского элемента
            
        Returns:
            Словарь с источниками БД {api_name: {table, link}}
        """
        bd_sources = {}
        if parent_bd_sources:
            bd_sources.update(parent_bd_sources)
        
        for key, value in data.items():
            if isinstance(value, list) and len(value) >= 2 and value[0] == 'bd':
                # Это источник базы данных
                table_name = value[1]
                link_attr = ''
                if len(value) >= 3 and isinstance(value[2], str) and value[2].startswith('link:'):
                    link_attr = value[2]  # "link:api1.id_wallet"
                bd_sources[key] = {
                    'table': table_name,
                    'link': link_attr
                }
        
        return bd_sources

