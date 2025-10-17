import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, init_db, User, News, Photo, Document, ProjectCategory
from utils import hash_password, check_password, allowed_file
from dotenv import load_dotenv
import requests

load_dotenv()

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_IMG = {'png','jpg','jpeg','gif','webp'}
ALLOWED_DOC = {'pdf'}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY','dev_secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL','sqlite:///mediacenter.db')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

login_manager = LoginManager()
login_manager.init_app(app)

# init DB
init_db(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    news = News.query.order_by(News.created_at.desc()).limit(20).all()
    categories = ProjectCategory.get_all()
    latest_photos = Photo.get_latest(8)
    return render_template('index.html', news=news, categories=categories, photos=latest_photos)

@app.route('/news/<int:news_id>')
def news_view(news_id):
    n = News.query.get_or_404(news_id)
    return render_template('news_item.html', news=n)

@app.route('/gallery')
def gallery():
    photos = Photo.query.order_by(Photo.created_at.desc()).all()
    return render_template('gallery.html', photos=photos)

@app.route('/projects')
def projects():
    cats = ProjectCategory.get_all()
    return render_template('projects.html', categories=cats)

@app.route('/team')
def team():
    team_members = User.query.filter(User.role != 'admin').all()
    return render_template('team.html', team=team_members)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- auth ---
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password(password, user.password_hash):
            login_user(user)
            flash('Выполнен вход', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверные данные', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- admin area ---
@app.route('/admin')
@login_required
def admin():
    if current_user.role not in ('admin','curator','press'):
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))
    news = News.query.order_by(News.created_at.desc()).all()
    photos = Photo.query.order_by(Photo.created_at.desc()).all()
    docs = Document.query.order_by(Document.created_at.desc()).all()
    return render_template('admin.html', news=news, photos=photos, docs=docs, ProjectCategory=ProjectCategory)

@app.route('/admin/post_news', methods=['POST'])
@login_required
def post_news():
    title = request.form['title']
    content = request.form['content']
    category = request.form.get('category')
    source = request.form.get('source','manual')

    n = News(title=title, content=content, category=category, source=source, author_id=current_user.id)
    db.session.add(n)
    db.session.commit()
    flash('Новость опубликована', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/upload_photo', methods=['POST'])
@login_required
def upload_photo():
    if 'photo' not in request.files:
        flash('Нет файла', 'danger')
        return redirect(url_for('admin'))
    f = request.files['photo']
    if f and allowed_file(f.filename):
        filename = secure_filename(f.filename)
        save_dir = os.path.join(app.config['UPLOAD_FOLDER'],'photos')
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, filename)
        f.save(path)
        p = Photo(filename=f'photos/{filename}', uploader_id=current_user.id)
        db.session.add(p)
        db.session.commit()
        flash('Фото загружено', 'success')
    else:
        flash('Неподдерживаемый формат', 'danger')
    return redirect(url_for('admin'))

@app.route('/admin/upload_doc', methods=['POST'])
@login_required
def upload_doc():
    if 'doc' not in request.files:
        flash('Нет файла', 'danger')
        return redirect(url_for('admin'))
    f = request.files['doc']
    if f and f.filename.rsplit('.',1)[-1].lower() in {'pdf'}:
        filename = secure_filename(f.filename)
        save_dir = os.path.join(app.config['UPLOAD_FOLDER'],'docs')
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, filename)
        f.save(path)
        d = Document(filename=f'docs/{filename}', uploader_id=current_user.id)
        db.session.add(d)
        db.session.commit()
        flash('Документ загружен', 'success')
    else:
        flash('Неподдерживаемый формат', 'danger')
    return redirect(url_for('admin'))

# --- Telegram webhook ---
@app.route('/tg-webhook', methods=['POST'])
def tg_webhook():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        return jsonify({'ok':False,'error':'no token'}), 400
    data = request.get_json(force=True)
    try:
        message = data.get('message') or data.get('channel_post')
        if not message:
            return jsonify({'ok':True})
        text = message.get('text') or message.get('caption') or ''
        photos = message.get('photo')
        from models import News, Photo
        n = News(title=(text[:120] + '...') if len(text)>120 else text, content=text, source='telegram')
        db.session.add(n)
        db.session.commit()
        if photos:
            file_id = photos[-1]['file_id']
            resp = requests.get(f'https://api.telegram.org/bot{token}/getFile', params={'file_id':file_id}).json()
            file_path = resp['result']['file_path']
            file_url = f'https://api.telegram.org/file/bot{token}/{file_path}'
            r = requests.get(file_url, stream=True)
            save_dir = os.path.join(app.config['UPLOAD_FOLDER'],'photos')
            os.makedirs(save_dir, exist_ok=True)
            fname = file_path.split('/')[-1]
            with open(os.path.join(save_dir,fname),'wb') as fw:
                for chunk in r.iter_content(1024):
                    fw.write(chunk)
            ph = Photo(filename=f'photos/{fname}', uploader_id=None, news_id=n.id)
            db.session.add(ph)
            db.session.commit()
        return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)}), 500

if __name__=='__main__':
    app.run(debug=True, port=5000)
