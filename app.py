from flask import Flask, request, jsonify
import base64
import requests
import os
from cert_generator import generate_certificate_bytes

app = Flask(__name__)

IMGBB_KEY = os.environ.get('IMGBB_KEY', '')


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

        # Generar certificado
        img_bytes = generate_certificate_bytes(nombre, horas, fecha, codigo, descripcion, url_qr)

        # Subir a ImgBB
        b64      = base64.b64encode(img_bytes).decode()
        resp     = requests.post('https://api.imgbb.com/1/upload', data={
            'key'  : IMGBB_KEY,
            'name' : codigo,
            'image': b64,
        })
        resp_data = resp.json()

        if not resp_data.get('success'):
            return jsonify({'error': 'ImgBB upload failed', 'details': resp_data}), 500

        return jsonify({'url': resp_data['data']['display_url'], 'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
