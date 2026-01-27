#!/bin/bash
# Скрипт для сборки проекта DISKOKRAS
# Берет исходники из 2_source, использует сборщик из 1_builder, сохраняет результат в 3_result

set -e  # Остановка при ошибке

# Определяем пути
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/2_source"
BUILDER_DIR="${SCRIPT_DIR}/1_builder"
OUTPUT_DIR="${SCRIPT_DIR}/3_result"

echo "============================================================"
echo "🚀 СБОРКА DISKOKRAS"
echo "============================================================"
echo "📁 Исходники: ${SOURCE_DIR}"
echo "📁 Сборщик: ${BUILDER_DIR}"
echo "📁 Результат: ${OUTPUT_DIR}"
echo ""

# Проверяем наличие директорий
if [ ! -d "${SOURCE_DIR}" ]; then
    echo "❌ Ошибка: Директория исходников не найдена: ${SOURCE_DIR}"
    exit 1
fi

if [ ! -d "${BUILDER_DIR}" ]; then
    echo "❌ Ошибка: Директория сборщика не найдена: ${BUILDER_DIR}"
    exit 1
fi

# Переходим в директорию сборщика
cd "${BUILDER_DIR}"

# Запускаем сборщик с правильными путями через Python
python3 << EOF
import sys
import os
import shutil
from pathlib import Path

# Предотвращаем создание __pycache__
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Добавляем путь к модулям
sys.path.insert(0, '${BUILDER_DIR}')

from loaders.config_loader import ConfigLoader
from core.config_manager import ConfigManager
from generators.section_generator import SectionGenerator
from generators.page_generator import PageGenerator
from generators.css_generator import CSSGenerator

# Определяем пути
source_dir = Path('${SOURCE_DIR}')
output_dir = Path('${OUTPUT_DIR}')

print("=" * 60)
print("🚀 СБОРКА DISKOKRAS (NEW_build)")
print("=" * 60)
print(f"📁 Исходники: {source_dir}")
print(f"📁 Результат: {output_dir}")
print()

try:
    # Удаляем старую директорию результата для чистой сборки
    if output_dir.exists():
        print("🗑️  Удаление старого результата...")
        shutil.rmtree(output_dir)
        print("   ✅ Старый результат удален")
        print()
    
    # Создаем директории для результата
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'pages').mkdir(exist_ok=True)
    (output_dir / 'sections').mkdir(exist_ok=True)
    (output_dir / 'css').mkdir(exist_ok=True)
    (output_dir / 'js').mkdir(exist_ok=True)
    (output_dir / 'img').mkdir(exist_ok=True)
    (output_dir / 'php').mkdir(exist_ok=True)
    (output_dir / 'bd').mkdir(exist_ok=True)
    
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
    
    # Копируем JSON файлы из bd
    source_bd_dir = source_dir / 'bd'
    output_bd_dir = output_dir / 'bd'
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
        print(f"   ✅ PHP скрипты скопированы")
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
    page_gen = PageGenerator(config_manager, sections_html, source_dir)
    pages_html = page_gen.generate_all()
    page_gen.save_all(pages_html, output_dir / 'pages')
    print(f"   ✅ Создано страниц: {len(pages_html)}")
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
EOF

echo "✅ Скрипт завершен успешно!"

