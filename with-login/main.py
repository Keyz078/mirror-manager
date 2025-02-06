from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import docker

app = Flask(__name__)
app.secret_key = "supersecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

mirror_data_path_ubuntu = ""
mirror_data_path_rhel = ""
mirror_list_file = ["mirror.list", "repo.conf"]
log_file = ["mirror.log", "reposync.log"]

# Connect to socket
client = docker.from_env()

sites = {
    "ubuntu": "index",
    "rhel": "rhel"
}

def get_container():
    return client.containers.list(all=True, filters={"name": "mirror"})

def read_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return [line.strip() for line in file.readlines()]
    return []

def write_file(file_path, content):
    with open(file_path, "w") as file:
        file.write(content.strip() + "\n")

class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {"admin": "admin"}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/")
@login_required
def index():
    entries = read_file(mirror_list_file[0])
    return render_template("index.html", mirror_data_path_ubuntu=mirror_data_path_ubuntu, entries=entries)

@app.route("/rhel")
@login_required
def rhel():
    entries = read_file(mirror_list_file[1])
    return render_template("rhel.html", mirror_data_path_rhel=mirror_data_path_rhel, entries=entries)

@app.route("/set_path", methods=["POST"])
@login_required
def set_path():
    global mirror_data_path_ubuntu, mirror_data_path_rhel, sites
    os_type = request.form["os_type"]
    new_path = request.form.get(f"mirror_data_path_{os_type}", "").strip()

    if not new_path:
        flash("Path mirror data tidak boleh kosong.", "error")
    else:
        print(f"Set path baru ke {new_path}")
        if os_type == "ubuntu":
            mirror_data_path_ubuntu = new_path
        elif os_type == "rhel":
            mirror_data_path_rhel = new_path
        flash("Path mirror data berhasil diperbarui!", "success")
        return redirect(url_for(f"{sites[os_type]}"))

@app.route("/update", methods=["POST"])
@login_required
def update():
    new_repo = request.form["entry"]
    os_type = request.form["os_type"]
    mirror_file = mirror_list_file[0] if os_type == "ubuntu" else mirror_list_file[1]
    
    write_file(mirror_file, new_repo)
    flash("list mirror repo berhasil diperbarui!", "success")
    return redirect(url_for(f"{sites[os_type]}"))

@app.route("/containers")
@login_required
def list_containers():
    containers = get_container()
    container_data = [{"id": c.id, "name": c.name, "status": c.status} for c in containers]
    return jsonify(container_data)

@app.route("/start_mirror", methods=["GET"])
@login_required
def start_mirror():
    global mirror_data_path_rhel, mirror_data_path_ubuntu
    os_type = request.args.get('os_type', 'ubuntu')
    if not mirror_data_path_ubuntu and not mirror_data_path_rhel:
        return {"status": "warning", "message": "Path belum diatur!"}
    
    mirror_list_file_exists = os.path.exists(mirror_list_file[0]) and os.path.exists(mirror_list_file[1])
    if not mirror_list_file_exists:
        return {"status": "warning", "message": "mirror.list belum ada"}

    try:
        container_name = f"mirror-{os_type}"
        image = "keyz078/apt-mirror:latest" if os_type == "ubuntu" else "keyz078/reposync:ubi8"
        bind_paths = {
            os.path.abspath(mirror_list_file[0] if os_type == "ubuntu" else mirror_list_file[1]): {
                "bind": "/etc/apt/mirror.list" if os_type == "ubuntu" else "/opt/scripts/config.conf", 
                "mode": "ro"
            },
            os.path.abspath(mirror_data_path_ubuntu if os_type == "ubuntu" else mirror_data_path_rhel): {
                "bind": "/var/spool/apt-mirror" if os_type == "ubuntu" else "/mirror", 
                "mode": "rw"
            }
        }

        container = client.containers.run(
            name=container_name,
            image=image,
            volumes=bind_paths,
            detach=True,
            remove=True,
            stdout=True,
            stderr=True
        )

        log_file_path = log_file[0] if os_type == "ubuntu" else log_file[1]
        with open(log_file_path, "w") as log:
            for line in container.logs(stream=True):
                log.write(line.decode("utf-8"))

        return {"status": "Complete", "message": "Proses mirroring telah selesai."}

    except Exception as e:
        print(e)
        return {"status": "running", "message": "Proses masih berjalan."}

@app.route("/stop_container")
@login_required
def stop_container():
    global container
    try:
        stop = container.stop()
        if stop:        
            return {"status": "success", "message": "Container berhasil dihentikan"}
    except Exception:
        return {"status": "warning", "message": "Container tidak ada atau sudah terhapus"}

@app.route("/container_logs", methods=["GET"])
@login_required
def container_logs():
    os_type = request.args.get('os_type', 'ubuntu')
    print(os_type)
    log_file_path = log_file[0] if os_type == "ubuntu" else log_file[1]
    
    if not os.path.exists(log_file_path):
        flash("Log tidak ditemukan. Pastikan proses mirroring sudah dijalankan.", "error")
        return redirect(url_for("index" if os_type == "ubuntu" else "rhel"))

    def generate_logs():
        with open(log_file_path, "r") as log_file_stream:
            for line in log_file_stream:
                yield f"{line}"

    return Response(generate_logs(), mimetype="text/plain")

@app.route("/stream_logs", methods=["GET"])
@login_required
def stream_logs():
    containerID = request.args.get('containerID', None)
    container = client.containers.get(containerID)
    
    def generate_logs():
        try:
            for log in container.logs(stream=True):
                yield f"{log.decode('utf-8')}"
        except Exception as e:
            yield f"Tidak ada container yang running"

    return Response(generate_logs(), content_type='text/event-stream')

@app.route("/delete", methods=["POST"])
@login_required
def delete():
    containerID = request.form['container_id']
    container = client.containers.get(containerID)
    try:
        container.remove(force=True)
        print(f"Container {containerID} berhasil dihapus")
        flash("Container berhasil dihapus", "success")
        return redirect(url_for('index'))
    except Exception as e:
        return True

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

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
    app.run(host='0.0.0.0', debug=True)
