const ROLE_DEFAULT_PERMISSIONS = {
    // ADMIN (id: 1)
    1: {
        1: [1, 2, 3],                    // extract
        2: [4, 5, 6, 7, 8, 9, 10],       // aging
        3: [11],                         // advice
        5: [12],                         // clients
        6: [13, 14, 15, 16],             // settings
        7: [17, 18, 19, 20, 21]          // approval
    },

    // SUPER ADMIN (id: 3)
    3: "ALL",

    // USER (id: 9)
    9: {
        2: [4, 5],                       // aging
        3: [11],                         // advice
        5: [12]                          // clients
    },

    // ACCOUNTS (id: 10)
    10: {
        2: [4, 5, 7, 8, 9, 10],   // aging + payment
        3: [11],                         // advice        
        7: [17, 20]                      // approval
    }
};
const USER_API_URL = `${API_BASE}/v1/users`;
const userRole = document.querySelector(".nav-profile-role")?.textContent.trim().toLowerCase();


// Profile Settings Logic
document.getElementById("edit_profile_image").addEventListener("change", e => {
    const file = e.target.files[0];
    if (file) {
        document.getElementById("edit_profile_image_preview").src =
            URL.createObjectURL(file);
    }
});

document.getElementById("edit_logo_image").addEventListener("change", e => {
    const file = e.target.files[0];
    if (file) {
        document.getElementById("edit_logo_image_preview").src =
            URL.createObjectURL(file);
    }
});

function canShowAction(ButtonName) {
    const settings = USER_MENUS.settings.buttons;
    
    if (!settings) return false;
    
    if (Array.isArray(settings)) {
        const buttonNames = settings.map(item => item.button_name);
        return buttonNames.includes(ButtonName);
    }
    
    if (typeof settings === 'object' && 'button_name' in settings) {
        return settings.button_name === ButtonName;
    }
    
    return false;
}

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
        
        users.forEach((u, index) => {
            let actionButtons = '';
            
            if (canShowAction('users_crud')){
                if (userRole === 'super admin') {
                    // Super Admin sees Edit + Delete for all users
                    actionButtons = `<td>
                        <button class="btn btn-sm btn-warning" onclick="openEditModal('${u.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteUser('${u.id}')">Delete</button>
                   </td> `;
                } else if (userRole === 'admin') {
                    if (u.role === 'admin') {
                        // Admin row: only Edit
                        actionButtons = `<td>
                            <button class="btn btn-sm btn-warning" onclick="openEditModal('${u.id}')">Edit</button>
                       </td> `;
                    } else {
                        // Non-admin row: Edit + Delete
                        actionButtons = `<td>
                            <button class="btn btn-sm btn-warning" onclick="openEditModal('${u.id}')">Edit</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteUser('${u.id}')">Delete</button>
                        </td>`;
                    }
                } else {
                    // Optional: regular users logic if needed
                    actionButtons = ''; // or whatever rules you want
                }
            }
            usersTable.innerHTML += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${u.username}</td>
                    <td>${u.email}</td>
                    <td>${u.role}</td>
                    
                        ${actionButtons}
                    
                </tr>
            `;
        });
         const container = document.querySelector(".permission_div");
         container.innerHTML = "";

        bindPermissionEvents(container);

// 👇 APPLY DEFAULT ROLE AUTOMATICALLY
// setTimeout(applyDefaultRoleOnLoad, 1000);
        
    } catch (error) {
        usersLoading.classList.add("d-none");
        usersError.classList.remove("d-none");
        usersError.textContent = error.message;
    }
}

document.addEventListener("DOMContentLoaded", loadUsers);
document.addEventListener("DOMContentLoaded", add_role_to_select);


// ================================
// CREATE NEW USER
// ================================
document.getElementById("saveUserBtn").addEventListener("click", async () => {
    
    // const payload = {
    //     full_name: document.getElementById("newFullName").value.trim(),
    //     username: document.getElementById("newUsername").value.trim(),
    //     email: document.getElementById("newEmail").value.trim(),
    //     role: document.getElementById("newRole").value,
    //     group_id: Number(document.getElementById("newGroupId").value),
    //     password: document.getElementById("newPassword").value.trim()
    // };
    const { menu_permission, button_permission } = collectPermissions();
    
    const payload = {
        subscriber: {
            username: document.getElementById("newUsername").value.trim(),
            email: document.getElementById("newEmail").value.trim(),
            role_id: Number(document.getElementById("newRole").value),
            group_id: Number(document.getElementById("newGroupId").value),
            company: document.getElementById("newCompany").value,
            mobile: Number(document.getElementById('newPhone').value)>0?Number(document.getElementById('newPhone').value):null,
            password: document.getElementById("newPassword").value.trim(),
            created_by: getCookie('user_id'),
            updated_by: getCookie('user_id'),
            status:1
        },
        menu_permission,
        button_permission,
        update: false,
        subscriber_id: 0
    };
    
    
    
    const res = await fetch(`${API_BASE}/v1/user/manage`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
    });
    const data = await res.json();

    // Safely extract subscriber_id
    const subscriberId = data.subscriber_id;
    console.log(subscriberId)
    
    if (res.ok) {
        updateProfileImage("profile_image","logo_image", subscriberId);
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
        const res = await fetch(`${API_BASE}/v1/user/read/${userId}`, {
            method: "GET",
            headers: getAuthHeaders()
        });
        
        if (!res.ok) {
            alert("Failed to load users");
            return;
        }
        
        
        const u = await res.json();
        
        // 2. Find the user by ID
        // const u = users.find(item => item.subscriber_id === Number(userId));
        
        if (!u) {
            alert("User not found");
            return;
        }
        
        // 3. Fill the edit modal
        document.getElementById("editUserId").value = u.subscriber_id;
        // document.getElementById("editFullName").value = u.full_name;
        document.getElementById("editUsername").value = u.username;
        document.getElementById("editEmail").value = u.email;
        document.getElementById("editRole").value = u.role_id;
        document.getElementById("editGroupId").value = u.group_id;
        document.getElementById("editCompany").value = u.company;
        document.getElementById("editPhone").value = u.mobile;
        document.getElementById("edit_profile_image_preview").src = u.profile?"/static/app/images/profiles/"+u.profile:"/static/app/images/profiles/default-profile.png";
        document.getElementById("edit_logo_image_preview").src = u.logo?"/static/app/images/logos/"+u.logo:"/static/app/images/logos/default-profile.png";
        loadPermissions("permission_div_edit");
        setTimeout(() => {
            applyEditPermissions(u);
        }, 300);
        
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
    
    const { menu_permission, button_permission } = collectPermissions();
    
    const payload = {
        subscriber: {
            username: document.getElementById("editUsername").value.trim(),
            email: document.getElementById("editEmail").value.trim(),
            role_id: Number(document.getElementById("editRole").value),
            group_id: Number(document.getElementById("editGroupId").value),
            password: document.getElementById("editPassword").value.trim(),
            company: document.getElementById("editCompany").value,
            mobile: Number(document.getElementById('editPhone').value)>0?Number(document.getElementById('editPhone').value):null,
            created_by: getCookie('user_id'),
            updated_by: getCookie('user_id'),
            status:1
        },
        menu_permission,
        button_permission,
        update: true,
        subscriber_id: username
    };
    
    
    
    const newPassword = document.getElementById("editPassword").value.trim();
    if (newPassword) payload.password = newPassword;
    
    const res = await fetch(`${API_BASE}/v1/user/manage`, {
        method: "post",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
    });
    
    if (res.ok) {
        // location.reload();
        
        updateProfileImage("edit_profile_image","edit_logo_image",username);
    } else {
        alert("Update failed");
    }
});


async function updateProfileImage(profile_image,logo_image,id){
    const profileImageInput = document.getElementById(profile_image);
    const logoImageInput = document.getElementById(logo_image);
    
    const formData = new FormData();
    
    if (profileImageInput.files.length > 0) {
        formData.append("profile_image", profileImageInput.files[0]);
    }
    
    if (logoImageInput.files.length > 0) {
        formData.append("company_logo", logoImageInput.files[0]);
    }
    if(profileImageInput.files.length > 0 ||
logoImageInput.files.length > 0){
    const res = await fetch(`${API_BASE}/v1/user/profile/${id}`, {
        method: "post",
        headers: {
            "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
        },
        body: formData
    });
    
    if (res.ok) {
        location.reload();
      } else {
        alert("Failed to delete user");
      }
    }else{
    location.reload();

  }
}

// ================================
// DELETE USER
// ================================
async function deleteUser(username) {
    if (!confirm("Are you sure you want to delete this user?")) return;
    
    const res = await fetch(`${API_BASE}/v1/user/delete/${username}`, {
        method: "DELETE",
        headers: getAuthHeaders()
    });
    
    if (res.ok) {
        location.reload();
    } else {
        alert("Failed to delete user");
    }
}

// const API_URL = `${API_BASE}/v1/users`;
function moveOptions(fromId, toId) {
    const from = document.getElementById(fromId);
    const to = document.getElementById(toId);
    Array.from(from.selectedOptions).forEach(opt => to.appendChild(opt));
}
$(document).ready(function(){
    loadPermissions("permission_div");
})
function loadPermissions(class_name) {
    
    const container = document.querySelector("." + class_name);
    container.innerHTML = "";
   
    Promise.all([
        fetch(`${API_BASE}/v1/menus/lists`, {
            headers: {
                accept: "application/json",
                Authorization: `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
            }
        }).then(res => res.json()),
        
        fetch(`${API_BASE}/v1/buttons/lists`, {
            headers: {
                accept: "application/json",
                Authorization: `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
            }
        }).then(res => res.json())
    ])
    .then(([menus, buttons]) => {       
        
        const buttonMap = {};
         buttons.filter(b => b.status === 1).forEach(b => {
            if (!buttonMap[b.menu_id]) buttonMap[b.menu_id] = [];
            buttonMap[b.menu_id].push(b);
        });
        
        menus.forEach(menu => {
            
            const menuButtons = buttonMap[menu.id];
            if (!menuButtons || !menuButtons.length) return;
            
            const group = document.createElement("div");
            group.className = "permission-group mb-4";
            
            const label = document.createElement("label");
            label.className = "form-label fw-bold";
            label.textContent = menu.menu_name.toUpperCase();
            
            const row = document.createElement("div");
            row.className = "row align-items-center";
            
            // Available
            const availableCol = document.createElement("div");
            availableCol.className = "col-md-5";
            
            const available = document.createElement("select");
            available.className = "form-control available";
            available.multiple = true;
            available.size = 6;
            available.dataset.menuId = menu.id;
            available.style.setProperty("height", "120px", "important");
            
            menuButtons.forEach(btn => {
                const opt = document.createElement("option");
                opt.value = btn.id;
                opt.textContent = btn.button_name.toUpperCase();
                available.appendChild(opt);
            });
            
            availableCol.appendChild(available);

            // Move buttons
            const btnCol = document.createElement("div");
            btnCol.className = "col-md-2 text-center";
            
            const rightBtn = document.createElement("button");
            rightBtn.className = "btn btn-outline-primary btn-sm";
            rightBtn.textContent = "▶";
            
            const leftBtn = document.createElement("button");
            leftBtn.className = "btn btn-outline-secondary btn-sm mt-2";
            leftBtn.textContent = "◀";
            
            btnCol.appendChild(rightBtn);
            btnCol.appendChild(document.createElement("br"));
            btnCol.appendChild(leftBtn);
            
            // Selected
            const selectedCol = document.createElement("div");
            selectedCol.className = "col-md-5";
            
            const selected = document.createElement("select");
            selected.className = "form-control selected";
            selected.multiple = true;
            selected.size = 6;
            selected.dataset.menuId = menu.id;
            selected.style.setProperty("height", "120px", "important");
            
            selectedCol.appendChild(selected);

            row.appendChild(availableCol);
            row.appendChild(btnCol);
            row.appendChild(selectedCol);
            
            group.appendChild(label);
            group.appendChild(row);
            container.appendChild(group);
      

            // Move logic
            rightBtn.onclick = () => {
                [...available.selectedOptions].forEach(o => selected.appendChild(o));
            };

            leftBtn.onclick = () => {
                [...selected.selectedOptions].forEach(o => available.appendChild(o));
            };
        });
    })
    .catch(err => console.error("Permission load error:", err));
}

function bindPermissionEvents(container) {
    
    container.addEventListener("click", function (e) {
        
        if (e.target.classList.contains("move-right")) {
            const group = e.target.closest(".permission-group");
            moveOptions(
                group.querySelector(".available"),
                group.querySelector(".selected")
            );
        }
        
        if (e.target.classList.contains("move-left")) {
            const group = e.target.closest(".permission-group");
            moveOptions(
                group.querySelector(".selected"),
                group.querySelector(".available")
            );
        }
    });
}

function moveOptions(from, to) {
    Array.from(from.selectedOptions).forEach(opt => {
        to.appendChild(opt);
    });
}

function collectPermissions() {
    
    const menu_permission = [];
    const button_permission = [];
    
    document.querySelectorAll(".permission-group").forEach(group => {
        
        const selectedSelect = group.querySelector(".selected");
        const menuId = Number(selectedSelect.dataset.menuId);
        
        // If at least one button is selected, menu permission is enabled
        if (selectedSelect.options.length > 0) {
            menu_permission.push({
                menu_id: menuId,
                status: 1,
                created_by:  getCookie('user_id')
            });
        }
        
        // Button permissions
        Array.from(selectedSelect.options).forEach(opt => {
            button_permission.push({
                menu_id: menuId,
                button_id: Number(opt.value),
                button_permission: opt.textContent,
                status: 1,
                created_by: getCookie('user_id')
            });
        });
    });
    
    return { menu_permission, button_permission };
}

function applyEditPermissions(userData) {
    
    const buttonPermissions = userData.button_permissions || [];
    
    document
    .querySelectorAll(".permission_div_edit .permission-group")
    .forEach(group => {
        
        const available = group.querySelector(".available");
        const selected = group.querySelector(".selected");
        
        const menuId = Number(available.dataset.menuId);
        
        // Get allowed button IDs for this menu
        const allowedButtonIds = buttonPermissions
        .filter(b => b.menu_id === menuId && b.status === 1)
        .map(b => b.button_id);
        
        // Move matching options to selected
        Array.from(available.options).forEach(option => {
            if (allowedButtonIds.includes(Number(option.value))) {
                selected.appendChild(option);
            }
        });
    });
}

function add_role_to_select(){
    $('#newRole,#editRole').empty();
    fetch(`${API_BASE}/v1/roles/lists`, {
        method: "GET",
        headers: {
            "accept": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
        }
    })
    .then(res => res.json())
    .then(res => {
        res.forEach(item => {
            $('#newRole,#editRole').append(`<option value="${item.id}">${item.role_name.toUpperCase().replace("_"," ")}</option>`)
        });
    });
}


function resetPermissionsUI() {
    document.querySelectorAll('.permission-group').forEach(group => {
        const available = group.querySelector('.available');
        const selected = group.querySelector('.selected');

        [...selected.options].forEach(opt => {
            available.appendChild(opt);
        });
    });
}

function applyRolePermissions(roleId) {

    const rolePerm = ROLE_DEFAULT_PERMISSIONS[roleId];
    if (!rolePerm) return;

    document.querySelectorAll('.permission-group').forEach(group => {

        const available = group.querySelector('.available');
        const selected = group.querySelector('.selected');
        const menuId = available.dataset.menuId;

        if (rolePerm === "ALL") {
            [...available.options].forEach(opt => selected.appendChild(opt));
            return;
        }

        const allowed = rolePerm[menuId];
        if (!allowed) return;

        [...available.options].forEach(opt => {
            if (allowed.includes(Number(opt.value))) {
                selected.appendChild(opt);
            }
        });
    });
}



document.getElementById('newRole')?.addEventListener('change', function () {
    resetPermissionsUI();
    applyRolePermissions(this.value);
});

document.getElementById('editRole')?.addEventListener('change', function () {
    resetPermissionsUI();
    applyRolePermissions(this.value);
});
function applyDefaultRoleOnLoad() {

    const roleSelect =
        document.getElementById('editRole') ||
        document.getElementById('newRole');

    if (!roleSelect || !roleSelect.value) return;

    resetPermissionsUI();
    applyRolePermissions(roleSelect.value);
}


const addUserModal = document.getElementById("addUserModal");

addUserModal.addEventListener("shown.bs.modal", () => {
   roleSelect =
        document.getElementById('newRole');

    if (!roleSelect || !roleSelect.value) return;

    resetPermissionsUI();
    applyRolePermissions(roleSelect.value);
  
});
