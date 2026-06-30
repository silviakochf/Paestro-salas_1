
class Modal {
    constructor() {
        this.modalOverlay = document.createElement('div');
        this.modalOverlay.className = 'modal-overlay';
        this.modalOverlay.innerHTML = `
            <div class="modal-container">
                <div class="modal-header">
                    <h3 class="modal-title"></h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body"></div>
                <div class="modal-footer"></div>
            </div>
        `;
        
        document.body.appendChild(this.modalOverlay);
        
        // Close modal when clicking overlay or close button
        this.modalOverlay.addEventListener('click', (e) => {
            if (e.target === this.modalOverlay || e.target.classList.contains('modal-close')) {
                this.close();
            }
        });
    }
    
    open(title, content, buttons = []) {
        this.modalOverlay.querySelector('.modal-title').textContent = title;
        this.modalOverlay.querySelector('.modal-body').innerHTML = content;
        
        const footer = this.modalOverlay.querySelector('.modal-footer');
        footer.innerHTML = '';
        
        buttons.forEach(btn => {
            const button = document.createElement('button');
            button.className = `modal-btn modal-btn-${btn.type || 'secondary'}`;
            button.textContent = btn.text;
            button.addEventListener('click', () => {
                if (btn.handler) btn.handler();
                if (btn.close !== false) this.close();
            });
            footer.appendChild(button);
        });
        
        this.modalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    close() {
        this.modalOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    alert(title, message, type = 'info') {
        const alertClass = {
            success: 'modal-alert-success',
            error: 'modal-alert-error',
            warning: 'modal-alert-warning',
            info: ''
        }[type];
        
        this.open(title, `
            <div class="modal-alert ${alertClass}">${message}</div>
        `, [
            { text: 'OK', type: 'primary' }
        ]);
    }
    
    confirm(title, message, confirmHandler, cancelHandler) {
        this.open(title, message, [
            { 
                text: 'Cancelar', 
                type: 'secondary',
                handler: cancelHandler
            },
            { 
                text: 'Confirmar', 
                type: 'primary',
                handler: confirmHandler
            }
        ]);
    }
    
    prompt(title, message, defaultValue = '', submitHandler) {
        const inputId = 'modal-prompt-' + Math.random().toString(36).substr(2, 9);
        
        this.open(title, `
            <p>${message}</p>
            <input type="text" id="${inputId}" class="modal-input" value="${defaultValue}">
        `, [
            { 
                text: 'Cancelar', 
                type: 'secondary'
            },
            { 
                text: 'Enviar', 
                type: 'primary',
                handler: () => {
                    const value = document.getElementById(inputId).value;
                    if (submitHandler) submitHandler(value);
                }
            }
        ]);
        
        // Focus input and select text
        setTimeout(() => {
            const input = document.getElementById(inputId);
            if (input) {
                input.focus();
                input.select();
            }
        }, 100);
    }
    
    loading(title = 'Processando...') {
        this.open(title, `
            <div class="modal-loading">
                <div class="modal-loading-spinner"></div>
            </div>
        `, []);
    }
}

// Create a single modal instance
const modal = new Modal();

// Replace native dialogs
window.showModal = modal;
window.showAlert = modal.alert.bind(modal);
window.showConfirm = (message, handler) => modal.confirm('Confirmação', message, handler);
window.showPrompt = (message, defaultValue, handler) => modal.prompt('Entrada', message, defaultValue, handler);

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = modal;
}