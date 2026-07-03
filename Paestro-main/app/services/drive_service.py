import os
import io
import json
import logging
from flask import request, jsonify, current_app
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DRIVE_ENABLED  = False
drive_service  = None

# Pasta padrão do Drive da secretaria
DEFAULT_FOLDER_ID = "1TzxE-VvnOQTXz-CBZsmWMPv--yK6ZA4U"


def initialize_drive():
    global DRIVE_ENABLED, drive_service
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/drive']

        json_creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not json_creds:
            logger.warning("⚠️ Variável GOOGLE_CREDENTIALS_JSON não encontrada.")
            return

        try:
            creds_dict = json.loads(json_creds)
        except json.JSONDecodeError:
            with open(json_creds) as f:
                creds_dict = json.load(f)

        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        DRIVE_ENABLED = True
        logger.info("✅ Google Drive conectado (Service Account)!")

    except ImportError:
        logger.error("❌ Bibliotecas do Google não instaladas.")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar no Drive: {e}")


initialize_drive()


def list_drive_folders(parent_id=None):
    """Lista subpastas de uma pasta do Drive (ou da raiz compartilhada)."""
    if not DRIVE_ENABLED or not drive_service:
        return []
    try:
        q = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        else:
            q += f" and '{DEFAULT_FOLDER_ID}' in parents"

        result = drive_service.files().list(
            q=q,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        return result.get('files', [])
    except Exception as e:
        logger.error(f"Erro list_drive_folders: {e}")
        return []


def upload_excel_to_drive(excel_data: bytes, file_name: str, folder_id: str = None) -> str | None:
    """Faz upload de bytes para o Drive. Retorna o file_id ou None."""
    if not DRIVE_ENABLED or not drive_service:
        return "drive-not-available"
    try:
        from googleapiclient.http import MediaIoBaseUpload

        fid = folder_id or DEFAULT_FOLDER_ID
        file_metadata = {'name': file_name, 'parents': [fid]}

        media = MediaIoBaseUpload(
            io.BytesIO(excel_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            resumable=True
        )

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()

        logger.info(f"✅ Upload Drive OK: {file.get('id')}")
        return file.get('id')
    except Exception as e:
        logger.error(f"Erro upload Drive: {e}")
        return None


def get_drive_folders():
    """Rota-helper: retorna lista de pastas da pasta principal + subpastas."""
    folders = list_drive_folders()
    if not DRIVE_ENABLED:
        from flask import jsonify
        return jsonify({'success': False, 'error': 'Drive não habilitado', 'folders': []})
    from flask import jsonify
    return jsonify({'success': True, 'folders': folders, 'default_folder_id': DEFAULT_FOLDER_ID})


def export_attendance_drive(app_data):
    """Mantido para compatibilidade com rotas antigas."""
    from flask import jsonify
    return jsonify({'success': False, 'error': 'Use /api/export_excel_drive'}), 400
