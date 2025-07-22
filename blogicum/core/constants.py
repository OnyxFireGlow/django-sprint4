"""
Модуль для хранения общих констант проекта.

Определяет стандартные значения, используемые в различных частях приложения:
- FIELD_LENGTHS: Словарь с длинами полей для моделей
  - TITLE: Максимальная длина заголовков (256 символов)
  - SHORT_DESCRIPTION: Максимальная длина кратких описаний (500 символов)
  - SLUG: Максимальная длина идентификаторов (100 символов)

Использование:
from core.constants import FIELD_LENGTHS

title = models.CharField(max_length=FIELD_LENGTHS['TITLE'])
"""

FIELD_LENGTHS = {
    'TITLE': 256,
    'SHORT_DESCRIPTION': 500,
    'SLUG': 100,
}
