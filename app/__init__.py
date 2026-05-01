from flask import Flask
from app.db import mysql

def create_app():
    app = Flask(__name__)

    # Configuración
    app.config.from_object('app.config.Config')

    # Inicializar DB
    mysql.init_app(app)

    # Registrar blueprints
    from app.auth.routes import auth_bp
    from app.productos.routes import productos_bp
    from app.inventario.routes import inventario_bp
    from app.ventas.routes import ventas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(ventas_bp)

    return app