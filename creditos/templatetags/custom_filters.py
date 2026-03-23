from django import template

register = template.Library()

@register.filter
def get_user_type(user):
    """Obtiene el tipo de usuario de forma segura"""
    if not user.is_authenticated:
        return None
    try:
        return user.perfil.tipo
    except:
        return None

@register.filter
def is_student(user):
    """Verifica si el usuario es estudiante"""
    if not user.is_authenticated:
        return False
    try:
        return user.perfil.tipo == 'estudiante'
    except:
        return False

@register.filter
def is_teacher(user):
    """Verifica si el usuario es profesor"""
    if not user.is_authenticated:
        return False
    try:
        return user.perfil.tipo == 'profesor'
    except:
        return False

@register.filter
def format_credits(value):
    """Formatea números con espacios cada 3 dígitos"""
    try:
        value = int(value)
        return f"{value:,}".replace(',', ' ')
    except (ValueError, TypeError):
        return value
