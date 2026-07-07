
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
    logger.info(f"Upload via Apps Script: {file_name} para pasta {fid}")
    try:
        payload = {
            'fileName': file_name,
            'folderId': fid,
            'fileData': base64.b64encode(excel_data).decode('utf-8')
        }
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=60)
        result = response.json()
        if result.get('success'):
            logger.info(f"Upload OK! fileId: {result.get('fileId')}")
            return result.get('fileId', 'ok')
        else:
            logger.error(f"Apps Script erro: {result.get('error')}")
            return None
    except Exception as e:
        logger.error(f"Erro upload: {e}")
        return None


def list_drive_folders(parent_id=None):
    return []


def get_drive_folders():
    from flask import jsonify
    return jsonify({'success': True, 'folders': [], 'default_folder_id': DEFAULT_FOLDER_ID})


def is_drive_connected():
    return True


def export_attendance_drive(app_data):
    from flask import jsonify
    return jsonify({'success': False, 'error': 'Use /api/export_excel_drive'}), 400
