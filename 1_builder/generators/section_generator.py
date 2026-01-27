#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор HTML секций
"""

from typing import Dict
from pathlib import Path
from core.config_manager import ConfigManager
from processors.element_processor import ElementProcessor
from processors.layout_processor import LayoutProcessor


class SectionGenerator:
    """Генерирует HTML секции"""
    
    def __init__(self, config_manager: ConfigManager, source_dir: Path = None):
        """
        Args:
            config_manager: Менеджер конфигураций
            source_dir: Путь к исходникам (для загрузки JSON из bd/)
        """
        self.config = config_manager
        self.source_dir = source_dir
    
    def generate_all(self) -> Dict[str, str]:
        """
        Генерирует все секции
        
        Returns:
            Словарь {section_name: html}
        """
        sections_html = {}
        
        # Получаем список секций из layout_html.json
        for section_name in self.config.html.keys():
            # Генерируем для каждой страницы (для обработки условий if)
            for page_name in self.config.pages.keys():
                html = self.generate_section(section_name, page_name)
                
                if html:
                    # Отладка: проверяем наличие script тегов
                    if 'type="application/json"' in html:
                        print(f"   ✅ Script теги найдены в generate_all для {section_name} (длина HTML: {len(html)})")
                    # Сохраняем только если еще не сохранили (берем первую сгенерированную версию)
                    if section_name not in sections_html:
                        sections_html[section_name] = html
                        # Отладка: проверяем после добавления
                        if 'type="application/json"' in sections_html[section_name]:
                            print(f"   ✅ Script теги найдены в sections_html после добавления для {section_name}")
                        else:
                            print(f"   ❌ Script теги НЕ найдены в sections_html после добавления для {section_name}")
        
        return sections_html
    
    def generate_section(self, section_name: str, current_page: str = None) -> str:
        """
        Генерирует HTML для одной секции
        
        Args:
            section_name: Реальное имя секции (header, turn, etc)
            current_page: Текущая страница (для обработки условий if)
            
        Returns:
            HTML строка
        """
        # В новом формате все данные в корне sections.json
        # Передаем все данные каждой секции
        section_data = self.config.sections
        
        # Получаем разметку по реальному имени секции
        html_config = self.config.html.get(section_name, {})
        
        if not html_config:
            return ''
        
        # Создаем контекст
        context = {
            'section_name': section_name,
            'current_page': current_page or '',
            'icons': self.config.icons,
            'if_values': self.config.if_values
        }
        
        # Создаем процессоры
        # Передаем objects_fun для генерации data-function атрибутов
        functions_config = getattr(self.config, 'objects_fun', {})
        element_processor = ElementProcessor(section_data, context, functions_config, self.source_dir)
        layout_processor = LayoutProcessor(html_config, section_name, element_processor, self.config.html_attrs)
        
        # Генерируем HTML
        html = layout_processor.generate_html()
        # Отладка: проверяем наличие script тегов
        if 'type="application/json"' in html:
            print(f"   ✅ Script теги найдены в generate_section для {section_name}")
        return html
    
    def save_all(self, sections_html: Dict[str, str], output_dir: Path):
        """
        Сохраняет все секции в файлы
        
        Args:
            sections_html: Словарь с HTML секций
            output_dir: Директория для сохранения
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем set чтобы избежать дублирования при сохранении
        saved_files = set()
        
        # Отладка: проверяем наличие script тегов в sections_html
        for section_key, html in sections_html.items():
            if 'type="application/json"' in html:
                print(f"   ✅ Script теги найдены в sections_html для {section_key}")
        
        for section_key, html in sections_html.items():
            # Отладка: проверяем наличие script тегов перед сохранением
            if 'type="application/json"' in html:
                print(f"   ✅ Script теги найдены в секции {section_key} перед сохранением")
            
            # Сохраняем файл
            file_path = output_dir / f"{section_key}.html"
            
            # Проверяем, не сохраняли ли уже идентичный файл
            file_signature = f"{section_key}:{html}"
            if file_signature not in saved_files:
                file_path.write_text(html, encoding='utf-8')
                saved_files.add(file_signature)
