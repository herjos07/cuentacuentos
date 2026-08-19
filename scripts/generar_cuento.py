def generar_con_reintento():
    # Modelos válidos y activos de la API
    modelos = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    
    for modelo in modelos:
        print(f"Intentando generar cuento con el modelo: {modelo}...")
        for intento in range(3):  # 3 intentos por modelo
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
                tiempo_espera = (intento + 1) * 5  # Espera 5s, luego 10s...
                print(f"⚠️ Error con {modelo} (intento {intento + 1}): {e}")
                print(f"Reintentando en {tiempo_espera} segundos...")
                time.sleep(tiempo_espera)
                
    raise Exception("No se pudo generar el cuento tras reintentar con múltiples modelos.")
