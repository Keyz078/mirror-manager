from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import docker

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Kunci untuk session dan flash messages

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Halaman login jika user belum login

# Tentukan path file dan direktori
mirror_data_path = ""
mirror_list_file = "mirror.list"
log_file = "mirror.log"

# User untuk autentikasi
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Dummy user untuk testing
users = {"admin": "password123"}

# Memuat user berdasarkan id
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/")
@login_required
def index():
    entries = []
    if os.path.exists(mirror_list_file):
        with open(mirror_list_file, "r") as file:
            entries = [line.strip() for line in file.readlines()]
    print(mirror_data_path, entries)  # Untuk debugging
    return render_template("index.html", mirror_data_path=mirror_data_path, entries=entries)

@app.route("/set_path", methods=["POST"])
@login_required
def set_path():
    global mirror_data_path
    new_path = request.form.get("mirror_data_path", "").strip()
    if not new_path:
        flash("Path mirror data tidak boleh kosong.", "error")
    else:
        mirror_data_path = new_path
        flash("Path mirror data berhasil diperbarui!", "success")
    return redirect(url_for("index"))

@app.route("/clear_path", methods=["POST"])
@login_required
def clear_path():
    global mirror_data_path
    mirror_data_path = ""  # Menghapus nilai path
    flash("Path mirror data telah dihapus.", "info")
    return redirect(url_for("index"))

@app.route("/add_entry", methods=["POST"])
@login_required
def add_entry():
    entry = request.form.get("entry", "").strip()
    if not entry:
        flash("Entry tidak boleh kosong.", "error")
    else:
        with open(mirror_list_file, "a") as file:
            file.write(entry + "\n")
        flash("Entry berhasil ditambahkan!", "success")
    return redirect(url_for("index"))

@app.route("/delete_entry", methods=["POST"])
@login_required
def delete_entry():
    entry_to_delete = request.form.get("entry_to_delete", "").strip()
    if not entry_to_delete:
        flash("Entry yang dipilih tidak valid.", "error")
    else:
        if os.path.exists(mirror_list_file):
            with open(mirror_list_file, "r") as file:
                lines = file.readlines()
            with open(mirror_list_file, "w") as file:
                for line in lines:
                    if line.strip() != entry_to_delete:
                        file.write(line)
            flash("Entry berhasil dihapus!", "success")
    return redirect(url_for("index"))

@app.route("/start_mirror", methods=["POST"])
@login_required
def start_mirror():
    global mirror_data_path
    try:
        client = docker.from_env()
        container = client.containers.run(
            name="mirror",
            image="apt-mirror:latest",
            volumes={
                os.path.abspath(mirror_list_file): {"bind": "/etc/apt/mirror.list", "mode": "ro"},
                os.path.abspath(mirror_data_path): {"bind": "/var/spool/apt-mirror", "mode": "rw"},
            },
            detach=True,
            remove=True,
            stdout=True,
            stderr=True
        )
        flash("Proses mirroring berhasil dijalankan!", "success")
        return redirect(url_for("index"))
    except docker.errors.APIError as e:
        if e.response.status_code == 409:  # Status code 409 berarti container sudah berjalan
            flash("Proses sync sedang berjalan. Tunggu hingga selesai sebelum memulai yang baru.", "warning")
        else:
            flash(f"Terjadi kesalahan: {e}", "error")
    return redirect(url_for("index"))

@app.route("/container_logs")
@login_required
def container_logs():
    """
    Menampilkan log yang telah disimpan ke file log
    """
    if not os.path.exists(log_file):
        flash("Log tidak ditemukan. Pastikan proses mirroring sudah dijalankan.", "error")
        return redirect(url_for("index"))

    def generate_logs():
        with open(log_file, "r") as log_file_stream:
            for line in log_file_stream:
                yield f"{line}"

    return Response(generate_logs(), mimetype="text/plain")

@app.route("/stream_logs")
@login_required
def stream_logs():
    """
    Streaming log secara real-time dari container ke klien
    """
    global container
    def generate_logs():
        if container and container.status == "running":
            # Stream log langsung dari container
            try:
                for log in container.logs(stream=True):
                    yield f"{log.decode('utf-8')}"
            except Exception as e:
                yield f"Proses mirroring selesai atau container tidak berjalan"
        else:
            yield f"Tidak ada container yang running"

    return Response(generate_logs(), content_type='text/event-stream')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Mengecek user dan password
        if users.get(username) == password:
            user = User(username)
            login_user(user)
            flash("Login berhasil!", "success")
            return redirect(url_for("index"))
        else:
            flash("Username atau password salah.", "error")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout berhasil.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
