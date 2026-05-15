import os
import json
import random
import requests

from docx import Document
from docx.shared import Pt

# =========================================================
# TOKENS
# =========================================================

ORG_TOKEN = (os.environ.get("ORG_PAT") or "").strip()

BANK_TOKEN = (
    os.environ.get("BANK_PAT") or ""
).strip() or ORG_TOKEN

# =========================================================
# URLS BANCOS
# =========================================================

QUESTION_BANK_GRAFOS = (
    os.environ.get("QUESTION_BANK_GRAFOS") or ""
).strip()

QUESTION_BANK_VECTORIAL = (
    os.environ.get("QUESTION_BANK_VECTORIAL") or ""
).strip()

# =========================================================
# CONFIG
# =========================================================

CONFIG_JSON = os.environ.get(
    "CONFIG_JSON_MIXTO",
    ""
)

ALUMNOS_CSV = os.environ.get(
    "ALUMNOS_CSV",
    ""
)

CONFIG = json.loads(CONFIG_JSON)

# =========================================================
# GLOBALES
# =========================================================

PREGUNTAS_USADAS = {}

# =========================================================
# LOAD JSON
# =========================================================

def cargar_banco(url, nombre):

    print(f"\n📦 Cargando banco: {nombre}")

    headers = {
        "Authorization": f"Bearer {BANK_TOKEN}",
        "Accept": "application/vnd.github.raw"
    }

    r = requests.get(url, headers=headers)

    print("📡 STATUS:", r.status_code)

    if r.status_code != 200:
        raise Exception(
            f"Error cargando banco {nombre}"
        )

    data = r.json()

    preguntas = data.get("ejercicios", [])

    for p in preguntas:
        p["banco"] = nombre

    print(
        f"✅ {nombre}: {len(preguntas)} preguntas"
    )

    return preguntas

# =========================================================
# CONTAR EXÁMENES
# =========================================================

def contar_examenes():

    contenido = (
        ALUMNOS_CSV
        .replace("\\n", "\n")
        .strip()
    )

    lines = [
        l.strip()
        for l in contenido.split("\n")
        if l.strip()
    ]

    total = max(len(lines) - 1, 1)

    print(f"👨‍🎓 Exámenes a generar: {total}")

    return total

# =========================================================
# SELECCIÓN
# =========================================================

def seleccionar_preguntas(
    banco_preguntas,
    config_banco
):

    seleccion = []

    for nivel, cantidad in (
        config_banco["cantidad"].items()
    ):

        subset = [
            p for p in banco_preguntas
            if p["nivel"].lower() == nivel.lower()
        ]

        if len(subset) < cantidad:

            raise Exception(
                f"No hay suficientes preguntas "
                f"{nivel} en {config_banco['nombre']}"
            )

        elegidas = random.sample(
            subset,
            cantidad
        )

        for p in elegidas:

            p["puntaje"] = (
                config_banco["puntaje"][nivel]
            )

        seleccion.extend(elegidas)

    return seleccion

# =========================================================
# RUBRICA RESUMIDA
# =========================================================

def rubrica_resumida(pregunta):

    criterios = (
        pregunta
        .get("respuesta", {})
        .get("criterios", [])
    )

    if not criterios:
        return "Sin rúbrica"

    return ", ".join(criterios[:3])

# =========================================================
# DOC EXAMEN
# =========================================================

# =========================================================
# GENERAR DOCX EXÁMENES
# =========================================================

def generar_doc_examenes(asignaciones):

    doc = Document()

    for examen_idx, preguntas in enumerate(asignaciones):

        # =====================================================
        # NUEVO EXAMEN
        # =====================================================

        if examen_idx > 0:
            doc.add_page_break()

        # =====================================================
        # TÍTULO
        # =====================================================

        titulo = doc.add_heading(
            "EXAMEN PRESENCIAL",
            level=1
        )

        titulo.runs[0].bold = True

        subtitulo = doc.add_paragraph(
            "Bases de Datos — Grafos y Vectoriales"
        )

        subtitulo.runs[0].font.size = Pt(11)

        # =====================================================
        # DATOS ESTUDIANTE
        # =====================================================

        p = doc.add_paragraph()

        r = p.add_run(
            "\nNombre del estudiante:\n\n"
            "________________________________________\n\n"
            "Firma:\n\n"
            "________________________________________\n"
        )

        r.bold = True
        r.font.size = Pt(11)

        # =====================================================
        # PREGUNTAS
        # =====================================================

        for i, pregunta in enumerate(preguntas, start=1):

            texto = (
                f"{i}. "
                f"{pregunta['enunciado']} "
                f"({pregunta['puntaje']} punto"
                f"{'s' if pregunta['puntaje'] != 1 else ''}) "
                f"(ID: {pregunta['id']})"
            )

            para = doc.add_paragraph()

            run = para.add_run(texto)

            run.font.size = Pt(11)

            # =================================================
            # ESPACIO RESPUESTA SEGÚN DIFICULTAD
            # =================================================

            nivel = pregunta["nivel"].lower()

            if nivel == "facil":
                espacio = 6

            elif nivel in ["medio", "intermedia"]:
                espacio = 8

            else:
                espacio = 10

            for _ in range(espacio):
                doc.add_paragraph("")

        # =====================================================
        # HOJA ADICIONAL
        # =====================================================

        doc.add_page_break()
        

        extra.runs[0].bold = True

        for _ in range(32):
            doc.add_paragraph("")

    # =========================================================
    # GUARDAR
    # =========================================================

    doc.save("examenes_presenciales.docx")

    print("✅ DOCX generado: examenes_presenciales.docx")

# =========================================================
# MAIN
# =========================================================

def main():

    print("🚀 Generador presencial mixto")

    banco_grafos = cargar_banco(
        QUESTION_BANK_GRAFOS,
        "grafos"
    )

    banco_vectoriales = cargar_banco(
        QUESTION_BANK_VECTORIAL,
        "vectoriales"
    )

    total_examenes = contar_examenes()

    examenes = []

    for _ in range(total_examenes):

        preguntas_finales = []

        for config_banco in CONFIG["bancos"]:

            nombre = config_banco["nombre"]

            if nombre == "grafos":
                banco_actual = banco_grafos
            else:
                banco_actual = banco_vectoriales

            seleccion = seleccionar_preguntas(
                banco_actual,
                config_banco
            )

            preguntas_finales.extend(
                seleccion
            )

        random.shuffle(preguntas_finales)

        for p in preguntas_finales:
            PREGUNTAS_USADAS[
                f"{p['banco']}-{p['id']}"
            ] = p

        examenes.append(
            preguntas_finales
        )

    generar_doc_examenes(examenes)

    print("🎉 FIN")

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()