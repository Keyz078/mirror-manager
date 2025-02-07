function refreshTable() {
    fetch('/containers')
        .then(response => response.json())
        .then(data => {
            let os_type = "ubuntu"; // Default
            if (window.location.pathname.includes("rhel")) {
                os_type = "rhel"; // Jika di halaman RHEL
            }
            let table = `<table class="w-full table-fixed text-sm text-left text-gray-500 dark:text-gray-400" id="containerTable">
                            <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-600 dark:text-gray-200">
                                <tr>
                                    <th scope="col" class="px-6 py-3">Container Name</th>
                                    <th scope="col" class="px-6 py-3">Status</th>
                                    <th scope="col" class="px-6 py-3">Action</th>
                                </tr>
                        </thead>
                        <tbody>`;
            data.forEach(row => {
                table += `<tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 border-gray-200">
                            <td class="px-6 py-4">${row.name}</td>
                            <td class="px-6 py-4">${row.status}</td>
                            <td class="px-6 py-4">
                                <div class="flex space-x-2">
                                    <form action="/delete" method="POST">
                                        <input type="hidden" name="container_id" value="${row.id}">
                                        <input type="hidden" name="os_type" value="${os_type}">
                                        <button type="submit" class="bg-red-400 text-white px-3 py-2 rounded-lg delete-btn">Delete</button>
                                    </form>
                                    <a href="/stream_logs?containerID=${row.id}" target="_blank" class="bg-indigo-500 text-white px-3 py-2 rounded-lg text-center">Stream Log</a>
                                </div>
                            </td>
                          </tr>`;
            });
            table += `</tbody></table>`;
            
            document.getElementById('table-container').innerHTML = table;

            // Attach confirm event listener setelah tabel diperbarui
            document.querySelectorAll('.delete-btn').forEach(button => {
                button.addEventListener('click', function(event) {
                    const confirmation = confirm('Are you sure you want to delete this container?');
                    if (!confirmation) {
                        event.preventDefault();
                    }
                });
            });
        })
        .catch(error => console.error('Error fetching table data:', error));
}

// Auto-refresh setiap 5 detik
setInterval(refreshTable, 15000);

// Jalankan saat halaman dimuat
window.onload = refreshTable;

// Start Mirror
const startMirrorBtn = document.getElementById('startMirrorBtn');

if (startMirrorBtn) {
    startMirrorBtn.addEventListener('click', async function () {
        if (confirm("Apakah anda yakin??")) {
            alert("Menjalankan mirror..");
            
            let containerName = document.getElementById("containerName").value;
            let os_type = "ubuntu"; // Default
            if (window.location.pathname.includes("rhel")) {
                os_type = "rhel"; // Jika di halaman RHEL
            }

            try {
                const response = await fetch(`/start_mirror?os_type=${os_type}&containerName=${containerName}`);
                const result = await response.json();
                alert(result.message);
            } catch (error) {
                console.error('Error starting mirror:', error);
            }
        }
    });
}

// Last log
const lastLogBtn = document.getElementById('lastLogBtn');

if (lastLogBtn) {
    lastLogBtn.addEventListener('click', async function () {
        let os_type = "ubuntu"; // Default
        if (window.location.pathname.includes("rhel")) {
            os_type = "rhel"; // Jika di halaman RHEL
        }

        try {
            const response = await fetch(`/container_logs?os_type=${os_type}`);
            if (response.ok) { // Pastikan request berhasil
                window.location.href = `/container_logs?os_type=${os_type}`;  // Arahkan ke halaman logs
            } else {
                console.error('Failed to fetch logs');
            }
        } catch (error) {
            console.error('Error reading last log', error);
        }
    });
}
// Stop container
const stopContainerBtn = document.getElementById('stopContainerBtn');
if (stopContainerBtn) {
    stopContainerBtn.addEventListener('click', async function () {
        if (confirm("Apakah anda yakin?")) {
            alert("Menghentikan mirror..");
            try {
                const response = await fetch('/stop_container');
                const result = await response.json();
                alert(result.message);
            } catch (error) {
                console.error('Error stopping container:', error);
            }
        }
    });
}

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

// Change the icons inside the button based on previous settings
if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    themeToggleLightIcon.classList.remove('hidden');
} else {
    themeToggleDarkIcon.classList.remove('hidden');
}

var themeToggleBtn = document.getElementById('theme-toggle');

themeToggleBtn.addEventListener('click', function() {

    // toggle icons inside button
    themeToggleDarkIcon.classList.toggle('hidden');
    themeToggleLightIcon.classList.toggle('hidden');

    // if set via local storage previously
    if (localStorage.getItem('color-theme')) {
        if (localStorage.getItem('color-theme') === 'light') {
            document.documentElement.classList.add('dark');
            localStorage.setItem('color-theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('color-theme', 'light');
        }

    // if NOT set via local storage previously
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