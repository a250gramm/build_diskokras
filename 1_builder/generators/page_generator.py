#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор HTML страниц
"""

import json
from typing import Dict
from pathlib import Path
from core.config_manager import ConfigManager


class PageGenerator:
    """Генерирует HTML страницы"""
    
    def __init__(self, config_manager: ConfigManager, sections_html: Dict[str, str], source_dir: Path = None, build_version: str = None):
        """
        Args:
            config_manager: Менеджер конфигураций
            sections_html: Словарь с HTML секций (может быть пустым, используется как кэш)
            source_dir: Путь к исходникам (для загрузки JSON из bd/)
            build_version: Версия сборки для сброса кэша (?v= в URL скриптов и конфигов)
        """
        self.config = config_manager
        self.sections_html = sections_html  # Используется как кэш
        self.source_dir = source_dir
        self.build_version = build_version or ''
        # Импортируем здесь для избежания циклических зависимостей
        from generators.section_generator import SectionGenerator
        self.section_generator = SectionGenerator(config_manager, source_dir)
    
    def generate_all(self) -> Dict[str, str]:
        """
        Генерирует все страницы
        
        Returns:
            Словарь {page_name: html}
        """
        pages_html = {}
        
        for page_name in self.config.pages.keys():
            html = self.generate_page(page_name)
            if html:
                pages_html[page_name] = html
        
        return pages_html
    
    def generate_page(self, page_name: str) -> str:
        """
        Генерирует HTML для одной страницы
        
        Args:
            page_name: Имя страницы
            
        Returns:
            HTML строка
        """
        # Получаем SEO данные
        seo = self.config.get_page_seo(page_name)
        title = seo[0] if len(seo) > 0 else ''
        description = seo[1] if len(seo) > 1 else ''
        keywords = seo[2] if len(seo) > 2 else ''
        
        # Получаем список секций
        section_keys = self.config.get_page_sections(page_name)
        
        # Генерируем HEAD
        head_html = self._generate_head(title, description, keywords)
        
        # Генерируем BODY
        body_html = self._generate_body(page_name, section_keys)
        
        # Собираем полный HTML
        return f'''<!DOCTYPE html>
<html lang="ru">
{head_html}
{body_html}
</html>'''
    
    def _generate_head(self, title: str, description: str, keywords: str) -> str:
        """Генерирует HEAD секцию"""
        css_href = f'../css/style.css?v={self.build_version}' if self.build_version else '../css/style.css'
        return f'''<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <title>{title}</title>
    <link rel="stylesheet" href="{css_href}">
</head>'''
    
    def _generate_body(self, page_name: str, section_keys: list) -> str:
        """Генерирует BODY секцию"""
        import re
        sections_html_parts = []
        script_tags = []  # Собираем все script теги из секций
        
        for sec_key in section_keys:
            # Генерируем секцию для конкретной страницы (чтобы правильно обработать условия if)
            section_html = self.section_generator.generate_section(sec_key, page_name)
            
            # Если не получилось, пытаемся взять из кэша
            if not section_html:
                section_html = self.sections_html.get(sec_key, '')
            
            if section_html:
                # Извлекаем script теги из секции
                script_matches = re.findall(r'<script[^>]*type="application/json"[^>]*>.*?</script>', section_html, re.DOTALL)
                script_tags.extend(script_matches)
                
                # Удаляем script теги из секции (они будут добавлены в конец body)
                section_html = re.sub(r'<script[^>]*type="application/json"[^>]*>.*?</script>', '', section_html, flags=re.DOTALL)
                
                # Оборачиваем в <section>
                section_tag = f'''<section id="{sec_key}" class="section-{sec_key}">
{section_html}
</section>'''
                sections_html_parts.append(section_tag)
        
        body_content = '\n    '.join(sections_html_parts)
        
        # Источники bd, уже вставленные из секций (с data-bd-api и фильтрами) — не дублировать
        # Также не добавляем script для PostgreSQL-источников (span с data-bd-url fetch_table.php)
        skip_sources = set()
        for tag in script_tags:
            m = re.search(r'data-bd-source="([^"]+)"', tag)
            if m:
                skip_sources.add(m.group(1))
        # Добавляем в skip все data-bd-source из body (включая span для PostgreSQL)
        for m in re.finditer(r'data-bd-source="([^"]+)"', body_content):
            skip_sources.add(m.group(1))
        
        scripts_html = self._generate_bd_scripts(skip_sources=skip_sources)
        if script_tags:
            scripts_html = '\n    '.join(script_tags) + ('\n' + scripts_html if scripts_html else '')
        elif scripts_html:
            scripts_html = scripts_html

        button_json_scripts = self._generate_button_json_config_scripts(body_content)
        if button_json_scripts:
            scripts_html = scripts_html + '\n    ' + button_json_scripts if scripts_html else button_json_scripts

        if_labels_script = self._generate_if_labels_script()
        if if_labels_script:
            scripts_html = scripts_html + '\n    ' + if_labels_script if scripts_html else if_labels_script
        
        from datetime import datetime
        build_marker = f'<!-- build: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} -->'
        v = self.build_version
        version_script = f'<script>window.BUILD_VERSION="{v}";</script>\n    ' if v else ''
        script_src = f'../js/script.js?v={v}' if v else '../js/script.js'
        return f'''<body data-page="{page_name}">
    {build_marker}
    {body_content}
{('    ' + scripts_html + '\n') if scripts_html else ''}
    {version_script}<script src="{script_src}"></script>
</body>'''
    
    def _generate_bd_scripts(self, skip_sources: set = None) -> str:
        """Генерирует script теги с данными из JSON файлов. Не добавляет скрипты для источников из skip_sources (уже вставлены из секций с data-bd-api и фильтрами)."""
        if not self.source_dir:
            return ''
        
        bd_dir = self.source_dir / 'bd_local'
        if not bd_dir.exists():
            return ''
        
        skip_sources = skip_sources or set()
        scripts = []
        for json_file in bd_dir.glob('*.json'):
            table_name = json_file.stem
            if table_name in skip_sources:
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    script_tag = f'<script type="application/json" data-bd-source="{table_name}">{json.dumps(data, ensure_ascii=False)}</script>'
                    scripts.append(script_tag)
            except Exception as e:
                print(f"   ⚠️ Ошибка загрузки {json_file}: {e}")
        
        return '\n    '.join(scripts) if scripts else ''

    def _generate_if_labels_script(self) -> str:
        """Скрипт с переводами из if.json (stat_pay, stat_ready) для подстановки в списках по значению из API."""
        if_values = getattr(self.config, 'if_values', None) or {}
        labels = {k: v for k, v in if_values.items() if isinstance(v, dict) and v and not any(str(key).startswith('/') for key in v.keys())}
        if not labels:
            return ''
        return f'<script type="application/json" data-if-labels>{json.dumps(labels, ensure_ascii=False)}</script>'

    def _generate_button_json_config_scripts(self, page_html: str) -> str:
        """Находит data-button-json=\"X\" на странице, подставляет конфиг из button_json/X.json — fallback при недоступном fetch."""
        if not self.source_dir or not page_html:
            return ''
        import re
        found = set(re.findall(r'data-button-json="([^"]+)"', page_html))
        if not found:
            return ''
        button_json_dir = self.source_dir / 'button_json'
        if not button_json_dir.exists():
            return ''
        scripts = []
        for name in found:
            path = button_json_dir / f'{name}.json'
            if not path.is_file():
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                tag = f'<script type="application/json" data-button-json-config="{name}">{json.dumps(data, ensure_ascii=False)}</script>'
                scripts.append(tag)
            except Exception as e:
                print(f"   ⚠️ button_json {name}: {e}")
        return '\n    '.join(scripts) if scripts else ''
    
    def save_all(self, pages_html: Dict[str, str], output_dir: Path):
        """
        Сохраняет все страницы в файлы
        
        Args:
            pages_html: Словарь с HTML страниц
            output_dir: Директория для сохранения
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for page_name, html in pages_html.items():
            file_path = output_dir / f"{page_name}.html"
            file_path.write_text(html, encoding='utf-8')
