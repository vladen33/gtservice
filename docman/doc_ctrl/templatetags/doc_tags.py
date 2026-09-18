from django import template
register = template.Library()

@register.filter
def file_icon_name(extension: str) -> str:
    """Возвращает id SVG-символа по расширению файла."""
    if not extension:
        return "icon-default"

    mapping = {
        ".pdf":  "icon-pdf",
        ".docx": "icon-docx",
        ".doc":  "icon-docx",
        ".xlsx": "icon-xlsx",
        ".xls":  "icon-xlsx",
        ".pptx": "icon-pptx",
        ".ppt":  "icon-pptx",
        ".txt":  "icon-txt",
        ".zip":  "icon-zip",
        ".rar":  "icon-zip",
        ".png":  "icon-png",
        ".jpg":  "icon-jpg",
        ".jpeg": "icon-jpg",
        ".csv":  "icon-csv",
    }

    return mapping.get(extension.lower(), "icon-default")


@register.filter
def file_ext_class(extension: str) -> str:
    if not extension:
        return ""
    ext = extension.lower().lstrip(".")
    return f"file-ext-{ext}"