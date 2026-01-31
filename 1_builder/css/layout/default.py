"""
Базовые стили по умолчанию для CSS
"""

import sys
from pathlib import Path
import json
from typing import Dict, Any, Optional

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from file_ignore import find_file_without_asterisk
from processors.value_processor import process_css_value


def load_default_config(default_json_path: Path) -> Dict[str, Any]:
    """
    Загружает настройки из default.json
    
    Args:
        default_json_path: Путь к файлу default.json
        
    Returns:
        Словарь с настройками (пустой словарь, если файл не найден)
        
    Raises:
        json.JSONDecodeError: Если файл содержит невалидный JSON
    """
    if not default_json_path.exists():
        # Если файл не найден (например, есть только со звездочкой), возвращаем пустой словарь
        return {}
    
    with open(default_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_default_css(source_dir: Optional[Path] = None, general_config: Optional[Dict] = None) -> str:
    """
    Возвращает базовые CSS стили на основе default.json
    
    Args:
        source_dir: Путь к директории sourse. Если None, вычисляется автоматически.
        
    Returns:
        Строка с CSS стилями
    """
    # Если путь не передан, вычисляем его относительно этого файла
    if source_dir is None:
        # От build/layout/default.py до sourse/css/default.json
        current_file = Path(__file__).resolve()
        source_dir = current_file.parent.parent.parent.parent / '2_source'
    
    # Ищем default.json, игнорируя файлы со звездочкой
    css_dir = source_dir / 'css'
    default_json_path = find_file_without_asterisk(css_dir, 'default', '.json')
    
    config = load_default_config(default_json_path)
    
    # Получаем font-family из конфига
    font_family = config.get('font-family', "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif")
    # Убираем точку с запятой если есть
    if font_family.endswith(';'):
        font_family = font_family[:-1]
    
    # Получаем ширину контейнера из general.json (device_* в layout) или wrapper/devices из default.json
    wrapper = config.get('wrapper', {})
    devices = config.get('devices', {})
    
    # Пытаемся получить device из general.json
    if general_config and 'layout' in general_config:
        layout_config = general_config['layout']
        if isinstance(layout_config, dict) and 'device' in layout_config:
            # Новый формат объекта: {"device": {"desktop": {"width": "1200px"}, ...}}
            # Или старый формат: {"device": {"desktop": ["1200","px"], ...}}
            device = layout_config['device']
            if isinstance(device, dict):
                # Обрабатываем значения: могут быть объектами {"width": "1200px"}, массивами [значение, единица] или строками
                def process_device_value(value, default):
                    if isinstance(value, dict) and 'width' in value:
                        # Новый формат: {"width": "1200px", "flex-wrap": "wrap", ...}
                        return [value['width']]
                    elif isinstance(value, list) and len(value) == 2:
                        # Старый формат: ["1200","px"]
                        return [f"{value[0]}{value[1]}"]
                    elif isinstance(value, str):
                        # Просто строка: "1200px"
                        return [value]
                    else:
                        return [default]
                
                wrapper = {
                    'desktop': process_device_value(device.get('desktop'), '1200px'),
                    'tablet': process_device_value(device.get('tablet'), '768px'),
                    'mobile': process_device_value(device.get('mobile'), '320px')
                }
        elif isinstance(layout_config, list):
            # Старый формат массива (для обратной совместимости)
            device_desktop = None
            device_tablet = None
            device_mobile = None
            for style in layout_config:
                if isinstance(style, str):
                    if style.startswith('device_desktop:'):
                        device_desktop = style.split(':', 1)[1].strip()
                    elif style.startswith('device_tablet:'):
                        device_tablet = style.split(':', 1)[1].strip()
                    elif style.startswith('device_mobile:'):
                        device_mobile = style.split(':', 1)[1].strip()
            
            if device_desktop:
                wrapper = {
                    'desktop': [device_desktop],
                    'tablet': [device_tablet] if device_tablet else ['768px'],
                    'mobile': [device_mobile] if device_mobile else ['320px']
                }
    
    # Используем wrapper, если devices нет
    if not devices and wrapper:
        desktop_width = wrapper.get('desktop', ['1200px'])
    elif devices:
        desktop_width = devices.get('desktop', ['1200px'])
    else:
        desktop_width = ['1200px']  # Значение по умолчанию
    
    if isinstance(desktop_width, list) and len(desktop_width) > 0:
        container_width = desktop_width[0]
    elif isinstance(desktop_width, str):
        container_width = desktop_width
    else:
        container_width = '1200px'  # Значение по умолчанию
    
    # Получаем базовые стили из конфига
    base_styles = config.get('base_styles', {})
    
    # Генерируем CSS из base_styles
    css_parts = ["/* Базовые стили */"]
    
    # Reset стили
    if 'reset' in base_styles:
        reset_styles = base_styles['reset']
        css_parts.append("* {")
        for prop, value in reset_styles.items():
            css_parts.append(f"    {prop}: {value};")
        css_parts.append("}\n")
    
    # Body стили
    if 'body' in base_styles:
        body_styles = base_styles['body']
        css_parts.append("body {")
        css_parts.append(f"    font-family: {font_family};")
        for prop, value in body_styles.items():
            css_parts.append(f"    {prop}: {value};")
        css_parts.append("}\n")
    
    # Button стили
    if 'button' in base_styles:
        button_styles = base_styles['button']
        css_parts.append("/* Сброс стилей для кнопок и ссылок */")
        css_parts.append("button {")
        for prop, value in button_styles.items():
            css_parts.append(f"    {prop}: {value};")
        css_parts.append("}\n")
    
    # Section-container стили
    # Всегда генерируем .layout с max-width из device (даже если default.json не загружен)
    css_parts.append(".layout {")
    css_parts.append(f"    max-width: {container_width};")
    if 'layout' in base_styles:
        container_styles = base_styles['layout']
        for prop, value in container_styles.items():
            css_parts.append(f"    {prop}: {value};")
    else:
        # Если base_styles нет, добавляем margin: 0 auto по умолчанию
        css_parts.append("    margin: 0 auto;")
    css_parts.append("}\n")
    
    # Section стили
    if 'section' in base_styles:
        section_styles = base_styles['section']
        css_parts.append("section {")
        for prop, value in section_styles.items():
            css_parts.append(f"    {prop}: {value};")
        css_parts.append("}\n")
    
    # Обработка структуры section из default.json (section.header, section.turn, section.body, section.footer)
    section_config = config.get('section', {})
    if section_config and isinstance(section_config, dict):
        # Генерируем CSS для каждого типа секции
        for section_type, section_styles in section_config.items():
            if isinstance(section_styles, dict):
                # Добавляем стили для section.section-{type} (для самого section элемента)
                css_parts.append(f"section.section-{section_type} {{")
                for prop, value in section_styles.items():
                    # Обрабатываем значение через process_css_value для поддержки ссылок и модификаторов
                    processed_value = process_css_value(value, general_config or {}, current_section='section')
                    # Преобразуем сокращения свойств
                    css_prop = prop.replace('bg-color', 'background-color')
                    css_prop = css_prop.replace('bg', 'background-color')
                    css_parts.append(f"    {css_prop}: {processed_value} !important;")
                css_parts.append("}\n")
                
                # Также добавляем стили для .section-{type} (для совместимости с другими элементами)
                css_parts.append(f".section-{section_type} {{")
                for prop, value in section_styles.items():
                    # Обрабатываем значение через process_css_value для поддержки ссылок и модификаторов
                    processed_value = process_css_value(value, general_config or {}, current_section='section')
                    # Преобразуем сокращения свойств
                    css_prop = prop.replace('bg-color', 'background-color')
                    css_prop = css_prop.replace('bg', 'background-color')
                    css_parts.append(f"    {css_prop}: {processed_value} !important;")
                css_parts.append("}\n")
                
                # Добавляем стили для .layout.section-{type} (для контейнера внутри section)
                css_parts.append(f".layout.section-{section_type} {{")
                for prop, value in section_styles.items():
                    # Обрабатываем значение через process_css_value для поддержки ссылок и модификаторов
                    processed_value = process_css_value(value, general_config or {}, current_section='section')
                    # Преобразуем сокращения свойств
                    css_prop = prop.replace('bg-color', 'background-color')
                    css_prop = css_prop.replace('bg', 'background-color')
                    css_parts.append(f"    {css_prop}: {processed_value} !important;")
                css_parts.append("}\n")
    
    return "\n".join(css_parts)


def get_section_styles_css(source_dir: Optional[Path] = None, general_config: Optional[Dict] = None) -> str:
    """
    Возвращает CSS стили для section из default.json (header, turn, body, footer)
    Эта функция вызывается ПОСЛЕ layout стилей, чтобы перекрыть их
    
    Args:
        source_dir: Путь к директории sourse. Если None, вычисляется автоматически.
        general_config: Конфигурация из general.json для разрешения ссылок
        
    Returns:
        Строка с CSS стилями для section
    """
    if source_dir is None:
        current_file = Path(__file__).resolve()
        source_dir = current_file.parent.parent.parent.parent / '2_source'
    
    # Ищем default.json, игнорируя файлы со звездочкой
    css_dir = source_dir / 'css'
    default_json_path = find_file_without_asterisk(css_dir, 'default', '.json')
    
    config = load_default_config(default_json_path)
    
    css_parts = []
    
    # Обработка структуры section из default.json (section.header, section.turn, section.body, section.footer)
    section_config = config.get('section', {})
    if section_config and isinstance(section_config, dict):
        # Генерируем CSS для каждого типа секции
        for section_type, section_styles in section_config.items():
            if isinstance(section_styles, dict):
                # Добавляем стили для section.section-{type} (для самого section элемента)
                css_parts.append(f"section.section-{section_type} {{")
                for prop, value in section_styles.items():
                    # Обрабатываем значение через process_css_value для поддержки ссылок и модификаторов
                    processed_value = process_css_value(value, general_config or {}, current_section='section')
                    # Преобразуем сокращения свойств
                    css_prop = prop.replace('bg-color', 'background-color')
                    css_prop = css_prop.replace('bg', 'background-color')
                    css_parts.append(f"    {css_prop}: {processed_value} !important;")
                css_parts.append("}\n")
                
                # Также добавляем стили для .section-{type} (для совместимости с другими элементами)
                css_parts.append(f".section-{section_type} {{")
                for prop, value in section_styles.items():
                    # Обрабатываем значение через process_css_value для поддержки ссылок и модификаторов
                    processed_value = process_css_value(value, general_config or {}, current_section='section')
                    # Преобразуем сокращения свойств
                    css_prop = prop.replace('bg-color', 'background-color')
                    css_prop = css_prop.replace('bg', 'background-color')
                    css_parts.append(f"    {css_prop}: {processed_value} !important;")
                css_parts.append("}\n")
                
                # Добавляем стили для .layout.section-{type} (для контейнера внутри section)
                css_parts.append(f".layout.section-{section_type} {{")
                for prop, value in section_styles.items():
                    # Обрабатываем значение через process_css_value для поддержки ссылок и модификаторов
                    processed_value = process_css_value(value, general_config or {}, current_section='section')
                    # Преобразуем сокращения свойств
                    css_prop = prop.replace('bg-color', 'background-color')
                    css_prop = css_prop.replace('bg', 'background-color')
                    css_parts.append(f"    {css_prop}: {processed_value} !important;")
                css_parts.append("}\n")
    
    return "\n".join(css_parts) if css_parts else ""


def get_component_css(source_dir: Optional[Path] = None) -> str:
    """
    Возвращает CSS стили для компонентов на основе default.json
    
    Args:
        source_dir: Путь к директории sourse. Если None, вычисляется автоматически.
        
    Returns:
        Строка с CSS стилями
    """
    if source_dir is None:
        current_file = Path(__file__).resolve()
        source_dir = current_file.parent.parent.parent.parent / '2_source'
    
    # Ищем default.json, игнорируя файлы со звездочкой
    css_dir = source_dir / 'css'
    default_json_path = find_file_without_asterisk(css_dir, 'default', '.json')
    
    # Если файл не найден (есть только со звездочкой), возвращаем пустые стили
    if not default_json_path.exists():
        return "/* Компоненты (default.json не найден или отключен) */\n"
    
    config = load_default_config(default_json_path)
    
    css_parts = ["/* Компоненты */"]
    component_styles = config.get('component_styles', {})
    
    for selector, styles in component_styles.items():
        css_parts.append(f".{selector} {{")
        for prop, value in styles.items():
            css_parts.append(f"    {prop}: {value};")
        css_parts.append("}\n")
    
    return "\n".join(css_parts)


def get_alignment_css(source_dir: Optional[Path] = None) -> str:
    """
    Возвращает CSS стили для выравнивания на основе default.json
    
    Args:
        source_dir: Путь к директории sourse. Если None, вычисляется автоматически.
        
    Returns:
        Строка с CSS стилями
    """
    if source_dir is None:
        current_file = Path(__file__).resolve()
        source_dir = current_file.parent.parent.parent.parent / '2_source'
    
    # Ищем default.json, игнорируя файлы со звездочкой
    css_dir = source_dir / 'css'
    default_json_path = find_file_without_asterisk(css_dir, 'default', '.json')
    
    # Если файл не найден (есть только со звездочкой), возвращаем пустые стили
    if not default_json_path.exists():
        return "/* Выравнивание (default.json не найден или отключен) */\n"
    
    config = load_default_config(default_json_path)
    
    css_parts = ["/* Выравнивание */"]
    alignment_styles = config.get('alignment_styles', {})
    
    for selector, styles in alignment_styles.items():
        css_parts.append(f".{selector} {{")
        for prop, value in styles.items():
            css_parts.append(f"    {prop}: {value};")
        css_parts.append("}\n")
    
    return "\n".join(css_parts)


def get_modal_css(source_dir: Optional[Path] = None) -> str:
    """
    Возвращает CSS стили для модальных окон на основе default.json
    
    Args:
        source_dir: Путь к директории sourse. Если None, вычисляется автоматически.
        
    Returns:
        Строка с CSS стилями
    """
    if source_dir is None:
        current_file = Path(__file__).resolve()
        source_dir = current_file.parent.parent.parent.parent / '2_source'
    
    # Ищем default.json, игнорируя файлы со звездочкой
    css_dir = source_dir / 'css'
    default_json_path = find_file_without_asterisk(css_dir, 'default', '.json')
    
    # Если файл не найден (есть только со звездочкой), возвращаем пустые стили
    if not default_json_path.exists():
        return "/* Модальные окна (default.json не найден или отключен) */\n"
    
    config = load_default_config(default_json_path)
    
    css_parts = ["/* Модальные окна */"]
    modal_styles = config.get('modal_styles', {})
    
    for selector, styles in modal_styles.items():
        css_parts.append(f".{selector} {{")
        for prop, value in styles.items():
            css_parts.append(f"    {prop}: {value};")
        css_parts.append("}\n")
    
    return "\n".join(css_parts)

