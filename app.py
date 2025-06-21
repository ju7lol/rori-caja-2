from flask import Flask, request, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt
import threading

app = Flask(__name__)
CORS(app, origins=["https://ju7lol.github.io"])

MQTT_BROKER = "ffb81d830b244852851f07010b2d10b7.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "poste1"  # Corrige si era un typo
MQTT_PASS = "Trasero123!"

client_mqtt = mqtt.Client()
client_mqtt.username_pw_set(MQTT_USER, MQTT_PASS)
client_mqtt.tls_set()

@app.route('/')
def index():
    return "✅ Caja RORI activa"

@app.route('/abrir', methods=['POST'])
def abrir_dispositivo():
    dispositivo = request.args.get('dispositivo')
    if not dispositivo:
        return jsonify({"ok": False, "mensaje": "Dispositivo no especificado"}), 400
    client_mqtt.publish(f"{dispositivo}/abrir", "1")
    print(f"🔓 Orden de apertura publicada a {dispositivo}")
    return jsonify({"ok": True})

@app.route('/validar_invitacion', methods=['POST'])
def validar_invitacion():
    data = request.get_json()
    codigo = data.get("codigo")
    if not codigo:
        return jsonify({"valid": False, "mensaje": "Código no proporcionado"}), 400
    if codigo == "0402":
        client_mqtt.publish("esp32/abrir", "1")
        print(f"✅ Acceso permitido con código {codigo}")
        return jsonify({"valid": True, "anfitrion": "Julio", "id_invitacion": "01_xah"})
    else:
        print(f"❌ Acceso denegado con código {codigo}")
        return jsonify({"valid": False})

def on_connect(client, userdata, flags, rc):
    print("Conectado al broker con código", rc)
    client.subscribe("caja/access_code")

def on_message(client, userdata, msg):
    codigo = msg.payload.decode()
    print(f"📥 Código recibido por MQTT: {codigo}")
    # Llama validación local directamente
    if codigo == "0402":
        client_mqtt.publish("esp32/abrir", "1")
        print(f"✅ Acceso permitido (MQTT code {codigo})")
    else:
        print(f"❌ Acceso denegado (MQTT code {codigo})")

def mqtt_thread():
    client_mqtt.on_connect = on_connect
    client_mqtt.on_message = on_message
    client_mqtt.connect(MQTT_BROKER, MQTT_PORT)
    client_mqtt.loop_forever()

threading.Thread(target=mqtt_thread, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
