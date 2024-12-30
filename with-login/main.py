rom flask import Flask, render_template, request, redirect, url_for, flash, session, Response
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
users = {"admin": "admin"}

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
    # print(mirror_data_path, entries)  # Untuk debugging
    return render_template("index.html", mirror_data_path=mirror_data_path, entries=entries)

@app.route("/set_path", methods=["POST"])
@login_required
def set_path():
    global mirror_data_path
    new_path = request.form.get("mirror_data_path", "").strip()
    if not new_path:
        flash("Path mirror data tidak boleh kosong.", "error")
    else:
        print(f"Set path baru ke {new_path}")
        mirror_data_path = new_path
        flash("Path mirror data berhasil diperbarui!", "success")
    return redirect(url_for("index"))

@app.route("/add_entry", methods=["POST"])
@login_required
def add_entry():
    entry = request.form.get("entry", "").strip()
    if not entry:
        flash("Entry tidak boleh kosong.", "error")
    else:
        # Baca file dan cek apakah entry sudah ada
        with open(mirror_list_file, "r") as file:
            existing_entries = file.readlines()

        # Hilangkan whitespace (strip) pada setiap baris untuk perbandingan
        existing_entries = [line.strip() for line in existing_entries]

        if entry in existing_entries:
            flash("Repo sudah ada pada list.", "error")
        else:
            with open(mirror_list_file, "a") as file:
                print(f"Menambahkan {entry} ke dalam list")
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
        print(f"Menghapus {entry_to_delete} dari list")
        if os.path.exists(mirror_list_file):
            with open(mirror_list_file, "r") as file:
                lines = file.readlines()
            with open(mirror_list_file, "w") as file:
                for line in lines:
                    if line.strip() != entry_to_delete:
                        file.write(line)
            flash("Entry berhasil dihapus!", "success")
    return redirect(url_for("index"))


@app.route("/start_mirror")
@login_required
def start_mirror():
    global mirror_data_path, container
    if not mirror_data_path:
        # return "Path mirror data belum diatur.", 400
        return {"status": "warning", "message": "Path belum diatur!"}
    if not os.path.exists(mirror_list_file):
        # return "File mirror.list belum ada. Tambahkan repository terlebih dahulu.", 400
        return {"status": "warning", "message": "mirror.list belum ada"}
    print("Menjalankan container mirror")
    try:
        #client = docker.from_env()
        client = docker.DockerClient(base_url='unix:////run/podman/podman.sock') # for podman
        container = client.containers.run(
            name="mirror",
            image="keyz078/apt-mirror:latest",
            volumes={
                os.path.abspath(mirror_list_file): {"bind": "/etc/apt/mirror.list", "mode": "ro"},
                os.path.abspath(mirror_data_path): {"bind": "/var/spool/apt-mirror", "mode": "rw"},
            },
            detach=True,
            remove=True,
            stdout=True,
            stderr=True
        )

        with open(log_file, "w") as log:
            for line in container.logs(stream=True):
                log.write(line.decode("utf-8"))

        return {"status": "Complete", "message": "Proses mirroring berhasil dijalankan!"}
    except Exception as e:
        print(e)
        return {"status": "running", "message": "Proses masih berjalan."}
        # return f"Terjadi kesalahan: {str(e)}", 500


@app.route("/stop_container")
@login_required
def stop_container():
    global container
    print("Stop container mirror")
    try:
        stop = container.stop()
        if stop:        
            return {"status": "success", "message": "Container behasil dihentikan"}
    except Exception:
        return {"status": "warning", "message": "Container tidak ada atau sudah terhapus"}

@app.route("/container_logs")
@login_required
def container_logs():
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
    global container
    def generate_logs():
        try:
            for log in container.logs(stream=True):
                yield f"{log.decode('utf-8')}"
        except Exception as e:
            yield f"Tidak ada container yang running"

    return Response(generate_logs(), content_type='text/event-stream')

@app.route("/check_status")
@login_required
def check_status():
    global container
    print("Reload status container")
    try:
        container.reload()
        if container.status == "running":
            return {"status": "running", "message": "Proses masih berjalan."}
    except Exception as e:
        return {"status": "complete", "message": "Tidak ada container yang running, silahkan cek log"}

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Mengecek user dan password
        if users.get(username) == password:
            user = User(username)
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Username atau password salah.", "error")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Anda telah logout.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)
