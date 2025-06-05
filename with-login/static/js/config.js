window.initConfigPage = function() {
    // Fetch config and populate both forms
    fetch('/api/config')
        .then(res => res.json())
        .then(cfg => {
            // Webserver form
            document.getElementById('web_server').value = cfg.web_server ? "true" : "false";
            document.getElementById('host_port').value = cfg.host_port || '';
            // Auth form
            document.getElementById('auth_user').value = (cfg.auth && cfg.auth.user) || '';
        });

    // Webserver form submit
    document.getElementById('webserverForm').addEventListener('submit', function(e) {
        e.preventDefault();
        if (!confirm("Are you sure you want to save this Web Server configuration?")) return;
        const data = {
            web_server: document.getElementById('web_server').value === "true",
            host_port: parseInt(document.getElementById('host_port').value, 10)
        };
        fetch('/api/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(resp => {
            if (resp.status === "Success") {
                alert("Web Server configuration saved!");
            } else {
                alert(resp.message || "Failed to save Web Server configuration.");
            }
        })
        .catch(() => {
            alert("Failed to save Web Server configuration.");
        });
    });

    // Auth form submit
    document.getElementById('authForm').addEventListener('submit', function(e) {
        e.preventDefault();
        // Validate new password match
        const oldPassword = document.getElementById('old_password').value;
        const newPassword = document.getElementById('new_password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        const username = document.getElementById('auth_user').value;

        if (!confirm("Are you sure you want to update authentication?")) return;
        if (!oldPassword || !newPassword || !confirmPassword) {
            alert("All password fields are required.");
            return;
        }
        if (newPassword !== confirmPassword) {
            alert("New password and confirmation do not match.");
            return;
        }

        // Optionally: you can POST to a dedicated /api/auth endpoint, but here we use /api/config
        fetch('/api/config')
            .then(res => res.json())
            .then(cfg => {
                // Check old password (client-side, for UX only; real check must be server-side)
                if (cfg.auth && oldPassword !== cfg.auth.password) {
                    alert("Old password is incorrect.");
                    return;
                }
                // Prepare data for update
                const data = {
                    auth: {
                        user: username,
                        password: newPassword
                    }
                };
                fetch('/api/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                })
                .then(res => res.json())
                .then(resp => {
                    if (resp.status === "Success") {
                        alert("Authentication updated!");
                        // Optionally clear password fields
                        document.getElementById('old_password').value = '';
                        document.getElementById('new_password').value = '';
                        document.getElementById('confirm_password').value = '';
                    } else {
                        alert(resp.message || "Failed to update authentication.");
                    }
                })
                .catch(() => {
                    alert("Failed to update authentication.");
                });
            });
    });
};

document.addEventListener('DOMContentLoaded', function () {
    const passwordInput = document.getElementById('auth_password');
    const togglePassword = document.getElementById('togglePassword');
    const eyeIcon = document.getElementById('eyeIcon');
    // SVG untuk open dan close
    const svgOpen = `
        <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
            <path stroke="currentColor" stroke-width="1.5" d="M21 12c0 1.2-4.03 6-9 6s-9-4.8-9-6c0-1.2 4.03-6 9-6s9 4.8 9 6Z"/>
            <path stroke="currentColor" stroke-width="1.5" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>
        </svg>`;
    const svgClosed = `
        <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3.933 13.909A4.357 4.357 0 0 1 3 12c0-1 4-6 9-6m7.6 3.8A5.068 5.068 0 0 1 21 12c0 1-3 6-9 6-.314 0-.62-.014-.918-.04M5 19 19 5m-4 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>
        </svg>`;
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function () {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            eyeIcon.innerHTML = type === 'text' ? svgOpen : svgClosed;
        });
    }
});

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.remove('border-blue-600', 'text-blue-600', 'dark:border-blue-400', 'dark:text-blue-400');
            b.classList.add('dark:border-gray-700', 'text-gray-700', 'dark:text-white');
        });
        this.classList.remove('dark:border-gray-700', 'text-gray-700', 'dark:text-white');
        this.classList.add('border-blue-600', 'text-blue-600', 'dark:border-blue-400', 'dark:text-blue-400');
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
        document.getElementById(this.dataset.tab + 'Form').classList.remove('hidden');
    });
});
// Default tab highlight
const defaultTab = document.getElementById('tab-webserver');
defaultTab.classList.add('border-blue-600', 'text-blue-600', 'dark:border-blue-400', 'dark:text-blue-400');
defaultTab.classList.remove('dark:border-gray-700', 'text-gray-700', 'dark:text-white');