from flask import Flask
from flask_pymongo import PyMongo

mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    
    # Konfigürasyon dosyasını yükle
    app.config.from_pyfile('../config.py')
    
    # MongoDB bağlantısını ayarla
    app.config["MONGO_URI"] = "mongodb://localhost:27017/makale_db"
    mongo.init_app(app)

    
    return app 
