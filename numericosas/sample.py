from __future__ import annotations

import json
import random
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOCAL_TZ = timezone(timedelta(hours=-3))
START = datetime(2026, 8, 10, 8, 0, tzinfo=LOCAL_TZ)

BLUEPRINTS = [
    {
        "name": "Ana Gómez",
        "chat_id": -1001000000001,
        "username": "ana_gomez_num",
        "type": "public_channel",
        "seed": 11,
        "active_weeks": {0, 1, 2, 3, 4, 5, 6, 7},
    },
    {
        "name": "Bruno Díaz",
        "chat_id": -1001000000002,
        "username": None,
        "type": "private_channel",
        "seed": 23,
        "active_weeks": {0, 1, 2, 4, 5, 7},
    },
    {
        "name": "Carla Ruiz",
        "chat_id": -1001000000003,
        "username": None,
        "type": "private_channel",
        "seed": 37,
        "active_weeks": {0, 1, 2, 3, 4, 5, 6, 7},
    },
    {
        "name": "Diego Sosa",
        "chat_id": -1001000000004,
        "username": None,
        "type": "private_channel",
        "seed": 53,
        "active_weeks": {0, 2, 3, 6, 7},
    },
]

ANSWERS = [
    "Resolví el ejercicio {n} con bisección: f(1) = -2 y f(2) = 1, así que hay raíz en [1, 2]. Iteré hasta |b-a| < 1e-6.",
    "Para el ejercicio {n} usé Newton. La derivada se anula cerca de la raíz, así que tuve que cambiar el punto inicial.",
    "Comparé Euler y Runge-Kutta para el ejercicio {n}. Con paso 0.1, RK4 baja el error dos órdenes.",
    "En el ejercicio {n} armé la tabla de diferencias divididas y me quedó un polinomio de grado 3.",
    "Resolví el sistema del ejercicio {n} con LU. El pivoteo fue necesario porque el primer pivote era casi cero.",
]

QUESTIONS = [
    "¿Alguien me explica por qué Newton diverge cerca de una raíz múltiple?",
    "¿El criterio de corte es sobre |x_k - x_{k-1}| o sobre |f(x_k)|? Me confunde cuál usar.",
    "¿Por qué conviene escalar las filas antes de aplicar Gauss-Seidel?",
    "¿La regla de Simpson compuesta necesita cantidad par de subintervalos, no?",
    "¿Cómo se elige el paso en Euler para que el error sea aceptable?",
]

CURIOSITIES = [
    "Dato: Simpson es exacto para polinomios de grado ≤ 3. Por eso conviene usarlo cuando el integrando es suave.",
    "Curiosidad: el método de la secante es como Newton pero con diferencias finitas en vez de derivada.",
    "Leí que la estabilidad de un método depende de la ecuación de prueba y' = λy. No es solo el orden.",
    "El número de condición de una matriz puede explotar aunque el determinante no sea chico.",
]

CONTRIBUTIONS = [
    "Probé cambiar el criterio de corte y la cantidad de iteraciones baja bastante. Les dejo la comparación en el próximo mensaje.",
    "Armé una planilla para comparar errores absolutos y relativos. Si quieren la comparto.",
    "Encontré que ordenar las filas por magnitud mejora la convergencia de Gauss-Seidel en este caso.",
]

REPOS = [
    (
        "Les dejo el repo con la implementación: ",
        {"type": "text_link", "text": "métodos numéricos", "href": "https://github.com/ejemplo/metodos"},
        " (bisección, Newton y LU).",
    ),
    (
        "Subí las funciones: ",
        {"type": "text_link", "text": "repo de la materia", "href": "https://github.com/ejemplo/numerico"},
        "",
    ),
]

MEDIA = [
    ("photo", "Foto del pizarrón de hoy", "photos/photo_{id}.jpg", None, None, 180_000),
    ("photo", "Cuando el profesor dice «es trivial»", "photos/meme_{id}.jpg", None, None, 95_000),
    ("photo", "", "photos/photo_{id}.jpg", None, None, 210_000),
    ("document", "Les dejo el apunte de interpolación", "files/apunte_{id}.pdf", "apunte_interpolacion.pdf", "application/pdf", 480_000),
    ("document", "Resumen de la unidad 2", "files/resumen_{id}.pdf", "resumen_unidad2.pdf", "application/pdf", 320_000),
    ("video_file", "Video corto de la iteración", "video_files/video_{id}.mp4", "iteracion.mp4", "video/mp4", 1_800_000),
    ("voice_message", "Audio explicando el ejercicio", "voice_messages/voice_{id}.ogg", "audio.ogg", "audio/ogg", 70_000),
    ("sticker", "Cuando compila a la primera", "stickers/sticker_{id}.webp", "sticker.webp", "image/webp", 24_000),
]

BARE_LINKS = [
    "https://example.edu/apuntes/interpolacion.pdf",
    "https://github.com/ejemplo/ejercicios-resueltos",
    "https://www.youtube.com/watch?v=ejemplo",
]


def generate_sample_export(root: str | Path) -> Path:
    """Genera un export sintético con 4 canales y ~120 mensajes."""
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    for blueprint in BLUEPRINTS:
        chat = _build_chat(blueprint)
        folder = root / _safe_folder(blueprint["name"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "result.json").write_text(
            json.dumps(chat, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return root


def _build_chat(blueprint: dict) -> dict:
    rng = random.Random(blueprint["seed"])
    planned: list[tuple[datetime, dict]] = []
    exercise = 1

    for week in range(8):
        if week not in blueprint["active_weeks"]:
            continue
        count = rng.randint(2, 4)
        for _ in range(count):
            dt = START + timedelta(
                weeks=week,
                days=rng.randint(0, 6),
                hours=rng.randint(0, 12),
                minutes=rng.randint(0, 59),
            )
            kind = _pick_kind(rng)
            content: dict = {"kind": kind, "dt": dt}

            if kind == "answer":
                content["text"] = rng.choice(ANSWERS).format(n=exercise)
                exercise += 1
            elif kind == "question":
                content["text"] = rng.choice(QUESTIONS)
            elif kind == "curiosity":
                content["text"] = rng.choice(CURIOSITIES)
            elif kind == "contribution":
                content["text"] = rng.choice(CONTRIBUTIONS)
            elif kind == "repo":
                content["text"] = list(rng.choice(REPOS))
            elif kind == "bare_link":
                content["text"] = rng.choice(BARE_LINKS)
            elif kind == "media":
                media = rng.choice(MEDIA)
                content["media"] = media
                content["text"] = media[1]

            planned.append((dt, content))

    planned.sort(key=lambda item: item[0])

    messages = [
        {
            "id": 1,
            "type": "service",
            "date": (START - timedelta(days=1)).isoformat(timespec="seconds"),
            "date_unixtime": str(int((START - timedelta(days=1)).timestamp())),
            "action": "pin_message",
            "text": "",
        }
    ]

    next_id = 2
    for dt, content in planned:
        message = {
            "id": next_id,
            "date": dt.isoformat(timespec="seconds"),
            "date_unixtime": str(int(dt.timestamp())),
            "text": content["text"],
        }

        media = content.get("media")
        if media:
            media_type, _caption, file_template, file_name, mime_type, size = media
            file_rel = file_template.format(id=next_id)
            message["media_type"] = media_type
            if media_type == "photo":
                message["photo"] = file_rel
            else:
                message["file"] = file_rel
            if file_name:
                message["file_name"] = file_name
            if mime_type:
                message["mime_type"] = mime_type
            message["file_size"] = size
        elif content["kind"] in {"bare_link", "repo"}:
            if rng.random() < 0.5:
                message["media_type"] = "webpage"

        if rng.random() < 0.18 and next_id > 2:
            message["reply_to_message_id"] = rng.randint(2, next_id - 1)

        if rng.random() < 0.35:
            message["reactions"] = [
                {"emoji": rng.choice(["👍", "🔥", "😂", "🤔"]), "count": rng.randint(1, 5)}
            ]

        if blueprint["type"] == "public_channel":
            message["views"] = rng.randint(8, 90)

        if rng.random() < 0.04:
            message["forwarded_from"] = "Canal de la facultad"

        messages.append(message)
        next_id += 1

    return {
        "name": blueprint["name"],
        "type": blueprint["type"],
        "id": blueprint["chat_id"],
        "username": blueprint["username"],
        "messages": messages,
    }


def _pick_kind(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.28:
        return "answer"
    if roll < 0.45:
        return "question"
    if roll < 0.57:
        return "curiosity"
    if roll < 0.67:
        return "contribution"
    if roll < 0.75:
        return "repo"
    if roll < 0.80:
        return "bare_link"
    return "media"


def _safe_folder(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name).strip()
    return name or "canal"
