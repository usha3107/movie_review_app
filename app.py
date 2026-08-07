import os
import json
import pickle
import random
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
MOVIES_JSON = os.path.join(BASE_DIR, "static", "movies.json")
MODEL_PATH = os.path.join(BASE_DIR, "model", "sentiment_model.keras")
TOKENIZER_PATH = os.path.join(BASE_DIR, "model", "tokenizer.pickle")
CONFIG_PATH = os.path.join(BASE_DIR, "model", "config.pickle")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# ---------------------------------------------------------------------------
# Load the trained Keras sentiment model + tokenizer once at startup
# ---------------------------------------------------------------------------
print("Loading trained sentiment model...")
sentiment_model = load_model(MODEL_PATH)
with open(TOKENIZER_PATH, "rb") as f:
    tokenizer = pickle.load(f)
with open(CONFIG_PATH, "rb") as f:
    model_config = pickle.load(f)

MAX_LEN = model_config["max_len"]
CLASS_NAMES = model_config["class_names"]  # ["Negative", "Neutral", "Positive"]

with open(MOVIES_JSON) as f:
    ALL_MOVIES = json.load(f)


def predict_sentiment(text):
    seq = tokenizer.texts_to_sequences([text])
    padded = pad_sequences(seq, maxlen=MAX_LEN, padding="post", truncating="post")
    probs = sentiment_model.predict(padded, verbose=0)[0]
    idx = int(np.argmax(probs))
    return CLASS_NAMES[idx]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("reviews_page"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if len(password) < 4:
            flash("Password should be at least 4 characters.", "error")
            return render_template("register.html")

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            flash("That username is already taken.", "error")
            return render_template("register.html")

        hashed = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed),
        )
        db.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password"], password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("reviews_page"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/reviews")
@login_required
def reviews_page():
    # Pick 3 random movies for this visit and remember them in session
    # so the submit step matches what was actually shown to the user.
    chosen = random.sample(ALL_MOVIES, 3)
    session["current_movies"] = [m["title"] for m in chosen]
    return render_template("reviews.html", movies=chosen, username=session.get("username"))


@app.route("/submit", methods=["POST"])
@login_required
def submit_reviews():
    movies = session.get("current_movies")
    if not movies:
        flash("Your review session expired. Please try again.", "error")
        return redirect(url_for("reviews_page"))

    db = get_db()
    results = []

    for movie_title in movies:
        field_name = f"review_{movie_title.replace(' ', '_')}"
        review_text = request.form.get(field_name, "").strip()

        if not review_text:
            continue  # skip empty reviews rather than failing the whole batch

        sentiment = predict_sentiment(review_text)

        db.execute(
            "INSERT INTO reviews (movie, review_text, sentiment) VALUES (?, ?, ?)",
            (movie_title, review_text, sentiment),
        )
        results.append({"movie": movie_title, "review": review_text, "sentiment": sentiment})

    db.commit()
    session.pop("current_movies", None)

    if not results:
        flash("Please write at least one review before submitting.", "error")
        return redirect(url_for("reviews_page"))

    session["last_results"] = results
    return redirect(url_for("results_page"))


@app.route("/results")
@login_required
def results_page():

    db = get_db()

    rows = db.execute(
        "SELECT sentiment, COUNT(*) as total FROM reviews GROUP BY sentiment"
    ).fetchall()


    totals = {
        "Positive": 0,
        "Negative": 0,
        "Neutral": 0
    }


    for row in rows:
        if row["sentiment"] in totals:
            totals[row["sentiment"]] = row["total"]


    grand_total = sum(totals.values())


    last_results = session.get("last_results", [])


    return render_template(
        "results.html",
        totals=totals,
        grand_total=grand_total,
        last_results=last_results,
        username=session.get("username")
    )

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found -- run init_db.py first.")
    app.run(host="0.0.0.0", port=5000, debug=True)
