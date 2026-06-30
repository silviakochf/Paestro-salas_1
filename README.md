# Paestro - Sistema de Gestão e Busca Ativa Educacional

O Paestro é um ecossistema de ferramentas desenvolvido para otimizar o monitoramento escolar e a Busca Ativa, utilizando como base os dados exportados do sistema EducarWeb.

## Funcionalidades Principais

**Módulo de Chamada (Visitas)**
Este módulo é utilizado para realizar o controle de presença durante as visitas às unidades escolares.
- Importação: Realiza o parseamento de arquivos HTML (listas de alunos) exportados do EducarWeb.
- Operação: Gera uma interface interativa para marcação de presença e registo de observações via Tablet ou PC.
- Destino: Exporta a planilha formatada (.xlsx) diretamente para a pasta da unidade no Google Drive via Conta de Serviço (Robô).

**Módulo de Análise (Busca Ativa)**
Este módulo identifica alunos com infrequência crítica através de dados do sistema.
- Entrada: Processa arquivos brutos de registos de chamadas escolares do EducarWeb.
- Inteligência: O backend (attendance_analyser.py) filtra alunos que atingiram níveis de falta que exigem atenção.
- Saída: Gera uma lista consolidada com estatísticas detalhadas de presença.

**Módulo de Relatório (Consolidado)**
Este módulo unifica as informações recolhidas em campo com os dados do sistema.
- Operação: Recebe os arquivos de Chamada e de Análise gerados pelo próprio aplicativo.
- Resultado: Cria um relatório final cruzando a visita presencial com os dados oficiais do sistema.

## Guia de Configuração (Service Account)

Para que o sistema funcione em servidores (Render) e Tablets sem exigir login manual, utilizamos uma Conta de Serviço do Google.

**Passo 1: Configuração do Arquivo .env**
Crie um arquivo chamado `.env` na raiz do projeto. Este arquivo deve conter as seguintes variáveis:
- `GOOGLE_CREDENTIALS_JSON=credentials.json` 
  *(Aponta para o arquivo físico no seu computador)*
- `APP_PASSWORD=`
  *(Senha de login)*

**Passo 2: Arquivos Ignorados (.gitignore)**
Para segurança, certifique-se de que estes arquivos nunca subam para o GitHub:
- venv
- .env
- __pycache__
- *.py[cod]
- session_data/
- *.log
- credentials.json

## Execução do Sistema

- Localmente: Execute o arquivo setup_and_run.bat(.\setup_and_run.bat).

## Informações Técnicas

- Backend: Flask (backend/app.py).
- Autenticação: Google Service Account (Server-side).
- Integração Drive: IDs configurados em FOLDER_MAP no arquivo backend/drive_exporter.py.
