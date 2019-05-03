from flask import render_template, jsonify, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user, confirm_login
from app import app
from forms import LoginForm, RegisterForm, UploadVideo, EditProfileForm
from models import User, Video, BannerAds
from extensions import db
import pandas as pd
from werkzeug.datastructures import CombinedMultiDict
from utils import rename_image
import os
from datetime import datetime, date, timedelta
from random import randint


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


def test_ads_values():
    banner_list = ['banner1', 'banner2', 'banner3']
    start_date = date(2019, 4, 1)
    end_date = date(2019, 5, 3)
    for single_date in daterange(start_date, end_date):
        for banner in banner_list:
            new_ban = BannerAds(name=banner, view_count=randint(10, 50), timestamp=single_date)
            db.session.add(new_ban)
    db.session.commit()


@app.route('/')
def home():
    if current_user.is_authenticated and current_user.role == 'Administrator':
        users = User.query.all()
        user_list = []
        video_count = []
        used_space = []
        for user in users:
            user_list.append(user.name)
            video_count.append(len(user.videos))
            used_space.append(user.format_without_symbol(user.video_size()))

        query = BannerAds.query.order_by('timestamp')
        df = pd.read_sql(query.statement, query.session.bind)
        df['timestamp'] = df['timestamp'].astype(str)
        banner_st = dict()
        for name, group in df.groupby(['name']):
            banner_st[name] = dict({
                'count': list(group['view_count']),
                'date': list(group['timestamp'])
            })
        b_labels = list(df['timestamp'].drop_duplicates())
        return render_template('admin/index.html', user_list=user_list, video_count=video_count, used_space=used_space,
                               b_labels=b_labels, banner_st=banner_st)
    videos = Video.query.join(User).filter(User.logged_in == True).all()
    return render_template('main/index.html', videos=videos)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        username = form.username.data
        password = form.password.data
        user = User(name=name, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created!', 'info')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.lower()).first()
        if user is not None:
            if user.validate_password(form.password.data):
                if not user.locked:
                    login_user(user)
                    flash('Login success.', 'info')
                    user.set_login()
                    user.login_attempt_count = 0
                    user.last_login_timestamp = datetime.utcnow()
                    db.session.commit()
                    return redirect(url_for('profile'))
                else:
                    flash('Your account is locked.', 'warning')
            else:
                if user.locked:
                    flash('Your account is locked.', 'warning')
                else:
                    user.login_attempt_count += 1
                    user.last_login_timestamp = datetime.utcnow()
                    if user.login_attempt_count >= current_app.config['LOGIN_ATTEMPT_LIMIT']:
                        user.locked = True
                    db.session.commit()
                    flash('Invalid password. You can try {} times more.'.format(
                        current_app.config['LOGIN_ATTEMPT_LIMIT'] - user.login_attempt_count), 'warning')
        else:
            flash('Account does not exist. Please register account.', 'warning')
    return render_template('auth/login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    current_user.set_logout()
    logout_user()
    flash('Logout success.', 'info')
    return redirect(url_for('home'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('main/profile.html', form=current_user)


@app.route('/profile/update', methods=['GET', 'POST'])
@login_required
def profile_update():
    form = EditProfileForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        avatar = form.avatar.data
        if avatar:
            filename = rename_image(avatar.filename)
            avatar.save(os.path.join(current_app.config['UPLOAD_PATH'], filename))
            current_user.avatar = filename
        current_user.name = name
        current_user.description = description
        db.session.commit()
        return redirect(url_for('profile'))
    form.name.data = current_user.name
    form.description.data = current_user.description
    if current_user.avatar:
        form.avatar.data = send_from_directory(current_app.config['UPLOAD_PATH'], current_user.avatar)
    return render_template('main/profile_update.html', form=form)


@app.route('/avatar')
@login_required
def get_avatar():
    if current_user.avatar:
        return send_from_directory(current_app.config['UPLOAD_PATH'], current_user.avatar)
    else:
        return send_from_directory(current_app.config['STATIC_IMAGE_PATH'], 'default-profile.png')


@app.route('/upload-video', methods=['GET', 'POST'])
@login_required
def upload_video():
    form = UploadVideo()
    if form.validate_on_submit():
        file = form.upload.data
        description = form.description.data
        filename = rename_image(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_PATH'], filename))
        size = os.stat(os.path.join(current_app.config['UPLOAD_PATH'], filename)).st_size

        if current_user.remain_size() < size:
            os.remove(os.path.join(app.config['UPLOAD_PATH'], filename))
            flash("You don't have enough space to upload this file!", 'warning')
        else:
            video = Video(
                filename=filename,
                description=description,
                filesize=size,
                author=current_user._get_current_object()
            )
            db.session.add(video)
            db.session.commit()
            return redirect(url_for('profile'))
    return render_template('main/upload_video.html', form=form)


@app.route('/video/update/<path:video_id>', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    video = Video.query.filter_by(id=video_id).first()
    if request.method == 'POST':
        description = request.form.get('description')
        video.description = description
        db.session.commit()
    return render_template('main/edit_video.html', video=video)


@app.route('/video/view')
def view_video():
    video_id = request.args['video_id']
    video = Video.query.get(video_id)
    video.add_view()
    return jsonify('')


@app.route('/video/delete/<path:video_id>', methods=['GET', 'POST'])
def delete_video(video_id):
    item = db.session.query(Video).get(video_id)
    try:
        os.remove(os.path.join(app.config['UPLOAD_PATH'], item.filename))
    except:
        pass
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('profile'))


@app.route('/uploads/<path:filename>')
def get_video(filename):
    return send_from_directory(current_app.config['UPLOAD_PATH'], filename)


@app.route('/profile/view')
def get_profile():
    video_id = request.args['video_id']
    video = Video.query.get(video_id)
    user = User.query.get(video.author_id)
    return render_template('main/profile_view.html', user=user, video=video)


@app.route('/advertisement/<path:banner_name>')
def advertisement(banner_name):
    banner = BannerAds.query.filter_by(name=banner_name, timestamp=datetime.utcnow().date()).first()
    if banner:
        banner.view_count += 1
        db.session.commit()
    else:
        banner = BannerAds(name=banner_name, view_count=1)
        db.session.add(banner)
        db.session.commit()

    return redirect(url_for('home'))
