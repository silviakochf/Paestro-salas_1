from flask import Flask
from dotenv import load_dotenv
from .config import Config

def create_app():
    """
    Application Factory para inicialização do Flask.
    """
    # Carrega variáveis de ambiente
    load_dotenv()

    # Define pastas de templates e static
    app = Flask(__name__, 
                static_folder='static', 
                template_folder='templates')
    
    # Carrega configurações
    app.config.from_object(Config)

    # Registra as rotas
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app