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

ESTILOS_DE_PROSA = [
    "minimalista: oraciones cortas, secas y directas de menos de diez palabras",
    "prosa poética: enfoque en la atmósfera, texturas, olores y ritmo lento",
    "formato documental: historia contada vía mensajes de texto, correos y audios",
    "flujo de conciencia: pensamientos caóticos sin filtros ni pausas tradicionales"
]

SUBVERSION_DE_TROPOS = [
    "anticlímax: el gran misterio se resuelve de la forma más común y mundana",
    "inversión de roles: el supuesto monstruo es la víctima y el héroe la amenaza",
    "final abierto existencial: se resuelve el dilema interno pero no la trama externa",
    "giro metanarrativo: el lector descubre que forma parte activa del misterio"
]

tema_hoy = random.choice(TEMAS)
genero_hoy = random.choice(GENEROS)
categoria_hoy = genero_hoy  # Para el esquema obligatorio de Astro

print(f"🎲 Tema seleccionado para hoy: {tema_hoy}")
print(f"🎲 Género seleccionado para hoy: {genero_hoy}")

# ---------------------------------------------------------------------------
# 3. LLAMADA A LA API DE GEMINI CON REINTENTOS
# ---------------------------------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
Escribe un cuento corto e inspirador.

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
# 6. ENVIAR NOTIFICACIÓN A TELEGRAM (CON PAUSA PARA PERMITIR DESPLIEGUE)
# ---------------------------------------------------------------------------
if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    base_url_clean = SITE_BASE_URL.strip().rstrip('/')
    slug_clean = slug_cuento.strip()
    
    url_cuento = f"{base_url_clean}/cuentos/{slug_clean}"
    
    print("⏳ Esperando 90 segundos para permitir que el sitio se publique en el servidor...")
    time.sleep(90)
    
    mensaje_telegram = (
        f"📖 <b>¡Nuevo cuento diario!</b>\n\n"
        f"📌 <b>{titulo}</b>\n\n"
        f"📝 {resumen}\n\n"
        f"🔗 <b>Lee el cuento completo aquí:</b>\n{url_cuento}"
    )
    
    url_api_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje_telegram,
        "parse_mode": "HTML",
        "link_preview_options": {
            "is_disabled": False,
            "url": url_cuento
        }
    }
    
    print("--- ENVIANDO A TELEGRAM ---")
    print(f"URL generada: {url_cuento}")
    try:
        res_telegram = requests.post(url_api_telegram, json=payload, timeout=10)
        print(f"Status Code Telegram: {res_telegram.status_code}")
    except Exception as e:
        print(f"❌ Error al conectar con Telegram: {e}")

        # ---------------------------------------------------------------------------
# PUBLICACIÓN EN FACEBOOK
# ---------------------------------------------------------------------------
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")

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
    
    print("--- ENVIANDO A FACEBOOK ---")
    try:
        res_fb = requests.post(url_fb, data=payload_fb, timeout=15)
        if res_fb.status_code == 200:
            print("✅ Publicado con éxito en Facebook.")
        else:
            print(f"⚠️ Error al publicar en Facebook ({res_fb.status_code}): {res_fb.text}")
    except Exception as e:
        print(f"❌ Error al conectar con la API de Facebook: {e}")
