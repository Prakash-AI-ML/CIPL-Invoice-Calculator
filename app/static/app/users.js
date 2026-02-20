
const USER_API_URL = `${API_BASE}/v1/users`;
const userRole = document.querySelector(".nav-profile-role")?.textContent.trim();


// ================================
// TOKEN HELPERS
// ================================
function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
    };
}



// ================================
// LOAD USERS
// ================================
const usersTable = document.querySelector("#usersTable tbody");
const usersLoading = document.getElementById("usersLoading");
const usersError = document.getElementById("usersError");

async function loadUsers() {
    try {
        const res = await fetch(`${USER_API_URL}/read`, {
            method: "GET",
            headers: getAuthHeaders()
        });

        if (!res.ok) throw new Error("Failed to load users");

        const users = await res.json();

        usersTable.innerHTML = "";
        usersLoading.classList.add("d-none");

        users.forEach(u => {
            let actionButtons = '';

            if (u.role === 'super_admin') {
                // Super Admin can see both edit and delete buttons
                actionButtons = `
                    <button class="btn btn-sm btn-warning" onclick="openEditModal('${u.id}')">Edit</button>
                        ${u.role !== "super_admin" 
    ? `<button class="btn btn-sm btn-danger" onclick="deleteUser('${u.id}')">Delete</button>`
    : ""
}                `;
            } else if (u.role === 'admin') {
                // Admin can only see the Edit button for non-admin users
                if (u.role !== 'super_admin') {
                    actionButtons = `
                       <button class="btn btn-sm btn-warning" onclick="openEditModal('${u.id}')">Edit</button>
                        ${u.role !== "super_admin" && u.role !== 'admin'
    ? `<button class="btn btn-sm btn-danger" onclick="deleteUser('${u.id}')">Delete</button>`
    : ""
}                    `;
                }
            } else {
                // Regular users can see both buttons for users that are not 'admin' or 'super_admin'
                if (u.role !== 'super_admin' && u.role !== 'admin') {
                    actionButtons = `
                        <button class="btn btn-sm btn-warning" onclick="openEditModal('${u.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteUser('${u.id}')">Delete</button>
                    `;
                }
            }
            usersTable.innerHTML += `
                <tr>
                    <td>${u.username}</td>
                    <td>${u.email}</td>
                    <td>${u.role}</td>
                    <td>
                        ${actionButtons}
                    </td>
                </tr>
            `;
        });

    } catch (error) {
        usersLoading.classList.add("d-none");
        usersError.classList.remove("d-none");
        usersError.textContent = error.message;
    }
}

document.addEventListener("DOMContentLoaded", loadUsers);


// ================================
// CREATE NEW USER
// ================================
document.getElementById("saveUserBtn").addEventListener("click", async () => {

    const payload = {
        full_name: document.getElementById("newFullName").value.trim(),
        username: document.getElementById("newUsername").value.trim(),
        email: document.getElementById("newEmail").value.trim(),
        role: document.getElementById("newRole").value,
        group_id: Number(document.getElementById("newGroupId").value),
        password: document.getElementById("newPassword").value.trim()
    };

    const res = await fetch(`${USER_API_URL}/create`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        location.reload();
    } else {
        alert("Failed to create user");
    }
});


// ================================
// OPEN EDIT MODAL
// ================================
async function openEditModal(userId) {
    try {
        // 1. Get all users first
        const res = await fetch(`${USER_API_URL}/read`, {
            method: "GET",
            headers: getAuthHeaders()
        });

        if (!res.ok) {
            alert("Failed to load users");
            return;
        }

        const users = await res.json();

        // 2. Find the user by ID
        const u = users.find(item => item.id === Number(userId));

        if (!u) {
            alert("User not found");
            return;
        }

        // 3. Fill the edit modal
        document.getElementById("editUserId").value = u.id;
        document.getElementById("editFullName").value = u.full_name;
        document.getElementById("editUsername").value = u.username;
        document.getElementById("editEmail").value = u.email;
        document.getElementById("editRole").value = u.role;
        document.getElementById("editGroupId").value = u.group_id;

        new bootstrap.Modal(document.getElementById("editUserModal")).show();

    } catch (error) {
        console.error(error);
        alert("Error retrieving user data");
    }
}

// ================================
// UPDATE USER
// ================================
document.getElementById("updateUserBtn").addEventListener("click", async () => {

    const username = document.getElementById("editUserId").value;

    const payload = {
        full_name: document.getElementById("editFullName").value.trim(),
        username: document.getElementById("editUsername").value.trim(),
        email: document.getElementById("editEmail").value.trim(),
        role: document.getElementById("editRole").value,
        group_id: Number(document.getElementById("editGroupId").value)
    };

    const newPassword = document.getElementById("editPassword").value.trim();
    if (newPassword) payload.password = newPassword;

    const res = await fetch(`${USER_API_URL}/update/${username}`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        location.reload();
    } else {
        alert("Update failed");
    }
});


// ================================
// DELETE USER
// ================================
async function deleteUser(username) {
    if (!confirm("Are you sure you want to delete this user?")) return;

    const res = await fetch(`${USER_API_URL}/delete/${username}`, {
        method: "DELETE",
        headers: getAuthHeaders()
    });

    if (res.ok) {
        location.reload();
    } else {
        alert("Failed to delete user");
    }
}
