from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# --- Initialize DB ---
def init_db():
    conn = sqlite3.connect('wellness.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            mood TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- DB Connection ---
def get_db_connection():
    conn = sqlite3.connect('wellness.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash("Please fill in all fields.")
            return redirect(url_for('register'))
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = username
            flash('Welcome back!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        mood = request.form['mood']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db_connection()
        conn.execute('INSERT INTO moods (username, mood, timestamp) VALUES (?, ?, ?)',
                     (session['username'], mood, timestamp))
        conn.commit()
        conn.close()
        return redirect(url_for('mood_page', mood=mood))

    return render_template('tracker.html', mood=None)

@app.route('/mood/<mood>')
def mood_page(mood):
    if 'username' not in session:
        return redirect(url_for('login'))

    suggestions_dict = {
        'Happy': ["Enjoy your day!", "Share your joy with someone."],
        'Sad': ["Try journaling.", "Watch your favorite show."],
        'Angry': ["Take deep breaths.", "Go for a walk."],
        'Neutral': ["Listen to calm music.", "Do something new."],
        'Good': ["Keep it going!", "Set a small goal for today."]
    }
    suggestions = suggestions_dict.get(mood, ["Be kind to yourself."])
    return render_template('mood_page.html', mood=mood, suggestions=suggestions)

@app.route('/tracker')
def tracker():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    data = conn.execute('SELECT mood, timestamp FROM moods WHERE username = ? ORDER BY timestamp ASC',
                        (session['username'],)).fetchall()
    conn.close()
    moods = [row['mood'] for row in data]
    dates = [row['timestamp'] for row in data]
    return render_template('tracker.html', moods=moods, dates=dates)

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return render_template('logout.html')

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
