import os
import json
import datetime
import time
from slugify import slugify
from google import genai
from google.genai import types
import requests

# 1. Obtener credenciales de GitHub Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://tusitio.com/cuentos")

client = genai.Client(api_key=GEMINI_API_KEY)

prompt = """
Actúa como un prolífico escritor de cuentos cortos en español. 
Genera un cuento corto original e inspirador ambientado en el folklore, misterio o la cotidianeidad de México.
El cuento debe poder leerse en aproximadamente 3 minutos.

Debes responder ÚNICAMENTE con un objeto JSON válido con la siguiente estructura exacta:
{
  "titulo": "Título del cuento",
  "categoria": "Categoría (ej. Leyendas, Misterio Urbano, Vida Cotidiana)",
  "resumen": "Un resumen de 2 líneas que enganche al lector.",
  "contenido_markdown": "El texto completo del cuento formateado en Markdown..."
}
"""

def enviar_telegram(titulo, resumen, url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram no configurado. Saltando notificación.")
        return

    mensaje = (
        f"📖 *Cuento del día:* {titulo}\n\n"
        f"_{resumen}_\n\n"
        f"👉 *Lee la historia completa aquí:* {url}"
    )
    
    endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    response = requests.post(endpoint, json=payload)
    print("Respuesta de Telegram:", response.json())

def generar_con_reintento():
    modelos = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
    
    for modelo in modelos:
        print(f"Intentando generar cuento con el modelo: {modelo}...")
        for intento in range(2):  # Reintenta 2 veces por modelo
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json'
                    )
                )
                return response.text
            except Exception as e:
                print(f"⚠️ Error con {modelo} (intento {intento + 1}): {e}")
                time.sleep(3)  # Espera 3 segundos antes de reintentar
                
    raise Exception("No se pudo generar el cuento tras reintentar con múltiples modelos.")

def main():
    texto_respuesta = generar_con_reintento().strip()

    # Limpiar posibles bloques de código JSON
    if texto_respuesta.startswith("```json"):
        texto_respuesta = texto_respuesta[7:]
    if texto_respuesta.endswith("```"):
        texto_respuesta = texto_respuesta[:-3]

    data = json.loads(texto_respuesta.strip())
    
    fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
    slug = slugify(data["titulo"])
    nombre_archivo = f"{fecha_hoy}-{slug}.md"
    
    # Limpia la URL base quitando slashes al final si existen
    base_clean = SITE_BASE_URL.rstrip("/")
    url_cuento = f"{base_clean}/{fecha_hoy}-{slug}"

    contenido_file = f"""---
title: "{data['titulo']}"
date: {fecha_hoy}
category: "{data['categoria']}"
summary: "{data['resumen']}"
slug: "{fecha_hoy}-{slug}"
---

{data['contenido_markdown']}
"""

    os.makedirs("content/cuentos", exist_ok=True)
    filepath = os.path.join("content/cuentos", nombre_archivo)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(contenido_file)

    print(f"✅ Cuento guardado con éxito en: {filepath}")

    enviar_telegram(data["titulo"], data["resumen"], url_cuento)

if __name__ == "__main__":
    main()
