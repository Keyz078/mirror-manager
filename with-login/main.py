from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import docker
import random
import string

app = Flask(__name__)
app.secret_key = "supersecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

repo_path = "repos"
log_path = "logs"
mirror_files = {}

# Connect to socket
client = docker.from_env()

# Function

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
    container_data = [{"id": c.id, "name": c.name, "status": c.status} for c in containers]
    return jsonify(container_data)


@app.route("/add", methods=["POST"])
@login_required
def start_mirror():
    global repo_path, mirror_files
    rand = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    
    mirror_path = request.form['mirror_path']
    container_name = request.form['container_name'] or rand
    os_type = request.form['os_type']

    if os_type not in ["ubuntu", "rhel"]:
        return {"status": "Error", "message": "Wrong OS Type!"}

    new_mirror_path = os.path.join(mirror_path, "ubuntu-sync" if os_type == "ubuntu" else "rhel")
    repo_list = request.form['repo_list']

    rhel_version = request.form.get("rhel_version", "").strip()

    try:
        os.makedirs(repo_path, exist_ok=True)
        os.makedirs(new_mirror_path, exist_ok=True)

        file_ext = "list" if os_type == "ubuntu" else "conf"
        file_name = f'mirror-{os_type}-{container_name}.{file_ext}'
        mirror_file = os.path.join(repo_path, file_name)

        with open(mirror_file, "w") as f:
            if os_type == "ubuntu":
                f.write(repo_list)
            else:  # RHEL/CentOS
                if not rhel_version:
                    return {"status": "Error", "message": "RHEL Version and Repo Name are required for RHEL mirroring."}
                f.write(repo_list)

        if not os.path.isfile(mirror_file):
            raise Exception(f"Error: {mirror_file} must be a file, not a directory.")

        if not os.path.isdir(new_mirror_path):
            raise Exception(f"Error: {new_mirror_path} must be a directory, not a file.")

        image = "keyz078/apt-mirror:latest" if os_type == "ubuntu" else "keyz078/reposync:dev"

        bind_paths = {
            os.path.abspath(mirror_file): {
                "bind": "/etc/apt/mirror.list" if os_type == "ubuntu" else "/opt/scripts/config.conf", 
                "mode": "ro"
            },
            os.path.abspath(new_mirror_path): {
                "bind": "/var/spool/apt-mirror/mirror" if os_type == "ubuntu" else "/mirror", 
                "mode": "rw"
            }
        }

        container_name = f"mirror-{os_type}-{container_name}"
        mirror_files[container_name] = mirror_file

        existing_containers = [c.name for c in client.containers.list(all=True)]
        if container_name in existing_containers:
            client.containers.get(container_name).remove(force=True)

        env_vars = {} 
        if os_type == "rhel":
            env_vars = {
                "VERSION": rhel_version
            }

        container = client.containers.run(
            name=container_name,
            image=image,
            volumes=bind_paths,
            environment=env_vars,
            detach=True,
            stdout=True,
            stderr=True
        )

        os.makedirs(log_path, exist_ok=True)
        log_file_path = os.path.join(log_path, f"{container_name}.log")

        with open(log_file_path, "w") as log:
            for line in container.logs(stream=True):
                log.write(line.decode("utf-8"))

        # Do symlink if ubuntu
        if os_type == "ubuntu":
            target = os.path.join(mirror_path, "ubuntu")
            find_and_symlink_folders(new_mirror_path, target)

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
        except Exception as e:
            yield f"This container no longer exists."

    return Response(generate_logs(), content_type='text/event-stream')

@app.route("/delete", methods=["POST"])
@login_required
def delete():
    global mirror_files
    print(mirror_files)
    containerID = request.form['container_id']
    container_name = request.form['container_name']
    os_type = request.form['os_type']
    container = client.containers.get(containerID)
    try:
        container.remove(force=True)
        print(f"Container {containerID} has been deleted")
        if container_name in mirror_files:
            file_to_delete = mirror_files.pop(container_name)
            print(file_to_delete)
            if os.path.exists(file_to_delete):
                os.remove(file_to_delete)
                print(f"File {file_to_delete} has been deleted.")
        log_file = os.path.join(log_path, f"{container_name}.log")
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
    container = client.containers.get(containerID)
    try:
        print(f"Restarting container {containerID}")
        container.restart()
        flash("Container restarted.", "success")
    except Exception as e:
        flash("Error while restarting container.", "error")

    return redirect(url_for('index'))

@app.route("/stop", methods=["POST"])
@login_required
def stop():
    containerID = request.form['container_id']
    container = client.containers.get(containerID)
    try:
        print(f"Stopping container {containerID}")
        container.stop()
        flash("Container stopped.", "success")
    except Exception as e:
        flash("Error while stopping container.", "error")

    return redirect(url_for('index'))

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
            flash("Wrong username or password.", "logout")

    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Successfully logged out!.", "logout")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
