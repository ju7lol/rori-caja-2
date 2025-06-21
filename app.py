from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import threading

app = Flask(__name__)

# Configuración de MQTT
MQTT_BROKER = "ffb81d830b244852851f07010b2d10b7.s1.eu.hivemq.cloud"  # Reemplaza con tu broker HiveMQ
MQTT_PORT = 8883
MQTT_USER = "poste1"
MQTT_PASS = "Trasero123!"

client_mqtt = mqtt.Client()
client_mqtt.username_pw_set(MQTT_USER, MQTT_PASS)
client_mqtt.tls_set()

@app.route('/')
def index():
    return "✅ Caja RORI activa"

@app.route('/validar_invitacion', methods=['POST'])
def validar_invitacion():
    data = request.get_json()
    codigo = data.get('codigo')
    print(f"📥 Validando invitación con código: {codigo}")

    # Simulación de validación (puedes reemplazar esto con lógica real o DB)
    if codigo == "25365534":
        response = {
            "valid": True,
            "anfitrion": "Julio",
            "id_invitacion": "01_xah"
        }
        # Publicar orden de abrir
        client_mqtt.publish("esp32/abrir", "1")
        print("🔓 Publicada orden de apertura para el dispositivo")
    else:
        response = {
            "valid": False
        }
        print("❌ Código inválido")

    return jsonify(response)

def on_connect(client, userdata, flags, rc):
    print("Conectado al broker con código", rc)
    client.subscribe("caja/access_code")

def on_message(client, userdata, msg):
    codigo = msg.payload.decode()
    print(f"📥 Código recibido por MQTT: {codigo}")
    # Puedes opcionalmente llamar al validador interno
    # validar_invitacion_backend(codigo)

def mqtt_thread():
    client_mqtt.on_connect = on_connect
    client_mqtt.on_message = on_message
    client_mqtt.connect(MQTT_BROKER, MQTT_PORT)
    client_mqtt.loop_forever()

# Inicia MQTT en un hilo separado
threading.Thread(target=mqtt_thread, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
