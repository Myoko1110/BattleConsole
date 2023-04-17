from flask import Flask
from flask_socketio import SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'battleearth'
socketio = SocketIO(app, cors_allowed_origins='*')
import manager.main
import manager.FileExplorer
import manager.gnuscreen_reader
import manager.ServerJob

if __name__ == "__main__":
    app.run(port=5000)
