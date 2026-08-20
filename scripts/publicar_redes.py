"""
Publica el cuento del día en Telegram y Facebook.

A diferencia de la versión anterior, este script corre DESPUÉS de que el
sitio ya fue compilado y desplegado (ver .github/workflows/cuento-diario.yml),
y antes de publicar verifica activamente que la URL responda 200. Esto evita
que Facebook/Telegram generen la previsualización contra una página que
todavía no existe (error 404).

También fuerza a Facebook a re-escanear la URL (endpoint de "scrape") justo
antes de publicar, para evitar que quede cacheada una previsualización rota
de un intento anterior.
"""

import os
import sys
import time
import requests

TITULO = os.environ.get("TITULO", "").strip()
RESUMEN = os.environ.get("RESUMEN", "").strip()
URL_CUENTO = os.environ.get("URL_CUENTO", "").strip()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")

if not URL_CUENTO:
    print("❌ No se recibió URL_CUENTO. Abortando publicación en redes.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 1. ESPERAR A QUE LA URL ESTÉ REALMENTE EN LÍNEA (evita el 404)
# ---------------------------------------------------------------------------
MAX_INTENTOS = 15
ESPERA_SEGUNDOS = 20  # hasta ~5 minutos en total

print(f"⏳ Verificando que {URL_CUENTO} esté disponible...")
url_en_linea = False
for intento in range(1, MAX_INTENTOS + 1):
    try:
        resp = requests.get(URL_CUENTO, timeout=10)
        print(f"   Intento {intento}/{MAX_INTENTOS} → status {resp.status_code}")
        if resp.status_code == 200:
            url_en_linea = True
            break
    except Exception as e:
        print(f"   Intento {intento}/{MAX_INTENTOS} → error de conexión: {e}")
    time.sleep(ESPERA_SEGUNDOS)

if not url_en_linea:
    print("❌ La URL no respondió 200 tras varios intentos. No se publicará en redes "
          "para evitar previsualizaciones rotas. Revisa el despliegue de GitHub Pages.")
    sys.exit(1)

print("✅ La página ya está en línea. Continuando con la publicación.")

# ---------------------------------------------------------------------------
# 2. TELEGRAM
# ---------------------------------------------------------------------------
if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    mensaje_telegram = (
        f"📖 <b>¡Nuevo cuento diario!</b>\n\n"
        f"📌 <b>{TITULO}</b>\n\n"
        f"📝 {RESUMEN}\n\n"
        f"🔗 <b>Lee el cuento completo aquí:</b>\n{URL_CUENTO}"
    )

    url_api_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje_telegram,
        "parse_mode": "HTML",
        "link_preview_options": {
            "is_disabled": False,
            "url": URL_CUENTO
        }
    }

    print("--- ENVIANDO A TELEGRAM ---")
    try:
        res_telegram = requests.post(url_api_telegram, json=payload, timeout=10)
        print(f"Status Code Telegram: {res_telegram.status_code}")
        if res_telegram.status_code != 200:
            print(f"⚠️ Respuesta de Telegram: {res_telegram.text}")
    except Exception as e:
        print(f"❌ Error al conectar con Telegram: {e}")
else:
    print("ℹ️ Variables de Telegram no configuradas, se omite ese paso.")

# ---------------------------------------------------------------------------
# 3. FACEBOOK
# ---------------------------------------------------------------------------
if FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN:
    # 3a. Forzar a Facebook a re-escanear el link antes de publicar, para que
    #     no reutilice una previsualización rota cacheada de un intento previo.
    print("--- REFRESCANDO CACHÉ DE FACEBOOK (scrape) ---")
    try:
        res_scrape = requests.post(
            "https://graph.facebook.com/v22.0/",
            data={
                "id": URL_CUENTO,
                "scrape": "true",
                "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
            },
            timeout=15,
        )
        print(f"Status Code Scrape: {res_scrape.status_code}")
        if res_scrape.status_code != 200:
            print(f"⚠️ Respuesta del scrape: {res_scrape.text}")
    except Exception as e:
        print(f"⚠️ No se pudo refrescar la caché de Facebook: {e}")

    # 3b. Publicar en el feed de la página
    url_fb = f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/feed"
    mensaje_facebook = (
        f"📖 ¡Nuevo cuento disponible hoy!\n\n"
        f"✨ {TITULO}\n\n"
        f"{RESUMEN}\n\n"
        f"Lee la historia completa en nuestro sitio web 👇\n"
        f"{URL_CUENTO}"
    )

    payload_fb = {
        "message": mensaje_facebook,
        "link": URL_CUENTO,
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
else:
    print("ℹ️ Variables de Facebook no configuradas, se omite ese paso.")
