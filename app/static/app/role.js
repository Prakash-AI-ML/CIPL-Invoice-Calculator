const userRole = document.querySelector(".nav-profile-role")?.textContent.trim().toLowerCase();


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


function loadRoleList() {
  $("#roleLoading").removeClass("d-none");
  $("#roleError").addClass("d-none");
  $("#roleTable tbody").empty();

  fetch(`${API_BASE}/v1/roles/lists`, {
    method: "GET",
    headers: {
      "accept": "application/json",
      "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
    }
  })
    .then(res => res.json())
    .then(res => {
      $("#roleLoading").addClass("d-none");

      const rows = res || [];
      if (!rows.length) {
        $("#roleTable tbody").html(`
          <tr>
            <td colspan="3" class="text-center">No roles found</td>
          </tr>
        `);
        return;
      }

      rows.forEach((r, index) => {
         let actionButtons = '';

        if (userRole === 'super admin') {
            if (r.role_name !== 'super_admin') {
                // Show Edit + Delete for non-super_admin roles
                actionButtons = `
                    <button class="btn btn-sm btn-primary" onclick="openEditRole(${r.id}, '${r.role_name}')">Edit</button>
                    <button class="btn btn-sm btn-danger ms-1" onclick="openDeleteRole(${r.id})">Delete</button>
                `;
            }
        } else if (userRole === 'admin') {
            if (r.role_name !== 'super_admin' && r.role_name !== 'admin') {
                // Show Edit + Delete for roles that are not admin or super_admin
                actionButtons = `
                    <button class="btn btn-sm btn-primary" onclick="openEditRole(${r.id}, '${r.role_name}')">Edit</button>
                    <button class="btn btn-sm btn-danger ms-1" onclick="openDeleteRole(${r.id})">Delete</button>
                `;
            }
        }

        $("#roleTable tbody").append(`
            <tr>
                <td>${index + 1}</td>
                <td>${r.role_name}</td>
                ${canShowAction('roles_crud') ? `
 
    <td>${actionButtons}</td>
` : ``}
                
            </tr>
        `);
    });
    //     $("#roleTable tbody").append(`
    //       <tr>
    //         <td>${r.id}</td>
    //         <td>${r.role_name}</td>
    //         <td>
    //           <button class="btn btn-sm btn-primary"
    //             onclick="openEditRole(${r.id}, '${r.role_name}')">
    //             Edit
    //           </button>
    //           <button class="btn btn-sm btn-danger ms-1"
    //             onclick="openDeleteRole(${r.id})">
    //             Delete
    //           </button>
    //         </td>
    //       </tr>
    //     `);
    //   });
    })


    .catch(err => {
      $("#roleLoading").addClass("d-none");
      $("#roleError").removeClass("d-none").text("Failed to load roles");
      console.error(err);
    });
}

/* =============================
   OPEN ADD ROLE MODAL
============================= */
function openAddRole() {
  $("#roleModalTitle").text("Add Role");
  $("#roleId").val("");
  $("#roleName").val("");
  $("#roleModal").modal("show");
}

/* =============================
   OPEN EDIT ROLE MODAL
============================= */
function openEditRole(id, roleName) {
  $("#roleModalTitle").text("Edit Role");
  $("#roleId").val(id);
  $("#roleName").val(roleName);
  $("#roleModal").modal("show");
}

/* =============================
   SAVE ROLE (CREATE / UPDATE)
============================= */
$("#roleForm").on("submit", function (e) {
  e.preventDefault();

  const roleId = $("#roleId").val();
  const userId = getCookie("user_id");

  if (!userId) {
    console.error("user_id not found in cookie");
    return;
  }

  const payload = {
    role_name: $("#roleName").val().trim()
  };

  if (!payload.role_name) return;

  // audit fields
  if (roleId) {
    payload.updated_by = userId;
  } else {
    payload.updated_by = userId;
    payload.created_by = userId;
  }

  const url = roleId
    ? `${API_BASE}/v1/roles/update/${roleId}`
    : `${API_BASE}/v1/roles/create`;

  const method = roleId ? "PUT" : "POST";

  fetch(url, {
    method: method,
    headers: {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
    },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(() => {
      $(".btn-close").trigger("click");
      loadRoleList();
    })
    .catch(err => console.error("Save role failed", err));
});

/* =============================
   DELETE ROLE
============================= */
function openDeleteRole(id) {
  $("#deleteRoleId").val(id);
  $("#deleteRoleModal").modal("show");
}

$("#confirmDeleteRole").on("click", async function  () {
  const id = $("#deleteRoleId").val();
const res = await fetch(`${API_BASE}/v1/roles/delete/${id}`, {
    method: "DELETE",
    headers: {
        accept: "application/json",
        Authorization: `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
    }
});

let data = null;

try {
    data = await res.json();
} catch (e) {
    // no response body
}

// ✅ Show toast for BOTH success and error (including 409)
if (data?.detail) {
  
          showToast(`${data.detail.message}`, 'danger');
    
}

// ✅ Only close modal + reload on success
$(".modal  .btn-close").trigger("click");

    loadRoleList();


});

/* =============================
   INIT
============================= */
$(document).ready(function () {
  loadRoleList();
  $("#addRoleBtn").on("click", openAddRole);
});


// Toast Notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed top-0 end-0 p-3`;
    toast.style.zIndex = 9999;
    toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
    document.body.appendChild(toast);
    new bootstrap.Toast(toast, { delay: 4000 }).show();
    setTimeout(() => toast.remove(), 5000);
}