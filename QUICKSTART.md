# 🚀 Guía Rápida de Inicio

## Activar el Entorno Virtual

### Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

### Windows (CMD):
```cmd
venv\Scripts\activate.bat
```

### macOS/Linux:
```bash
source venv/bin/activate
```

## Iniciar la Aplicación

```bash
# Aplicar migraciones (primera vez)
python manage.py migrate

# Crear datos de prueba (primera vez)
python manage.py init_data

# Iniciar el servidor
python manage.py runserver
```

## Acceder a la Aplicación

- **Sitio web:** http://localhost:8000
- **Admin:** http://localhost:8000/admin

## Usuarios de Prueba

### Estudiante:
- Usuario: **Est1** (o Est2, Est3, Est4, Est5)
- Contraseña: **1234**

### Profesor:
- Usuario: **profesor1**
- Contraseña: **1234**

## Acciones Disponibles

### Para Estudiantes:
1. Ir a "Inicio"
2. Elegir una opción:
   - 📝 Enviar rectificación
   - 📚 Enviar ejercicio CP (con PDF)
   - 😂 Compartir meme (con imagen)
3. Completar el formulario y enviar
4. Ver ranking y créditos en tiempo real

### Para Profesores:
1. Ir a "Panel de Profesor"
2. Ver envíos pendientes por tipo
3. Hacer clic en un envío para revisarlo
4. Decidir si aceptar o rechazar
5. Asignar créditos
6. Guardar revisión

## URLs Principales

| URL | Descripción |
|-----|-------------|
| `/` | Login |
| `/estudiante/` | Inicio del estudiante |
| `/estudiante/rectificacion/` | Enviar rectificación |
| `/estudiante/cp/` | Enviar CP |
| `/estudiante/meme/` | Enviar meme |
| `/estudiante/historial/` | Historial de envíos |
| `/profesor/` | Panel del profesor |
| `/profesor/revisar/<id>/` | Revisar un envío |
| `/profesor/historial/` | Historial de revisiones |
| `/admin/` | Panel de administración |

## Solución de Problemas

### El servidor no inicia
- Verifica que el puerto 8000 esté disponible
- Intenta con otro puerto: `python manage.py runserver 8001`

### Error de "No such table"
- Ejecuta: `python manage.py migrate`

### No se pueden subir archivos
- Verifica que exista la carpeta `media/`
- Crea la carpeta si no existe

## Testing

Para interactuar en la shell de Django:
```bash
python manage.py shell
```

Ejemplos útiles:
```python
from creditos.models import Perfil, Envio
from django.contrib.auth.models import User

# Ver todos los usuarios
User.objects.all()

# Ver todos los envíos
Envio.objects.all()

# Ver créditos de un estudiante
Perfil.objects.filter(tipo='estudiante')
```

---

¡Estás listo para usar el sistema de créditos! 🎉
