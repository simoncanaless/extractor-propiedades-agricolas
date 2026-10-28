"""Punto de entrada: levanta el panel web del extractor."""
import io
import sys

from flask import Flask

import config
from api.routes import main_bp
from db.database_manager import DatabaseManager

# Consola de Windows: evita errores con emojis y tildes en los print
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
app.register_blueprint(main_bp)

if __name__ == '__main__':
    db = DatabaseManager()
    db.crear_tablas()

    print(f"🚀 Servidor iniciado en http://127.0.0.1:{config.FLASK_PORT}")
    app.run(debug=config.FLASK_DEBUG, port=config.FLASK_PORT)
