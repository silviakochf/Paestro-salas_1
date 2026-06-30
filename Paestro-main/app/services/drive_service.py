import os
import io
import json
import logging
from flask import request, jsonify, current_app
from dotenv import load_dotenv

# Importa o exportador 
from .excel_service import export_to_excel, get_excel_filename

# Carrega as variáveis do arquivo .env
load_dotenv()

logger = logging.getLogger(__name__)

# Variável para controlar se temos Google Drive habilitado
DRIVE_ENABLED = False
drive_service = None

# ==============================================================================
# CONFIGURAÇÃO DE AUTENTICAÇÃO (SERVICE ACCOUNT - MODO WEB)
# ==============================================================================
def initialize_drive():
    global DRIVE_ENABLED, drive_service
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Pega as credenciais da variável de ambiente (Service Account)
        json_creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        
        if json_creds:
            SCOPES = ['https://www.googleapis.com/auth/drive']
            
            try:
                # Tenta carregar como JSON string (Render)
                creds_dict = json.loads(json_creds)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict, scopes=SCOPES
                )
            except json.JSONDecodeError:
                # Tenta carregar como caminho de arquivo (Local)
                credentials = service_account.Credentials.from_service_account_file(
                    json_creds, scopes=SCOPES
                )

            drive_service = build('drive', 'v3', credentials=credentials)
            DRIVE_ENABLED = True
            logger.info("✅ Google Drive conectado (Modo Service Account)!")
        else:
            logger.warning("⚠️ Variável GOOGLE_CREDENTIALS_JSON não encontrada.")

    except ImportError:
        logger.error("❌ Bibliotecas do Google não instaladas.")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar no Drive: {str(e)}")

# Inicializa ao carregar o módulo
initialize_drive()

# ==============================================================================
# FUNÇÕES DE SERVIÇO
# ==============================================================================

def upload_excel_to_drive(excel_data, file_name, folder_id=None):
    """Faz upload de um arquivo Excel para o Google Drive."""
    if not DRIVE_ENABLED or not drive_service:
        return "drive-not-available"
        
    try:
        from googleapiclient.http import MediaIoBaseUpload

        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]

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

        logger.info(f"Upload realizado: {file.get('id')}")
        return file.get('id')
    except Exception as e:
        logger.error(f"Erro no Upload Drive: {str(e)}")
        return None

def get_drive_folders():
    """Retorna a lista de pastas disponíveis no Google Drive (via Config)."""
    if not DRIVE_ENABLED:
        return jsonify({
            'success': False, 
            'error': 'Google Drive não está habilitado nesta instalação.',
            'folders': []
        }) 
   
    try:
        # Pega o mapa de pastas direto da configuração global do app
        folder_map = current_app.config.get('FOLDER_MAP', {})
        folder_list = [{'id': v, 'name': k} for k, v in folder_map.items()]
        return jsonify({'success': True, 'folders': folder_list})
    except Exception as e:
        logger.error(f"Erro ao listar pastas: {e}")
        return jsonify({'success': False, 'error': str(e)})

def export_attendance_drive(app_data):
    """Lógica completa de exportação e upload."""
    if not DRIVE_ENABLED:
        return jsonify({
            'success': False, 
            'error': 'Google Drive indisponível.',
            'alternate_message': 'Download manual disponível.'
        }), 400
        
    try:
        data = request.json
        if not data: return jsonify({'success': False, 'error': 'Sem dados'}), 400

        folder_id = data.get('folder_id')
        escola_selecionada = data.get('escola')
        auto_clear = data.get('auto_clear', False)

        if not folder_id:
            return jsonify({'success': False, 'error': 'ID da pasta inválido'}), 400

        # Filtra as turmas
        if 'saved_classes' not in app_data:
            return jsonify({'success': False, 'error': 'Nada salvo'}), 400

        if escola_selecionada:
            turmas_salvas = app_data['saved_classes'].get(escola_selecionada, [])
        else:
            turmas_salvas = set().union(*app_data['saved_classes'].values())

        if not turmas_salvas:
            return jsonify({'success': False, 'error': 'Nenhuma turma para exportar'}), 400

        # Prepara dados para o Excel Service
        classes_to_export = {}
        attendance_to_export = {}
        observations_to_export = {}

        for turma in turmas_salvas:
            for escola, turmas in app_data['schools'].items():
                if turma in turmas:
                    if escola_selecionada and escola != escola_selecionada: continue
                    classes_to_export[turma] = app_data['schools'][escola][turma]
                    attendance_to_export[turma] = app_data['attendance_status'].get(turma, {})
                    observations_to_export[turma] = app_data['observations'].get(turma, {})
                    break

        periodo = data.get('periodo') or app_data.get('periodo', 'N/D')
        current_user = app_data.get('current_user', 'Usuario')

        # 1. Gera o Excel na memória
        output = export_to_excel(
            classes_to_export,
            attendance_to_export,
            observations_to_export,
            app_data.get('html_content', {}).get(escola_selecionada),
            current_user,
            periodo,
            escola_selecionada or "Geral"
        )

        # 2. Faz o Upload
        excel_data = output.getvalue()
        file_name = get_excel_filename(escola_selecionada or "Geral", periodo, current_user)
        
        drive_file_id = upload_excel_to_drive(excel_data, file_name, folder_id)
        
        if not drive_file_id:
            return jsonify({'success': False, 'error': 'Erro de permissão/upload no Drive.'}), 500

        return jsonify({'success': True, 'drive_file_id': drive_file_id}), 200

    except Exception as e:
        logger.error(f"Erro exportação Drive: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500