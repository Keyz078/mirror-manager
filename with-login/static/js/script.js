function refreshTable() {
    fetch('/containers')
        .then(response => response.json())
        .then(data => {
            let table = `<table class="w-full table-auto text-sm text-left text-gray-500 dark:text-gray-400" id="containerTable">
                            <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-600 dark:text-gray-200">
                                <tr>
                                    <th scope="col" class="px-6 py-3 w-1/3 min-w-0">Container Name</th>
                                    <th scope="col" class="px-6 py-3 w-1/4 min-w-0">Status</th>
                                    <th scope="col" class="px-6 py-3 w-1/4 min-w-0 text-center">Action</th>
                                </tr>
                            </thead>
                            <tbody>`;

            data.forEach(row => {
                table += `<tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 border-gray-200">
                            <td class="px-6 py-4 break-words">${row.name}</td>
                            <td class="px-6 py-4 break-words">${row.status}</td>
                            <td class="px-6 py-4 text-center">
                                <div class="flex justify-center space-x-2">
                                    <form action="/stop" method="POST">
                                        <input type="hidden" name="container_id" value="${row.id}">
                                        <button type="submit" class="bg-gray-400 text-white px-3 py-2 rounded-lg stop-btn">Stop</button>
                                    </form>
                                    <form action="/restart" method="POST">
                                        <input type="hidden" name="container_id" value="${row.id}">
                                        <button type="submit" class="bg-yellow-500 text-white px-3 py-2 rounded-lg restart-btn">Restart</button>
                                    </form>
                                    <form action="/delete" method="POST">
                                        <input type="hidden" name="container_name" value="${row.name}">
                                        <input type="hidden" name="container_id" value="${row.id}">
                                        <input type="hidden" name="os_type" value="${os_type}">
                                        <button type="submit" class="bg-red-400 text-white px-3 py-2 rounded-lg delete-btn">Delete</button>
                                    </form>
                                    <form action="/stream_logs" method="POST" target="_blank">
                                        <input type="hidden" name="container_id" value="${row.id}">
                                        <button type="submit" class="bg-indigo-500 text-white px-3 py-2 rounded-lg log-btn">Logs</button>
                                    </form>
                                </div>
                            </td>
                          </tr>`;
            });

            table += `</tbody></table>`;
            document.getElementById('table-container').innerHTML = table;

            document.querySelectorAll('.delete-btn').forEach(button => {
                button.addEventListener('click', function(event) {
                    if (!confirm('Are you sure you want to delete this container?')) {
                    }
                });
            });
        })
        .catch(error => console.error('Error fetching table data:', error));
}


// Auto-refresh every 15 second
setInterval(refreshTable, 15000);
window.onload = refreshTable;

// Close alert
const closeButton = document.getElementById('close-alert');
const alertBox = document.getElementById('alert-border-1');

if (closeButton && alertBox) {
    closeButton.addEventListener('click', () => {
        alertBox.style.display = 'none';
    });
}

// Toggle Dark mode
if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
} else {
    document.documentElement.classList.remove('dark')
}

var themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
var themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');

if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    themeToggleLightIcon.classList.remove('hidden');
} else {
    themeToggleDarkIcon.classList.remove('hidden');
}

var themeToggleBtn = document.getElementById('theme-toggle');

themeToggleBtn.addEventListener('click', function() {

    themeToggleDarkIcon.classList.toggle('hidden');
    themeToggleLightIcon.classList.toggle('hidden');

    if (localStorage.getItem('color-theme')) {
        if (localStorage.getItem('color-theme') === 'light') {
            document.documentElement.classList.add('dark');
            localStorage.setItem('color-theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('color-theme', 'light');
        }

    } else {
        if (document.documentElement.classList.contains('dark')) {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('color-theme', 'light');
        } else {
            document.documentElement.classList.add('dark');
            localStorage.setItem('color-theme', 'dark');
        }
    }

});

// Modal Form
document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modal");
    const openModalBtn = document.getElementById("openModal");
    const closeModalBtn = document.getElementById("closeModal");
    const form = modal.querySelector("form");
    const mirrorPathInput = document.getElementById("mirror_path");
    const defaultCheckbox = document.getElementById("path-checkbox");

    if (localStorage.getItem("mirror_path")) {
        mirrorPathInput.value = localStorage.getItem("mirror_path");
        defaultCheckbox.checked = true;
    }

    defaultCheckbox.addEventListener("change", function () {
        if (this.checked) {
            localStorage.setItem("mirror_path", mirrorPathInput.value);
        } else {
            localStorage.removeItem("mirror_path");
        }
    });

    mirrorPathInput.addEventListener("input", function () {
        if (defaultCheckbox.checked) {
            localStorage.setItem("mirror_path", this.value);
        }
    });

    openModalBtn.addEventListener("click", function () {
        modal.classList.remove("hidden");
    });

    closeModalBtn.addEventListener("click", function () {
        modal.classList.add("hidden");
    });

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        alert("🚀 Initializing container...");
        modal.classList.add("hidden"); 

        const formData = new FormData(form);

        fetch(form.action, {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "Complete") {
                alert(`✅ Success: ${data.message}`);
            } else {
                alert(`❌ Error: ${data.message}`);
            }
        })
    });
});
