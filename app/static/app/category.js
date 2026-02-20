
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

/* =============================
   LOAD CATEGORY LIST
============================= */
function loadCategoryList() {
  $("#categoryLoading").removeClass("d-none");
  $("#categoryError").addClass("d-none");
  $("#categoryTable tbody").empty();

  fetch(`${API_BASE}/v1/category/lists`, {
    method: "GET",
    headers: {
      "accept": "application/json",
      "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
    }
  })
    .then(res => res.json())
    .then(res => {
      $("#categoryLoading").addClass("d-none");

      const rows = res || [];
      if (!rows.length) {
        $("#categoryTable tbody").html(`
          <tr>
            <td colspan="3" class="text-center">No categories found</td>
          </tr>
        `);
        return;
      }

      rows.forEach((c, index) => {
        $("#categoryTable tbody").append(`
          <tr>
            <td>${index + 1}</td>
            <td>${c.category_name.toUpperCase()}</td>
            ${canShowAction('categories_crud') ? `
  <td>
   <button class="btn btn-sm btn-primary"
                      onclick="openEditCategory(${c.id}, '${c.category_name}')">
                Edit
              </button>
              <button class="btn btn-sm btn-danger ms-1"
                      onclick="openDeleteCategory(${c.id}, '${c.category_name}')">
                Delete
              </button>
  </td>
` : ``}
            
          </tr>
        `);
      });
    })
    .catch(err => {
      $("#categoryLoading").addClass("d-none");
      $("#categoryError")
        .removeClass("d-none")
        .text("Failed to load categories");
      console.error(err);
    });
}

/* =============================
   OPEN ADD CATEGORY MODAL
============================= */
function openAddCategory() {
  $("#categoryModalTitle").text("Add Category");
  $("#categoryId").val("");
  $("#categoryName").val("");
  $("#categoryModal").modal("show");
}

/* =============================
   OPEN EDIT CATEGORY MODAL
============================= */
function openEditCategory(id, name) {
  $("#categoryModalTitle").text("Edit Category");
  $("#categoryId").val(id);
  $("#categoryName").val(name);
  $("#categoryModal").modal("show");
}

/* =============================
   SAVE CATEGORY (CREATE / UPDATE)
============================= */
$("#categoryForm").on("submit", function (e) {
  e.preventDefault();

  const categoryId = $("#categoryId").val();
  const userId = getCookie("user_id");
  const payload = {
    category_name: $("#categoryName").val().trim()
  };

  if (!payload.category_name) return;

  // audit fields
  if (categoryId) {
    payload.updated_by = userId;
  } else {
    payload.updated_by = userId;
    payload.created_by = userId;
  }

  const url = categoryId
    ? `${API_BASE}/v1/category/update/${categoryId}`
    : `${API_BASE}/v1/category/create`;

  const method = categoryId ? "PUT" : "POST";

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
      $("#categoryModal").modal("hide");
      loadCategoryList();
    })
    .catch(err => console.error("Save category failed", err));
});

/* =============================
   DELETE CATEGORY
============================= */
async function openDeleteCategory(id, category_name) {
  $("#deleteCategoryId").val(id);
  $("#deleteCategoryName").val(category_name);
  $("#deleteCategoryModal").modal("show");
}

$("#confirmDeleteCategory").on("click", async function () {
  const id = $("#deleteCategoryId").val();
  const category_name = $("#deleteCategoryName").val();

  let res, data = null;

  try {
    res = await fetch(
      `${API_BASE}/v1/category/delete/${id}?category_name=${encodeURIComponent(category_name)}`,
      {
        method: "DELETE",
        headers: {
          "accept": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
        }
      }
    );

    try {
      data = await res.json();
    } catch (e) {
      // no response body
    }

    // ❌ Error response (409, 400, etc.)
    if (!res.ok) {
      showToast(data?.detail?.message || "Delete failed", "danger");
      return; // ⛔ do NOT close modal
    }

    // ✅ Success
    showToast(data?.detail?.message || "Category deleted", "success");
    $("#deleteCategoryModal").modal("hide");
    loadCategoryList();

  } catch (err) {
    console.error("Delete category failed", err);
    showToast("Network error", "danger");
  }
});

/* =============================
   INIT
============================= */
$(document).ready(function () {
  loadCategoryList();
  $("#addCategoryBtn").on("click", openAddCategory);
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
