function refreshTable() {
    fetch('/containers')
        .then(response => response.json())
        .then(data => {
            let table = `<table class="w-full table-auto text-sm text-left text-gray-500 dark:text-gray-400" id="containerTable">
                            <thead class="text-xs text-gray-700 uppercase bg-gray-100 dark:bg-gray-600 dark:text-gray-200">
                                <tr>
                                    <th scope="col" class="px-6 py-3 w-1/3 min-w-0">Container Name</th>
                                    <th scope="col" class="px-6 py-3 w-1/4 min-w-0">Status</th>
                                    <th scope="col" class="px-6 py-3 w-1/4 min-w-0 text-center">Action</th>
                                </tr>
                            </thead>
                            <tbody>`;

            data.forEach(row => {
                const isMirrorManager = row.name === "mirror-manager";
                const deleteDisabled = isMirrorManager ? "disabled class='bg-red-400 text-white px-3 py-2 rounded-lg cursor-not-allowed'" : "class='bg-red-400 text-white px-3 py-2 rounded-lg delete-btn'";
                const stopDisabled = isMirrorManager ? "disabled class='bg-gray-400 text-white px-3 py-2 rounded-lg stop-btn cursor-not-allowed'" : "class='bg-gray-400 text-white px-3 py-2 rounded-lg stop-btn'"
                const restartDisabled = isMirrorManager ? "disabled class='bg-yellow-500 text-white px-3 py-2 rounded-lg restart-btn cursor-not-allowed'" : "class='bg-yellow-500 text-white px-3 py-2 rounded-lg restart-btn'"
                table += `<tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 border-gray-200">
                            <td class="px-6 py-4 break-words">${row.name}</td>
                            <td class="px-6 py-4 break-words">${row.status}</td>
                            <td class="px-6 py-4 text-center">
                                <div class="flex justify-center space-x-2">
                                    <form action="/stop" method="POST">
                                        <input type="hidden" name="container_id" value="${row.id}">
                                        <button type="submit" ${stopDisabled}>Stop</button>
                                    </form>
                                    <form action="/restart" method="POST">
                                        <input type="hidden" name="container_id" value="${row.id}">
                                        <button type="submit" ${restartDisabled}>Restart</button>
                                    </form>
                                    <form action="/delete" method="POST">
                                        <input type="hidden" name="container_name" value="${row.name}">
                                        <input type="hidden" name="container_id" value="${row.id}">
                                        <input type="hidden" name="os_type" value="${os_type}">
                                        <button type="submit" ${deleteDisabled}>Delete</button>
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

            // Hanya pasang event listener ke tombol Delete yang tidak disable
            document.querySelectorAll('.delete-btn').forEach(button => {
                button.addEventListener('click', function(event) {
                    if (!confirm('Are you sure you want to delete this container?')) {
                        event.preventDefault();
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

// Modal
document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modal");
    const openModalBtn = document.getElementById("openModal");
    const closeModalBtn = document.getElementById("closeModal");
    const form = modal.querySelector("form");
    const osTypeSelect = document.getElementById("os_type");
    const rhelOptions = document.getElementById("rhel-options");
    const rhelVersionInput = document.getElementById("parent_dir"); // Get input RHEL Version

    // Show/hide RHEL input fields and set required attribute
    osTypeSelect.addEventListener("change", function () {
        if (this.value === "rhel") {
            rhelOptions.classList.remove("hidden");
            rhelVersionInput.required = true; // Set required to true
        } else {
            rhelOptions.classList.add("hidden");
            rhelVersionInput.required = false; // Set required to false
            rhelVersionInput.value = ""; // Clear the input value
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
        .then(response => {
            // Coba parse JSON, jika gagal kemungkinan besar redirect ke login
            return response.json().catch(() => {
                window.location.href = "/login";
                return Promise.reject("Redirecting to login...");
            });
        })
        .then(data => {
            if (data.status === "Complete") {
                alert(`✅ Success: ${data.message}`);
            } else {
                alert(`❌ Error: ${data.message}`);
            }
        })
        .catch(error => {
            if (error !== "Redirecting to login...") {
                alert(`❌ Error: ${error.message || error}`);
            }
        });
    });
});