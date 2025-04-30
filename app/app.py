from flask import Flask, jsonify
from flask_cors import CORS
import os

from app.controlador.MedicationRequestCrud import GetMedicationRequestById

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde otros orígenes (como el frontend en otro dominio)

@app.route('/api/medication/<string:med_id>', methods=['GET'])
def get_medication_by_id(med_id):
    status, data = GetMedicationRequestById(med_id)
    if status == "success":
        return jsonify(data)
    elif status == "notFound":
        return jsonify({"error": "No encontrado"}), 404
    else:
        return jsonify({"error": status}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Para Render o local
    app.run(host='0.0.0.0', port=port)
