import os
import json
import datetime
from slugify import slugify
import google.generativeai as genai
import requests

# 1. Configurar credenciales
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://tusitio.com/cuentos")

genai.configure(api_key=GEMINI_API_KEY)

# 2. Prompt estructurado para la historia
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

def main():
    # Usar el modelo estable gemini-1.5-flash
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )

    data = json.loads(response.text)
    
    fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
    slug = slugify(data["titulo"])
    nombre_archivo = f"{fecha_hoy}-{slug}.md"
    url_cuento = f"{SITE_BASE_URL}/{fecha_hoy}-{slug}"

    # Formatear el contenido Markdown
    contenido_file = f"""---
title: "{data['titulo']}"
date: {fecha_hoy}
category: "{data['categoria']}"
summary: "{data['resumen']}"
slug: "{fecha_hoy}-{slug}"
---

{data['contenido_markdown']}
"""

    # Guardar en la carpeta content/cuentos/
    os.makedirs("content/cuentos", exist_ok=True)
    filepath = os.path.join("content/cuentos", nombre_archivo)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(contenido_file)

    print(f"✅ Cuento guardado con éxito en: {filepath}")

    # Enviar a Telegram
    enviar_telegram(data["titulo"], data["resumen"], url_cuento)

if __name__ == "__main__":
    main()
