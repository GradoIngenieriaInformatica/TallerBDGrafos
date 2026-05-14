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

def generar_doc_examen(examenes):

    doc = Document()

    for numero, preguntas in enumerate(examenes):

        # =================================================
        # CABECERA
        # =================================================

        doc.add_heading(
            "EXAMEN PRESENCIAL",
            level=1
        )

        p = doc.add_paragraph()

        r = p.add_run(
            "Nombre: ________________________________\n\n"
        )

        r.bold = True

        r2 = p.add_run(
            "Firma: _________________________________"
        )

        r2.bold = True

        doc.add_paragraph("")

        total = 0

        # =================================================
        # PREGUNTAS
        # =================================================

        for i, pregunta in enumerate(
            preguntas,
            start=1
        ):

            total += pregunta["puntaje"]

            texto = (
                f"{i}. "
                f"{pregunta['enunciado']}\n\n"
                f"ID: {pregunta['id']}\n"
                f"Banco: {pregunta['banco']}\n"
                f"Dificultad: {pregunta['nivel']}\n"
                f"Puntaje: {pregunta['puntaje']}\n"
                f"Rúbrica: {rubrica_resumida(pregunta)}"
            )

            p = doc.add_paragraph()

            run = p.add_run(texto)

            run.font.size = Pt(11)

            # ============================
            # ESPACIO RESPUESTA
            # ============================

            for _ in range(10):
                doc.add_paragraph("__________________________________________________")

            doc.add_paragraph("")

        # =================================================
        # FIRMA FINAL
        # =================================================

        doc.add_paragraph("")

        p2 = doc.add_paragraph()

        rf = p2.add_run(
            "Firma final del estudiante:\n\n"
            "____________________________________"
        )

        rf.bold = True

        doc.add_paragraph(
            f"\nPuntaje total del examen: {total}"
        )

        # =================================================
        # CARILLA LIBRE
        # =================================================

        doc.add_page_break()

        doc.add_paragraph(
            "HOJA ADICIONAL PARA RESPUESTAS"
        )

        for _ in range(40):
            doc.add_paragraph("")

        # =================================================
        # SIGUIENTE ALUMNO
        # =================================================

        doc.add_page_break()

    doc.save("examen_mixto.docx")

    print("✅ examen_mixto.docx generado")

# =========================================================
# DOC RESPUESTAS
# =========================================================

def generar_doc_respuestas():

    doc = Document()

    doc.add_heading(
        "RESPUESTAS OFICIALES",
        level=1
    )

    usadas = sorted(
        PREGUNTAS_USADAS.values(),
        key=lambda x: (
            x["banco"],
            x["id"]
        )
    )

    for p in usadas:

        doc.add_heading(
            f"Pregunta ID {p['id']}",
            level=2
        )

        doc.add_paragraph(
            f"Banco: {p['banco']}"
        )

        doc.add_paragraph(
            f"Dificultad: {p['nivel']}"
        )

        doc.add_paragraph(
            f"Puntaje: {p['puntaje']}"
        )

        doc.add_paragraph(
            f"Enunciado:\n{p['enunciado']}"
        )

        criterios = (
            p.get("respuesta", {})
            .get("criterios", [])
        )

        doc.add_paragraph(
            "Criterios esperados:"
        )

        for c in criterios:

            doc.add_paragraph(
                f"- {c}"
            )

        doc.add_page_break()

    doc.save("respuestas_mixto.docx")

    print("✅ respuestas_mixto.docx generado")

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

    generar_doc_examen(examenes)

    generar_doc_respuestas()

    print("🎉 FIN")

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()