#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Кастомные исключения для сборщика
"""


class BuilderException(Exception):
    """Базовое исключение для сборщика"""
    pass


class ConfigurationError(BuilderException):
    """Ошибка конфигурации"""
    pass


class ValidationError(BuilderException):
    """Ошибка валидации"""
    pass


class ProcessingError(BuilderException):
    """Ошибка обработки"""
    pass


class ElementNotFoundError(ProcessingError):
    """Элемент не найден"""
    pass


class TemplateError(ProcessingError):
    """Ошибка обработки шаблона"""
    pass


class DatabaseError(ProcessingError):
    """Ошибка работы с базой данных"""
    pass

