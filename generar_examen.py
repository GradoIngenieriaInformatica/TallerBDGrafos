import os
import json
import random
import requests

ORG = "GradoIngenieriaInformatica"

# =========================
# CONFIG
# =========================

BASE_REPO = "taller-base-datos-grafos"

ORG_TOKEN = (os.environ.get("ORG_PAT") or "").strip()
BANK_TOKEN = (os.environ.get("BANK_PAT") or "").strip() or ORG_TOKEN

QUESTION_BANK_URL = (os.environ.get("QUESTION_BANK_CONFIG") or "").strip()
CONFIG_JSON = os.environ.get("CONFIG_JSON", "")
ALUMNOS_CSV = os.environ.get("ALUMNOS_CSV", "")

CONFIG = json.loads(CONFIG_JSON) if CONFIG_JSON else {}

HEADERS = {
    "Authorization": f"token {ORG_TOKEN}",
    "Accept": "application/vnd.github+json"
}

RESULTADOS = []

# =========================
# PREGUNTAS
# =========================

def cargar_preguntas():
    print("\n📦 Cargando preguntas...")

    headers = {
        "Authorization": f"Bearer {BANK_TOKEN}",
        "Accept": "application/vnd.github.raw"
    }

    r = requests.get(QUESTION_BANK_URL, headers=headers)

    print("📡 STATUS:", r.status_code)

    if r.status_code != 200:
        raise Exception("Error cargando preguntas")

    data = r.json()
    preguntas = data.get("ejercicios", [])

    print(f"✅ Preguntas cargadas: {len(preguntas)}")
    return preguntas

# =========================
# CSV
# =========================

def parsear_alumnos():
    contenido = ALUMNOS_CSV.replace("\\n", "\n").strip()
    lines = [l.strip() for l in contenido.split("\n") if l.strip()]

    delimiter = ";" if ";" in lines[0] else ","

    alumnos = []

    for line in lines[1:]:
        parts = [p.strip() for p in line.split(delimiter)]

        if len(parts) >= 4:
            alumnos.append(parts[3])

    print(f"👨‍🎓 TOTAL alumnos: {len(alumnos)}")
    return alumnos

# =========================
# REPO
# =========================

def construir_repo(user):
    return f"{BASE_REPO}-{user}"

def repo_existe(repo):
    url = f"https://api.github.com/repos/{ORG}/{repo}"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200

# =========================
# ISSUE
# =========================

def crear_issue(repo, title, body):
    url = f"https://api.github.com/repos/{ORG}/{repo}/issues"

    r = requests.post(
        url,
        headers=HEADERS,
        json={"title": title, "body": body}
    )

    print(f"📝 {repo} → {r.status_code}")

# =========================
# FORMATO ENUNCIADO
# =========================

def formatear_enunciado(p, index):
    tipo = p.get("tipo")

    texto = f"**{index}.** {p['enunciado']}"

    if tipo in ["modify_query", "fix_query"]:
        base = p.get("query_base", "")
        if base:
            texto += f"\n\n```cypher\n{base}\n```"

    return texto

# =========================
# SELECCIÓN
# =========================

def seleccionar_preguntas(preguntas):
    seleccion = []

    for nivel, cantidad in CONFIG.get("distribucion", {}).items():
        subset = [p for p in preguntas if p["nivel"] == nivel]

        if len(subset) < cantidad:
            raise Exception(f"No hay suficientes preguntas para nivel {nivel}")

        seleccion += random.sample(subset, cantidad)

    return seleccion

# =========================
# GENERAR
# =========================

def generar(user, preguntas):

    repo = construir_repo(user)

    if not repo_existe(repo):
        print(f"❌ Repo no existe: {repo}")
        return

    seleccion = seleccionar_preguntas(preguntas)
    ids = [p["id"] for p in seleccion]

    print(f"📦 {user} → {ids}")

    # -------------------------
    # ISSUE (ENUNCIADO)
    # -------------------------

    enunciado = "\n\n---\n\n".join([
        formatear_enunciado(p, i + 1)
        for i, p in enumerate(seleccion)
    ])

    crear_issue(
        repo,
        "📄 Enunciado del examen",
        enunciado
    )

    # -------------------------
    # RESULTADOS (SIN DETALLE)
    # -------------------------

    RESULTADOS.append({
        "alumno": user,
        "repo": repo,
        "examen": ids
    })

# =========================
# EXPORT
# =========================

def guardar_resultados():
    print("\n💾 Guardando archivo...")

    with open("examenes_generados.json", "w", encoding="utf-8") as f:
        json.dump(RESULTADOS, f, indent=2, ensure_ascii=False)

    print("✅ Archivo generado")

# =========================
# MAIN
# =========================

def main():
    print("🚀 Generando exámenes por ISSUE")

    preguntas = cargar_preguntas()
    alumnos = parsear_alumnos()

    for a in alumnos:
        generar(a, preguntas)

    guardar_resultados()

    print("🎉 FIN")

if __name__ == "__main__":
    main()