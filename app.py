from flask import Flask
import paho.mqtt.client as mqtt
import requests
import threading

app = Flask(__name__)

MQTT_BROKER = "ffb81d830b244852851f07010b2d10b7.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "poste1"
MQTT_PASS = "Trasero123!"

client_mqtt = mqtt.Client()
client_mqtt.username_pw_set(MQTT_USER, MQTT_PASS)
client_mqtt.tls_set()

@app.route('/')
def index():
    return "Caja RORI funcionando"

def on_connect(client, userdata, flags, rc):
    print("Conectado al broker con código", rc)
    client.subscribe("caja/access_code")

def on_message(client, userdata, msg):
    codigo = msg.payload.decode()
    print(f"📥 Código recibido: {codigo}")
    validar_en_backend(codigo)

def validar_en_backend(codigo):
    url = "https://rori-caja.onrender.com/validar_invitacion"
    data = { "codigo": codigo }
    try:
        resp = requests.post(url, json=data)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("valid"):
                print(f"✅ Acceso permitido. Anfitrión: {result.get('anfitrion')}, ID: {result.get('id_invitacion')}")
                client_mqtt.publish("esp32/abrir", "1")
            else:
                print("❌ Acceso denegado.")
        else:
            print("⚠ Error en backend:", resp.status_code)
    except Exception as e:
        print("⚠ Error al validar:", e)

def mqtt_thread():
    client_mqtt.on_connect = on_connect
    client_mqtt.on_message = on_message
    client_mqtt.connect(MQTT_BROKER, MQTT_PORT)
    client_mqtt.loop_forever()

# Iniciar MQTT en un hilo
threading.Thread(target=mqtt_thread).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
