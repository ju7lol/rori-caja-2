from flask import Flask, render_template, request, jsonify, redirect, url_for
import paho.mqtt.publish as publish

app = Flask(__name__)

# --- Configuración MQTT ---
MQTT_BROKER = "ef91b613700d4d89b3bad259f7d88126.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "xPostex"
MQTT_PASSWORD = "Julito123!"

# --- Base de datos simulada
estancias = {
    "ahdo": {
        "nombre": "Residencial Alcazar",
        "dispositivos": {
            "esp32-principal": "Portón principal",
            "esp32-secundario": "Puerta peatonal"
        },
        "invitaciones": [
            {"codigo": "123456", "dispositivo_id": "esp32-principal"},
            {"codigo": "654321", "dispositivo_id": "esp32-secundario"}
        ]
    },
    "estancia2": {
        "nombre": "Colegio Central",
        "dispositivos": {
            "dispositivo1": "Acceso frontal",
            "dispositivo2": "Acceso trasero"
        },
        "invitaciones": [
            {"codigo": "112233", "dispositivo_id": "dispositivo1"},
            {"codigo": "445566", "dispositivo_id": "dispositivo2"}
        ]
    }
}

# --- Estado de dispositivos en memoria
estados_dispositivos = {
    "ahdo": {
        "esp32-principal": "cerrado",
        "esp32-secundario": "cerrado"
    },
    "estancia2": {
        "dispositivo1": "cerrado",
        "dispositivo2": "cerrado"
    }
}

# --- Registros de acceso en memoria
registros_acceso = {
    "ahdo": [],
    "estancia2": []
}

@app.route('/')
def index():
    return render_template("estancias.html", estancias=estancias)

@app.route('/estancia/<estancia_id>/menu')
def menu_estancia(estancia_id):
    estancia = estancias.get(estancia_id)
    if not estancia:
        return "Estancia no encontrada", 404
    return render_template("menu_estancia.html", estancia_id=estancia_id, estancia=estancia)

@app.route('/estancia/<estancia_id>/invitaciones')
def ver_invitaciones(estancia_id):
    estancia = estancias.get(estancia_id)
    if not estancia:
        return "Estancia no encontrada", 404
    return render_template("invitaciones.html", estancia=estancia, estancia_id=estancia_id)

@app.route('/estancia/<estancia_id>/registros')
def ver_registros(estancia_id):
    estancia = estancias.get(estancia_id)
    if not estancia:
        return "Estancia no encontrada", 404
    registros = registros_acceso.get(estancia_id, [])
    return render_template("registros.html", registros=registros, estancia=estancia, estancia_id=estancia_id)

@app.route('/estancia/<estancia_id>/dispositivos')
def ver_dispositivos(estancia_id):
    estancia = estancias.get(estancia_id)
    if not estancia:
        return "Estancia no encontrada", 404
    estados = estados_dispositivos.get(estancia_id, {})
    return render_template("dispositivos.html", estancia=estancia, estancia_id=estancia_id, estados=estados)

# --- Controlar relé (botón abrir/cerrar)
@app.route('/estancia/<estancia_id>/dispositivos/<dispositivo_id>/<accion>', methods=["POST"])
def controlar_rele(estancia_id, dispositivo_id, accion):
    if estancia_id not in estancias or dispositivo_id not in estancias[estancia_id]["dispositivos"]:
        return "Dispositivo o estancia inválido", 404

    if accion not in ["abrir", "cerrar"]:
        return "Acción inválida", 400

    topic = f"rori/{estancia_id}/dispositivos/{dispositivo_id}/control_remoto"
    try:
        publish.single(
            topic,
            accion,
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            auth={"username": MQTT_USER, "password": MQTT_PASSWORD},
            tls={"cert_reqs": 0}
        )
        estados_dispositivos[estancia_id][dispositivo_id] = "abierto" if accion == "abrir" else "cerrado"
        return "", 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Validación de códigos
@app.route("/validar-codigo", methods=["POST"])
def validar_codigo():
    data = request.json
    estancia_id = data.get("real_estate_uuid")
    dispositivo_id = data.get("device_uuid")
    codigo = data.get("codigo")

    if not (estancia_id and dispositivo_id and codigo):
        return jsonify({"success": False, "message": "Datos incompletos"}), 400

    estancia = estancias.get(estancia_id)
    if not estancia:
        return jsonify({"success": False, "message": "Estancia no encontrada"}), 404

    invitacion_valida = any(
        inv["codigo"] == codigo and inv["dispositivo_id"] == dispositivo_id
        for inv in estancia["invitaciones"]
    )

    registros_acceso.setdefault(estancia_id, []).append({
        "mensaje": "Dispositivo activado" if invitacion_valida else "Intento fallido",
        "codigo": codigo
    })

    return jsonify({"success": invitacion_valida}), 200

# --- Modo manual ---
@app.route('/estancia/<estancia_id>/validar', methods=["GET", "POST"])
def validar_codigo_web(estancia_id):
    estancia = estancias.get(estancia_id)
    if not estancia:
        return "Estancia no encontrada", 404

    resultado = None

    if request.method == "POST":
        codigo = request.form.get("codigo")
        dispositivo_id = request.form.get("dispositivo_id")

        invitacion_valida = any(
            inv["codigo"] == codigo and inv["dispositivo_id"] == dispositivo_id
            for inv in estancia["invitaciones"]
        )

        registros_acceso.setdefault(estancia_id, []).append({
            "mensaje": "Dispositivo activado (web)" if invitacion_valida else "Intento fallido (web)",
            "codigo": codigo
        })

        if invitacion_valida:
            topic = f"rori/{estancia_id}/dispositivos/{dispositivo_id}/abrir"
            try:
                publish.single(
                    topic,
                    "abrir",
                    hostname=MQTT_BROKER,
                    port=MQTT_PORT,
                    auth={"username": MQTT_USER, "password": MQTT_PASSWORD},
                    tls={"cert_reqs": 0}
                )
            except Exception as e:
                resultado = f"Error al abrir el dispositivo: {str(e)}"
            else:
                resultado = "✅ Código válido. Dispositivo abierto."
        else:
            resultado = "❌ Código inválido."

    return render_template("validar_codigo.html", estancia=estancia, estancia_id=estancia_id, resultado=resultado)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
