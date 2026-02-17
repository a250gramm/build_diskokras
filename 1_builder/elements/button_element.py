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
        
        is_button_json = (self.value[0] == 'button_json')
        button_content = self.value[1]
        button_type = ' type="button"'  # По умолчанию type="button" чтобы не отправлять форму
        modal_attr = ''
        button_json_attr = ' data-action="button_json"' if is_button_json else ''
        button_json_config_attr = ''

        # Если 3+ параметра, проверяем что это
        if len(self.value) >= 3:
            third_param = self.value[2]

            # button_json: второй параметр — имя конфига (shino), третий — контент
            if is_button_json and isinstance(self.value[1], str) and not self.value[1].startswith('text:') and not self.value[1].startswith('icon:'):
                config_name = self.value[1]
                button_json_config_attr = f' data-button-json="{config_name}"'
                button_content = third_param
            # Если это modal:id
            elif isinstance(third_param, str) and third_param.startswith('modal:'):
                modal_id = third_param.split(':', 1)[1]
                modal_attr = f' data-modal="{modal_id}"'
            # Иначе это тип кнопки (submit, reset, button)
            elif isinstance(third_param, str) and not third_param.startswith('text:') and not third_param.startswith('icon:'):
                button_type = f' type="{third_param}"'
                if len(self.value) >= 4:
                    button_content = self.value[3]
        
        # save_bd: если в параметрах есть "save_bd", добавляем data-save-bd и data-save-bd-config
        save_bd_attr = ''
        if is_button_json and 'save_bd' in self.value:
            idx = self.value.index('save_bd')
            save_bd_config = self.value[idx + 1] if idx + 1 < len(self.value) else ''
            save_bd_attr = f' data-save-bd="1" data-save-bd-config="{save_bd_config}"'

        # Определяем тип контента
        content_html = self.resolve_content(button_content)
        
        # Добавляем ключ элемента как дополнительный класс
        css_classes = "button"
        if self.key and self.key != "button" and "_" in self.key:
            # Извлекаем имя класса из ключа (button_btn1 -> btn1)
            class_from_key = self.key.split('_', 1)[1] if self.key.startswith('button_') else self.key
            css_classes = f"button {class_from_key}"
        if is_button_json:
            css_classes = f"{css_classes} button_json"
        
        return f'<button{button_type}{modal_attr}{button_json_attr}{button_json_config_attr}{save_bd_attr} class="{css_classes}">{content_html}</button>'

