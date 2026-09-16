import logging

from django.core.exceptions import ValidationError

from .constants import MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)


def validate_doc_file(file):
    import os
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        message = f'Максимальный размер файла — {MAX_FILE_SIZE_MB} МБ'
        logger.error(message)
        raise ValidationError(message)