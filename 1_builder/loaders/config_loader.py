#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузчик конфигураций
"""

from pathlib import Path
from typing import Dict, Any
from .file_loader import load_json_safe, load_css_variables_safe


class ConfigLoader:
    """Загружает все конфигурационные файлы из директории source"""
    
    def __init__(self, source_dir: Path):
        """
        Args:
            source_dir: Путь к директории с исходниками
        """
        self.source_dir = Path(source_dir)
    
    def load_all(self) -> Dict[str, Any]:
        """
        Загружает все конфиги
        
        Returns:
            Словарь с конфигами:
            {
                'pages': {...},
                'sections': {...},
                'html': {...},
                'css': {...},
                'general': {...},
                'tag': {...},
                'report': {...},
                'config': {...}
            }
        """
        configs = {}
        
        # 1. pages.json - структура страниц
        pages_file = self.source_dir / 'general' / 'pages.json'
        configs['pages'] = load_json_safe(pages_file, {})
        
        # 2. objects.json - объекты (элементы) для всех секций
        objects_file = self.source_dir / 'general' / 'objects.json'
        configs['sections'] = load_json_safe(objects_file, {})
        
        # 3. layout_html.json - структура разметки
        html_file = self.source_dir / 'layout' / 'layout_html.json'
        configs['html'] = load_json_safe(html_file, {})
        
        # 4. layout_col.json - адаптивные ширины колонок
        layout_col_file = self.source_dir / 'layout' / 'layout_col.json'
        configs['css'] = load_json_safe(layout_col_file, {})
        
        # 5. design/layout_css.json - составные селекторы (объединяем с css)
        css_file = self.source_dir / 'design' / 'layout_css.json'
        css_data = load_json_safe(css_file, {})
        configs['css'].update(css_data)
        
        # 5.5. design/objects_css.json - стили для конкретных объектов
        objects_css_file = self.source_dir / 'design' / 'objects_css.json'
        configs['objects_css'] = load_json_safe(objects_css_file, {})
        
        # 5.6. design/objects_fun.json - функции для объектов (sum, avg, etc)
        objects_fun_file = self.source_dir / 'design' / 'objects_fun.json'
        configs['objects_fun'] = load_json_safe(objects_fun_file, {})
        
        # 6. design/html.json - HTML атрибуты для групп/элементов (tag, href и т.д.)
        html_attrs_file = self.source_dir / 'design' / 'html.json'
        configs['html_attrs'] = load_json_safe(html_attrs_file, {})
        
        # 6.5. library/icon.json - SVG иконки
        icon_file = self.source_dir / 'library' / 'icon.json'
        configs['icons'] = load_json_safe(icon_file, {})
        
        # 6.6. library/if.json - Условные значения для страниц
        if_file = self.source_dir / 'library' / 'if.json'
        configs['if_values'] = load_json_safe(if_file, {})
        
        # 7. default.json - базовые стили (пустой если нет)
        default_file = self.source_dir / 'css' / 'default.json'
        configs['default'] = load_json_safe(default_file, {})
        
        # 8. default/general.json - глобальные CSS стили
        general_file = self.source_dir / 'default' / 'general.json'
        configs['general'] = load_json_safe(general_file, {})
        
        # 8.5. default/div_column.json - стили для колонок (col-1, col-2, etc)
        div_column_file = self.source_dir / 'default' / 'div_column.json'
        configs['div_column'] = load_json_safe(div_column_file, {})
        
        # 9. default/tag.json - стили тегов
        tag_file = self.source_dir / 'default' / 'tag.json'
        configs['tag'] = load_json_safe(tag_file, {})
        
        # 10. default_report - отладочные стили (папки/файлы с * в имени не участвуют)
        report_dir = self.source_dir / 'default_report'
        report_general = report_dir / 'general.json'
        report_tag = report_dir / 'tag.json'
        report_general_data = load_json_safe(report_general, {})
        report_tag_data = load_json_safe(report_tag, {})
        configs['report'] = {**report_general_data, **report_tag_data}
        
        # 10.1. default_report/objects_css.json - отладочные стили для объектов
        report_objects_css_file = report_dir / 'objects_css.json'
        configs['report_objects_css'] = load_json_safe(report_objects_css_file, {})
        
        # 11. config.json - настройки сборки
        config_file = self.source_dir / 'config.json'
        configs['config'] = load_json_safe(config_file, {})
        
        # 12. library/color.css - библиотека цветов (приоритет над color.json)
        color_css_file = self.source_dir / 'library' / 'color.css'
        colors_from_css = load_css_variables_safe(color_css_file, {})
        
        # Если color.css не найден или пуст, загружаем color.json как fallback
        if not colors_from_css:
            color_json_file = self.source_dir / 'library' / 'color.json'
            colors_from_json = load_json_safe(color_json_file, {})
            configs['colors'] = colors_from_json
        else:
            configs['colors'] = colors_from_css
        
        return configs
