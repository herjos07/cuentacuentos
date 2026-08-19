import os
import re
import json
import time
import requests
from datetime import datetime
from slugify import slugify
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# 1. CONFIGURACIÓN Y CREDENCIALES
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://herjos07.github.io/cuentacuentos").rstrip("/")

if not GEMINI_API_KEY:
    raise ValueError("❌ No se encontró GEMINI_API_KEY en los Secrets de GitHub.")

client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# 2. PROMPT Y GENERACIÓN CON GEMINI
# ---------------------------------------------------------------------------
prompt = """
Genera un cuento corto original, reflexivo e imaginativo en español.
Devuelve la respuesta ÚNICAMENTE en formato JSON válido con la siguiente estructura:
{
  "titulo": "Título breve y atractivo",
  "resumen": "Resumen de una sola frase para la vista previa.",
  "cuento": "El texto completo del cuento aquí, dividido en varios párrafos."
}
"""

def generar_con_reintento():
    # Modelos recomendados y activos según la API
    modelos = ['gemini-3.6-flash', 'gemini-2.5-flash-lite']
    
    for modelo in modelos:
        print(f"🤖 Intentando generar cuento con el modelo: {modelo}...")
        for intento in range(3):
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json'
                    )
                )
                if response.text:
                    print(f"✅ Cuento generado con éxito usando {modelo}.")
                    return response.text
            except Exception as e:
                tiempo_espera = (intento + 1) * 5
                print(f"⚠️ Error con {modelo} (intento {intento + 1}): {e}")
                print(f"Reintentando en {tiempo_espera} segundos...")
                time.sleep(tiempo_espera)
                
    raise Exception("❌ No se pudo generar el cuento tras reintentar con múltiples modelos.")

# ---------------------------------------------------------------------------
# 3. PROCESAMIENTO DE LA RESPUESTA
# ---------------------------------------------------------------------------
raw_json = generar_con_reintento()

try:
    datos_cuento = json.loads(raw_json)
    titulo = datos_cuento.get("titulo", "Cuento Sin Título")
    resumen = datos_cuento.get("resumen", "Un relato generado hoy.")
    cuento_texto = datos_cuento.get("cuento", "")
except Exception as e:
    print(f"⚠️ Falló el parseo estricto de JSON: {e}. Limpiando texto...")
    match = re.search(r'\{.*\}', raw_json, re.DOTALL)
    if match:
        datos_cuento = json.loads(match.group(0))
        titulo = datos_cuento.get("titulo", "Cuento Sin Título")
        resumen = datos_cuento.get("resumen", "Un relato generado hoy.")
        cuento_texto = datos_cuento.get("cuento", "")
    else:
        raise Exception("No se pudo extraer el JSON de la respuesta.")

fecha_hoy = datetime.now().strftime("%Y-%m-%d")
slug_titulo = slugify(titulo)
slug_cuento = f"{fecha_hoy}-{slug_titulo}"

# ---------------------------------------------------------------------------
# 4. GUARDAR ARCHIVO PARA ASTRO
# ---------------------------------------------------------------------------
directorio_destino = "src/content/cuentos"
os.makedirs(directorio_destino, exist_ok=True)

ruta_archivo = os.path.join(directorio_destino, f"{slug_cuento}.md")

# Ajustado para cumplir con el schema de Astro (date y category obligatorios)
contenido_markdown = f"""---
title: "{titulo}"
date: {fecha_hoy}
pubDate: {fecha_hoy}
description: "{resumen}"
category: "Ficción"
---

{cuento_texto}
"""

print("--- DEBUG DE ARCHIVO ---")
print(f"💾 Guardando archivo en: {ruta_archivo}")

with open(ruta_archivo, "w", encoding="utf-8") as f:
    f.write(contenido_markdown)

print("✅ Archivo guardado correctamente en disco.")

# ---------------------------------------------------------------------------
# 5. ENVIAR NOTIFICACIÓN A TELEGRAM
# ---------------------------------------------------------------------------
if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    # Este es el enlace directo a la historia con fecha y título
    url_cuento = f"{SITE_BASE_URL}/cuentos/{slug_cuento}"
    
    # Mensaje simplificado solo con el enlace directo al cuento
    mensaje = (
        f"📖 ¡Nuevo cuento diario!\n\n"
        f"📌 {titulo}\n\n"
        f"📝 {resumen}\n\n"
        f"🔗 Léelo aquí:\n{url_cuento}"
    )
    
    url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
    }
    
    print("--- DEBUG DE TELEGRAM ---")
    print(f"Enviando mensaje a chat_id: {TELEGRAM_CHAT_ID}...")
    try:
        res_telegram = requests.post(url_telegram, json=payload, timeout=10)
        print(f"Status Code Telegram: {res_telegram.status_code}")
        print(f"Respuesta de Telegram: {res_telegram.text}")
    except Exception as e:
        print(f"❌ Error al conectar con la API de Telegram: {e}")
else:
    print("⚠️ No se configuraron TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID. Se omite la notificación.")
