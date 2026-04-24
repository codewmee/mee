from flask import Flask, render_template, request, jsonify, session
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
    id          = db.Column(db.Integer,     primary_key=True)
    full_name   = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    branch      = db.Column(db.String(20),  nullable=False)
    roll_number = db.Column(db.String(30),  unique=True, nullable=False)
    password    = db.Column(db.String(255), nullable=False)
    approved    = db.Column(db.Boolean,     default=False, nullable=False)


class YearbookEntry(db.Model):
    """Separate table — one row per published yearbook card."""
    id         = db.Column(db.Integer,     primary_key=True)
    user_id    = db.Column(db.Integer,     db.ForeignKey('user.id'), unique=True, nullable=False)
    photo      = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('yearbook_entry', uselist=False))


class WallMessage(db.Model):
    id         = db.Column(db.Integer,     primary_key=True)
    text       = db.Column(db.Text,        nullable=False)
    author     = db.Column(db.String(120), nullable=False, default='Anonymous')
    created_at = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)


# =========================
# HELPERS
# =========================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, prefix):
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(f"{prefix}.{ext}")
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return '/' + filepath.replace('\\', '/')


def me_payload(user):
    entry = user.yearbook_entry
    return {
        'loggedIn':     True,
        'name':         user.full_name,
        'roll':         user.roll_number,
        'branch':       user.branch,
        'has_yearbook': entry is not None,
        'pfp':          entry.photo if entry else '',
    }


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
            parts      = name_without_ext.split('_', 1)
            raw_date   = parts[0] if parts else '2025-01-01'
            title      = parts[1] if len(parts) > 1 else 'Untitled Memory'
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
    data = request.get_json()

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
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'success': False, 'message': 'Incorrect credentials'})

    if not user.approved:
        return jsonify({'success': False, 'message': 'Your account is pending admin approval'})

    session['user_id'] = user.id
    payload = me_payload(user)
    payload['success'] = True
    return jsonify(payload)


@app.route('/signout', methods=['POST'])
def signout():
    session.clear()
    return jsonify({'success': True})


@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})

    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})

    new_name         = request.form.get('new_name', '').strip()
    current_password = request.form.get('current_password', '')
    new_password     = request.form.get('new_password', '')

    if new_name:
        user.full_name = new_name

    if new_password:
        if not current_password or not check_password_hash(user.password, current_password):
            return jsonify({'success': False, 'message': 'Wrong current password'})
        user.password = generate_password_hash(new_password)

    db.session.commit()
    return jsonify({'success': True, 'name': user.full_name})


@app.route('/api/me')
def api_me():
    if 'user_id' not in session:
        return jsonify({'loggedIn': False})
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'loggedIn': False})
    return jsonify(me_payload(user))


# =========================
# YEARBOOK
# =========================

@app.route('/api/yearbook')
def api_yearbook():
    entries = (
        db.session.query(YearbookEntry)
        .join(User)
        .filter(User.approved == True)
        .order_by(User.full_name)
        .all()
    )
    return jsonify([
        {
            'entry_id': e.id,
            'user_id':  e.user_id,
            'name':     e.user.full_name,
            'roll':     e.user.roll_number,
            'branch':   e.user.branch,
            'photo':    e.photo or '',
        }
        for e in entries
    ])


@app.route('/api/yearbook/save', methods=['POST'])
def api_yearbook_save():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    user = db.session.get(User, session['user_id'])
    if not user or not user.approved:
        return jsonify({'success': False, 'message': 'Account not approved'}), 403

    entry   = user.yearbook_entry
    was_new = entry is None

    if was_new:
        entry = YearbookEntry(user_id=user.id)
        db.session.add(entry)

    photo = request.files.get('photo')
    if photo and photo.filename:
        url = save_upload(photo, f"yb_{user.id}")
        if not url:
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
        entry.photo = url

    db.session.commit()
    return jsonify({'success': True, 'created': was_new, 'photo': entry.photo or ''})


# =========================
# WALL
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
        f"<tr>"
        f"<td>{u.id}</td><td>{u.full_name}</td><td>{u.email}</td>"
        f"<td>{u.branch}</td><td>{u.roll_number}</td>"
        f"<td>{'✅' if u.approved else '❌'}</td>"
        f"<td>{'📖' if u.yearbook_entry else '—'}</td>"
        f"<td>"
        f"{'<a href=\"/admin/approve/' + str(u.id) + '\">Approve</a> | ' if not u.approved else ''}"
        f"<a href='/admin/remove/{u.id}' onclick=\"return confirm('Remove user?')\">Remove</a>"
        f"</td></tr>"
        for u in users
    )
    return (
        "<style>body{font-family:sans-serif;padding:20px}"
        "table{border-collapse:collapse;width:100%}"
        "td,th{padding:10px 14px;border:1px solid #ddd;text-align:left}"
        "tr:hover{background:#f5f5f5}</style>"
        "<h2>Users</h2>"
        "<table><tr><th>ID</th><th>Name</th><th>Email</th><th>Branch</th>"
        "<th>Roll</th><th>Approved</th><th>Yearbook</th><th>Actions</th></tr>"
        f"{rows}</table><br><a href='/admin/yearbook'>→ Manage Yearbook Entries</a>"
    )


@app.route('/admin/yearbook')
def admin_yearbook():
    entries = db.session.query(YearbookEntry).join(User).order_by(User.full_name).all()
    rows = "".join(
        f"<tr>"
        f"<td>{e.id}</td>"
        f"<td>{e.user.full_name}</td>"
        f"<td>{e.user.roll_number}</td>"
        f"<td>{e.user.branch}</td>"
        f"<td>{'<img src=\"' + e.photo + '\" style=\"height:48px;border-radius:6px\">' if e.photo else '—'}</td>"
        f"<td>{e.created_at.strftime('%d %b %Y')}</td>"
        f"<td><a href='/admin/yearbook/remove/{e.id}' onclick=\"return confirm('Remove?')\">Remove</a></td>"
        f"</tr>"
        for e in entries
    )
    return (
        "<style>body{font-family:sans-serif;padding:20px}"
        "table{border-collapse:collapse;width:100%}"
        "td,th{padding:10px 14px;border:1px solid #ddd;text-align:left}"
        "tr:hover{background:#f5f5f5}</style>"
        "<h2>Yearbook Entries</h2>"
        "<table><tr><th>ID</th><th>Name</th><th>Roll</th><th>Branch</th>"
        "<th>Photo</th><th>Published</th><th>Action</th></tr>"
        f"{rows}</table><br><a href='/admin/users'>← Back to Users</a>"
    )


@app.route('/admin/yearbook/remove/<int:entry_id>')
def admin_remove_yearbook(entry_id):
    entry = db.session.get(YearbookEntry, entry_id)
    if not entry:
        return 'Entry not found', 404
    name = entry.user.full_name
    db.session.delete(entry)
    db.session.commit()
    return f'🗑️ Yearbook entry for {name} removed. <a href="/admin/yearbook">Back</a>'


@app.route('/admin/approve/<int:user_id>')
def approve_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return 'User not found', 404
    user.approved = True
    db.session.commit()
    return f'✅ {user.full_name} approved. <a href="/admin/users">Back</a>'


@app.route('/admin/remove/<int:user_id>')
def remove_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return 'User not found', 404
    name = user.full_name
    db.session.delete(user)
    db.session.commit()
    return f'🗑️ {name} removed. <a href="/admin/users">Back</a>'


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