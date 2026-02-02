#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор JSON-шаблонов форм для 3_result.
После отправки формы данные пользователя можно сохранять в эти файлы.
"""

import json
from pathlib import Path
from typing import Dict, Any

from utils.form_structure_extractor import extract_forms_structure


class FormJsonGenerator:
    """Генерирует JSON-шаблоны структур форм в 3_result."""

    def __init__(self, configs: Dict[str, Any]):
        """
        Args:
            configs: Загруженные конфиги (должны быть 'sections' и опционально 'send_form').
        """
        self.configs = configs
        self.sections = configs.get('sections', {})
        self.send_form = configs.get('send_form', {})

    def generate(self, output_dir: Path) -> Dict[str, Path]:
        """
        Извлекает структуру форм из objects и записывает JSON-файлы в output_dir.

        Args:
            output_dir: Директория результата (3_result).

        Returns:
            Словарь { form_class: путь_к_файлу }.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        forms = extract_forms_structure(self.sections)
        written = {}

        for form_class, fields in forms.items():
            if not fields:
                continue
            # Имя файла: из send_form[form_id].output или по умолчанию form_{form_class}_data.json
            filename = f"form_{form_class}_data.json"
            for form_id, form_config in self.send_form.items():
                if isinstance(form_config, dict) and form_config.get('form_class') == form_class:
                    filename = form_config.get('output', filename)
                    break
            file_path = output_dir / filename
            file_path.write_text(json.dumps(fields, ensure_ascii=False, indent=2), encoding='utf-8')
            written[form_class] = file_path

        return written
