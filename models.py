import os
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hurry.filesize import size

from extensions import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    username = db.Column(db.String(254), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(30), default='User')
    videos = db.relationship('Video', back_populates='author', cascade='all')

    locked = db.Column(db.Boolean, default=False)
    logged_in = db.Column(db.Boolean, default=False)
    login_attempt_count = db.Column(db.Integer, default=0)
    last_login_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    description = db.Column(db.Text, default='')
    avatar = db.Column(db.String(200), default='')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def lock(self):
        self.locked = True
        db.session.commit()

    def unlock(self):
        self.locked = False
        db.session.commit()

    def set_role(self):
        if self.username == current_app.config['ADMIN_EMAIL']:
            self.role = 'Administrator'
        else:
            self.role = 'User'
        db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.set_role()

    @property
    def is_admin(self):
        return self.role == 'Administrator'

    def set_login(self):
        self.logged_in = True
        db.session.commit()

    def set_logout(self):
        self.logged_in = False
        db.session.commit()

    def video_size(self):
        return sum(video.filesize for video in self.videos)

    def remain_size(self):
        return current_app.config['MAX_UPLOAD_SIZE'] - self.video_size()

    def format_bytes(self, s):
        return size(s)

    def format_without_symbol(self, s):
        si = [
            (1000 ** 5, ''),
            (1000 ** 4, ''),
            (1000 ** 3, ''),
            (1000 ** 2, ''),
            (1000 ** 1, ''),
            (1000 ** 0, ''),
        ]
        return size(s, si)


class BannerAds(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, default='')
    view_count = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.Date, default=datetime.utcnow)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    filename = db.Column(db.String(64))
    filesize = db.Column(db.BigInteger)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    viewed = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    author = db.relationship('User', back_populates='videos')

    def add_view(self):
        self.viewed += 1
        db.session.commit()


@db.event.listens_for(Video, 'after_delete', named=True)
def delete_videos(**kwargs):
    target = kwargs['target']
    path = os.path.join(current_app.config['UPLOAD_PATH'], target.filename)
    if os.path.exists(path):
        os.remove(path)
