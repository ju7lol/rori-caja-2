from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests

app = Flask(__name__)

# --- Dirección pública o local de la caja ---
CAJA_URL = "https://rori-caja.onrender.com"  # o "http://localhost:5000" si pruebas local

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

# --- Estado actual de los dispositivos (solo memoria)
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

# --- Registro de accesos (memoria)
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

@app.route('/estancia/<estancia_id>/dispositivos/<dispositivo_id>/<accion>', methods=["POST"])
def controlar_rele(estancia_id, dispositivo_id, accion):
    if estancia_id not in estancias or dispositivo_id not in estancias[estancia_id]["dispositivos"]:
        return "Dispositivo o estancia inválido", 404

    if accion not in ["abrir", "cerrar"]:
        return "Acción inválida", 400

    try:
        # Petición a la caja
        respuesta = requests.post(f"{CAJA_URL}/abrir-dispositivo", json={
            "real_estate_uuid": estancia_id,
            "device_uuid": dispositivo_id,
            "accion": accion
        })

        if respuesta.status_code == 200:
            estados_dispositivos[estancia_id][dispositivo_id] = "abierto" if accion == "abrir" else "cerrado"
            return "", 204
        else:
            return jsonify({"error": "Caja respondió con error", "detalle": respuesta.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
