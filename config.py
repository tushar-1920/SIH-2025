import os

class Config:
    # Secret key for sessions & forms
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # ✅ Use SQLite (creates site.db in your project folder)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
