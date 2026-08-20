import os
import re
import time
import random
import requests
from datetime import datetime
from slugify import slugify
from google import genai

# ---------------------------------------------------------------------------
# 1. CONFIGURACIÓN Y VARIABLES DE ENTORNO
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# Dominio base con fallback por si no existe en las variables del workflow
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://herjos.com/cuentacuentos")

if not GEMINI_API_KEY:
    raise ValueError("❌ Error: La variable GEMINI_API_KEY no está configurada.")

# ---------------------------------------------------------------------------
# 2. VARIADORES DE CONTENIDO
# ---------------------------------------------------------------------------

TEMAS = [
    "un secreto familiar guardado en un objeto que se abre por accidente",
    "un mensaje anónimo que predice un evento minutos antes de que ocurra",
    "un personaje atrapado en un lugar del que debe salir antes de que se agote el tiempo",
    "un trato o promesa del pasado que viene a cobrarse en el peor momento",
    "la desaparición inexplicable de algo cotidiano pero vital para los personajes",
    "un objeto común que empieza a comportarse de forma físicamente imposible",
    "un personaje que descubre que la versión oficial de su propia historia es mentira",
    "dos rivales obligados a cooperar para ocultar un error que arruinaría a ambos",
    "una oferta irresistible que oculta un precio demasiado alto o una trampa"
]

GENEROS = [
    "fantasía suave", 
    "misterio ligero", 
    "realismo mágico", 
    "aventura cotidiana", 
    "ciencia ficción cercana", 
    "cuento reflexivo/humano"
]

ESTRUCTURAS_TEMPORALES = [
    "cronología inversa: la historia comienza en el clímax y avanza hacia atrás",
    "narrativa fragmentada: saltos constantes entre pasado, presente y recuerdos",
    "tiempo congelado: el relato ocurre en el espacio de un solo segundo expandido",
    "líneas paralelas: dos eventos simultáneos que se entrelazan párrafo a párrafo"
]

VOCES_NARRATIVAS = [
    "segunda persona: el narrador te habla a ti ('tú') para máxima inmersión",
    "narrador poco confiable: el protagonista miente o percibe la realidad alterada",
    "perspectiva coral: el punto de vista cambia entre personajes en cada sección",
    "omnisciente cínico: una voz externa con humor negro que rompe la cuarta pared"
]

SUBVERSION_DE_TROPOS = [
    "anticlímax: el gran misterio se resuelve de la forma más común y mundana",
    "inversión de roles: el supuesto monstruo es la víctima y el héroe la amenaza",
    "final abierto existencial: se resuelve el dilema interno pero no la trama externa",
    "giro metanarrativo: el lector descubre que forma parte activa del misterio"
]

tema_hoy = random.choice(TEMAS)
genero_hoy = random.choice(GENEROS)
estructuras = random.choice(ESTRUCTURAS_TEMPORALES)
voces = random.choice(VOCES_NARRATIVAS)
tropos = random.choice(SUBVERSION_DE_TROPOS)
categoria_hoy = genero_hoy  # Para el esquema obligatorio de Astro

print(f"🎲 Tema seleccionado para hoy: {tema_hoy}")
print(f"🎲 Género seleccionado para hoy: {genero_hoy}")

# ---------------------------------------------------------------------------
# 3. LLAMADA A LA API DE GEMINI CON REINTENTOS
# ---------------------------------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""


Instrucciones estrictas:
- Tema obligatorio: {tema_hoy}.
- Género: {genero_hoy}.
- Estructuras temporales: {estructuras}.
- Voces narrativas: {voces}.
- Subversion de tropos: {tropos}.
- RESTRICCIÓN: EVITA hablar sobre tiempo, relojes, segundos, minutos, arena, pasado o futuro. Busca imágenes y conceptos frescos.
- Extensión del cuento: Al menos 500 palabras, limite el que sea conveniente pero que no sea muy larga y tienda a ser aburrida.
- Idioma: Español.

Actúa como un escritor de narrativa experto en atrapamiento psicológico, ritmo ágil y ganchos narrativos. Tu objetivo es escribir un cuento o historia que sumerja al lector inmediatamente desde la primera oración y mantenga la tensión para que no pueda dejar de leer hasta el final.

Instrucciones de la historia:

Extensión: Entre 400 y 3000 palabras (asegúrate de no quedar por debajo ni superarlo).

Inicio: Debe comenzar en media res (en medio de la acción, un dilema o una revelación impacto) para enganchar al lector desde el primer segundo.

Ritmo y Tensión: Mantén un conflicto claro, revelaciones paulatinas y un ritmo dinámico que sostenga el interés.

Tema: Libres de elegir el género (misterio, ciencia ficción, suspenso, fantasía o vida cotidiana), pero debe centrarse en un secreto oculto, una decisión límite o un giro inesperado al final.

RESTRICCIÓN DE FORMATO OBLIGATORIA:
Debes responder ÚNICAMENTE utilizando la siguiente estructura exacta, respetando los nombres de las etiquetas y sin agregar introducciones, notas o saludos antes o después del texto:

TITULO: [Escribe aquí un título atractivo sin comillas]
RESUMEN: [Escribe un breve resumen de máximo 2 oraciones para redes sociales]
CUENTO:
[Escribe aquí el texto completo del cuento dividido en párrafos]
"""

modelos = ['gemini-3.6-flash', 'gemini-2.5-flash-lite']
texto_generado = None

for modelo in modelos:
    for intento in range(1, 4):
        try:
            print(f"🧠 Generando cuento con {modelo} (Intento {intento})...")
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
            )
            if response and response.text:
                texto_generado = response.text
                break
        except Exception as e:
            err_msg = str(e)
            print(f"⚠️ Error en {modelo} (Intento {intento}): {err_msg}")
            if "404" in err_msg or "NOT_FOUND" in err_msg:
                print(f"❌ El modelo {modelo} no está disponible. Cambiando...")
                break
            time.sleep(5)
            
    if texto_generado:
        break

if not texto_generado:
    raise RuntimeError("❌ No se pudo obtener respuesta de la API tras varios intentos.")

# ---------------------------------------------------------------------------
# 4. EXTRACCIÓN Y FORMATEO DE DATOS
# ---------------------------------------------------------------------------
titulo_match = re.search(r"TITULO:\s*(.*)", texto_generado)
resumen_match = re.search(r"RESUMEN:\s*(.*)", texto_generado)
cuento_match = re.search(r"CUENTO:\s*([\s\S]*)", texto_generado)

titulo = titulo_match.group(1).strip() if titulo_match else "Cuento del Día"
resumen = resumen_match.group(1).strip() if resumen_match else "Una historia original para disfrutar hoy."
contenido_cuento = cuento_match.group(1).strip() if cuento_match else texto_generado

fecha_hoy = datetime.now().strftime("%Y-%m-%d")
slug_titulo = slugify(titulo)
slug_cuento = f"{fecha_hoy}-{slug_titulo}"

# ---------------------------------------------------------------------------
# 5. GUARDAR ARCHIVO MARKDOWN (INCLUYE CATEGORY PARA ASTRO)
# ---------------------------------------------------------------------------
output_dir = "src/content/cuentos"
os.makedirs(output_dir, exist_ok=True)
file_path = os.path.join(output_dir, f"{slug_cuento}.md")

titulo_clean = titulo.replace('"', '\\"')
resumen_clean = resumen.replace('"', '\\"')

markdown_content = f"""---
title: "{titulo_clean}"
description: "{resumen_clean}"
date: "{fecha_hoy}"
category: "{categoria_hoy}"
---

{contenido_cuento}
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(markdown_content)

print(f"✅ Archivo guardado correctamente en: {file_path}")

# ---------------------------------------------------------------------------
# 6. EXPONER DATOS PARA EL PASO DE PUBLICACIÓN EN REDES (que corre DESPUÉS
#    de que el sitio ya fue compilado y desplegado, no aquí).
# ---------------------------------------------------------------------------
base_url_clean = SITE_BASE_URL.strip().rstrip('/')
url_cuento = f"{base_url_clean}/cuentos/{slug_cuento.strip()}"

github_output = os.environ.get("GITHUB_OUTPUT")
if github_output:
    def _escapar(valor: str) -> str:
        # Escapa saltos de línea para que GITHUB_OUTPUT no se rompa
        return valor.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")

    with open(github_output, "a", encoding="utf-8") as f:
        f.write(f"titulo={_escapar(titulo)}\n")
        f.write(f"resumen={_escapar(resumen)}\n")
        f.write(f"url_cuento={_escapar(url_cuento)}\n")
        f.write(f"slug={slug_cuento.strip()}\n")

print(f"🔗 URL del cuento (se publicará en redes tras el despliegue): {url_cuento}")
