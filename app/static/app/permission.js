/* =============================
   LOAD PERMISSION LIST
============================= */
function loadPermissionList() {
  $("#permissionLoading").removeClass("d-none");
  $("#permissionError").addClass("d-none");
  $("#permissionTable tbody").empty();

  fetch(`${API_BASE}/v1/permissions/list`, {
    method: "GET",
    headers: {
      "accept": "application/json",
      "Authorization": `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    }
  })
    .then(res => res.json())
    .then(res => {
      $("#permissionLoading").addClass("d-none");

      const rows = res.permissions || [];
      if (!rows.length) {
        $("#permissionTable tbody").html(`
          <tr>
            <td colspan="3" class="text-center">No permissions found</td>
          </tr>
        `);
        return;
      }

      rows.forEach(p => {
        $("#permissionTable tbody").append(`
          <tr>
            <td>${p.id}</td>
            <td>${p.name}</td>
            <td>
              <button class="btn btn-sm btn-primary"
                onclick="openEditPermission(${p.id}, '${p.name}')">
                Edit
              </button>
              <button class="btn btn-sm btn-danger ms-1"
                onclick="openDeletePermission(${p.id})">
                Delete
              </button>
            </td>
          </tr>
        `);
      });
    })
    .catch(err => {
      $("#permissionLoading").addClass("d-none");
      $("#permissionError").removeClass("d-none").text("Failed to load permissions");
      console.error(err);
    });
}

/* =============================
   OPEN ADD PERMISSION MODAL
============================= */
function openAddPermission() {
  $("#permissionModalTitle").text("Add Permission");
  $("#permissionId").val("");
  $("#permissionName").val("");
  $("#permissionModal").modal("show");
}

/* =============================
   OPEN EDIT PERMISSION MODAL
============================= */
function openEditPermission(id, name) {
  $("#permissionModalTitle").text("Edit Permission");
  $("#permissionId").val(id);
  $("#permissionName").val(name);
  $("#permissionModal").modal("show");
}

/* =============================
   SAVE PERMISSION (CREATE / UPDATE)
============================= */
$("#permissionForm").on("submit", function (e) {
  e.preventDefault();

  const permissionId = $("#permissionId").val();
  const userId = getCookie("user_id");

  if (!userId) {
    console.error("user_id not found in cookie");
    return;
  }

  const payload = {
    name: $("#permissionName").val().trim()
  };

  if (!payload.name) return;

  // audit fields
  if (permissionId) {
    payload.updated_by = userId;
  } else {
    payload.created_by = userId;
  }

  const url = permissionId
    ? `${API_BASE}/v1/permissions/${permissionId}`
    : `${API_BASE}/v1/permissions`;

  const method = permissionId ? "PUT" : "POST";

  fetch(url, {
    method: method,
    headers: {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(() => {
      $("#permissionModal").modal("hide");
      loadPermissionList();
    })
    .catch(err => console.error("Save permission failed", err));
});

/* =============================
   DELETE PERMISSION
============================= */
function openDeletePermission(id) {
  $("#deletePermissionId").val(id);
  $("#deletePermissionModal").modal("show");
}

$("#confirmDeletePermission").on("click", function () {
  const id = $("#deletePermissionId").val();

  fetch(`${API_BASE}/v1/permissions/${id}`, {
    method: "DELETE",
    headers: {
      "accept": "application/json",
      "Authorization": `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    }
  })
    .then(res => res.json())
    .then(() => {
      $("#deletePermissionModal").modal("hide");
      loadPermissionList();
    })
    .catch(err => console.error("Delete permission failed", err));
});

/* =============================
   INIT
============================= */
$(document).ready(function () {
  loadPermissionList();
  $("#addPermissionBtn").on("click", openAddPermission);
});
