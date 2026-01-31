#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StyleValidator - Валидатор соответствия HTML структуры и CSS стилей
Проверяет правильность применения стилей для column и row во всех секциях
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Добавляем путь к build для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.layout_structure_analyzer import LayoutStructureAnalyzer


class StyleValidator:
    """Валидатор стилей для проверки соответствия структуры и CSS"""
    
    def __init__(self, html_config: Dict[str, Any]):
        """
        Args:
            html_config: Конфигурация из layout_html.json
        """
        self.html_config = html_config
        self.structure_analyzer = LayoutStructureAnalyzer(html_config)
        
    def analyze_structure(self, section_name: str) -> Dict[str, Any]:
        """
        Анализирует структуру секции и возвращает информацию о вложенности
        
        Returns:
            {
                'starts_with': 'rows' | 'columns',
                'has_nested_rows': bool,  # есть ли row внутри column
                'has_nested_columns': bool,  # есть ли column внутри row
                'row_paths': List[str],  # пути к row элементам
                'column_paths': List[str]  # пути к column элементам
            }
        """
        section_config = self.html_config.get(section_name, {})
        if not section_config:
            return {}
        
        starts_with_rows = self.structure_analyzer.is_section_starts_with_rows(section_name)
        
        # Анализируем вложенность
        row_paths = []
        column_paths = []
        has_nested_rows = False
        has_nested_columns = False
        
        def traverse(path: str, config: Any, level: int = 0):
            if isinstance(config, dict):
                for key, value in config.items():
                    if key.startswith('column_'):
                        column_paths.append(f"{path}.{key}" if path else key)
                        traverse(f"{path}.{key}" if path else key, value, level + 1)
                    elif key.startswith('row_'):
                        row_paths.append(f"{path}.{key}" if path else key)
                        if level > 0:
                            has_nested_rows = True
                        traverse(f"{path}.{key}" if path else key, value, level + 1)
            elif isinstance(config, list):
                pass
        
        traverse('', section_config)
        
        # Проверяем вложенность column в row
        if starts_with_rows:
            # Если начинается с rows, проверяем есть ли column внутри
            for row_key in section_config.keys():
                if row_key.startswith('row_'):
                    row_value = section_config[row_key]
                    if isinstance(row_value, dict):
                        for col_key in row_value.keys():
                            if col_key.startswith('column_'):
                                has_nested_columns = True
                                column_paths.append(f"{row_key}.{col_key}")
        
        return {
            'starts_with': 'rows' if starts_with_rows else 'columns',
            'has_nested_rows': has_nested_rows or (not starts_with_rows and len(row_paths) > 0),
            'has_nested_columns': has_nested_columns or (starts_with_rows and len(column_paths) > 0),
            'row_paths': row_paths,
            'column_paths': column_paths
        }
    
    def validate_css_selectors(self, css_content: str, section_name: str) -> Dict[str, List[str]]:
        """
        Проверяет наличие необходимых CSS селекторов для секции
        
        Args:
            css_content: Содержимое CSS файла
            section_name: Имя секции
            
        Returns:
            {
                'missing_selectors': List[str],  # отсутствующие селекторы
                'conflicting_selectors': List[str],  # конфликтующие селекторы
                'found_selectors': List[str]  # найденные селекторы
            }
        """
        structure = self.analyze_structure(section_name)
        if not structure:
            return {'missing_selectors': [], 'conflicting_selectors': [], 'found_selectors': []}
        
        import re
        
        missing = []
        found = []
        conflicting = []
        
        # Проверяем селекторы для column (простой поиск подстроки)
        column_selector = f".layout.section-{section_name} .column"
        column_found = column_selector in css_content
        if column_found:
            found.append(column_selector)
        else:
            missing.append(column_selector)
        
        # Проверяем селекторы для row (простой поиск подстроки)
        row_selector = f".layout.section-{section_name} .row"
        row_found = row_selector in css_content
        if row_found:
            found.append(row_selector)
        else:
            missing.append(row_selector)
        
        # Проверяем специфичные селекторы если есть вложенность
        if structure['has_nested_columns']:
            nested_column_selector = f".layout.section-{section_name} .row .column"
            nested_column_found = nested_column_selector in css_content
            if nested_column_found:
                found.append(nested_column_selector)
            else:
                # Если есть вложенность, но нет специфичного селектора - проверяем базовый
                if not column_found:
                    missing.append(f"Ожидается либо {column_selector} либо {nested_column_selector}")
        
        if structure['has_nested_rows']:
            nested_row_selector = f".layout.section-{section_name} .column .row"
            nested_row_found = nested_row_selector in css_content
            if nested_row_found:
                found.append(nested_row_selector)
            else:
                # Если есть вложенность, но нет специфичного селектора - проверяем базовый
                if not row_found:
                    missing.append(f"Ожидается либо {row_selector} либо {nested_row_selector}")
        
        return {
            'missing_selectors': missing,
            'conflicting_selectors': conflicting,
            'found_selectors': found
        }
    
    def validate_all_sections(self, css_content: str) -> Dict[str, Dict[str, Any]]:
        """
        Валидирует все секции
        
        Returns:
            {
                'section_name': {
                    'structure': {...},
                    'validation': {...}
                }
            }
        """
        results = {}
        
        for section_name in self.html_config.keys():
            structure = self.analyze_structure(section_name)
            validation = self.validate_css_selectors(css_content, section_name)
            
            results[section_name] = {
                'structure': structure,
                'validation': validation
            }
        
        return results
    
    def generate_report(self, css_content: str) -> str:
        """
        Генерирует отчет о всех проблемах
        
        Returns:
            Текст отчета
        """
        results = self.validate_all_sections(css_content)
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ОТЧЕТ О ПРОВЕРКЕ СТРУКТУРЫ И CSS СЕЛЕКТОРОВ")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for section_name, data in results.items():
            structure = data['structure']
            validation = data['validation']
            
            report_lines.append(f"СЕКЦИЯ: {section_name}")
            report_lines.append("-" * 80)
            
            # Информация о структуре
            report_lines.append(f"  Структура:")
            report_lines.append(f"    - Начинается с: {structure.get('starts_with', 'unknown')}")
            report_lines.append(f"    - Есть вложенные row: {structure.get('has_nested_rows', False)}")
            report_lines.append(f"    - Есть вложенные column: {structure.get('has_nested_columns', False)}")
            
            if structure.get('row_paths'):
                report_lines.append(f"    - Пути к row: {', '.join(structure['row_paths'])}")
            if structure.get('column_paths'):
                report_lines.append(f"    - Пути к column: {', '.join(structure['column_paths'])}")
            
            report_lines.append("")
            
            # Проблемы
            if validation.get('missing_selectors'):
                report_lines.append(f"  ❌ ОТСУТСТВУЮТ СЕЛЕКТОРЫ:")
                for selector in validation['missing_selectors']:
                    report_lines.append(f"    - {selector}")
                report_lines.append("")
            
            if validation.get('found_selectors'):
                report_lines.append(f"  ✅ НАЙДЕННЫЕ СЕЛЕКТОРЫ:")
                for selector in validation['found_selectors']:
                    report_lines.append(f"    - {selector}")
                report_lines.append("")
            
            report_lines.append("")
        
        # Общие проблемы
        report_lines.append("=" * 80)
        report_lines.append("ОБЩИЕ РЕКОМЕНДАЦИИ:")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("1. Селекторы .layout.section-{name} .column должны находить ВСЕ column")
        report_lines.append("2. Селекторы .layout.section-{name} .row должны находить ВСЕ row")
        report_lines.append("3. CSS автоматически применяется ко вложенным элементам")
        report_lines.append("4. НЕ нужно создавать специфичные селекторы для вложенных элементов")
        report_lines.append("")
        
        return "\n".join(report_lines)


def main():
    """Основная функция для запуска валидатора"""
    import sys
    from pathlib import Path
    
    # Определяем пути
    current_file = Path(__file__).resolve()
    build_dir = current_file.parent.parent
    project_root = build_dir.parent
    source_dir = project_root / '2_source'
    output_dir = project_root / '3_result'
    
    # Загружаем layout_html.json
    html_config_path = source_dir / 'layout' / 'layout_html.json'
    with open(html_config_path, 'r', encoding='utf-8') as f:
        html_config = json.load(f)
    
    # Загружаем CSS из результата сборки
    css_paths = [
        output_dir / 'css' / 'style.css',
    ]
    
    css_content = ""
    css_found = False
    for css_path in css_paths:
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            print(f"✅ CSS найден: {css_path}")
            css_found = True
            break
    
    if not css_found:
        print(f"❌ CSS файл не найден. Пробовали пути:")
        for css_path in css_paths:
            print(f"   - {css_path}")
    
    # Создаем валидатор
    validator = StyleValidator(html_config)
    
    # Генерируем отчет
    report = validator.generate_report(css_content)
    
    print(report)
    
    # Сохраняем отчет
    report_path = build_dir / 'style_validation_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Отчет сохранен: {report_path}")


if __name__ == '__main__':
    main()

