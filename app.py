import paho.mqtt.client as mqtt
import json
import time
import requests  # para hacer el POST al simulador

# --- CONFIGURACIÓN ---
broker = "ef91b613700d4d89b3bad259f7d88126.s1.eu.hivemq.cloud"
port = 8883
user = "xPostex"
password = "Julito123!"
topic_base = "rori/ahdo/dispositivos/esp32-principal"

# URL del simulador
simulador_url = "http://192.168.10.250:5000/validar-codigo"  # Cambia la IP según sea necesario

# --- Conexión y manejo MQTT ---
def on_connect(client, userdata, flags, rc):
    print("🟢 Conectado al broker:", rc)
    client.subscribe(f"{topic_base}/estado")

def on_message(client, userdata, msg):
    print(f"📩 [{msg.topic}] {msg.payload.decode()}")
    try:
        data = json.loads(msg.payload.decode())
        codigo = data.get("codigo")

        # Datos para enviar al simulador
        payload = {
            "codigo": codigo,
            "real_estate_uuid": "estancia1",  # ← cambia si es necesario
            "device_uuid": "dispositivo1"     # ← cambia si es necesario
        }

        # Petición al simulador
        respuesta = requests.post(simulador_url, json=payload)
        resultado = respuesta.json()

        if resultado.get("valido"):
            print("✅ Código válido desde el simulador.")
            client.publish(f"{topic_base}/status", json.dumps({"validacion": "valido"}))
            client.publish(f"{topic_base}/abrir", "abrir")
        else:
            print("⛔ Código inválido según simulador.")
            client.publish(f"{topic_base}/status", json.dumps({"validacion": "invalido"}))

    except Exception as e:
        print("❌ Error procesando mensaje:", e)

# --- Cliente MQTT ---
client = mqtt.Client()
client.username_pw_set(user, password)
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, port, 60)
client.loop_start()

# --- Mantener vivo ---
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("🔴 Detenido por el usuario")
    client.loop_stop()
