from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(200))
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='press')

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(400))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(200))
    source = db.Column(db.String(200))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(400))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=True)

    @staticmethod
    def get_latest(n=8):
        return Photo.query.order_by(Photo.created_at.desc()).limit(n).all()

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(400))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class ProjectCategory:
    CATS = [
        'Учись и познавай!', 'Дерзай и открывай!', 'Найди призвание!', 'Создавай и вдохновляй!',
        'Благо твори!', 'Служи Отечеству!', 'Достигай и побеждай!', 'Будь здоров!',
        'Расскажи о главном!', 'Умей дружить!', 'Береги планету!', 'Открывай страну!'
    ]

    @staticmethod
    def get_all():
        return ProjectCategory.CATS

def init_db(app):
    app.config.setdefault('SQLALCHEMY_DATABASE_URI','sqlite:///mediacenter.db')
    db.init_app(app)
    with app.app_context():
        db.create_all()
