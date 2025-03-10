# mirror-manager

Hi, this is my first python project, based on what I usually do, this tool makes it easy for us to mirror repos, currently the existing feature only does remote mirroring based on a web server with flask.

### New!

1. Fix sync path for rhel.
2. Auto symlink feature for ubuntu type os to simplify repo path.

New path structure should be like this:
```
/repo-local/
├── rhel
│   └── rhel8
├── ubuntu
│   ├── archive
│   ├── mongodb
│   ├── nginx
│   ├── postgresql
│   ├── security
│   └── zabbix
└── ubuntu-sync
    ├── archive.ubuntu.com
    ├── download.postgresql.org
    ├── nginx.org
    ├── repo.mongodb.org
    ├── repo.zabbix.com
    └── security.ubuntu.com
```

> Symlinked ubuntu-sync -> ubuntu

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
