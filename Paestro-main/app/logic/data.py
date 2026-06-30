import json
import os
import logging
import unicodedata
import copy

# Configuração de Logger
logger = logging.getLogger(__name__)

def normalize_school_name(name):
    """
    Normaliza nomes de escolas (remove acentos, minúsculas).
    """
    if not name:
        return ""
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return name.lower().strip()

def load_data(filepath):
    """
    Carrega os dados a partir do arquivo JSON compartilhado.
    """
    default_structure = {
        'schools': {},          # Estrutura: {NomeEscola: {Turma: [Alunos]}}
        'saved_classes': {},    # Turmas que já tiveram chamada salva {Escola: [Turmas]}
        'attendance_status': {}, # {Turma: {Aluno: Status}} (P, F, FJ)
        'observations': {},      # {Turma: {Aluno: Obs}}
        'html_content': {},      # Conteúdo HTML bruto para exportação
        'unit_annotations': {},  # Anotações gerais da unidade
        'current_user': None,
        'periodo': None,
        'analyzed_files': [],    # (Legado/Em memória) Resultados da análise
        'salas_meta': {},        # {Escola: {Turma: {sala, turno}}}
        'salas_turmas': {},      # {Escola: [{turma, sala, turno}]}
        'salas_marks': {},       # {Escola: {index: {status, sala_real, obs}}}
    }

    if not os.path.exists(filepath):
        return default_structure

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Garante que chaves essenciais existam
            for key, val in default_structure.items():
                if key not in data:
                    data[key] = val
            return data
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Erro ao carregar dados de {filepath}: {e}")
        return default_structure

def save_data(data, filepath):
    """
    Salva os dados no arquivo JSON compartilhado.
    Remove a chave 'analyzed_files' antes de salvar para garantir
    que a análise de busca ativa seja isolada por sessão e não compartilhada.
    """
    try:
        # Cria uma cópia rasa para não modificar o objeto original em memória que o Flask está usando
        data_to_save = copy.copy(data)
        
        # Remove analyzed_files se existir, para não persistir histórico de análise no arquivo compartilhado
        if 'analyzed_files' in data_to_save:
            del data_to_save['analyzed_files']

        # Garante que o diretório existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar dados em {filepath}: {e}")
        return False

def merge_data(current_data, new_data_from_parser):
    """
    Mescla os dados novos vindos de um upload (parser) com os dados já existentes.
    """
    if not new_data_from_parser or 'schools' not in new_data_from_parser:
        return current_data

    # Mescla escolas e turmas
    for escola, turmas in new_data_from_parser['schools'].items():
        if escola not in current_data['schools']:
            current_data['schools'][escola] = {}
        
        for turma, alunos in turmas.items():
            current_data['schools'][escola][turma] = alunos

    return current_data