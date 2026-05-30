from flask import Flask, render_template, request, redirect, url_for, session, flash # type: ignore
import os, re, sqlite3, joblib, pandas as pd # type: ignore
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smart_grievance_secret_key"
DB_NAME, MODEL_DIR = "complaints.db", "models"

vectorizer = joblib.load(os.path.join(MODEL_DIR, "vectorizer.pkl"))
dept_model = joblib.load(os.path.join(MODEL_DIR, "dept_model.pkl"))
urg_model = joblib.load(os.path.join(MODEL_DIR, "urg_model.pkl"))

USERS = {
    "user": {"password": "123", "role": "user"},
    "admin": {"password": "123", "role": "authority"}
}

SEVERITY_WORDS = {
    "fire": 5, "accident": 5, "danger": 5, "death": 5, "injury": 5,
    "urgent": 4, "emergency": 4, "overflow": 3, "sparks": 4,
    "blocked": 2, "delay": 2, "problem": 1, "issue": 1,
    "garbage": 2, "potholes": 3, "water": 2, "sewage": 3, "electricity": 2
}

LOCATION_COORDS = {
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "kolkata": (22.5726, 88.3639),
    "chennai": (13.0827, 80.2707),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "bhopal": (23.2599, 77.4126),
    "indore": (22.7196, 75.8577),
    "patna": (25.5941, 85.1376),
    "ahmedabad": (23.0225, 72.5714),
    "surat": (21.1702, 72.8311),
    "kanpur": (26.4499, 80.3319),
    "nagpur": (21.1458, 79.0882)
}

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_dicts(rows):
    return [dict(r) for r in rows]

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            complaint_text TEXT NOT NULL,
            location TEXT NOT NULL,
            department TEXT,
            ml_urgency TEXT,
            final_priority TEXT,
            score INTEGER,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def preprocess_text(text):
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(text).lower())
    return re.sub(r'\s+', ' ', text).strip()

def keyword_score(text):
    score = 0
    for word, count in Counter(preprocess_text(text).split()).items():
        if word in SEVERITY_WORDS:
            score += SEVERITY_WORDS[word] * count
    return score

def location_frequency(location):
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM complaints WHERE LOWER(location)=LOWER(?)",
        (location,)
    ).fetchone()["cnt"]
    conn.close()
    return count

def geo_priority(location):
    if not os.path.exists("geo_data.csv"):
        return 0
    df = pd.read_csv("geo_data.csv")
    if "location" not in df.columns or "pending" not in df.columns:
        return 0
    row = df[df["location"].astype(str).str.lower() == str(location).lower()]
    if row.empty:
        return 0
    pending = int(row.iloc[0]["pending"])
    return 4 if pending > 200 else 3 if pending > 100 else 2 if pending > 50 else 1

def calculate_final_priority(ml_urgency, severity_score, loc_freq, geo_score):
    total = 5 if ml_urgency.lower() == "high" else 3 if ml_urgency.lower() == "medium" else 1
    total += severity_score + geo_score
    total += 4 if loc_freq >= 5 else 2 if loc_freq >= 3 else 1 if loc_freq >= 1 else 0
    return ("High", total) if total >= 10 else ("Medium", total) if total >= 5 else ("Low", total)

def get_coords(location):
    key = str(location).strip().lower()
    if key in LOCATION_COORDS:
        return LOCATION_COORDS[key]
    seed = sum(ord(c) for c in key)
    lat = 20 + (seed % 1200) / 100
    lng = 72 + (seed % 1600) / 100
    return round(lat, 4), round(lng, 4)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = USERS.get(username)
        if user and user["password"] == password:
            session["username"], session["role"] = username, user["role"]
            return redirect(url_for("authority_dashboard" if user["role"] == "authority" else "home"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    if "username" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    complaint_text = request.form.get("complaint_text", "").strip()
    location = request.form.get("location", "").strip()

    if not name or not complaint_text or not location:
        flash("All fields are required.")
        return redirect(url_for("home"))

    clean_text = preprocess_text(complaint_text)
    text_vec = vectorizer.transform([clean_text])
    department = dept_model.predict(text_vec)[0]
    ml_urgency = urg_model.predict(text_vec)[0]
    final_priority, total_score = calculate_final_priority(
        ml_urgency, keyword_score(clean_text), location_frequency(location), geo_priority(location)
    )

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO complaints
        (name, complaint_text, location, department, ml_urgency, final_priority, score, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, complaint_text, location, department, ml_urgency,
        final_priority, total_score, "Pending",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    complaint_id = c.lastrowid
    conn.commit()
    conn.close()
    return redirect(url_for("track", complaint_id=complaint_id))

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    if session.get("role") != "authority":
        return redirect(url_for("login"))

    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Please select a CSV file.")
        return redirect(url_for("home"))

    df = pd.read_csv(file)
    if not {"name", "complaint_text", "location"}.issubset(df.columns):
        flash("CSV must contain columns: name, complaint_text, location")
        return redirect(url_for("home"))

    conn = get_connection()
    c = conn.cursor()

    for _, row in df.iterrows():
        name = str(row["name"]).strip()
        complaint_text = str(row["complaint_text"]).strip()
        location = str(row["location"]).strip()
        if not complaint_text:
            continue

        clean_text = preprocess_text(complaint_text)
        text_vec = vectorizer.transform([clean_text])
        department = dept_model.predict(text_vec)[0]
        ml_urgency = urg_model.predict(text_vec)[0]
        final_priority, total_score = calculate_final_priority(
            ml_urgency, keyword_score(clean_text), location_frequency(location), geo_priority(location)
        )

        c.execute("""
            INSERT INTO complaints
            (name, complaint_text, location, department, ml_urgency, final_priority, score, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, complaint_text, location, department, ml_urgency,
            final_priority, total_score, "Pending",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    conn.commit()
    conn.close()
    flash("CSV uploaded successfully.")
    return redirect(url_for("authority_dashboard"))

@app.route("/track/<int:complaint_id>")
def track(complaint_id):
    if "username" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    complaint = row_to_dict(conn.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,)).fetchone())
    conn.close()
    if complaint is None:
        return "Complaint not found", 404
    return render_template("track.html", complaint=complaint)

@app.route("/user_dashboard")
def user_dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    complaints = rows_to_dicts(conn.execute("SELECT * FROM complaints ORDER BY id DESC").fetchall())
    conn.close()
    return render_template("user_dashboard.html", complaints=complaints)

@app.route("/authority_dashboard")
def authority_dashboard():
    if session.get("role") != "authority":
        return redirect(url_for("login"))

    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) AS cnt FROM complaints").fetchone()["cnt"]
    pending = conn.execute("SELECT COUNT(*) AS cnt FROM complaints WHERE status!='Resolved'").fetchone()["cnt"]
    resolved = conn.execute("SELECT COUNT(*) AS cnt FROM complaints WHERE status='Resolved'").fetchone()["cnt"]
    high = conn.execute("SELECT COUNT(*) AS cnt FROM complaints WHERE final_priority='High'").fetchone()["cnt"]
    medium = conn.execute("SELECT COUNT(*) AS cnt FROM complaints WHERE final_priority='Medium'").fetchone()["cnt"]
    low = conn.execute("SELECT COUNT(*) AS cnt FROM complaints WHERE final_priority='Low'").fetchone()["cnt"]
    hotspot = row_to_dict(conn.execute("""
        SELECT location, COUNT(*) AS cnt
        FROM complaints
        GROUP BY location
        ORDER BY cnt DESC
        LIMIT 1
    """).fetchone())
    complaints = rows_to_dicts(conn.execute("""
        SELECT * FROM complaints
        ORDER BY CASE final_priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
                 score DESC, id DESC
    """).fetchall())
    conn.close()

    return render_template(
        "authority_dashboard.html",
        complaints=complaints, total=total, pending=pending, resolved=resolved,
        hotspot=hotspot, high=high, medium=medium, low=low
    )

@app.route("/update_status/<int:complaint_id>/<new_status>")
def update_status(complaint_id, new_status):
    if session.get("role") != "authority":
        return redirect(url_for("login"))
    if new_status == "InProgress":
        new_status = "In Progress"
    conn = get_connection()
    conn.execute("UPDATE complaints SET status=? WHERE id=?", (new_status, complaint_id))
    conn.commit()
    conn.close()
    return redirect(url_for("authority_dashboard"))

@app.route("/delete_complaint/<int:complaint_id>")
def delete_complaint(complaint_id):
    if "username" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    conn.execute("DELETE FROM complaints WHERE id=?", (complaint_id,))
    conn.commit()
    conn.close()
    flash("Complaint deleted successfully.")
    return redirect(url_for("authority_dashboard" if session.get("role") == "authority" else "user_dashboard"))

@app.route("/heatmap")
def heatmap():
    if session.get("role") != "authority":
        return redirect(url_for("login"))

    conn = get_connection()
    rows = conn.execute("""
        SELECT location, COUNT(*) AS pending
        FROM complaints
        GROUP BY location
        ORDER BY pending DESC
    """).fetchall()
    conn.close()

    geo_points = []
    for row in rows:
        lat, lng = get_coords(row["location"])
        geo_points.append({
            "location": row["location"],
            "lat": lat,
            "lng": lng,
            "pending": row["pending"]
        })

    return render_template("heatmap.html", geo_points=geo_points)

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if "username" not in session:
        return redirect(url_for("login"))

    reply, suggestions = "", []

    if request.method == "POST":
        msg = request.form.get("message", "").strip().lower()

        if any(x in msg for x in ["hello", "hi", "hey"]):
            reply = "Hello! Main Smart Grievance Assistant hoon. Main complaint submit, track, priority, dashboard aur heatmap ke baare me help kar sakta hoon."
            suggestions = ["How to submit complaint?", "How is priority calculated?", "How to track complaint?"]

        elif "submit" in msg or "register" in msg or "complaint" in msg:
            reply = "Home page par name, complaint text aur location enter karo. System ML se department aur urgency predict karta hai aur final priority assign karta hai."
            suggestions = ["What happens after submit?", "How is department predicted?", "How is priority assigned?"]

        elif "track" in msg or "status" in msg:
            reply = "User Dashboard me View option se complaint track hoti hai. Tracking page par ID, location, priority, status aur time show hota hai."
            suggestions = ["What do pending and resolved mean?", "How do authorities update status?"]

        elif "priority" in msg or "urgent" in msg:
            reply = "Priority ML urgency, keyword severity, same location frequency aur geo pending data se calculate hoti hai."
            suggestions = ["What is ML urgency?", "What is geo priority?", "How are complaints sorted?"]

        elif "department" in msg or "authority" in msg:
            reply = "System complaint text ko analyze karke department predict karta hai, jaise electricity, water, municipal ya roads. Ye authority side par visible hota hai."
            suggestions = ["Can users see authority?", "How does ML classify complaint?"]

        elif "heatmap" in msg or "map" in msg:
            reply = "Heatmap ab real complaints data se banta hai. Jis location par jitni complaints, usi hisaab se hotspot dikhte hain."
            suggestions = ["How is hotspot decided?", "Who can see heatmap?"]

        elif "graph" in msg or "analysis" in msg or "dashboard" in msg:
            reply = "Authority dashboard me total, pending, resolved aur hotspot cards hote hain. Saath hi priority graph aur sorted complaints list hoti hai."
            suggestions = ["What is hotspot?", "What is final score?"]

        elif "delete" in msg or "remove" in msg:
            reply = "Haan, complaint delete ki ja sakti hai. Delete karne par complaint database se remove ho jaati hai."
            suggestions = ["Can admin delete any complaint?", "Is deleted complaint recoverable?"]

        else:
            reply = "Main complaint submit, tracking, dashboard, priority, heatmap aur portal working ke baare me help kar sakta hoon."
            suggestions = ["How to submit complaint?", "How to track complaint?", "How is priority calculated?"]

    return render_template("chatbot.html", reply=reply, suggestions=suggestions)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)