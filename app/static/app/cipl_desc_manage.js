    const API_BASE_URL = API_BASE+"/v1/cipl-desc";

const headers = {
  "Content-Type": "application/json",
  "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`,
  "accept": "application/json"
};

const ciplTableBody = document.querySelector("#ciplTable tbody");
const ciplLoading = document.getElementById("ciplLoading");
const ciplError = document.getElementById("ciplError");

/* =========================
   LOAD DESCRIPTIONS
========================= */
async function loadCiplDesc() {
  if ($.fn.DataTable.isDataTable('#ciplTable')) {
    $('#ciplTable').DataTable().destroy();
  }
  ciplLoading.classList.remove("d-none");
  ciplTableBody.innerHTML = "";

  try {
    const res = await fetch(`${API_BASE_URL}/read`, { headers });
    const data = await res.json();

    data.forEach((c, index) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${index + 1}</td>
        <td>${c.item_id ?? "-"}</td>
        <td>${c.original}</td>
        <td>${c.modified}</td>
        <td>${c.lines}</td>
        <td>${c.status === '1' ? "Active" : "Inactive"}</td>
        <td>
          <button class="btn btn-sm btn-warning me-1" onclick="editCipl(${c.id})">Edit</button>
          <button class="btn btn-sm btn-danger" onclick="openDelete(${c.id})">Delete</button>
        </td>
      `;
      ciplTableBody.appendChild(tr);
    });

    $('#ciplTable').DataTable();
  } catch (err) {
    ciplError.textContent = "Failed to load descriptions";
    ciplError.classList.remove("d-none");
  } finally {
    ciplLoading.classList.add("d-none");
  }
}

/* =========================
   ADD / EDIT MODAL
========================= */
document.getElementById("addCiplBtn")?.addEventListener("click", () => {
  document.getElementById("ciplForm").reset();
  document.getElementById("ciplPkId").value = "";
  document.getElementById("ciplModalTitle").textContent = "Add Description";
});

/* =========================
   SAVE (CREATE / UPDATE)
========================= */
document.getElementById("ciplForm").addEventListener("submit", async e => {
  e.preventDefault();

  const pkId = document.getElementById("ciplPkId").value;

  const payload = {
    item_id: Number(document.getElementById("itemId").value),
    original: document.getElementById("original").value,
    modified: document.getElementById("modified").value,
    lines: Number(document.getElementById("lines").value),
    status: Number(document.getElementById("statuss")),
    created_by: Number(getCookie('user_id')),
    updated_by: Number(getCookie('user_id'))
  };

  const url = pkId ? `${API_BASE_URL}/update/${pkId}` : `${API_BASE_URL}/create`;
  const method = pkId ? "PATCH" : "POST";

  await fetch(url, { method, headers, body: JSON.stringify(payload) });

  bootstrap.Modal.getInstance(document.getElementById("ciplModal")).hide();
  loadCiplDesc();
});

/* =========================
   EDIT DESCRIPTION
========================= */
async function editCipl(id) {
  const res = await fetch(`${API_BASE_URL}/read/${id}`, { headers });
  const data = await res.json();

  const c = data;
  document.getElementById("ciplPkId").value = c.id;
  document.getElementById("itemId").value = c.item_id;
  document.getElementById("original").value = c.original;
  document.getElementById("modified").value = c.modified;
  document.getElementById("lines").value = c.lines;
  document.getElementById("statuss").value = c.status;

  document.getElementById("ciplModalTitle").textContent = "Edit Description";
  new bootstrap.Modal(document.getElementById("ciplModal")).show();
}

/* =========================
   DELETE DESCRIPTION
========================= */
function openDelete(id) {
  document.getElementById("deleteCiplId").value = id;
  new bootstrap.Modal(document.getElementById("deleteCiplModal")).show();
}

document.getElementById("confirmDeleteCipl").addEventListener("click", async () => {
  const id = document.getElementById("deleteCiplId").value;

  await fetch(`${API_BASE_URL}/delete/${id}`, { method: "DELETE", headers });

  bootstrap.Modal.getInstance(document.getElementById("deleteCiplModal")).hide();
  loadCiplDesc();
});

/* INIT */
loadCiplDesc();