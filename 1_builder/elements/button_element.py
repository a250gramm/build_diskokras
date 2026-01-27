#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Элемент кнопки
"""

from .base_element import BaseElement


class ButtonElement(BaseElement):
    """Элемент кнопки"""
    
    def render(self) -> str:
        """
        Генерирует HTML для кнопки
        
        Формат с текстом: ["button", "text:Найти"]
        Формат с иконкой: ["button", "icon:grid_3x3"]
        Формат с модалкой: ["button", "text:Создать", "modal:modal1", {...}]
        Формат с типом: ["button", "submit", "text:Отправить"]
        
        Генерирует: <button>Найти</button> или <button data-modal="modal1">...</button>
        """
        if not isinstance(self.value, list) or len(self.value) < 2:
            return ''
        
        button_content = self.value[1]
        button_type = ' type="button"'  # По умолчанию type="button" чтобы не отправлять форму
        modal_attr = ''
        
        # Если 3+ параметра, проверяем что это
        if len(self.value) >= 3:
            third_param = self.value[2]
            
            # Если это modal:id
            if isinstance(third_param, str) and third_param.startswith('modal:'):
                modal_id = third_param.split(':', 1)[1]
                modal_attr = f' data-modal="{modal_id}"'
            # Иначе это тип кнопки (submit, reset, button)
            elif isinstance(third_param, str) and not third_param.startswith('text:') and not third_param.startswith('icon:'):
                button_type = f' type="{third_param}"'
                if len(self.value) >= 4:
                    button_content = self.value[3]
        
        # Определяем тип контента
        content_html = self.resolve_content(button_content)
        
        # Добавляем ключ элемента как дополнительный класс
        css_classes = "button"
        if self.key and self.key != "button" and "_" in self.key:
            # Извлекаем имя класса из ключа (button_btn1 -> btn1)
            class_from_key = self.key.split('_', 1)[1] if self.key.startswith('button_') else self.key
            css_classes = f"button {class_from_key}"
        
        return f'<button{button_type}{modal_attr} class="{css_classes}">{content_html}</button>'

