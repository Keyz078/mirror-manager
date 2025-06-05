# mirror-manager branch DEV (For ongoing feature and testing)

Hi, this is my first python project, based on what I usually do, this tool makes it easy for us to mirror repos, currently the existing feature only does remote mirroring based on a web server with flask.

### New!

1. Fix sync path for rhel.
2. Auto symlink feature for ubuntu type os to simplify repo path.
3. Container web server for serving local repository
4. Reconfigure existing config (New!)
5. Run on container mode is now available (New!)

New path structure should be like this:
```
/mirror/
├── configs
├── logs
├── repos
│   ├── rhel
│   │   └── rhel8
│   └── ubuntu
│       ├── nginx
│       └── zabbix
└── ubuntu-sync
    ├── nginx.org
    │   └── packages
    └── repo.zabbix.com
        └── zabbix
```

> Symlinked ubuntu-sync -> repos/ubuntu

### How it works?

It creates container which automatically mirroring the repos, you can create multiple container and see the logs each of container.

### Supported OS for mirror:
- Ubuntu/Debian base
- Rhel/Fedora/Centos/Rocky RPM base

### Prerequisite:
- Docker or Podman

### Step

#### Python method

1. Install requirements

```
pip install -r requirements.txt
```

2. Run the flask
```
python3 main.py --config /path/to/your/config.json
```

#### Binary method

Get the binary from [release](https://github.com/Keyz078/mirror-manager/releases) page

```
chmod +x mirror-manager
```

Make config file, for example:

```
{
    "mirror_path": "/mirror",
    "repo_path": "/mirror/repos",
    "repo_config_path": "/mirror/configs",
    "repo_log_path": "/mirror/logs",
    "web_server": true,
    "host_port": 5080,
    "auth": {
        "user": "admin",
        "password": "admin"
    }
}
```

Start service

```
./mirror-manager --config /path/to/your/config.json
```

#### Container method docker/podman

```
docker run -d -p 5000:5000 -v /var/run/docker.sock:/var/run/docker.sock \
-v /path/for/mirror:/path/for/mirror \
-v /path/to/config.json:/app/config/config.json \
keyz078/mirror-manager:latest
```

> For podman, change the docker into podman with the socket also

### Start mirroring

Access the web ui http://your-address:5000

#### Add new mirror

Just create a new container, fill in the form, while in the `Repos` section you need to fill in the repo configuration like .list for ubuntu/debian based or .repo for fedora/rhel family.

![image](https://github.com/user-attachments/assets/37f70f5e-d549-46fe-94a5-51a409d90ea4)


> For Ubuntu/Debian

![image](https://github.com/user-attachments/assets/b9aacbd7-cf37-4ce1-b4be-d1d3d95eb162)


> For Fedora/rhel/centos/rocky


When it's done, access web-server container http://your-address:host-port
