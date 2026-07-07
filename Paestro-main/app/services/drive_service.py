import os
import io
import json
import base64
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DRIVE_ENABLED = True  # Sempre habilitado via Apps Script
DEFAULT_FOLDER_ID = "1TzxE-VvnOQTXz-CBZsmWMPv--yK6ZA4U"

# URL do Google Apps Script que faz o upload
APPS_SCRIPT_URL = os.environ.get(
    'GOOGLE_APPS_SCRIPT_URL',
    'https://script.google.com/macros/s/AKfycbynKYAQnvRy-s3bMm57KuADK1inIz8E4YcZJhWCm8lJxeCvzjljEr9EuggMRfW7MqYkhg/exec'
)


def upload_excel_to_drive(excel_data: bytes, file_name: str, folder_id: str = None) -> str:
    """
    Faz upload do Excel para o Google Drive via Apps Script.
    Retorna o file_id ou None em caso de erro.
    """
    fid = folder_id or DEFAULT_FOLDER_ID
    logger.info(f"📤 Upload via Apps Script: {file_name} → pasta {fid}")

    try:
        payload = {
            'fileName': file_name,
            'folderId': fid,
            'fileData': base64.b64encode(excel_data).decode('utf-8')
        }

        response = requests.post(
            APPS_SCRIPT_URL,
            json=payload,
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )

        result = response.json()

        if result.get('success'):
            file_id = result.get('fileId', 'ok')
            logger.info(f"✅ Upload OK! fileId: {file_id}")
            return file_id
        else:
            error = result.get('error', 'Erro desconhecido')
            logger.error(f"❌ Apps Script retornou erro: {error}")
            return None

    except requests.exceptions.Timeout:
        logger.error("❌ Timeout ao chamar o Apps Script")
        return None
    except Exception as e:
        logger.error(f"❌ Erro no upload via Apps Script: {e}")
        return None


def list_drive_folders(parent_id=None):
    """Não usado — pastas vêm do FOLDER_MAP do config.py"""
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
