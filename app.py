from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yearbook.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)


# =========================
# MODELS
# =========================

class User(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    full_name   = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    branch      = db.Column(db.String(20),  nullable=False)
    roll_number = db.Column(db.String(30),  unique=True, nullable=False)
    password    = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255), default='')
    approved    = db.Column(db.Boolean, default=False, nullable=False)


class WallMessage(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    text       = db.Column(db.Text,        nullable=False)
    author     = db.Column(db.String(120), nullable=False, default='Anonymous')
    created_at = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)


# =========================
# HELPERS
# =========================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# =========================
# PAGES
# =========================

@app.route('/')
def home():
    return render_template('landing_page.html')

@app.route('/journey')
def journey():
    return render_template('journey.html')

@app.route('/yearbook')
def yearbook():
    return render_template('yearbook.html')

@app.route('/wall')
def wall():
    return render_template('wall.html')

@app.route('/credit')
def credit():
    return render_template('credits.html')


# =========================
# VAULT
# =========================

UPLOAD_ROOT = os.path.join('static', 'uploads')
YEARS = ['1st', '2nd', '3rd', '4th', 'feasts']

@app.route('/vault')
def vault():
    images = []
    for year in YEARS:
        folder = os.path.join(UPLOAD_ROOT, year)
        if not os.path.exists(folder):
            continue
        for file in os.listdir(folder):
            if not file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            name_without_ext = os.path.splitext(file)[0]
            parts = name_without_ext.split('_', 1)
            raw_date = parts[0] if len(parts) > 0 else '2025-01-01'
            title    = parts[1] if len(parts) > 1 else 'Untitled Memory'
            try:
                parsed_date = datetime.strptime(raw_date, '%Y-%m-%d')
                pretty_date = parsed_date.strftime('%d %b')
                sort_date   = parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                pretty_date = raw_date
                sort_date   = '2025-01-01'
            images.append({
                'src':       f'/static/uploads/{year}/{file}',
                'year':      year,
                'date':      pretty_date,
                'sort_date': sort_date,
                'title':     title
            })
    images.sort(key=lambda x: x['sort_date'], reverse=True)
    return render_template('vault.html', images=images)


# =========================
# AUTH
# =========================

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'})

    user = User(
        full_name   = data['full_name'],
        email       = data['email'],
        branch      = data['branch'],
        roll_number = data['roll_number'],
        password    = generate_password_hash(data['password']),
        approved    = False
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Account request created successfully'})


@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'success': False, 'message': 'Incorrect credentials'})

    if not user.approved:
        return jsonify({'success': False, 'message': 'Your account is pending admin approval'})

    session['user_id'] = user.id
    return jsonify({'success': True, 'name': user.full_name, 'pfp': user.profile_pic})


@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})

    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})

    new_name         = request.form.get('new_name')
    current_password = request.form.get('current_password')
    new_password     = request.form.get('new_password')
    file             = request.files.get('pfp')

    if new_name:
        user.full_name = new_name

    if new_password:
        if not current_password or not check_password_hash(user.password, current_password):
            return jsonify({'success': False, 'message': 'Wrong current password'})
        user.password = generate_password_hash(new_password)

    if file and file.filename:
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Invalid file type'})
        filename = f"user_{user.id}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        user.profile_pic = '/' + filepath.replace('\\', '/')

    db.session.commit()
    return jsonify({'success': True, 'name': user.full_name, 'pfp': user.profile_pic})


@app.route('/signout', methods=['POST'])
def signout():
    session.clear()
    return jsonify({'success': True})


# =========================
# WALL MESSAGES
# =========================

@app.route('/api/messages', methods=['GET'])
def get_messages():
    messages = WallMessage.query.order_by(WallMessage.id.desc()).all()
    return jsonify([
        {
            'id':         m.id,
            'text':       m.text,
            'author':     m.author,
            'created_at': m.created_at.strftime('%d %b %Y')
        }
        for m in messages
    ])


@app.route('/api/messages', methods=['POST'])
def post_message():
    data   = request.get_json()
    text   = (data.get('text') or '').strip()
    author = (data.get('author') or 'Anonymous').strip()

    if not text:
        return jsonify({'error': 'Message cannot be empty'}), 400

    msg = WallMessage(text=text, author=author)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'success': True})


# =========================
# ADMIN
# =========================

@app.route('/admin/users')
def list_users():
    users = User.query.all()
    rows = "".join(
        f"<tr><td>{u.id}</td><td>{u.full_name}</td><td>{u.email}</td>"
        f"<td>{'✅' if u.approved else '❌'}</td>"
        f"<td><a href='/admin/approve/{u.id}'>Approve</a></td></tr>"
        for u in users
    )
    return f"<table border='1'><tr><th>ID</th><th>Name</th><th>Email</th><th>Approved</th><th>Action</th></tr>{rows}</table>"


@app.route('/admin/approve/<int:user_id>')
def approve_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return 'User not found', 404
    user.approved = True
    db.session.commit()
    return f'✅ {user.full_name} approved'


# =========================
# RUN
# =========================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=9000)
# ============================= for protecting the page from entering without signing in =============================
# @app.route('/journey')
# def journey():
#     if "user" not in session:
#         flash('Please sign in to access the journey.')
#         return redirect('/')
#     return render_template('journey.html')-
# ============================== for protecting the page from entering without signing in =============================