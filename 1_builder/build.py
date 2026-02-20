#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный скрипт сборки DISKOKRAS (NEW_build)
"""

import sys
import os
import shutil
from pathlib import Path

# Предотвращаем создание __pycache__
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from loaders.config_loader import ConfigLoader
from core.config_manager import ConfigManager
from generators.section_generator import SectionGenerator
from generators.page_generator import PageGenerator
from generators.css_generator import CSSGenerator
from generators.form_json_generator import FormJsonGenerator


SOURCE_DIR_NAME = '2_source'
OUTPUT_DIR_NAME = '3_result'


def main():
    """Главная функция сборки"""
    
    # Определяем пути
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent  # корень проекта (build_diskokras)
    source_dir = project_root / SOURCE_DIR_NAME
    output_dir = project_root / OUTPUT_DIR_NAME
    
    print("=" * 60)
    print("🚀 СБОРКА DISKOKRAS (NEW_build)")
    print("=" * 60)
    print(f"📁 Исходники: {source_dir}")
    print(f"📁 Результат: {output_dir}")
    print()
    
    try:
        # Удаляем старую директорию результата для чистой сборки (если не удалось — перезаписываем файлы)
        if output_dir.exists():
            print("🗑️  Удаление старого результата...")
            try:
                shutil.rmtree(output_dir)
                print("   ✅ Старый результат удален")
            except OSError as e:
                print(f"   ⚠️  Не удалось удалить (перезаписываем): {e}")
            print()
        
        # Создаем директории для результата
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / 'pages').mkdir(exist_ok=True)
        (output_dir / 'sections').mkdir(exist_ok=True)
        (output_dir / 'css').mkdir(exist_ok=True)
        (output_dir / 'js').mkdir(exist_ok=True)
        (output_dir / 'img').mkdir(exist_ok=True)
        (output_dir / 'php').mkdir(exist_ok=True)
        (output_dir / 'bd_local').mkdir(exist_ok=True)
        (output_dir / 'button_json').mkdir(exist_ok=True)
        (output_dir / 'data').mkdir(exist_ok=True)
        (output_dir / 'data' / 'tmp').mkdir(exist_ok=True)

        # Копируем конфиги button_json (shino.json, result.json и т.д.)
        source_button_json_dir = source_dir / 'button_json'
        output_button_json_dir = output_dir / 'button_json'
        if source_button_json_dir.exists():
            print("📦 Копирование конфигов button_json...")
            for json_file in source_button_json_dir.glob('*.json'):
                if json_file.is_file():
                    shutil.copy2(json_file, output_button_json_dir / json_file.name)
            count = len(list(output_button_json_dir.glob('*.json')))
            if count:
                print(f"   ✅ Скопировано файлов: {count}")
            print()

        # Копируем конфиги save_bd (shino2.json, include.json, run_create_price.php и т.д.)
        source_save_bd_dir = source_dir / 'save_bd'
        output_save_bd_dir = output_dir / 'save_bd'
        if source_save_bd_dir.exists():
            output_save_bd_dir.mkdir(exist_ok=True)
            print("📦 Копирование конфигов save_bd...")
            for json_file in source_save_bd_dir.glob('*.json'):
                if json_file.is_file():
                    shutil.copy2(json_file, output_save_bd_dir / json_file.name)
            for php_file in source_save_bd_dir.glob('*.php'):
                if php_file.is_file():
                    shutil.copy2(php_file, output_save_bd_dir / php_file.name)
            for sql_file in source_save_bd_dir.glob('*.sql'):
                if sql_file.is_file():
                    shutil.copy2(sql_file, output_save_bd_dir / sql_file.name)
            count = len(list(output_save_bd_dir.iterdir()))
            if count:
                print(f"   ✅ Скопировано файлов: {count}")
            print()

        # Копируем изображения
        source_img_dir = source_dir / 'img'
        output_img_dir = output_dir / 'img'
        if source_img_dir.exists():
            print("🖼️  Копирование изображений...")
            for img_file in source_img_dir.iterdir():
                if img_file.is_file():
                    shutil.copy2(img_file, output_img_dir / img_file.name)
            print(f"   ✅ Изображения скопированы")
            print()
        
        # Копируем и объединяем JS файлы
        source_js_dir = source_dir / 'js'
        output_js_file = output_dir / 'js' / 'script.js'
        if source_js_dir.exists():
            print("📜 Обработка JavaScript...")
            js_content = []
            for js_file in sorted(source_js_dir.glob('*.js')):
                if js_file.is_file():
                    js_content.append(f"// {js_file.name}\n")
                    js_content.append(js_file.read_text(encoding='utf-8'))
                    js_content.append("\n\n")
            
            if js_content:
                output_js_file.write_text(''.join(js_content), encoding='utf-8')
                print(f"   ✅ JS создан")
            print()
        
        # Копируем JSON файлы из bd_local
        source_bd_dir = source_dir / 'bd_local'
        output_bd_dir = output_dir / 'bd_local'
        if source_bd_dir.exists():
            print("💾 Копирование JSON из базы данных...")
            for json_file in source_bd_dir.glob('*.json'):
                if json_file.is_file():
                    shutil.copy2(json_file, output_bd_dir / json_file.name)
            print(f"   ✅ JSON файлы скопированы")
            print()
        
        # Копируем PHP скрипты
        source_php_dir = source_dir / 'php'
        output_php_dir = output_dir / 'php'
        if source_php_dir.exists():
            print("🐘 Копирование PHP скриптов...")
            for php_file in source_php_dir.glob('*.php'):
                if php_file.is_file():
                    shutil.copy2(php_file, output_php_dir / php_file.name)
            # view_table.php — в owner/bd/ для просмотра таблиц
            view_table = source_php_dir / 'view_table.php'
            if view_table.is_file():
                (output_dir / 'owner' / 'bd').mkdir(parents=True, exist_ok=True)
                dest = output_dir / 'owner' / 'bd' / 'view_table.php'
                shutil.copy2(view_table, dest)
                # путь к include для owner/bd (на 2 уровня выше)
                content = dest.read_text(encoding='utf-8')
                content = content.replace("__DIR__ . '/../save_bd/", "__DIR__ . '/../../save_bd/")
                dest.write_text(content, encoding='utf-8')
            print(f"   ✅ PHP скрипты скопированы")
            print()
        
        # Копируем JSON файлы из базы данных
        source_bd_dir = source_dir / 'bd_local'
        output_bd_dir = output_dir / 'bd_local'
        if source_bd_dir.exists():
            print("💾 Копирование данных БД...")
            for json_file in source_bd_dir.glob('*.json'):
                if json_file.is_file():
                    shutil.copy2(json_file, output_bd_dir / json_file.name)
            print(f"   ✅ Данные БД скопированы")
            print()
        
        # ЭТАП 1: Загрузка конфигураций
        print("📋 Загрузка конфигураций...")
        config_loader = ConfigLoader(source_dir)
        configs = config_loader.load_all()
        print("   ✅ Конфиги загружены")
        print()
        
        # ЭТАП 2: Создание ConfigManager
        print("⚙️  Инициализация менеджера конфигураций...")
        config_manager = ConfigManager(configs)
        try:
            config_manager.validate()
            print(f"   ✅ Найдено страниц: {len(config_manager.pages)}")
            print(f"   ✅ Найдено секций: {len(config_manager.sections)}")
            print()
        except Exception as e:
            print(f"   ❌ Ошибка валидации: {e}")
            raise
        
        # ЭТАП 3: Генерация секций
        print("📄 Генерация секций...")
        section_gen = SectionGenerator(config_manager, source_dir)
        sections_html = section_gen.generate_all()
        section_gen.save_all(sections_html, output_dir / 'sections')
        print(f"   ✅ Создано секций: {len(sections_html)} (включая дубликаты)")
        print()
        
        # ЭТАП 4: Генерация страниц
        print("📑 Генерация страниц...")
        from datetime import datetime
        build_version = datetime.now().strftime('%Y%m%d%H%M')
        page_gen = PageGenerator(config_manager, sections_html, source_dir, build_version=build_version)
        pages_html = page_gen.generate_all()
        page_gen.save_all(pages_html, output_dir / 'pages')
        print(f"   ✅ Создано страниц: {len(pages_html)}")

        # Корневой index.html — перенаправление на главную (чтобы / загружал страницу с верными путями к CSS/JS)
        root_index = output_dir / 'index.html'
        root_index.write_text(
            '<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">'
            '<meta http-equiv="refresh" content="0;url=pages/index.html">'
            '<title>DISKOKRAS CRM</title>'
            '<script>location.replace("pages/index.html");</script>'
            '</head><body><p><a href="pages/index.html">Перейти на главную</a></p></body></html>',
            encoding='utf-8'
        )
        print("   ✅ Корневой index.html (редирект на pages/index.html)")
        print()
        
        # ЭТАП 5: Генерация CSS
        print("🎨 Генерация CSS...")
        css_gen = CSSGenerator(configs)
        css_content = css_gen.generate(source_dir)
        css_file = output_dir / 'css' / 'style.css'
        
        # Статистика CSS
        css_size = len(css_content)
        has_report = 'ОТЛАДОЧНЫЕ' in css_content
        
        print(f"   📏 Размер CSS: {css_size} символов")
        print(f"   🔍 Отладочные стили: {'✅ включены' if has_report else '❌ выключены'}")
        
        # Сохраняем CSS
        css_gen.save(css_content, css_file)
        print("   ✅ CSS создан")
        print()

        # ЭТАП 6: JSON-шаблоны форм (для сохранения данных после отправки)
        print("📋 Генерация JSON-шаблонов форм...")
        form_gen = FormJsonGenerator(configs)
        form_files = form_gen.generate(output_dir)
        if form_files:
            print(f"   ✅ Создано файлов форм: {len(form_files)}")
            for form_class, fp in form_files.items():
                print(f"      — {fp.name}")
        else:
            print("   (форм с button_json не найдено)")
        print()

        # Итоги
        print("=" * 60)
        print("✅ СБОРКА ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 60)
        print(f"📊 Создано страниц: {len(pages_html)}")
        print(f"📊 Создано секций: {len([k for k in sections_html.keys() if not k.startswith('sec_')])}")
        print(f"📁 Результаты в: {output_dir}")
        print()
        
    except Exception as e:
        print(f"\n❌ Ошибка сборки: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
