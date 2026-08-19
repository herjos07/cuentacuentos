import os
import re
import sys
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
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")

SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://herjos.com/cuentacuentos")

MODO_SOLO_GENERAR = "--solo-generar" in sys.argv
MODO_SOLO_NOTIFICAR = "--solo-notificar" in sys.argv

if not MODO_SOLO_GENERAR and not MODO_SOLO_NOTIFICAR:
    MODO_SOLO_GENERAR = True
    MODO_SOLO_NOTIFICAR = True

# ---------------------------------------------------------------------------
# 2. FUNCIONES
# ---------------------------------------------------------------------------

def generar_y_guardar_cuento():
    if not GEMINI_API_KEY:
        raise ValueError("❌ Error: La variable GEMINI_API_KEY no está configurada.")

    TEMAS = [
        "un viaje de exploración o descubrimiento de un lugar desconocido",
        "un misterio ligero en una ciudad pequeña",
        "una invención o descubrimiento culinario/artesanal peculiar",
        "la conexión entre una persona y un animal o entorno natural",
        "un desafío personal, la superación de un miedo o una decisión importante",
        "un evento mágico o extraordinario irrumpiendo en un día cotidiano",
        "un encuentro inesperado entre dos desconocidos con perspectivas opuestas",
        "una tradición antigua transmitida a una nueva generación",
        "un viaje en carretera que cambia los planes de los pasajeros",
        "fantasía y magia", "superación personal", "Secretos familiares",
        "casas embrujadas", "amor imposible"
    ]

    GENEROS = [
        "fantasía suave", "misterio ligero", "realismo mágico", 
        "aventura cotidiana", "ciencia ficción cercana", "cuento reflexivo/humano",
        "misterio y suspenso", "terror y paranormal", "drama y romance"
    ]

    tema_hoy = random.choice(TEMAS)
    genero_hoy = random.choice(GENEROS)

    print(f"🎲 Tema: {tema_hoy} | Género: {genero_hoy}")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
Escribe un cuento o historia corta, facil de leer para cualquier público y que te sumerga en la lectura.

Instrucciones estrictas:
- Tema obligatorio: {tema_hoy}.
- Género: {genero_hoy}.
- RESTRICCIÓN: EVITA hablar sobre tiempo, relojes, segundos, minutos, arena, pasado o futuro. Busca imágenes y conceptos frescos.
- Extensión del cuento: entre 350 y 1000 palabras.
- Idioma: Español.

Debes devolver la respuesta en el siguiente formato EXACTO sin omitir ninguna etiqueta:

TITULO: [Escribe aquí un título atractivo sin comillas]
RESUMEN: [Escribe un breve resumen de máximo 2 oraciones para redes sociales]
CUENTO:
[Escribe aquí el texto completo del cuento dividido en párrafos]
"""

  modelos = ['gemini-2.5-flash', 'gemini-2.5-flash-lite']
    texto_generado = None

    for modelo in modelos:
        for intento in range(1, 4):
            try:
                print(f"🧠 Generando con {modelo} (Intento {intento})...")
                response = client.models.generate_content(model=modelo, contents=prompt)
                if response and response.text:
                    texto_generado = response.text
                    break
            except Exception as e:
                print(f"⚠️ Error en {modelo}: {e}")
                time.sleep(3)
        if texto_generado:
            break

    if not texto_generado:
        raise RuntimeError("❌ No se pudo obtener respuesta de Gemini.")

    # Extracción con limpieza para no perder el RESUMEN
    titulo_match = re.search(r"TITULO:\s*(.*)", texto_generado, re.IGNORECASE)
    resumen_match = re.search(r"RESUMEN:\s*(.*)", texto_generado, re.IGNORECASE)
    cuento_match = re.search(r"CUENTO:\s*([\s\S]*)", texto_generado, re.IGNORECASE)

    titulo = titulo_match.group(1).strip() if titulo_match else "Cuento del Día"
    resumen = resumen_match.group(1).strip() if resumen_match else "Una historia original para disfrutar hoy."
    contenido_cuento = cuento_match.group(1).strip() if cuento_match else texto_generado

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    slug_titulo = slugify(titulo)
    slug_cuento = f"{fecha_hoy}-{slug_titulo}"

    output_dir = "src/content/cuentos"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{slug_cuento}.md")

    titulo_clean = titulo.replace('"', '\\"')
    resumen_clean = resumen.replace('"', '\\"')

    markdown_content = f"""---
title: "{titulo_clean}"
description: "{resumen_clean}"
date: "{fecha_hoy}"
category: "{genero_hoy}"
---

{contenido_cuento}
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"✅ Cuento guardado en: {file_path}")


def notificar_redes_sociales():
    output_dir = "src/content/cuentos"
    archivos = sorted([f for f in os.listdir(output_dir) if f.endswith(".md")])
    if not archivos:
        print("❌ No se encontraron cuentos para notificar.")
        return

    ultimo_archivo = archivos[-1]
    file_path = os.path.join(output_dir, ultimo_archivo)

    with open(file_path, "r", encoding="utf-8") as f:
        contenido = f.read()

    titulo_match = re.search(r'title:\s*"(.*?)"', contenido)
    resumen_match = re.search(r'description:\s*"(.*?)"', contenido)

    titulo = titulo_match.group(1) if titulo_match else "Cuento del Día"
    resumen = resumen_match.group(1) if resumen_match else "¡Descubre nuestro cuento de hoy!"
    slug_cuento = ultimo_archivo.replace(".md", "")

    base_url_clean = SITE_BASE_URL.strip().rstrip('/')
    url_cuento = f"{base_url_clean}/cuentos/{slug_cuento}"

    print(f"🔗 Notificando con URL: {url_cuento}")

    # 1. TELEGRAM
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        mensaje_telegram = (
            f"📖 <b>¡Nuevo cuento diario!</b>\n\n"
            f"📌 <b>{titulo}</b>\n\n"
            f"📝 {resumen}\n\n"
            f"🔗 <b>Lee el cuento completo aquí:</b>\n{url_cuento}"
        )
        url_api_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload_tg = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje_telegram,
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": False, "url": url_cuento}
        }
        try:
            res_tg = requests.post(url_api_telegram, json=payload_tg, timeout=10)
            print(f"📱 Telegram Status: {res_tg.status_code}")
        except Exception as e:
            print(f"❌ Error Telegram: {e}")

    # 2. FACEBOOK
    if FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN:
        url_fb = f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/feed"
        mensaje_facebook = (
            f"📖 ¡Nuevo cuento disponible hoy!\n\n"
            f"✨ {titulo}\n\n"
            f"{resumen}\n\n"
            f"Lee la historia completa en nuestro sitio web 👇\n"
            f"{url_cuento}"
        )
        payload_fb = {
            "message": mensaje_facebook,
            "link": url_cuento,
            "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
        }
        try:
            res_fb = requests.post(url_fb, data=payload_fb, timeout=15)
            print(f"📘 Facebook Status: {res_fb.status_code}")
        except Exception as e:
            print(f"❌ Error Facebook: {e}")

if __name__ == "__main__":
    if MODO_SOLO_GENERAR:
        print("🚀 [ETAPA 1] Generando cuento...")
        generar_y_guardar_cuento()
    
    if MODO_SOLO_NOTIFICAR:
        print("🚀 [ETAPA 2] Enviando notificaciones...")
        notificar_redes_sociales()
