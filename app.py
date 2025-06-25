from flask import Flask
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# Parámetros MQTT
broker = "ef91b613700d4d89b3bad259f7d88126.s1.eu.hivemq.cloud"
port = 8883
user = "xPostex"
password = "Julito123!"
topic_base = "rori/ahdo/dispositivos/esp32-principal"

# Códigos válidos locales
CODIGOS_VALIDOS = ["771200", "040200"]

def on_connect(client, userdata, flags, rc):
    print("🟢 Conectado al broker con código", rc)
    client.subscribe(f"{topic_base}/estado")

def on_message(client, userdata, msg):
    print(f"📩 Mensaje en {msg.topic}: {msg.payload}")
    try:
        data = json.loads(msg.payload.decode())
        codigo = data.get("codigo")
        print("Código recibido:", codigo)

        if codigo in CODIGOS_VALIDOS:
            respuesta = {"validacion": "valido"}
            client.publish(f"{topic_base}/status", json.dumps(respuesta))
            client.publish(f"{topic_base}/abrir", "abrir")
        else:
            respuesta = {"validacion": "invalido"}
            client.publish(f"{topic_base}/status", json.dumps(respuesta))

    except Exception as e:
        print("❌ Error al procesar:", e)

client = mqtt.Client()
client.username_pw_set(user, password)
client.tls_set()  # Conexión segura
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port, 60)

client.loop_start()
