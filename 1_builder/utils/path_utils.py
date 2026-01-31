#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PathUtils - Утилиты для работы с путями
"""

from pathlib import Path
from typing import Tuple


class PathUtils:
    """Утилиты для работы с путями проекта"""
    
    @staticmethod
    def get_project_paths() -> Tuple[Path, Path, Path]:
        """
        Вычисляет пути проекта
        
        Returns:
            (source_dir, build_dir, output_dir)
        """
        # Путь к текущему скрипту
        current_file = Path(__file__).absolute()
        
        # build (1_builder) находится в родительской директории utils/
        build_dir = current_file.parent.parent
        project_root = build_dir.parent
        
        # Исходники и результат
        source_dir = project_root / '2_source'
        output_dir = project_root / '3_result'
        
        return source_dir, build_dir, output_dir
    
    @staticmethod
    def page_path_to_name(page_path: str) -> str:
        """
        Преобразует путь страницы в имя файла
        
        Args:
            page_path: Путь типа "/index" или "/shino"
            
        Returns:
            Имя файла типа "index.html" или "shino.html"
        """
        page_name = page_path.lstrip('/')
        if page_name == 'index' or not page_name:
            return 'index.html'
        return f"{page_name}.html"
    
    @staticmethod
    def page_name_to_path(page_name: str) -> str:
        """
        Преобразует имя страницы в путь
        
        Args:
            page_name: Имя типа "index" или "shino"
            
        Returns:
            Путь типа "/index" или "/shino"
        """
        if page_name == 'index':
            return '/index'
        return f"/{page_name}"

