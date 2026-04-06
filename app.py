from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/")
def home():
    return render_template("landing_page.html")

@app.route("/journey")
def journey():
    return render_template("journey.html")


@app.route("/yearbook")
def yearbook():
    return render_template("yearbook.html")

@app.route("/vault")
def vault():        
    return render_template("vault.html")

@app.route("/wall")
def wall():             
    return render_template("wall.html")


if __name__ == "__main__":
    app.run(debug=True)