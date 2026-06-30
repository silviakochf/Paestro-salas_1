document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.querySelector('.file-input-label');
    // Assegura que o browseBtn aponta para o elemento correto
    console.log('browseBtn element found:', browseBtn);
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const processBtn = document.getElementById('process-btn');
    const results = document.getElementById('results');
    const escolasCount = document.getElementById('escolas-count');
    const goToSalasBtn = document.getElementById('go-to-salas');
    const importedFilesList = document.getElementById('imported-files-list');
    const dataAtualElement = document.getElementById('data-atual');
    const nomeUsuarioElement = document.getElementById('nome-usuario');

    // Estado para armazenar arquivos selecionados
    let selectedFiles = [];

    // Exibe data atual e usuário
    const hoje = new Date();
    dataAtualElement.textContent = hoje.toLocaleDateString('pt-BR');

    // Busca o usuário do servidor (com fallback para sessionStorage)
    fetch('/api/get_current_user')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const username = data.username || sessionStorage.getItem('paestro_usuario_temp') || '';
                const periodo = data.periodo || sessionStorage.getItem('paestro_periodo_temp') || '';
                
                nomeUsuarioElement.textContent = `${username}`;
                
                // Atualizar o período no cabeçalho
                const periodoElement = document.getElementById('periodo-usuario');
                if (periodoElement) {
                    periodoElement.textContent = periodo;
                }
            }
        })
        .catch(error => {
            console.error('Erro ao obter usuário:', error);
            nomeUsuarioElement.textContent = sessionStorage.getItem('paestro_usuario_temp') || '';
            
            const periodoElement = document.getElementById('periodo-usuario');
            if (periodoElement) {
                periodoElement.textContent = sessionStorage.getItem('paestro_periodo_temp') || '';
            }
        });

    // Prevenir comportamentos padrão para drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    // Handle dropped files
    dropArea.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    // Configure file input button
    browseBtn.addEventListener('click', function(e) {
        e.preventDefault(); // Previne o comportamento padrão
        fileInput.click();
        // Evitar que o input seja fechado após a seleção
        return false;
    });

    fileInput.addEventListener('change', function(e) {
        // Previne o comportamento padrão de fechar o seletor
        e.stopPropagation();
        
        if (this.files.length) {
            handleFiles(this.files);
        }
    });

    // Carrega arquivos importados ao iniciar
    loadImportedFiles();

    function loadImportedFiles() {
        modal.loading('Carregando arquivos importados...');

        fetch('/api/get_imported_files')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateFilesList(data.files);
                } else {
                    console.error('Erro ao carregar arquivos:', data.error);
                    modal.alert('Erro', 'Falha ao carregar arquivos importados', 'error');
                }
            })
            .catch(error => {
                console.error('Erro ao carregar arquivos:', error);
                modal.alert('Erro', 'Falha na conexão com o servidor', 'error');
                showEmptyMessage();
            })
            .finally(() => {
                modal.close();
            });
    }

    function updateFilesList(files) {
        importedFilesList.innerHTML = '';

        if (files.length === 0) {
            showEmptyMessage();
            return;
        }

        files.forEach(file => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="file-name">${file.name}</span>
                <button data-filename="${file.name}" class="delete-file-btn">
                    Excluir
                </button>
            `;
            importedFilesList.appendChild(li);
        });

        // Adiciona eventos aos botões de exclusão
        document.querySelectorAll('.delete-file-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const filename = this.getAttribute('data-filename');
                confirmDeleteFile(filename);
            });
        });
    }

    function showEmptyMessage() {
        importedFilesList.innerHTML = `
            <li class="empty-message">Nenhum arquivo importado ainda</li>
        `;
    }

    function confirmDeleteFile(filename) {
        modal.confirm(
            'Confirmar Exclusão', 
            `Tem certeza que deseja excluir o arquivo "${filename}"?\nEsta ação removerá todas as turmas associadas.`,
            () => deleteFile(filename),
            () => {}
        );
    }

    function deleteFile(filename) {
        modal.loading('Excluindo arquivo...');

        fetch('/api/delete_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadImportedFiles();
                modal.alert('Sucesso', 'Arquivo e turmas associadas foram removidos com sucesso!', 'success');
            } else {
                modal.alert('Erro', 'Erro ao excluir arquivo: ' + (data.error || 'Erro desconhecido'), 'error');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            modal.alert('Erro', 'Falha ao comunicar com o servidor', 'error');
        })
        .finally(() => {
            modal.close();
        });
    }

    function handleFiles(files) {
        // Converte FileList para array e filtra apenas HTML
        const fileArray = Array.from(files).filter(file => 
            file.name.match(/\.(html|htm)$/i)
        );

        if (fileArray.length === 0) {
            modal.alert('Atenção', 'Por favor, selecione arquivos HTML (.html ou .htm)', 'warning');
            return;
        }

        // Atualiza lista de arquivos selecionados
        selectedFiles = fileArray;

        // Atualiza UI
        fileInfo.style.display = 'block';
        cancelBtn.style.display = 'inline-block';
        
        // Exibe nomes dos arquivos
        let fileNames = '';
        selectedFiles.forEach((file, index) => {
            fileNames += file.name;
            if (index < selectedFiles.length - 1) {
                fileNames += ', ';
            }
        });
        
        // Mostra nomes dos arquivos e ativa botão de processamento
        fileName.textContent = fileNames;
        processBtn.disabled = false;
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Botão de processamento de arquivos
    processBtn.addEventListener('click', function() {
        if (selectedFiles.length === 0) {
            modal.alert('Atenção', 'Nenhum arquivo válido selecionado', 'warning');
            return;
        }

        modal.loading('Processando arquivos...');
        
        // Clonar a lista de arquivos selecionados antes de enviar
        // Isso previne problemas ao reselecionar o mesmo arquivo
        const filesToUpload = [...selectedFiles];
        
        const formData = new FormData();
        filesToUpload.forEach(file => {
            formData.append('files', file); // Alterado para 'files' para corresponder ao backend
        });

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Oculta informações do arquivo e limpa input
                fileInfo.style.display = 'none';
                fileInput.value = '';
                selectedFiles = [];
                
                // Mostra resultados
                results.style.display = 'block';
                escolasCount.textContent = data.schools?.length || 0;
                
                // Recarrega a lista de arquivos importados
                loadImportedFiles();
                
                modal.alert('Sucesso', 'Arquivos processados com sucesso!', 'success');
            } else {
                modal.alert('Erro', data.error || 'Erro desconhecido no processamento', 'error');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            modal.alert('Erro', 'Falha na conexão com o servidor', 'error');
        })
        .finally(() => {
            modal.close();
            processBtn.disabled = selectedFiles.length === 0;
        });
    });
    
    // Botão para ir para a conferência de salas
    goToSalasBtn.addEventListener('click', function() {
        window.location.href = '/salas';
    });
    
    // Botão para cancelar a seleção
    const cancelBtn = document.getElementById('cancel-btn');
    cancelBtn.addEventListener('click', function() {
        // Limpa a seleção de arquivos
        fileInput.value = '';
        selectedFiles = [];
        fileName.textContent = '';
        fileInfo.style.display = 'none';
        cancelBtn.style.display = 'none';
        processBtn.disabled = true;
    });

    // Melhoria: Focar na área de drop quando a página carrega
    dropArea.focus();
});