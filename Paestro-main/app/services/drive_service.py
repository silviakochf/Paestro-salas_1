import os
import io
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DRIVE_ENABLED = False
drive_service = None

DEFAULT_FOLDER_ID = "1TzxE-VvnOQTXz-CBZsmWMPv--yK6ZA4U"


def initialize_drive():
    global DRIVE_ENABLED, drive_service
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/drive']

        json_creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not json_creds:
            logger.warning("⚠️ GOOGLE_CREDENTIALS_JSON não encontrada — Drive desabilitado.")
            return

        # Tenta parsear como JSON direto
        try:
            creds_dict = json.loads(json_creds)
            logger.info(f"✅ Credencial lida da variável de ambiente (project: {creds_dict.get('project_id')})")
        except json.JSONDecodeError:
            # É um caminho de arquivo
            logger.info(f"Lendo credencial do arquivo: {json_creds}")
            with open(json_creds) as f:
                creds_dict = json.load(f)

        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        DRIVE_ENABLED = True
        logger.info(f"✅ Google Drive conectado! Service Account: {creds_dict.get('client_email')}")

    except ImportError as e:
        logger.error(f"❌ Biblioteca Google não instalada: {e}")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Drive: {type(e).__name__}: {e}")


initialize_drive()


def upload_excel_to_drive(excel_data: bytes, file_name: str, folder_id: str = None):
    """Faz upload de bytes para o Drive. Retorna file_id ou None."""
    if not DRIVE_ENABLED or not drive_service:
        logger.error("❌ upload_excel_to_drive: Drive não habilitado")
        return "drive-not-available"

    fid = folder_id or DEFAULT_FOLDER_ID
    logger.info(f"📤 Iniciando upload: {file_name} → pasta {fid}")

    try:
        from googleapiclient.http import MediaIoBaseUpload

        file_metadata = {'name': file_name, 'parents': [fid]}
        media = MediaIoBaseUpload(
            io.BytesIO(excel_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            resumable=False
        )

        result = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        file_id = result.get('id')
        logger.info(f"✅ Upload concluído! file_id: {file_id}")
        return file_id

    except Exception as e:
        logger.error(f"❌ Erro no upload para pasta {fid}: {type(e).__name__}: {e}")
        return None


def list_drive_folders(parent_id=None):
    """Lista subpastas de uma pasta do Drive."""
    if not DRIVE_ENABLED or not drive_service:
        return []
    try:
        q = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        q += f" and '{parent_id or DEFAULT_FOLDER_ID}' in parents"
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


def get_drive_folders():
    from flask import jsonify
    if not DRIVE_ENABLED:
        return jsonify({'success': False, 'error': 'Drive não habilitado', 'folders': []})
    folders = list_drive_folders()
    return jsonify({'success': True, 'folders': folders, 'default_folder_id': DEFAULT_FOLDER_ID})


def export_attendance_drive(app_data):
    from flask import jsonify
    return jsonify({'success': False, 'error': 'Use /api/export_excel_drive'}), 400
