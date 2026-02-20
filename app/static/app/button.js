/* =============================
   LOAD BUTTON LIST
============================= */
function loadButtonList() {
  $("#buttonLoading").removeClass("d-none");
  $("#buttonError").addClass("d-none");
  $("#buttonTable tbody").empty();

  fetch(`${API_BASE}/v1/buttons/lists`, {
    method: "GET",
    headers: {
      "accept": "application/json",
      "Authorization": `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    }
  })
    .then(res => res.json())
    .then(res => {
      $("#buttonLoading").addClass("d-none");

      const rows = res || [];
      if (!rows.length) {
        $("#buttonTable tbody").html(`
          <tr>
            <td colspan="3" class="text-center">No buttons found</td>
          </tr>
        `);
        return;
      }

      rows.forEach(b => {
        $("#buttonTable tbody").append(`
          <tr>
            <td>${b.id}</td>
            <td>${b.button_name.toUpperCase()}</td>
            <td>
              <button class="btn btn-sm btn-primary"
                onclick="openEditButton(${b.id}, '${b.button_name}')">
                Edit
              </button>
              <button class="btn btn-sm btn-danger ms-1"
                onclick="openDeleteButton(${b.id})">
                Delete
              </button>
            </td>
          </tr>
        `);
      });
    })
    .catch(err => {
      $("#buttonLoading").addClass("d-none");
      $("#buttonError").removeClass("d-none").text("Failed to load buttons");
      console.error(err);
    });
}

/* =============================
   OPEN ADD BUTTON MODAL
============================= */
function openAddButton() {
  $("#buttonModalTitle").text("Add Button");
  $("#buttonId").val("");
  $("#buttonName").val("");
  $("#buttonModal").modal("show");
}

/* =============================
   OPEN EDIT BUTTON MODAL
============================= */
function openEditButton(id, name) {
  $("#buttonModalTitle").text("Edit Button");
  $("#buttonId").val(id);
  $("#buttonName").val(name);
  $("#buttonModal").modal("show");
}

/* =============================
   SAVE BUTTON (CREATE / UPDATE)
============================= */
$("#buttonForm").on("submit", function (e) {
  e.preventDefault();

  const buttonId = $("#buttonId").val();
  const userId = getCookie("user_id");

  if (!userId) {
    console.error("user_id not found in cookie");
    return;
  }

  const payload = {
    button_name: $("#buttonName").val().trim()
  };

  if (!payload.button_name) return;

  // audit fields
  if (buttonId) {
    payload.updated_by = userId;
  } else {
    payload.created_by = userId;
  }

  const url = buttonId
    ? `${API_BASE}/v1/buttons/update/${buttonId}`
    : `${API_BASE}/v1/buttons/create`;

  const method = buttonId ? "PUT" : "POST";

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
      $("#buttonModal").modal("hide");
      loadButtonList();
    })
    .catch(err => console.error("Save button failed", err));
});

/* =============================
   DELETE BUTTON
============================= */
function openDeleteButton(id) {
  $("#deleteButtonId").val(id);
  $("#deleteButtonModal").modal("show");
}

$("#confirmDeleteButton").on("click", function () {
  const id = $("#deleteButtonId").val();

  fetch(`${API_BASE}/v1/buttons/delete/${id}`, {
    method: "DELETE",
    headers: {
      "accept": "application/json",
      "Authorization": `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    }
  })
    .then(() => {
      $("#deleteButtonModal").modal("hide");
      loadButtonList();
    })
    .catch(err => console.error("Delete button failed", err));
});

/* =============================
   INIT
============================= */
$(document).ready(function () {
  loadButtonList();
  $("#addButtonBtn").on("click", openAddButton);
});
