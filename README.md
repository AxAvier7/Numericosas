# Numericosas

Seguimiento de la actividad de estudiantes de **Matemática Numérica** en sus canales de Telegram.

La fase actual (**M0**) importa un export de Telegram Desktop y genera un Excel de inventario: qué hay en cada canal, cuándo, con qué tipo de contenido y con un link de evidencia. Todavía no hay etiquetas ni radares; eso llega en M1/M2.

## Instalación

Requiere Python 3.11 o superior.

```powershell
python -m pip install -e .
```

Para desarrollo:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

## Probar con datos sintéticos

Antes de tocar tus canales:

```powershell
python -m numericosas demo
```

Genera 4 canales falsos en `data/raw/demo`, los importa a `data/demo.sqlite` y crea:

```
out/demo_inventario.xlsx
```

## Usar tus canales

### 1. Exportar desde Telegram Desktop

1. Abrí Telegram Desktop.
2. `Configuración` → `Avanzado` → `Exportar datos de Telegram`.
3. Elegí los canales de los estudiantes. El diálogo permite seleccionar varios chats; si tu versión no lo permite, exportá uno por uno.
4. Formato **JSON**, con los medios que quieras conservar.
5. Guardá el export en `data/raw/` (o pasá otra ruta con `--raw`).

El resultado son carpetas con esta forma:

```
data/raw/
  Ana Gomez/
    result.json
    photos/
    files/
  Bruno Diaz/
    result.json
```

### 2. Importar a SQLite

```powershell
python -m numericosas ingest --raw data/raw --db data/numericosas.sqlite
```

El importador es idempotente: podés volver a correrlo cuando haya mensajes nuevos y actualiza sin duplicar. Los mensajes de servicio (pins, ingresos) se omiten.

### 3. Generar el Excel

```powershell
python -m numericosas report --db data/numericosas.sqlite --out out/inventario.xlsx
```

## Qué trae el Excel

| Hoja | Contenido |
|---|---|
| `00_Portada` | Resumen, rango de fechas y guía de hojas. |
| `01_Alumnos` | Una fila por canal/alumno: totales, días y semanas activas, links, media, respuestas, reacciones. |
| `02_Inventario` | Una fila por mensaje: fecha, tipo, archivo, links, texto recortado, permalink y fuente. |
| `03_Resumen` | Conteos por tipo de contenido (texto, foto, documento, video, audio, sticker). |
| `04_Timeline_Semanas` | Actividad por semana ISO. |
| `05_Timeline_Meses` | Actividad por mes. |
| `06_Importacion` | Trazabilidad de cada corrida. |
| `99_Leyenda` | Definiciones y criterios de conteo. |

Cada fila del inventario se puede rastrear con **Fuente + ID**. Si el canal es público o es un canal/supergrupo privado, también se genera un permalink de Telegram.

## Estructura

```
numericosas/
  ingest/
    base.py            interfaz común de adaptadores
    desktop_export.py  parser de result.json
    service.py         carga idempotente a SQLite
  report/
    inventory.py       generador del Excel
  sample.py            datos sintéticos
  cli.py               comandos ingest / report / demo
  db.py                esquema y persistencia
tests/
```

El adaptador de Telethon se agrega en `ingest/telethon.py` sin tocar el parser ni el reporte: solo tiene que devolver `ParsedChat` / `ParsedMessage`.

## Privacidad

Los exports y la base contienen datos de estudiantes. Están en `.gitignore` y no deben subirse al repo. El `.session` de Telethon tampoco.

## Roadmap

- **M0 (actual):** inventario en Excel.
- **M1:** taxonomía editable y herramienta de etiquetado manual.
- **M2:** tabla estudiantes × actividades, perfiles y radares por dimensión.
- **M3:** ingesta automática con Telethon y detección de canales nuevos.
