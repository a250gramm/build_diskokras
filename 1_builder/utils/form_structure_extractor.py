#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Извлечение структуры форм из objects.json для генерации JSON-шаблонов.
"""

import re
from typing import Dict, Any, List
from .element_utils import parse_html_tag


def _is_input_or_field_value(value: Any) -> bool:
    """Проверяет, является ли значение полем ввода (input/field)."""
    if not isinstance(value, list) or len(value) < 2:
        return False
    first = value[0]
    return first in ('input', 'field')


def _path_to_field_name(full_path: str) -> str:
    """Преобразует полный путь элемента в имя поля для name/JSON (точки → подчёркивания)."""
    return full_path.replace('.', '_')


def _collect_fields_inside(
    data: Dict,
    base_path: str,
    fields: Dict[str, str],
    form_prefix: str = "",
) -> None:
    """
    Рекурсивно собирает все поля ввода внутри data, записывает в fields.
    base_path — путь от корня формы. form_prefix — полный путь до формы (для совпадения с name в HTML).
    """
    for key, value in data.items():
        if key == 'if':
            if isinstance(value, dict):
                for sub_data in value.values():
                    if isinstance(sub_data, dict):
                        _collect_fields_inside(sub_data, base_path, fields, form_prefix)
                    elif isinstance(sub_data, list) and len(sub_data) >= 4 and isinstance(sub_data[3], dict):
                        _collect_fields_inside(sub_data[3], base_path, fields, form_prefix)
            continue

        if isinstance(value, list):
            if _is_input_or_field_value(value):
                path_key = f"{base_path}.{key}" if base_path else key
                full_path = f"{form_prefix}.{path_key}" if form_prefix else path_key
                name = _path_to_field_name(full_path)
                fields[name] = ""
            continue

        if isinstance(value, dict):
            sub_path = f"{base_path}.{key}" if base_path else key
            _collect_fields_inside(value, sub_path, fields, form_prefix)


def _extract_forms_from_section(section_data: Dict, section_key: str) -> Dict[str, Dict[str, str]]:
    """
    Из одной секции (блока objects) извлекает все блоки form_* и поля внутри.
    form_prefix = путь до формы (section.form_form1), чтобы имена полей совпадали с name в HTML.
    """
    result = {}

    def walk(data: Dict, path: str) -> None:
        for key, value in data.items():
            if key == 'if':
                if isinstance(value, dict):
                    for cond, branch in value.items():
                        if isinstance(branch, dict):
                            walk(branch, path)
                        elif isinstance(branch, list) and len(branch) >= 4 and isinstance(branch[3], dict):
                            # Путь к модалке как в рендере: path.btn_modal.modal
                            modal_path = f"{path}.{branch[0]}.modal" if path else f"{branch[0]}.modal"
                            walk(branch[3], modal_path)
                continue

            # Ветка if даёт объект { "btn_modal": [ ..., modal_dict ] } — заходим в модалку
            if isinstance(value, list) and len(value) >= 4 and isinstance(value[3], dict):
                modal_path = f"{path}.{key}.modal" if path else f"{key}.modal"
                walk(value[3], modal_path)
                continue

            tag_info = parse_html_tag(key) if isinstance(key, str) else None
            if tag_info:
                tag_name, class_name, _ = tag_info
                if tag_name == 'form' and class_name:
                    form_prefix = f"{path}.{key}" if path else key
                    form_fields = {}
                    if isinstance(value, dict):
                        _collect_fields_inside(value, "", form_fields, form_prefix)
                    result[class_name] = {**result.get(class_name, {}), **form_fields}
                    continue

            if isinstance(value, dict):
                sub_path = f"{path}.{key}" if path else key
                walk(value, sub_path)

    walk(section_data, section_key)
    return result


def _collect_forms_with_button_json(data: Dict, path: str, current_form_class: str,
                                    result: set) -> None:
    """
    Рекурсивно ищет внутри data кнопки с типом button_json.
    Если находит — добавляет current_form_class в result.
    """
    for key, value in data.items():
        if key == 'if':
            if isinstance(value, dict):
                for branch in value.values():
                    if isinstance(branch, dict):
                        _collect_forms_with_button_json(branch, path, current_form_class, result)
                    elif isinstance(branch, list) and len(branch) >= 4 and isinstance(branch[3], dict):
                        _collect_forms_with_button_json(branch[3], path, current_form_class, result)
            continue

        if isinstance(value, list) and len(value) >= 1 and value[0] == 'button_json':
            if current_form_class:
                result.add(current_form_class)
            continue

        if isinstance(value, list) and len(value) >= 4 and isinstance(value[3], dict):
            _collect_forms_with_button_json(value[3], path, current_form_class, result)
            continue

        if isinstance(value, dict):
            tag_info = parse_html_tag(key) if isinstance(key, str) else None
            form_class = None
            if tag_info:
                tag_name, class_name, _ = tag_info
                if tag_name == 'form' and class_name:
                    form_class = class_name
            _collect_forms_with_button_json(
                value, path, form_class if form_class else current_form_class, result
            )


def forms_with_button_json(sections: Dict[str, Any]) -> set:
    """
    Возвращает множество имён классов форм (form1, form2, ...), внутри которых есть кнопка button_json.

    Args:
        sections: configs['sections'] — объекты из objects.json

    Returns:
        Множество строк, например {"form2"}.
    """
    result = set()
    for section_key, section_data in sections.items():
        if not isinstance(section_data, dict):
            continue
        _collect_forms_with_button_json(section_data, section_key, '', result)
    return result


def extract_forms_structure(sections: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Извлекает структуру всех форм из objects (sections).
    
    Args:
        sections: configs['sections'] — объекты из objects.json
        
    Returns:
        Словарь { "form1": { "input": "" }, "form2": { "field": "", "field_2": "", ... } }
        Ключ — класс формы (form1, form2), значение — шаблон полей для JSON.
    """
    merged: Dict[str, Dict[str, str]] = {}
    for section_key, section_data in sections.items():
        if not isinstance(section_data, dict):
            continue
        forms = _extract_forms_from_section(section_data, section_key)
        for form_class, fields in forms.items():
            merged[form_class] = {**merged.get(form_class, {}), **fields}
    return merged
