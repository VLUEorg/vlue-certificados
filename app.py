from flask import Flask, request, jsonify
import base64
import os
from cert_generator import generate_certificate_bytes

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/generate', methods=['POST'])
def generate():
    try:
        data        = request.json
        codigo      = data['codigo']
        nombre      = data['nombre']
        fecha       = data['fecha']
        descripcion = data['descripcion']
        horas       = data.get('horas', '')
        url_qr      = data.get('url_qr', None)

        # Generar certificado y devolver base64 directamente
        img_bytes = generate_certificate_bytes(nombre, horas, fecha, codigo, descripcion, url_qr)
        b64       = base64.b64encode(img_bytes).decode()

        return jsonify({'image_b64': b64, 'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
