#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки API элементов
"""

import sys
from pathlib import Path
import json

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from loaders.config_loader import ConfigLoader
from core.config_manager import ConfigManager
from elements.text_element import TextElement


def test_api_elements():
    """Проверяет все элементы с флагом api"""
    
    # Определяем пути
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    source_dir = project_root / '2_source'
    
    print("=" * 60)
    print("🔍 ПРОВЕРКА API ЭЛЕМЕНТОВ")
    print("=" * 60)
    print()
    
    # Загружаем конфигурации
    config_loader = ConfigLoader(source_dir)
    configs = config_loader.load_all()
    config_manager = ConfigManager(configs)
    
    # Получаем все элементы
    objects = config_manager.sections
    
    # Ищем элементы с флагом api
    api_elements = []
    for key, value in objects.items():
        if isinstance(value, list) and len(value) > 2 and value[2] == 'api':
            api_elements.append((key, value))
    
    print(f"📋 Найдено элементов с флагом 'api': {len(api_elements)}")
    print()
    
    if not api_elements:
        print("❌ Элементы с флагом 'api' не найдены!")
        return
    
    # Проверяем каждый элемент
    all_ok = True
    for key, value in api_elements:
        print(f"🔹 Проверка элемента: {key}")
        print(f"   Формат: {value}")
        
        # Проверяем формат
        if not isinstance(value, list) or len(value) < 3:
            print(f"   ❌ Неправильный формат (должен быть массив с 3 элементами)")
            all_ok = False
            continue
        
        if value[0] != 'text':
            print(f"   ⚠️  Тип элемента: {value[0]} (ожидается 'text')")
        
        if value[2] != 'api':
            print(f"   ❌ Третий элемент должен быть 'api', получен: {value[2]}")
            all_ok = False
            continue
        
        # Создаем элемент и проверяем генерацию HTML
        try:
            element = TextElement(key, value)
            html = element.render()
            
            # Проверяем наличие атрибутов
            has_data_source = 'data-source="api"' in html
            has_api_url = f'data-api-url="/php/{key}.php"' in html
            
            print(f"   HTML: {html}")
            
            if has_data_source:
                print(f"   ✅ Атрибут data-source='api' присутствует")
            else:
                print(f"   ❌ Атрибут data-source='api' отсутствует")
                all_ok = False
            
            if has_api_url:
                print(f"   ✅ Атрибут data-api-url='/php/{key}.php' присутствует")
            else:
                print(f"   ❌ Атрибут data-api-url='/php/{key}.php' отсутствует")
                all_ok = False
            
            # Проверяем наличие PHP файла
            php_file = source_dir / 'php' / f'{key}.php'
            if php_file.exists():
                print(f"   ✅ PHP файл существует: {php_file}")
            else:
                print(f"   ❌ PHP файл отсутствует: {php_file}")
                all_ok = False
            
        except Exception as e:
            print(f"   ❌ Ошибка при создании элемента: {e}")
            all_ok = False
        
        print()
    
    # Проверяем layout_html.json
    print("=" * 60)
    print("🔍 ПРОВЕРКА РАЗМЕЩЕНИЯ В LAYOUT")
    print("=" * 60)
    print()
    
    layout_html = config_manager.html
    found_in_layout = {}
    
    for section_name, section_layout in layout_html.items():
        section_str = json.dumps(section_layout, ensure_ascii=False)
        for key, _ in api_elements:
            if key in section_str:
                if key not in found_in_layout:
                    found_in_layout[key] = []
                found_in_layout[key].append(section_name)
    
    for key, _ in api_elements:
        if key in found_in_layout:
            print(f"✅ {key} найден в секциях: {', '.join(found_in_layout[key])}")
        else:
            print(f"⚠️  {key} не найден в layout_html.json")
    
    print()
    print("=" * 60)
    if all_ok and found_in_layout:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("⚠️  ЕСТЬ ПРОБЛЕМЫ - проверьте вывод выше")
    print("=" * 60)


if __name__ == '__main__':
    test_api_elements()


