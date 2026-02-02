#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Элемент поля ввода
"""

from .base_element import BaseElement


class FieldElement(BaseElement):
    """Элемент поля ввода"""
    
    def render(self) -> str:
        """
        Генерирует HTML для поля ввода
        
        Старый формат: ["field", "Поиск заказа", "form"]
        Новый формат: ["input", "text", "Поиск заказа", "form"]
        
        Генерирует: <input type="text" placeholder="Поиск заказа" class="field" data-form="form">
        """
        if not isinstance(self.value, list) or len(self.value) < 2:
            return ''
        
        element_type = self.value[0]
        
        # Новый формат: ["input", "text:Placeholder"] или ["input", "checkbox"]
        if element_type == 'input' and len(self.value) == 2:
            param2 = self.value[1]
            
            # Если есть двоеточие, то формат "type:placeholder"
            if isinstance(param2, str) and ':' in param2:
                input_type, placeholder = param2.split(':', 1)
                
                # Добавляем класс из ключа
                css_class = "field"
                if self.key:
                    css_class = f"field {self.key}"
                
                # name для формы (совпадает с ключами в JSON-шаблоне)
                name_attr = self._get_name_attr()
                
                # Проверяем есть ли функция в контексте
                function_attr = ''
                if self.context and 'function' in self.context:
                    func_info = self.context['function']
                    result_var = func_info.get('result', '')
                    if result_var:
                        function_attr = f' data-function-sum="{result_var}"'
                
                # Для checkbox/radio создаём label
                if input_type in ['checkbox', 'radio']:
                    return f'<label><input type="{input_type}" class="{css_class}"{name_attr}>{placeholder}</label>'
                # Для обычных полей используем placeholder
                else:
                    return f'<input type="{input_type}" placeholder="{placeholder}" class="{css_class}"{name_attr}{function_attr}>'
            else:
                # Формат без двоеточия - просто type (например "checkbox")
                input_type = param2
                return f'<input type="{input_type}" class="field">'
        
        # Новый формат: ["input", "text", "Поиск заказа", "form"]
        if element_type == 'input' and len(self.value) >= 3:
            input_type = self.value[1]  # text, number, email, password, checkbox, radio и т.д.
            placeholder_raw = self.value[2]
            
            # Парсим формат "text:значение"
            content = placeholder_raw
            if isinstance(placeholder_raw, str) and ':' in placeholder_raw:
                content_type, content_value = placeholder_raw.split(':', 1)
                if content_type == 'text':
                    content = content_value
            
            data_attrs = ''
            
            # Обрабатываем 4-й параметр (data-form или data-toggle)
            if len(self.value) > 3:
                param4 = self.value[3]
                if isinstance(param4, str):
                    if param4.startswith('toggle:'):
                        toggle_target = param4.split(':', 1)[1]
                        data_attrs = f' data-toggle="{toggle_target}"'
                    else:
                        data_attrs = f' data-form="{param4}"'
            
            # Добавляем класс из ключа для идентификации поля
            css_class = "field"
            if self.key:
                css_class = f"field {self.key}"
            
            # name для формы (совпадает с ключами в JSON-шаблоне)
            name_attr = self._get_name_attr()
            
            # Для checkbox и radio создаём label
            if input_type in ['checkbox', 'radio']:
                return f'<label><input type="{input_type}" class="{css_class}"{name_attr}{data_attrs}>{content}</label>'
            # Для обычных полей используем placeholder
            else:
                return f'<input type="{input_type}" placeholder="{content}" class="{css_class}"{name_attr}{data_attrs}>'
        
        # Старый формат: ["field", "Поиск заказа", "form"] - для обратной совместимости
        else:
            placeholder = self.value[1]
            data_form = ''
            
            if len(self.value) > 2:
                form_id = self.value[2]
                data_form = f' data-form="{form_id}"'
            
            name_attr = self._get_name_attr()
            return f'<input type="text" placeholder="{placeholder}" class="field"{name_attr}{data_form}>'

    def _get_name_attr(self) -> str:
        """Возвращает атрибут name для поля формы (путь с точками → подчёркивания)."""
        path = self.context.get('element_path') if self.context else None
        if not path:
            path = self.key or 'field'
        name = path.replace('.', '_')
        return f' name="{name}"' if name else ''
