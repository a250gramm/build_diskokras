#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор JSON для форм в 3_result.
Создаёт только form_*_db_paths.json для форм с кнопкой button_json.
"""

from pathlib import Path
from typing import Dict, Any

from utils.form_structure_extractor import forms_with_button_json


class FormJsonGenerator:
    """Генерирует JSON для форм в 3_result (только db_paths для форм с button_json)."""

    def __init__(self, configs: Dict[str, Any]):
        """
        Args:
            configs: Загруженные конфиги (должны быть 'sections').
        """
        self.configs = configs
        self.sections = configs.get('sections', {})

    def generate(self, output_dir: Path) -> Dict[str, Path]:
        """
        Для форм с кнопкой button_json создаёт пустой JSON (описание путей в БД) в output_dir.

        Args:
            output_dir: Директория результата (3_result).

        Returns:
            Словарь { form_class_db_paths: путь_к_файлу }.
        """
        output_dir = Path(output_dir)
        send_form_dir = output_dir / 'send_form_json'
        send_form_dir.mkdir(parents=True, exist_ok=True)
        written = {}

        # Для форм с кнопкой button_json создаём пустой JSON — описание будущих путей в БД
        for form_class in forms_with_button_json(self.sections):
            db_paths_filename = f"form_{form_class}_db_paths.json"
            db_paths_path = send_form_dir / db_paths_filename
            db_paths_path.write_text("{}", encoding='utf-8')
            written[f"{form_class}_db_paths"] = db_paths_path

        return written
