import os
import logging
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, session, send_file, current_app

from app.services import drive_service
from app.logic import data as data_manager
from app.logic import parser_salas_meta
from app.logic.relatorio_salas import gerar_relatorio_salas_xlsx
from app.logic.relatorio_salas_xml import gerar_relatorio_salas_xml

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


@main_bp.context_processor
def inject_now():
    """Injeta a variável 'now' em todos os templates."""
    return {'now': datetime.now()}


# ==============================================================================
# 1. ROTAS DE NAVEGAÇÃO (PÁGINAS)
# ==============================================================================

@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/importar')
def importar():
    return render_template('importar.html')


@main_bp.route('/salas')
def salas():
    return render_template('salas.html')


@main_bp.route('/exportar')
def exportar():
    return render_template('exportar.html')


# ==============================================================================
# 2. FUNÇÕES AUXILIARES
# ==============================================================================

def get_session_file():
    filename = "SHARED_VISIT_DATA.json"
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    return os.path.join(current_app.config['UPLOAD_FOLDER'], filename)


# ==============================================================================
# 3. API - LOGIN E USUÁRIO
# ==============================================================================

@main_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    periodo = data.get('periodo')
    senha = data.get('senha')

    correct_password = os.environ.get('APP_PASSWORD')
    if correct_password and senha != correct_password:
        return jsonify({'success': False, 'error': 'Senha incorreta'}), 401

    session['username'] = username
    session['periodo'] = periodo

    app_data = data_manager.load_data(get_session_file())
    app_data['current_user'] = username
    app_data['periodo'] = periodo
    data_manager.save_data(app_data, get_session_file())

    return jsonify({'success': True})


@main_bp.route('/api/get_current_user', methods=['GET'])
def get_current_user():
    app_data = data_manager.load_data(get_session_file())
    username = app_data.get('current_user') or session.get('username')
    periodo = app_data.get('periodo') or session.get('periodo')
    return jsonify({'success': True, 'username': username, 'periodo': periodo})


# ==============================================================================
# 4. API - ESCOLAS
# ==============================================================================

@main_bp.route('/api/get_schools', methods=['GET'])
def get_schools():
    app_data = data_manager.load_data(get_session_file())
    schools = sorted(list(app_data.get('salas_turmas', {}).keys()))
    return jsonify({'success': True, 'schools': schools})


# ==============================================================================
# 5. API - IMPORTAR HTML (EXTRAI TURMAS + SALAS)
# ==============================================================================

@main_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Recebe um ou mais HTMLs do EducarWEB e extrai turma/sala/turno de cada escola."""
    if 'files[]' not in request.files and 'files' not in request.files and 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400

    if 'file' in request.files:
        files = [request.files['file']]
    else:
        files = request.files.getlist('files[]') or request.files.getlist('files')

    session_file = get_session_file()
    current_data = data_manager.load_data(session_file)
    processed_count = 0
    errors = []
    escolas_processadas = []

    for file in files:
        if not file or file.filename == '':
            continue
        try:
            content = file.read().decode('utf-8', errors='ignore')
            meta = parser_salas_meta.parse_salas_meta(content)

            if not meta.get('turmas'):
                errors.append(f"Nenhuma turma encontrada em {file.filename}")
                continue

            escola_nome = meta.get('escola') or file.filename.rsplit('.', 1)[0]

            sala_dict = {t['turma']: {'sala': t['sala'], 'turno': t['turno']} for t in meta['turmas']}
            current_data.setdefault('salas_meta', {})[escola_nome] = sala_dict
            current_data.setdefault('salas_turmas', {})[escola_nome] = meta['turmas']
            current_data.setdefault('salas_marks', {}).setdefault(escola_nome, {})

            processed_count += 1
            escolas_processadas.append(escola_nome)

        except Exception as e:
            errors.append(f"Erro em {file.filename}: {str(e)}")
            logger.error(f"Upload erro: {e}")

    data_manager.save_data(current_data, session_file)

    return jsonify({
        'success': processed_count > 0,
        'processed_count': processed_count,
        'schools': escolas_processadas,
        'error': "; ".join(errors) if errors else None
    })


@main_bp.route('/api/get_imported_files', methods=['GET'])
def get_imported_files():
    app_data = data_manager.load_data(get_session_file())
    files = []
    for escola, turmas in app_data.get('salas_turmas', {}).items():
        files.append({'name': f"Dados de {escola}", 'count': len(turmas)})
    return jsonify({'success': True, 'files': files})


@main_bp.route('/api/delete_file', methods=['POST'])
def delete_file():
    filename = request.json.get('filename', '')
    escola_nome = filename.replace("Dados de ", "")
    app_data = data_manager.load_data(get_session_file())

    removed = False
    for key in ('salas_meta', 'salas_turmas', 'salas_marks'):
        if escola_nome in app_data.get(key, {}):
            del app_data[key][escola_nome]
            removed = True

    if removed:
        data_manager.save_data(app_data, get_session_file())
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Arquivo não encontrado'})


# ==============================================================================
# 6. API - CONFERÊNCIA DE SALAS
# ==============================================================================

@main_bp.route('/api/get_salas_turmas', methods=['POST'])
def get_salas_turmas():
    """Retorna a lista de turmas+salas de uma escola já importada."""
    req = request.json
    escola = req.get('escola', '')

    app_data = data_manager.load_data(get_session_file())
    turmas = app_data.get('salas_turmas', {}).get(escola, [])
    marks = app_data.get('salas_marks', {}).get(escola, {})

    return jsonify({'success': True, 'turmas': turmas, 'marks': marks})


@main_bp.route('/api/save_salas_marks', methods=['POST'])
def save_salas_marks():
    """Persiste as marcações SN/NE/C de uma escola."""
    try:
        req = request.json
        escola = req.get('escola', '')
        turmas = req.get('turmas', [])
        marks = req.get('marks', {})

        app_data = data_manager.load_data(get_session_file())
        app_data.setdefault('salas_marks', {})[escola] = marks
        if turmas:
            app_data.setdefault('salas_turmas', {})[escola] = turmas

        data_manager.save_data(app_data, get_session_file())
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro save_salas_marks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# 7. API - EXPORTAÇÃO (EXCEL / XML / DRIVE)
# ==============================================================================

@main_bp.route('/api/exportar_relatorio_salas', methods=['POST'])
def exportar_relatorio_salas():
    """Gera e devolve o Excel de conferência de salas de UMA escola."""
    try:
        req = request.json
        escola = req.get('escola', 'Escola')
        turmas = req.get('turmas', [])
        marks = req.get('marks', {})

        if not turmas:
            app_data = data_manager.load_data(get_session_file())
            turmas = app_data.get('salas_turmas', {}).get(escola, [])
            marks = app_data.get('salas_marks', {}).get(escola, {})

        buf = gerar_relatorio_salas_xlsx(escola, turmas, marks)
        date_str = datetime.now().strftime('%d-%m-%Y')
        filename = f"conferencia_salas_{escola}_{date_str}.xlsx".replace(' ', '_')

        return send_file(
            buf,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Erro exportar_relatorio_salas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/exportar_relatorio_xml', methods=['POST'])
def exportar_relatorio_xml():
    """Gera e devolve o XML de conferência de salas de UMA escola."""
    try:
        req = request.json
        escola = req.get('escola', 'Escola')
        turmas = req.get('turmas', [])
        marks = req.get('marks', {})

        if not turmas:
            app_data = data_manager.load_data(get_session_file())
            turmas = app_data.get('salas_turmas', {}).get(escola, [])
            marks = app_data.get('salas_marks', {}).get(escola, {})

        xml_bytes = gerar_relatorio_salas_xml(escola, turmas, marks)
        date_str = datetime.now().strftime('%d-%m-%Y')
        filename = f"conferencia_salas_{escola}_{date_str}.xml".replace(' ', '_')

        return send_file(
            xml_bytes,
            mimetype='application/xml',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Erro exportar_relatorio_xml: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/exportar_todas_xml_drive', methods=['POST'])
def exportar_todas_xml_drive():
    """
    Gera um XML por escola (todas as escolas importadas) e envia cada um
    para a pasta do Google Drive correspondente (FOLDER_MAP em config.py).
    """
    try:
        app_data = data_manager.load_data(get_session_file())
        salas_turmas = app_data.get('salas_turmas', {})
        salas_marks = app_data.get('salas_marks', {})
        folder_map = current_app.config.get('FOLDER_MAP', {})

        if not salas_turmas:
            return jsonify({'success': False, 'error': 'Nenhuma escola importada ainda.'}), 400

        resultados = []
        date_str = datetime.now().strftime('%d-%m-%Y')

        for escola, turmas in salas_turmas.items():
            marks = salas_marks.get(escola, {})
            xml_buf = gerar_relatorio_salas_xml(escola, turmas, marks)
            xml_bytes = xml_buf.getvalue()

            filename = f"conferencia_salas_{escola}_{date_str}.xml".replace(' ', '_')
            folder_id = folder_map.get(escola.upper()) or folder_map.get(escola)

            if not folder_id:
                resultados.append({'escola': escola, 'success': False, 'error': 'Pasta do Drive não mapeada para esta escola'})
                continue

            file_id = drive_service.upload_excel_to_drive(xml_bytes, filename, folder_id)
            if file_id in (None, 'drive-not-available'):
                resultados.append({'escola': escola, 'success': False, 'error': 'Falha no upload ao Drive'})
            else:
                resultados.append({'escola': escola, 'success': True, 'file_id': file_id})

        sucesso_total = all(r['success'] for r in resultados) if resultados else False
        return jsonify({'success': sucesso_total, 'resultados': resultados})

    except Exception as e:
        logger.error(f"Erro exportar_todas_xml_drive: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/get_drive_folders', methods=['GET'])
def get_drive_folders():
    return drive_service.get_drive_folders()


@main_bp.route('/api/export_xml_drive', methods=['POST'])
def export_xml_drive():
    """Exporta o XML de UMA escola específica para uma pasta escolhida manualmente no Drive."""
    try:
        req = request.json
        escola = req.get('escola', 'Escola')
        folder_id = req.get('folder_id')
        turmas = req.get('turmas', [])
        marks = req.get('marks', {})

        if not folder_id:
            return jsonify({'success': False, 'error': 'ID da pasta não informado'}), 400

        if not turmas:
            app_data = data_manager.load_data(get_session_file())
            turmas = app_data.get('salas_turmas', {}).get(escola, [])
            marks = app_data.get('salas_marks', {}).get(escola, {})

        xml_buf = gerar_relatorio_salas_xml(escola, turmas, marks)
        date_str = datetime.now().strftime('%d-%m-%Y')
        filename = f"conferencia_salas_{escola}_{date_str}.xml".replace(' ', '_')

        file_id = drive_service.upload_excel_to_drive(xml_buf.getvalue(), filename, folder_id)

        if file_id in (None, 'drive-not-available'):
            return jsonify({'success': False, 'error': 'Falha no upload ao Drive (verifique credenciais e permissões da pasta)'}), 500

        return jsonify({'success': True, 'file_id': file_id})
    except Exception as e:
        logger.error(f"Erro export_xml_drive: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/export_excel_drive', methods=['POST'])
def export_excel_drive():
    """Gera o Excel de uma escola e envia para a pasta do Drive escolhida."""
    try:
        from app.services.drive_service import DEFAULT_FOLDER_ID

        req       = request.json
        escola    = req.get('escola', '')
        turmas    = req.get('turmas', [])
        marks     = req.get('marks', {})
        folder_id = req.get('folder_id') or DEFAULT_FOLDER_ID

        if not escola:
            return jsonify({'success': False, 'error': 'Escola não informada'}), 400

        # Carrega do servidor se não veio no payload
        if not turmas:
            app_data = data_manager.load_data(get_session_file())
            turmas   = app_data.get('salas_turmas', {}).get(escola, [])
            marks    = app_data.get('salas_marks',  {}).get(escola, {})

        buf      = gerar_relatorio_salas_xlsx(escola, turmas, marks)
        date_str = datetime.now().strftime('%d-%m-%Y')
        filename = f"conferencia_salas_{escola}_{date_str}.xlsx".replace(' ', '_')

        file_id = drive_service.upload_excel_to_drive(buf.getvalue(), filename, folder_id)

        if file_id in (None, 'drive-not-available'):
            return jsonify({
                'success': False,
                'error': 'Falha no upload. Verifique as credenciais e permissões da pasta.'
            }), 500

        return jsonify({'success': True, 'file_id': file_id, 'filename': filename})

    except Exception as e:
        logger.error(f"Erro export_excel_drive: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/list_drive_folders', methods=['GET'])
def list_drive_folders_route():
    """Retorna pastas do FOLDER_MAP do config — sem depender de API do Drive."""
    try:
        folder_map = current_app.config.get('FOLDER_MAP', {})
        folders = [{'id': v, 'name': k} for k, v in sorted(folder_map.items())]
        from app.services.drive_service import DEFAULT_FOLDER_ID
        return jsonify({
            'success': True,
            'folders': folders,
            'default_folder_id': DEFAULT_FOLDER_ID
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'folders': []})
