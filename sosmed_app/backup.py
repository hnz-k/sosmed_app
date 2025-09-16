from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3, os, smtplib, ssl, random, time
from werkzeug.utils import secure_filename
from datetime import datetime, timezone, timedelta
import pytz
from otp import send_otp_email, update_config

app = Flask(__name__)
app.secret_key = "rahasia123"
app.config['SESSION_TYPE'] = 'filesystem'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")

# Konfigurasi upload file
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size

# Timezone Indonesia (WIB)
WIB = pytz.timezone('Asia/Jakarta')

update_config({
    'app_name': 'Acong App',
    'support_email': 'acong8709@gmail.com'
})
# Simpan OTP sementara beserta timestamp
otp_storage = {}

# === FUNGSI BANTU ===
def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_time():
    """Mendapatkan waktu saat ini dalam timezone Indonesia"""
    return datetime.now(WIB)

def format_datetime(dt_string, format_type='relative'):
    """
    Format datetime untuk ditampilkan
    format_type: 'relative' (x menit yang lalu), 'short' (DD/MM/YY HH:MM), 'long' (DD Month YYYY HH:MM)
    """
    if not dt_string:
        return "Waktu tidak tersedia"
    
    # Jika dt_string adalah string, konversi ke datetime
    if isinstance(dt_string, str):
        try:
            # Handle format dengan timezone offset (2025-09-14 09:27:43.121468+07:00)
            if '+' in dt_string:
                # Pisahkan bagian datetime dan timezone
                dt_part = dt_string.split('+')[0].strip()
                # Hapus microseconds jika ada
                if '.' in dt_part:
                    dt_part = dt_part.split('.')[0]
                
                # Parse datetime
                dt = datetime.strptime(dt_part, '%Y-%m-%d %H:%M:%S')
                # Asumsikan waktu dari database adalah WIB, konversi ke timezone aware
                dt = WIB.localize(dt)
            else:
                # Coba parsing format default SQLite
                dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
                # Asumsikan waktu dari database adalah UTC, konversi ke WIB
                dt = pytz.utc.localize(dt).astimezone(WIB)
        except ValueError:
            try:
                # Coba format lain jika ada
                dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S.%f')
                dt = pytz.utc.localize(dt).astimezone(WIB)
            except:
                return "Waktu tidak valid"
    else:
        dt = dt_string
    
    if format_type == 'relative':
        now = datetime.now(WIB)
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} tahun yang lalu"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} bulan yang lalu"
        elif diff.days > 0:
            return f"{diff.days} hari yang lalu"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} jam yang lalu"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} menit yang lalu"
        else:
            return "Baru saja"
    
    elif format_type == 'short':
        return dt.strftime('%d/%m/%y %H:%M')
    
    elif format_type == 'long':
        months_id = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        return f"{dt.day} {months_id[dt.month-1]} {dt.year} {dt.hour:02d}:{dt.minute:02d}"
    
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tabel users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  email TEXT UNIQUE,
                  password TEXT,
                  profile_picture TEXT,
                  display_name TEXT,
                  bio TEXT,
                  location TEXT,
                  website TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tabel posts
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  content TEXT,
                  image_path TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Tabel follows
    c.execute('''CREATE TABLE IF NOT EXISTS follows
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  follower_id INTEGER,
                  following_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  UNIQUE(follower_id, following_id),
                  FOREIGN KEY (follower_id) REFERENCES users (id),
                  FOREIGN KEY (following_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()
    
    # Buat folder uploads jika belum ada
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f"Created upload folder: {UPLOAD_FOLDER}")

# === Kirim OTP ke Email ===
def send_otp(receiver_email):
    """
    Mengirim OTP ke email menggunakan template modern
    
    Args:
        receiver_email (str): Email penerima
        
    Returns:
        str: OTP code atau None jika gagal
    """
    try:
        # Kirim email menggunakan module otp.py
        otp = send_otp_email(receiver_email)
        
        if otp:
            # Simpan OTP dengan timestamp (kode yang sudah ada)
            otp_storage[receiver_email] = {
                'otp': otp,
                'timestamp': time.time()
            }
            print(f"✅ OTP berhasil dikirim ke {receiver_email}")
            return otp
        else:
            print(f"❌ Gagal mengirim OTP ke {receiver_email}")
            return None
            
    except Exception as e:
        print(f"❌ Error dalam send_otp: {e}")
        return None

# === Validasi OTP ===
def validate_otp(email, otp_input):
    if email in otp_storage:
        stored_otp_data = otp_storage[email]
        stored_otp = stored_otp_data['otp']
        otp_timestamp = stored_otp_data['timestamp']
        
        # Cek apakah OTP masih berlaku (5 menit)
        if time.time() - otp_timestamp < 300:  # 300 detik = 5 menit
            return stored_otp == otp_input
        else:
            # Hapus OTP yang sudah kadaluarsa
            del otp_storage[email]
    return False

# === ROUTES ===
@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        identity = request.form["identity"]
        password = request.form["password"]

        conn = get_db_connection()
        if "@" in identity:
            user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", 
                               (identity, password)).fetchone()
        else:
            user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", 
                               (identity, password)).fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["email"] = user["email"]
            session["user_id"] = user["id"]
            return redirect(url_for("home"))
        else:
            error = "Email/Username atau password salah!"
    return render_template("login.html", error=error)

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                      (username, email, password))
            conn.commit()
            conn.close()
            flash("Registrasi berhasil! Silakan login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            error = "Username atau Email sudah dipakai!"
    return render_template("register.html", error=error)

# FORGOT PASSWORD
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    msg = None
    if request.method == "POST":
        email = request.form["email"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user:
            send_otp(email)
            session["reset_email"] = email
            return redirect(url_for("verify_otp"))
        else:
            msg = "Email tidak terdaftar!"
    return render_template("forgot_password.html", msg=msg)

# VERIFY OTP
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    error = None
    if request.method == "POST":
        email = session.get("reset_email")
        otp_input = request.form["otp"]

        if email and validate_otp(email, otp_input):
            return redirect(url_for("reset_password"))
        else:
            error = "OTP salah atau kadaluarsa!"
    return render_template("verify_otp.html", error=error)

# KIRIM ULANG OTP
@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    email = session.get("reset_email")
    if email:
        # Hapus OTP lama jika ada
        if email in otp_storage:
            del otp_storage[email]
        
        # Kirim OTP baru
        send_otp(email)
        return jsonify({"success": True, "message": "OTP berhasil dikirim ulang"})
    else:
        return jsonify({"success": False, "message": "Sesi reset password tidak valid"}), 400

# RESET PASSWORD
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    error = None
    if request.method == "POST":
        email = session.get("reset_email")
        password = request.form["password"]

        if email:
            conn = get_db_connection()
            conn.execute("UPDATE users SET password=? WHERE email=?", (password, email))
            conn.commit()
            conn.close()
            session.pop("reset_email", None)
            if email in otp_storage:
                del otp_storage[email]
            flash("Password berhasil direset! Silakan login.", "success")
            return redirect(url_for("login"))
        else:
            error = "Sesi reset password tidak valid!"
    return render_template("reset_password.html", error=error)

# HOME (Dashboard User)
@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    
    # Get user info
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    
    # Get user stats
    post_count = conn.execute("SELECT COUNT(*) FROM posts WHERE user_id=?", 
                            (session["user_id"],)).fetchone()[0]
    
    followers_count = conn.execute("SELECT COUNT(*) FROM follows WHERE following_id=?", 
                                 (session["user_id"],)).fetchone()[0]
    
    following_count = conn.execute("SELECT COUNT(*) FROM posts WHERE user_id=?", 
                                 (session["user_id"],)).fetchone()[0]
    
    conn.close()
    
    if user:
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'profile_picture': user['profile_picture'] if user['profile_picture'] else '/static/default-avatar.png',
            'display_name': user['display_name'] if user['display_name'] else user['username'],
            'bio': user['bio'] if user['bio'] else 'Belum ada bio',
            'location': user['location'] if user['location'] else 'Belum diatur',
            'website': user['website'] if user['website'] else '#',
            'created_at': user['created_at']
        }
        return render_template("home.html", user=user_data, 
                             post_count=post_count,
                             followers_count=followers_count,
                             following_count=following_count)
    else:
        return redirect(url_for("login"))

# CREATE POST
@app.route("/create-post", methods=["GET", "POST"])
def create_post():
    if "username" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        content = request.form["content"]
        image_path = None
        
        # Handle file upload
        file = request.files.get('post_image')
        if file and file.filename != '':
            if allowed_file(file.filename):
                try:
                    file_ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"post_{session['user_id']}_{int(time.time())}.{file_ext}"
                    filename = secure_filename(filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    image_path = filename
                except Exception as e:
                    flash("Error uploading image", "error")
        
        # Simpan dengan waktu yang tepat
        current_time = datetime.now(WIB)
        conn = get_db_connection()
        conn.execute("INSERT INTO posts (user_id, content, image_path, created_at) VALUES (?, ?, ?, ?)",
                    (session['user_id'], content, image_path, current_time))
        conn.commit()
        conn.close()
        
        flash("Postingan berhasil dibuat!", "success")
        return redirect(url_for("home"))
    
    return render_template("create_post.html")

# SEARCH USERS
@app.route("/search")
def search():
    if "username" not in session:
        return redirect(url_for("login"))
    
    query = request.args.get("q", "")
    results = []
    
    if query:
        conn = get_db_connection()
        results = conn.execute(
            "SELECT id, username, display_name, profile_picture FROM users WHERE username LIKE ? OR display_name LIKE ?",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
        conn.close()
    
    return render_template("search.html", query=query, results=results)

# USER PROFILE
@app.route("/profile/<username>")
def profile(username):
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    
    # Get user info
    user = conn.execute(
        "SELECT id, username, display_name, profile_picture, bio, location, website, created_at FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    
    if not user:
        flash("User tidak ditemukan", "error")
        return redirect(url_for("home"))
    
    # Get user posts
    posts = conn.execute(
        "SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC",
        (user['id'],)
    ).fetchall()
    
    # Get follow stats
    followers_count = conn.execute(
        "SELECT COUNT(*) FROM follows WHERE following_id = ?",
        (user['id'],)
    ).fetchone()[0]
    
    following_count = conn.execute(
        "SELECT COUNT(*) FROM follows WHERE follower_id = ?",
        (user['id'],)
    ).fetchone()[0]
    
    # Check if current user follows this user
    is_following = False
    if session['user_id'] != user['id']:
        follow = conn.execute(
            "SELECT * FROM follows WHERE follower_id = ? AND following_id = ?",
            (session['user_id'], user['id'])
        ).fetchone()
        is_following = bool(follow)
    
    conn.close()
    
    return render_template("profile.html", 
                          user=user, 
                          posts=posts, 
                          followers_count=followers_count,
                          following_count=following_count,
                          is_following=is_following,
                          format_datetime=format_datetime)

# FOLLOW/UNFOLLOW
@app.route("/follow/<int:user_id>", methods=["POST"])
def follow_user(user_id):
    if "username" not in session:
        return redirect(url_for("login"))
    
    if session['user_id'] == user_id:
        flash("Tidak bisa follow diri sendiri", "error")
        return redirect(request.referrer or url_for("home"))
    
    conn = get_db_connection()
    
    # Check if already following
    existing = conn.execute(
        "SELECT * FROM follows WHERE follower_id = ? AND following_id = ?",
        (session['user_id'], user_id)
    ).fetchone()
    
    if existing:
        conn.execute(
            "DELETE FROM follows WHERE follower_id = ? AND following_id = ?",
            (session['user_id'], user_id)
        )
        action = "unfollowed"
    else:
        conn.execute(
            "INSERT INTO follows (follower_id, following_id) VALUES (?, ?)",
            (session['user_id'], user_id)
        )
        action = "followed"
    
    conn.commit()
    conn.close()
    
    flash(f"Berhasil {action} user", "success")
    return redirect(request.referrer or url_for("home"))

# FEED (Timeline)
@app.route("/feed")
def feed():
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    
    # Get posts from users that the current user follows
    posts = conn.execute('''
        SELECT p.*, u.username, u.display_name, u.profile_picture 
        FROM posts p 
        JOIN users u ON p.user_id = u.id 
        WHERE p.user_id = ? OR p.user_id IN (
            SELECT following_id FROM follows WHERE follower_id = ?
        )
        ORDER BY p.created_at DESC
    ''', (session['user_id'], session['user_id'])).fetchall()
    
    conn.close()
    
    return render_template("feed.html", posts=posts, format_datetime=format_datetime)

# EDIT PROFILE
@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", 
        (session['user_id'],)
    ).fetchone()
    
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        bio = request.form.get("bio", "").strip()
        location = request.form.get("location", "").strip()
        website = request.form.get("website", "").strip()
        
        # Handle profile picture upload
        profile_picture = user['profile_picture']
        file = request.files.get('profile_picture')
        if file and file.filename != '':
            if allowed_file(file.filename):
                try:
                    # Delete old profile picture if exists
                    if profile_picture:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_picture)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    # Save new profile picture
                    file_ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"profile_{session['user_id']}_{int(time.time())}.{file_ext}"
                    filename = secure_filename(filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    profile_picture = filename
                except Exception as e:
                    flash("Error uploading profile picture", "error")
        
        conn.execute(
            "UPDATE users SET display_name = ?, bio = ?, location = ?, website = ?, profile_picture = ? WHERE id = ?",
            (display_name, bio, location, website, profile_picture, session['user_id'])
        )
        conn.commit()
        conn.close()
        
        flash("Profile berhasil diperbarui!", "success")
        return redirect(url_for("profile", username=session['username']))
    
    conn.close()
    return render_template("edit_profile.html", user=user)

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# DELETE POST
@app.route("/delete-post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    
    # Verify post ownership
    post = conn.execute(
        "SELECT * FROM posts WHERE id = ? AND user_id = ?",
        (post_id, session['user_id'])
    ).fetchone()
    
    if post:
        # Delete associated image if exists
        if post['image_path']:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], post['image_path'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        flash("Postingan berhasil dihapus", "success")
    else:
        flash("Tidak bisa menghapus postingan ini", "error")
    
    conn.close()
    return redirect(request.referrer or url_for("home"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)