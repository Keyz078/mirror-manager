window.initConfigPage = function() {
    // Fetch current config and populate form
    fetch('/api/config')
        .then(res => res.json())
        .then(cfg => {
            document.getElementById('web_server').value = cfg.web_server ? "true" : "false";
            document.getElementById('host_port').value = cfg.host_port || '';
            document.getElementById('auth_user').value = (cfg.auth && cfg.auth.user) || '';
            document.getElementById('auth_password').value = (cfg.auth && cfg.auth.password) || '';
        });

    document.getElementById('configForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const data = {
            web_server: document.getElementById('web_server').value === "true",
            host_port: parseInt(document.getElementById('host_port').value, 10),
            auth: {
                user: document.getElementById('auth_user').value,
                password: document.getElementById('auth_password').value
            }
        };
        fetch('/api/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(resp => {
            const msg = document.getElementById('configMessage');
            if (resp.status === "Success") {
                msg.textContent = "Configuration saved!";
                msg.className = "text-green-600 mt-4";
            } else {
                msg.textContent = resp.message || "Failed to save configuration.";
                msg.className = "text-red-600 mt-4";
            }
        })
        .catch(() => {
            const msg = document.getElementById('configMessage');
            msg.textContent = "Failed to save configuration.";
            msg.className = "text-red-600 mt-4";
        });
    });
};