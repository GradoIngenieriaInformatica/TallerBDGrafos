import os
import json
import random
import shutil
from pathlib import Path

# =========================
# CARGA DE SECRETOS
# =========================

preguntas_json = json.loads(os.environ["PREGUNTAS_JSON"])
config = json.loads(os.environ["CONFIG_JSON"])

ejercicios = preguntas_json["ejercicios"]

# =========================
# CONFIG
# =========================

TOTAL = config["total_preguntas"]
TIPOS = config["tipos"]
NIVELES = config["niveles"]

# =========================
# FILTRADO
# =========================

def filtrar(tipo, nivel):
    return [
        e for e in ejercicios
        if e["tipo"] == tipo and e["nivel"] == nivel
    ]

seleccion = []

for tipo, cantidad_tipo in TIPOS.items():
    if cantidad_tipo == 0:
        continue

    for nivel, porcentaje in NIVELES.items():
        if porcentaje == 0:
            continue

        n = int(cantidad_tipo * porcentaje)

        if n == 0:
            continue

        pool = filtrar(tipo, nivel)

        if len(pool) < n:
            raise Exception(f"No hay suficientes preguntas para {tipo}-{nivel}")

        seleccion.extend(random.sample(pool, n))

# Ajuste final
if len(seleccion) > TOTAL:
    seleccion = random.sample(seleccion, TOTAL)

random.shuffle(seleccion)

# =========================
# LIMPIEZA PREVIA
# =========================

respuestas_dir = Path("respuestas")

if respuestas_dir.exists():
    shutil.rmtree(respuestas_dir)

respuestas_dir.mkdir()

# =========================
# GENERAR EXAMEN
# =========================

md = "# 🧠 Examen Neo4j - Cypher\n\n"
md += f"Total preguntas: {len(seleccion)}\n\n"
md += "---\n\n"

for i, e in enumerate(seleccion, 1):
    md += f"## Pregunta {i}\n"
    md += f"- Tipo: {e['tipo']}\n"
    md += f"- Nivel: {e['nivel']}\n\n"
    md += f"{e['enunciado']}\n\n"

Path("examen.md").write_text(md, encoding="utf-8")

# =========================
# GENERAR RESPUESTAS
# =========================

def generar_template_respuesta(e, i):
    contenido = f"# Pregunta {i}\n\n"
    contenido += f"**Tipo:** {e['tipo']}  \n"
    contenido += f"**Nivel:** {e['nivel']}  \n\n"
    contenido += f"{e['enunciado']}\n\n"

    if "query_base" in e:
        contenido += "### Consulta base\n"
        contenido += "```cypher\n"
        contenido += e["query_base"]
        contenido += "\n```\n\n"

    contenido += "### Respuesta\n"
    contenido += "```cypher\n\n```\n"

    return contenido

# =========================
# MAPA DE PREGUNTAS (CLAVE)
# =========================

mapa = []

for i, e in enumerate(seleccion, 1):
    path = respuestas_dir / f"pregunta-{i}.md"
    contenido = generar_template_respuesta(e, i)
    path.write_text(contenido, encoding="utf-8")

    mapa.append({
        "pregunta_local": i,
        "id_original": e["id"],
        "tipo": e["tipo"],
        "nivel": e["nivel"]
    })

# Guardar mapa (CRÍTICO para evaluación)
Path("mapa_preguntas.json").write_text(
    json.dumps(mapa, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# =========================
# ELIMINAR GENERADOR
# =========================

# eliminar script
try:
    Path(__file__).unlink()
except:
    pass

# eliminar workflow
workflow_path = Path(".github/workflows/generar-examen.yml")
if workflow_path.exists():
    workflow_path.unlink()

print("✅ Examen generado correctamente")
print("🧠 Mapa de preguntas guardado")
print("🧹 Generador eliminado")