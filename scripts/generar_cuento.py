import os
import re
import random
import requests
from slugify import slugify
from google import genai

# ---------------------------------------------------------------------------
# 1. CONFIGURACIÓN Y VARIABLES DE ENTORNO
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://herjos.com/cuentacuentos")

if not GEMINI_API_KEY:
    raise ValueError("❌ Error: La variable GEMINI_API_KEY no está configurada.")

# ---------------------------------------------------------------------------
# 2. VARIADORES DE CONTENIDO (Para evitar repetición de temas)
# ---------------------------------------------------------------------------
TEMAS = [
    "un viaje de exploración o descubrimiento de un lugar desconocido",
    "un misterio ligero en una ciudad pequeña",
    "una invención o descubrimiento culinario/artesanal peculiar",
    "la conexión entre una persona y un animal o entorno natural",
    "un desafío personal, la superación de un miedo o una decisión importante",
    "un evento mágico o extraordinario irrumpiendo en un día cotidiano",
    "un encuentro inesperado entre dos desconocidos con perspectivas opuestas",
    "una tradición antigua transmitida a una nueva generación",
    "un viaje en carretera que cambia los planes de los pasajeros"
]

GENEROS = [
    "fantasía suave", 
    "misterio ligero", 
    "realismo mágico", 
    "aventura cotidiana", 
    "ciencia ficción cercana", 
    "cuento reflexivo/humano"
]

tema_hoy = random.choice(TEMAS)
genero_hoy = random.choice(GENEROS)

print(f"🎲 Tema seleccionado para hoy: {tema_hoy}")
print(f"🎲 Género seleccionado para hoy: {genero_hoy}")

# ---------------------------------------------------------------------------
# 3. LLAMADA A LA API DE GEMINI
# ---------------------------------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
Escribe un cuento corto e inspirador.

Instrucciones strictly:
- Tema obligatorio: {tema_hoy}.
- Género: {genero_hoy}.
- RESTRICCIÓN: EVITA hablar sobre tiempo, relojes, segundos, minutos, arena, pasado o futuro. Busca imágenes y conceptos frescos.
- Extensión del cuento: entre 350 y 500 palabras.
- Idioma: Español.

Debes devolver la respuesta en el siguiente formato EXACTO sin omitir ninguna etiqueta:

TITULO: [Escribe aquí un título atractivo sin comillas]
RESUMEN: [Escribe un breve resumen de máximo 2 oraciones para redes sociales]
CUENTO:
[Escribe aquí el texto completo del cuento dividido en párrafos]
"""

print("🧠 Generando cuento con Gemini...")

# Usamos el identificador estándar recomendado por el SDK
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt,
)

texto_generado = response.text
print("--- RESPUESTA GENERADA ---")
print(texto_generado[:200] + "...")

# ---------------------------------------------------------------------------
# 4. PROCESAMIENTO DEL TEXTO Y EXTRACCIÓN DE DATOS
# ---------------------------------------------------------------------------
titulo_match = re.search(r"TITULO:\s*(.*)", texto_generado)
resumen_match = re.search(r"RESUMEN:\s*(.*)", texto_generado)
cuento_match = re.search(r"CUENTO:\s*([\s\S]*)", texto_generado)

titulo = titulo_match.group(1).strip() if titulo_match else "Cuento del Día"
resumen = resumen_match.group(1).strip() if resumen_match else "Una historia original para disfrutar hoy."
contenido_cuento = cuento_match.group(1).strip() if cuento_match else texto_generado

# Generar fecha y slug
from datetime import datetime
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
slug_titulo = slugify(titulo)
slug_cuento = f"{fecha_hoy}-{slug_titulo}"

# ---------------------------------------------------------------------------
# 5. GUARDAR ARCHIVO MARKDOWN PARA ASTRO
# ---------------------------------------------------------------------------
output_dir = "src/content/cuentos"
os.makedirs(output_dir, exist_ok=True)
file_path = os.path.join(output_dir, f"{slug_cuento}.md")

# Limpiar comillas para evitar errores en YAML Frontmatter
titulo_clean = titulo.replace('"', '\\"')
resumen_clean = resumen.replace('"', '\\"')

markdown_content = f"""---
title: "{titulo_clean}"
description: "{resumen_clean}"
date: "{fecha_hoy}"
---

{contenido_cuento}
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(markdown_content)

print(f"✅ Archivo guardado correctamente en: {file_path}")

# ---------------------------------------------------------------------------
# 6. ENVIAR NOTIFICACIÓN A TELEGRAM (URL ÚNICA Y LIMPIA)
# ---------------------------------------------------------------------------
if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    # Sanitización de la URL para evitar que se rompa con saltos de línea
    base_url_clean = SITE_BASE_URL.strip().rstrip('/')
    slug_clean = slug_cuento.strip()
    
    url_cuento = f"{base_url_clean}/cuentos/{slug_clean}"
    
    # Formato Markdown para que aparezca como hipervínculo limpio
    mensaje_telegram = (
        f"📖 *¡Nuevo cuento diario!*\n\n"
        f"📌 *{titulo}*\n\n"
        f"📝 {resumen}\n\n"
        f"🔗 [Lee el cuento completo aquí]({url_cuento})"
    )
    
    url_api_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje_telegram,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    print("--- ENVIANDO A TELEGRAM ---")
    print(f"URL generada: {url_cuento}")
    try:
        res_telegram = requests.post(url_api_telegram, json=payload, timeout=10)
        print(f"Status Code Telegram: {res_telegram.status_code}")
    except Exception as e:
        print(f"❌ Error al conectar con la API de Telegram: {e}")
