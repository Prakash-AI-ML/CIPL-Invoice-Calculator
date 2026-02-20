const API_BASE_URL = API_BASE+"/v1/client-details";

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

const headers = {
  "Content-Type": "application/json",
  
      "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`,
  "accept": "application/json"
};

const clientTableBody = document.querySelector("#clientTable tbody");
const clientLoading = document.getElementById("clientLoading");
const clientError = document.getElementById("clientError");

/* =========================
   LOAD CLIENT LIST
========================= */
async function loadClients() {
  if ($.fn.DataTable.isDataTable('#clientTable')) {
              $('#clientTable').DataTable().destroy();
            }
  clientLoading.classList.remove("d-none");
  clientTableBody.innerHTML = "";

  try {
    const res = await fetch(`${API_BASE_URL}/read`, { headers });
    const data = await res.json();

    data.clients.forEach((c, index) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${index + 1}</td>
        <td>${c.client_id ?? "-"}</td>
        <td>${c.name}</td>
        <td>${c.phone ?? "-"}</td>
        <td>${c.pay_term === null ? "-" : (c.pay_term === 0 ? "COD" : c.pay_term)}</td>
        <td>${c.merchant_category ?? "-"}</td>
        <td>${c.template ?? "-"}</td>
        <td>${c.status === 1 ? "Active" : "Inactive"}</td>
        ${canShowAction('clients_crud') ? `
  <td>
    <button class="btn btn-sm btn-warning me-1" onclick="editClient(${c.id})">Edit</button>
    <button class="btn btn-sm btn-danger" onclick="openDelete(${c.id})">Delete</button>
  </td>
` : ``}
        
      `;
      clientTableBody.appendChild(tr);
    });
    $('#clientTable').DataTable();
  } catch (err) {
    clientError.textContent = "Failed to load clients";
    clientError.classList.remove("d-none");
  } finally {
    clientLoading.classList.add("d-none");
  }
}

/* =========================
   ADD CLIENT
========================= */
const addClientBtn = document.getElementById("addClientBtn");

if (addClientBtn) {
  addClientBtn.addEventListener("click", () => {
    document.getElementById("clientForm").reset();
    document.getElementById("clientPkId").value = "";
    document.getElementById("clientModalTitle").textContent = "Add Client";
  });
}

/* =========================
   SAVE (CREATE / UPDATE)
========================= */
document.getElementById("clientForm").addEventListener("submit", async e => {
  e.preventDefault();

  const pkId = document.getElementById("clientPkId").value;

   payload = {
    client_id: clientId.value,
    name: clientName.value,
    phone: phone.value,
    address: address.value,
    pay_term: payTerm.value,
    merchant_category: merchantCategory.value,
    template: template.value,
    bank_name: bankName.value,
    bank_acc_number: bankAcc.value,
    bank_origin: bankOrigin.value,
    iban_no: ibanNo.value,
    swift_code: shiftCode.value,
    status: Number(statuss.value),
    created_by: Number(getCookie('user_id')),
    updated_by: Number(getCookie('user_id'))
  };

payload = Object.fromEntries(
  Object.entries(payload).filter(
    ([_, value]) =>
      value !== null &&
      value !== undefined &&
      !(typeof value === "string" && value.trim() === "")
  )
);

  const url = pkId ? `${API_BASE_URL}/update/${pkId}` : `${API_BASE_URL}/create`;
  const method = pkId ? "PUT" : "POST";

  await fetch(url, {
    method,
    headers,
    body: JSON.stringify(payload)
  });

  bootstrap.Modal.getInstance(document.getElementById("clientModal")).hide();
  loadClients();
});

/* =========================
   EDIT CLIENT
========================= */
async function editClient(id) {
  const res = await fetch(`${API_BASE_URL}/read/${id}`, { headers });
  const data = await res.json();
  const c = data.clients[0];

  clientPkId.value = c.id;
  clientId.value = c.client_id;
  clientName.value = c.name;
  phone.value = c.phone;
  address.value = c.address;
  merchantCategory.value = c.merchant_category;
  bankName.value = c.bank_name;
  bankAcc.value = c.bank_acc_number;
  bankOrigin.value = c.bank_origin;
  shiftCode.value = c.swift_code;
  ibanNo.value = c.iban_no;
  payTerm.value = c.pay_term;
  template.value = c.template;
  statuss.value = c.status;
sessionStorage.setItem("selected_template", c.template);
  const templatePreview = document.getElementById("templatePreview");
  templatePreview.src = "/static/app/7templates.html";
  document.getElementById("clientModalTitle").textContent = "Edit Client";
  new bootstrap.Modal(document.getElementById("clientModal")).show();
}

/* =========================
   DELETE CLIENT
========================= */
function openDelete(id) {
  deleteClientId.value = id;
  new bootstrap.Modal(document.getElementById("deleteClientModal")).show();
}

document.getElementById("confirmDeleteClient").addEventListener("click", async () => {
  const id = deleteClientId.value;

  await fetch(`${API_BASE_URL}/delete/${id}`, {
    method: "DELETE",
    headers
  });

  bootstrap.Modal.getInstance(document.getElementById("deleteClientModal")).hide();
  loadClients();
});

/* INIT */
loadClients();


$(document).ready(function() {
  $('#template').on('change', function() {
    const selectedTemplate = $(this).val();
    sessionStorage.setItem("selected_template", selectedTemplate);
    const templatePreview = document.getElementById("templatePreview");
    templatePreview.src = "/static/app/7templates.html";
  });
});

loadCategoryList('merchantCategory')

function loadCategoryList(select_id) {
  $(`#${select_id}`).empty()
  fetch(`${API_BASE}/v1/category/lists`, {
    method: "GET",
    headers: {
      "accept": "application/json",
      "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
    }
  })
    .then(res => res.json())
    .then(res => {

      const rows = res || [];
      
      $(`#${select_id}`).append(
          `<option value=''>Select Category</option>
          `
        );
      rows.forEach(c => {
        $(`#${select_id}`).append(
          `<option value=${c.category_name}>${c.category_name.toUpperCase()}</option>
          `
        );
      });
    })
    .catch(err => {
    
    });
}
