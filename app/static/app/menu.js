/* =============================
   LOAD MENU LIST
============================= */
function loadMenuList() {
  $("#menuLoading").removeClass("d-none");
  $("#menuError").addClass("d-none");
  $("#menuTable tbody").empty();

  fetch(`${API_BASE}/v1/menus/lists`, {
    method: "GET",
    headers: {
      "accept": "application/json",
      "Authorization": `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    }
  })
    .then(res => res.json())
    .then(res => {
      $("#menuLoading").addClass("d-none");

      const rows = res || [];
      if (!rows.length) {
        $("#menuTable tbody").html(`
          <tr>
            <td colspan="3" class="text-center">No menus found</td>
          </tr>
        `);
        return;
      }

      rows.forEach(m => {
        $("#menuTable tbody").append(`
          <tr>
            <td>${m.id}</td>
            <td>${m.menu_name.toUpperCase()}</td>
            <td>
              <button class="btn btn-sm btn-primary"
                onclick="openEditMenu(${m.id}, '${m.menu_name}')">
                Edit
              </button>
              <button class="btn btn-sm btn-danger ms-1"
                onclick="openDeleteMenu(${m.id})">
                Delete
              </button>
            </td>
          </tr>
        `);
      });
    })
    .catch(err => {
      $("#menuLoading").addClass("d-none");
      $("#menuError").removeClass("d-none").text("Failed to load menus");
      console.error(err);
    });
}

/* =============================
   OPEN ADD MENU MODAL
============================= */
function openAddMenu() {
  $("#menuModalTitle").text("Add Menu");
  $("#menuId").val("");
  $("#menuName").val("");
  $("#menuModal").modal("show");
}

/* =============================
   OPEN EDIT MENU MODAL
============================= */
function openEditMenu(id, name) {
  $("#menuModalTitle").text("Edit Menu");
  $("#menuId").val(id);
  $("#menuName").val(name);
  $("#menuModal").modal("show");
}

/* =============================
   SAVE MENU (CREATE / UPDATE)
============================= */
$("#menuForm").on("submit", function (e) {
  e.preventDefault();

  const menuId = $("#menuId").val();
  const userId = getCookie("user_id");

  // if (!userId) {
  //   console.error("user_id not found in cookie");
  //   return;
  // }

  const payload = {
    menu_name: $("#menuName").val().trim()
  };

  if (!payload.menu_name) return;

  // audit fields
  if (menuId) {
    payload.updated_by = userId;
  } else {
    payload.created_by = userId;
  }

  const url = menuId
    ? `${API_BASE}/v1/menus/update/${menuId}`
    : `${API_BASE}/v1/menus/create`;

  const method = menuId ? "PUT" : "POST";

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
      $("#menuModal").modal("hide");
      loadMenuList();
    })
    .catch(err => console.error("Save menu failed", err));
});

/* =============================
   DELETE MENU
============================= */
function openDeleteMenu(id) {
  $("#deleteMenuId").val(id);
  $("#deleteMenuModal").modal("show");
}

$("#confirmDeleteMenu").on("click", function () {
  const id = $("#deleteMenuId").val();

  fetch(`${API_BASE}/v1/menus/delete/${id}`, {
    method: "DELETE",
    headers: {
      "accept": "application/json",
      "Authorization": `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    }
  })
    .then(() => {
      $("#deleteMenuModal").modal("hide");
      loadMenuList();
    })
    .catch(err => console.error("Delete menu failed", err));
});

/* =============================
   INIT
============================= */
$(document).ready(function () {
  loadMenuList();
  $("#addMenuBtn").on("click", openAddMenu);
});
