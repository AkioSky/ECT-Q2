import os
import sys

#basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@admin.com')
    UPLOAD_PATH = os.path.join(basedir, 'uploads')
    STATIC_IMAGE_PATH = os.path.join(basedir, 'static/img')
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret key')
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024

    BOOTSTRAP_SERVE_LOCAL = True

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOGIN_ATTEMPT_LIMIT = 3
