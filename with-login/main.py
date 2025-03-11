from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os
import docker
import random
import string
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

mirror_files = {}
client = docker.from_env()

CONFIG_PATH = "config/config.json"

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

config = load_config()

def web_server():
    repo_path = config.get("repo_path")
    web_server = config.get("web_server")
    host_port = config.get("host_port")

    if "nginx-repo" in [c.name for c in client.containers.list(all=True)]:
        client.containers.get("nginx-repo").remove(force=True)

    if web_server == "enabled" and host_port:
        bind_paths = {
            os.path.abspath(repo_path): {"bind": "/var/www/html", "mode": "ro"},
            os.path.abspath("config/nginx.conf"): {"bind": "/etc/nginx/conf.d/default.conf", "mode": "ro"}
        }
        try:
            client.containers.run(
                name="nginx-repo",
                image="nginx:alpine",
                volumes=bind_paths,
                ports={"80/tcp": host_port},
                detach=True
            )
        except Exception as e:
            print(f"Error: {e}")

web_server()

def find_and_symlink_folders(source_root, target_root):
    base_repos = {"archive.ubuntu.com": "archive", "security.ubuntu.com": "security"}
    
    for root, dirs, _ in os.walk(source_root):
        for folder in ('dists', 'pool'):
            if folder in dirs:
                old_path = os.path.join(root, folder)
                relative_path = os.path.relpath(root, source_root).split(os.sep)
                domain_name = relative_path[0]
                
                if domain_name in base_repos:
                    domain_name = base_repos[domain_name]  
                else:
                    domain_parts = domain_name.split('.')
                    if len(domain_parts) > 2:
                        domain_name = domain_parts[-2]  
                    else:
                        domain_name = domain_parts[0] 
                
                sub_path = relative_path[1:-1] if len(relative_path) > 2 else []
                if sub_path and sub_path[0].lower() == domain_name.lower():
                    sub_path = sub_path[1:]
                
                new_path = os.path.join(target_root, domain_name, *sub_path, folder)
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                
                if not os.path.exists(new_path):
                    os.symlink(old_path, new_path)
                    print(f"Symlinked {old_path} -> {new_path}")
                else:
                    print(f"Symlink already exists: {new_path}")

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
    return render_template("index.html")

@app.route("/containers")
@login_required
def list_containers():
    containers = get_container()
    return jsonify([{"id": c.id, "name": c.name, "status": c.status} for c in containers])

@app.route("/add", methods=["POST"])
@login_required
def start_mirror():
    global mirror_files, config
    
    mirror_path = config.get("mirror_path")
    repo_path = config.get("repo_path")
    repo_config_path = config.get("repo_config_path")
    repo_log_path = config.get("repo_log_path")
    container_name = request.form['container_name'] or ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    os_type = request.form['os_type']

    if os_type not in ["ubuntu", "rhel"]:
        return {"status": "Error", "message": "Wrong OS Type!"}

    new_mirror_path = os.path.join(mirror_path, "ubuntu-sync" if os_type == "ubuntu" else os.path.join(repo_path, "rhel"))
    repo_list = request.form['repo_list']
    rhel_version = request.form.get("rhel_version", "").strip()

    try:
        os.makedirs(repo_config_path, exist_ok=True)
        os.makedirs(new_mirror_path, exist_ok=True)

        file_ext = "list" if os_type == "ubuntu" else "conf"
        mirror_file = os.path.join(repo_config_path, f'mirror-{os_type}-{container_name}.{file_ext}')

        with open(mirror_file, "w") as f:
            if os_type == "ubuntu":
                f.write(repo_list)
            else:
                if not rhel_version:
                    return {"status": "Error", "message": "RHEL Version and Repo Name are required for RHEL mirroring."}
                f.write(repo_list)

        image = "keyz078/apt-mirror:latest" if os_type == "ubuntu" else "keyz078/reposync:dev"
        bind_paths = {
            os.path.abspath(mirror_file): {"bind": "/etc/apt/mirror.list" if os_type == "ubuntu" else "/opt/scripts/config.conf", "mode": "ro"},
            os.path.abspath(new_mirror_path): {"bind": "/var/spool/apt-mirror/mirror" if os_type == "ubuntu" else "/mirror", "mode": "rw"}
        }

        container_name = f"mirror-{os_type}-{container_name}"
        mirror_files[container_name] = mirror_file

        if container_name in [c.name for c in client.containers.list(all=True)]:
            client.containers.get(container_name).remove(force=True)

        env_vars = {"VERSION": rhel_version} if os_type == "rhel" else {}
        container = client.containers.run(name=container_name, image=image, volumes=bind_paths, environment=env_vars, detach=True)

        os.makedirs(repo_log_path, exist_ok=True)
        log_file_path = os.path.join(repo_log_path, f"{container_name}.log")

        with open(log_file_path, "w") as log:
            for line in container.logs(stream=True):
                log.write(line.decode("utf-8"))

        if os_type == "ubuntu":
            find_and_symlink_folders(new_mirror_path, os.path.join(repo_path, "ubuntu"))

        return {"status": "Complete", "message": f"The {container_name} mirroring process has been completed."}

    except Exception as e:
        print(e)
        return {"status": "Error", "message": str(e)}

@app.route("/stream_logs", methods=["POST"])
@login_required
def stream_logs():
    containerID = request.form['container_id']
    def generate_logs():
        try:
            container = client.containers.get(containerID)
            for log in container.logs(stream=True):
                yield f"{log.decode('utf-8')}"
        except Exception:
            yield f"This container no longer exists."

    return Response(generate_logs(), content_type='text/event-stream')

@app.route("/delete", methods=["POST"])
@login_required
def delete():
    global mirror_files, config
    repo_log_path = config.get("repo_log_path")
    containerID = request.form['container_id']
    container_name = request.form['container_name']
    try:
        container = client.containers.get(containerID)
        container.remove(force=True)
        print(f"Container {containerID} has been deleted")
        if container_name in mirror_files:
            file_to_delete = mirror_files.pop(container_name)
            if os.path.exists(file_to_delete):
                os.remove(file_to_delete)
                print(f"File {file_to_delete} has been deleted.")
        log_file = os.path.join(repo_log_path, f"{container_name}.log")
        if os.path.exists(log_file):
            os.remove(log_file)
            print(f"Log {log_file} has been deleted.")
        flash("Container was successfully deleted!", "success")
    except Exception as e:
        flash(f"{e}", "error")
    return redirect(url_for('index'))

@app.route("/restart", methods=["POST"])
@login_required
def restart():
    containerID = request.form['container_id']
    try:
        client.containers.get(containerID).restart()
        flash("Container restarted.", "success")
    except Exception:
        flash("Error while restarting container.", "error")
    return redirect(url_for('index'))

@app.route("/stop", methods=["POST"])
@login_required
def stop():
    containerID = request.form['container_id']
    try:
        client.containers.get(containerID).stop()
        flash("Container stopped.", "success")
    except Exception:
        flash("Error while stopping container.", "error")
    return redirect(url_for('index'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if users.get(username) == password:
            login_user(User(username))
            return redirect(url_for("index"))
        else:
            flash("Wrong username or password.", "logout")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Successfully logged out!.", "logout")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)