import os
import io
import json
import base64
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DRIVE_ENABLED = True
DEFAULT_FOLDER_ID = "1TzxE-VvnOQTXz-CBZsmWMPv--yK6ZA4U"

APPS_SCRIPT_URL = os.environ.get(
    'GOOGLE_APPS_SCRIPT_URL',
    'https://script.google.com/macros/s/AKfycbynKYAQnvRy-s3bMm57KuADK1inIz8E4YcZJhWCm8lJxeCvzjljEr9EuggMRfW7MqYkhg/exec'
)


def upload_excel_to_drive(excel_data: bytes, file_name: str, folder_id: str = None) -> str:
    fid = folder_id or DEFAULT_FOLDER_ID
    logger.info(f"📤 Upload via Apps Script: {file_name} → pasta {fid}")

    try:
        payload = {
            'fileName': file_name,
            'folderId': fid,
            'fileData': base64.b64encode(excel_data).decode('utf-8')
        }

        # Apps Script redireciona POST → precisa de sessão para seguir
        session = requests.Session()
        response = session.post(
            APPS_SCRIPT_URL,
            data=json.dumps(payload),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=60,
            allow_redirects=True
        )

        logger.info(f"Status: {response.status_code} | URL final: {response.url}")
        logger.info(f"Resposta: {response.text[:300]}")

        text = response.text.strip()
        if not text:
            logger.error("❌ Resposta vazia do Apps Script")
            return None

        # Tenta parsear JSON
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # Apps Script às vezes retorna HTML de erro
            if 'success' in text.lower():
                logger.info("✅ Upload aparentemente OK (resposta não-JSON)")
                return 'ok'
            logger.error(f"❌ Resposta inválida: {text[:200]}")
            return None

        if result.get('success'):
            file_id = result.get('fileId', 'ok')
            logger.info(f"✅ Upload OK! fileId: {file_id}")
            return file_id
        else:
            logger.error(f"❌ Erro do Apps Script: {result.get('error')}")
            return None

    except requests.exceptions.Timeout:
        logger.error("❌ Timeout ao chamar Apps Script")
        return None
    except Exception as e:
        logger.error(f"❌ Erro upload: {e}")
        return None


def list_drive_folders(parent_id=None):
    return []


def get_drive_folders():
    from flask import jsonify
    return jsonify({
        'success': True,
        'folders': [],
        'default_folder_id': DEFAULT_FOLDER_ID
    })


def is_drive_connected():
    return True


def export_attendance_drive(app_data):
    from flask import jsonify
    return jsonify({'success': False, 'error': 'Use /api/export_excel_drive'}), 400
