# mirror-manager

Hi, this is my first python project, based on what I usually do, this tool makes it easy for us to mirror repos, currently the existing feature only does remote mirroring based on a web server with flask, to setup a local repository you still have to prepare a web server and do symlinks manually.

### How it works?

It creates container which automatically mirroring the repos, you can create multiple container and see the logs each of container.

### Supported OS for mirror:
- Ubuntu/Debian base
- Rhel/Fedora/Centos/Rocky RPM base

### Prerequisite:
- Docker or Podman

### Step

1. Install requirements

```
pip install -r requirements.txt
```

2. Run the flask
```
python3 main.py
```
