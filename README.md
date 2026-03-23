# 📚 Sistema de Gestión de Créditos

Un sistema web desarrollado con Django que permite a estudiantes enviar rectificaciones de ejercicios, ejercicios CP y memes, mientras que los profesores pueden revisar y otorgar créditos.

## 🌟 Características

### Para Estudiantes:
- 📝 Enviar rectificaciones de ejercicios con contexto
- 📚 Enviar ejercicios CP con adjuntos PDF
- 😂 Compartir memes para ganar créditos
- 💰 Ver sus créditos y posición en el ranking
- 📋 Ver historial de envíos y su estado

### Para Profesores:
- ✅ Revisar envíos pendientes de estudiantes
- 🏆 Asignar créditos a los envíos
- 📊 Ver estadísticas y historial de revisiones
- 🎯 Gestionar valores por defecto de créditos para CP

## 📦 Requisitos

- Python 3.11+
- Django 6.0.3
- Pillow (para manejo de imágenes)

## 🚀 Instalación y Uso

### 1. Activar el Entorno Virtual

```bash
# En Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# En Windows (CMD)
venv\Scripts\activate.bat

# En macOS/Linux
source venv/bin/activate
```

### 2. Inicializar la Base de Datos

```bash
# Aplicar migraciones
python manage.py migrate

# Crear datos de prueba (usuarios y valores de CP)
python manage.py init_data
```

### 3. Ejecutar el Servidor

```bash
python manage.py runserver
```

Accede a `http://localhost:8000` en tu navegador.

## 👥 Usuarios de Prueba

### Estudiante:
- **Usuario:** Est1 (o Est2, Est3, Est4, Est5)
- **Contraseña:** 1234

### Profesor:
- **Usuario:** profesor1
- **Contraseña:** 1234

## 📁 Estructura del Proyecto

```
.
├── creditos/                    # Aplicación principal
│   ├── migrations/             # Migraciones de base de datos
│   ├── management/commands/    # Comandos personalizados
│   ├── templates/creditos/     # Plantillas HTML
│   ├── models.py              # Modelos de Django
│   ├── views.py               # Vistas principales
│   ├── forms.py               # Formularios
│   ├── urls.py                # URLs de la app
│   └── admin.py               # Configuración de admin
├── myproject/                 # Configuración del proyecto
│   ├── settings.py           # Configuración
│   ├── urls.py               # URLs principales
│   └── wsgi.py               # Configuración WSGI
├── manage.py                 # Script de management
└── requirements.txt          # Dependencias
```

## 🗄️ Modelos de Base de Datos

### Perfil
Perfil extendido del usuario para diferenciar estudiantes de profesores.
- `usuario`: OneToOne con User
- `tipo`: 'estudiante' o 'profesor'
- `creditos`: Número de créditos acumulados

### Envio
Registro de envíos de estudiantes.
- `estudiante`: ForeignKey a User
- `tipo`: 'rectificacion', 'cp' o 'meme'
- `descripcion`: Descripción general
- `fecha_envio`: Timestamp
- `aceptado`: None (pendiente), True (aceptado), False (rechazado)
- `creditos_otorgados`: Créditos asignados

### Revision
Revisión realizada por un profesor.
- `envio`: OneToOne con Envio
- `profesor`: ForeignKey a User
- `aceptado`: Boolean
- `creditos_otorgados`: Créditos asignados
- `comentarios`: Comentarios opcionales
- `fecha_revision`: Timestamp

### ValorCP
Valores por defecto de créditos para cada inciso de CP.
- `numero_cp`: Identificador del CP
- `numero_inciso`: Identificador del inciso
- `valor_defecto`: Créditos por defecto

## 🎯 Flujo de Trabajo

1. **Estudiante Envía:**
   - El estudiante va a la opción correspondiente (Rectificación, CP o Meme)
   - Completa el formulario con los detalles
   - Envía el formulario

2. **Profesor Revisa:**
   - Accede al panel de profesor
   - Ve los envíos pendientes
   - Revisa cada envío
   - Decide si aceptarlo o rechazarlo
   - Asigna créditos (para CP, hay valores por defecto)

3. **Estudiante Recibe Créditos:**
   - Al ser aceptado un envío, los créditos se suman automáticamente
   - El estudiante puede ver sus créditos actualizados
   - Su ranking se actualiza automáticamente

## 🎨 Interfaz de Usuario

- **Diseño Responsive:** Usa Bootstrap 5 para adaptarse a cualquier dispositivo
- **Dark Mode Support:** Navbar oscuro para mejor experiencia visual
- **Colores Intuitivos:** Cada tipo de envío tiene un color asociado

## 📝 Ranking de Estudiantes

El ranking muestra:
- Número de posición
- Nombre del estudiante (oculto con asteriscos para otros)
- Total de créditos
- Distancia en créditos respecto al usuario actual

Formato:
```
3. *************************** 135 000
4. Lorem Ipsum               112 000
5. **********************   108 000
```

## 🔐 Seguridad

- Autenticación de Django incorporada
- CSRF protection en todos los formularios
- Acceso restringido según tipo de usuario
- Validación de formularios en cliente y servidor

## 🛠️ Personalización

### Agregar más usuarios:

```bash
python manage.py createsuperuser
```

### Agregar valores de CP:

Accede a `http://localhost:8000/admin/` con credenciales de admin.

### Cambiar valores de CP:

Los profesores pueden modificar manualmente los valores de los incisos en la sección de admin.

## 📚 Comandos Útiles

```bash
# Ver todas las URL disponibles
python manage.py show_urls

# Crear un superusuario
python manage.py createsuperuser

# Acceder a la shell de Django
python manage.py shell

# Limpiar la base de datos (cuidado)
python manage.py flush

# Crear una copia de seguridad de datos
python manage.py dumpdata > backup.json

# Restaurar desde copia de seguridad
python manage.py loaddata backup.json
```

## 🐛 Solución de Problemas

### Error: "Port 8000 is already in use"
```bash
python manage.py runserver 8001
```

### Error: "Table does not exist"
```bash
python manage.py migrate
```

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

## 🤝 Contribuciones

Para contribuir al proyecto, por favor:
1. Hacer fork
2. Crear una rama para tu feature
3. Commit de tus cambios
4. Push a la rama
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo LICENSE para más detalles.

---

**¡Disfruta del Sistema de Gestión de Créditos! 🎓**
