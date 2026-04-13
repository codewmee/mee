from flask import Flask, request, redirect, flash, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yearbook.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    branch = db.Column(db.String(20), nullable=False)
    roll = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


@app.route('/')
def home():
    return render_template('landing_page.html')


@app.route('/signup', methods=['POST'])
def signup():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    branch = request.form.get('branch')
    roll = request.form.get('roll')
    password = request.form.get('password')

    # check existing user
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Account already exists. Please sign in.')
        return redirect('/')

    hashed_password = generate_password_hash(password)

    new_user = User(
        full_name=full_name,
        email=email,
        branch=branch,
        roll=roll,
        password=hashed_password,
    )

    db.session.add(new_user)
    db.session.commit()

    flash('Signup successful. Please sign in now.')
    return redirect('/')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if not user:
        flash('User not found. Please sign up first.')
        return redirect('/')

    if not check_password_hash(user.password, password):
        flash('Wrong password.')
        return redirect('/')
    session["user"] = user.email


    flash(f'Welcome back, {user.full_name}!')
    return redirect('/journey')




@app.route('/journey')
def journey():
    return render_template('journey.html')

@app.route('/yearbook')
def yearbook():
    return render_template('yearbook.html')


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

            # filename format: 2025-02-14_Farewell Night.jpg
            name_without_ext = os.path.splitext(file)[0]
            parts = name_without_ext.split('_', 1)

            raw_date = parts[0] if len(parts) > 0 else '2025-01-01'
            title = parts[1] if len(parts) > 1 else 'Untitled Memory'

            try:
                parsed_date = datetime.strptime(raw_date, '%Y-%m-%d')
                pretty_date = parsed_date.strftime('%d %b')
                sort_date = parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                pretty_date = raw_date
                sort_date = '2025-01-01'

            images.append({
                'src': f'/static/uploads/{year}/{file}',
                'year': year,
                'date': pretty_date,
                'sort_date': sort_date,
                'title': title
            })

    images.sort(key=lambda x: x['sort_date'], reverse=True)
    return render_template('vault.html', images=images)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    
    
# ============================= for protecting the page from entering without signing in =============================
# @app.route('/journey')
# def journey():
#     if "user" not in session:
#         flash('Please sign in to access the journey.')
#         return redirect('/')
#     return render_template('journey.html')-
# ============================== for protecting the page from entering without signing in =============================