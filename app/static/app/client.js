
// Helper: Format amount or show "-"
function fmt(val) {
  const num = parseFloat(val);
  return isNaN(num) || num === 0 ? '-' : parseFloat(num.toFixed(2)).toLocaleString();
}

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

function canShowAction(ButtonName) {
    const clients = USER_MENUS.clients.buttons;

    if (!clients) return false;

    if (Array.isArray(clients)) {
        const buttonNames = clients.map(item => item.button_name);
        return buttonNames.includes(ButtonName);
    }

    if (typeof clients === 'object' && 'button_name' in clients) {
        return clients.button_name === ButtonName;
    }

    return false;
}


// Helper: Format amount or show "-"
function fmt(val) {
  const num = parseFloat(val);
  return isNaN(num) || num === 0 ? '-' : parseFloat(num.toFixed(2)).toLocaleString();
}


/* =============================
   LOAD CLIENT SUMMARY LIST
============================= */
function loadClientSummary() {
  $("#clientLoading").removeClass("d-none");
  $("#clientError").addClass("d-none");
  $("#clientTable tbody").empty();

  fetch(`${API_BASE}/v1/client/lists`, {
    method: "POST",
    headers: {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    },
    body: JSON.stringify({})
  })
    .then(res => {
      if (res.status === 401) {
        console.error("401 Unauthorized - clearing token & redirecting");
        document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        window.location.href = "/";
        return;
      }

      if (res.status === 403) {
        showToast("This user doesn’t have permission to access this menu right now.", "danger");
        return;
      }

      return res.json();
    })
    .then(res => {
      if (!res) return;

      $("#clientLoading").addClass("d-none");

      const rows = res.clients || [];
      const hasViewPermission = canShowAction("view");
      const colspan = hasViewPermission ? 6 : 5;

      if (!rows.length) {
        $("#clientTable tbody").html(`
          <tr>
            <td colspan="${colspan}" class="text-center">
              No customers with current due
            </td>
          </tr>
        `);
        return;
      }

      rows.forEach(item => {
        let actionCell = "";

        if (hasViewPermission) {
          actionCell = `
            <button class="btn btn-sm btn-primary"
              onclick="openClinetInvoiceModal(
                '${item.customer_id}',
                '${item.customer_name || "Unknown"}',
                '${item.pay_term_days || 30}'
              )">
              <i class="mdi mdi-eye" style="font-size:20px;color:#fff;vertical-align:middle;"></i>
              <i class="mdi mdi-file-multiple"></i>
            </button>
          `;
        }

        $("#clientTable tbody").append(`
          <tr>
            <td style="width:10%;">${item.customer_id}</td>
            <td style="width:35%;">${item.customer_name}</td>
            <td style="width:15%;">${item.paid_invoices}</td>
            <td style="width:15%;">${item.unpaid_invoices}</td>
            <td style="width:15%;" class="fw-bold">${item.total_invoices}</td>
            <td style="width:10%; text-align:center;">
              ${actionCell}
            </td>
          </tr>
        `);
      });
    })
    .catch(err => {
      $("#clientLoading").addClass("d-none");
      $("#clientError")
        .removeClass("d-none")
        .text("Failed to load client summary");
      console.error(err);
    });
}



// MAIN FUNCTION - Open Client Invoice Modal
async function openClinetInvoiceModal(customerId, customerName, payTerm) {
  
  sessionStorage.setItem("customerId", customerId);
  sessionStorage.setItem("customerName", customerName);
  sessionStorage.setItem("payTerm", payTerm);

   document.getElementById('modalCustomerNameClient').textContent = customerName;
  document.getElementById('modalCustomerIdClient').textContent = customerId;
  console.log(customerId, customerName, payTerm)

  // Show loading in both tables
  const tables = ['currentTableClient', 'paidTable1Client']; // Fixed: was 'paidTable' before!
  tables.forEach(id => {
    const table = document.getElementById(id);
    if (!table) return console.error(`Table #${id} not found in DOM`);
    
    const tbody = table.querySelector('tbody');
    const colspan = table.querySelectorAll('thead th').length;
    tbody.innerHTML = `<tr><td colspan="${colspan}" class="text-center py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading...</td></tr>`;
  });

  // Show modal
  const modalEl = document.getElementById('clientModal');
  const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
  modal.show();

  try {
    // Fetch both unpaid and paid invoices in parallel
    const [unpaidRes, paidRes] = await Promise.all([
      fetch(`${API_BASE}/v1/client/lists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
       
         },
        body: JSON.stringify({ customer_id: customerId, status: 'unpaid', payment_term: payTerm })
      }).then(r => r.json()),

      fetch(`${API_BASE}/v1/client/lists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
       
         },
        body: JSON.stringify({ customer_id: customerId, status: 'paid', payment_term: payTerm })
      }).then(r => r.json())
    ]);

    // Render tables

    
    renderClientCurrentTable(unpaidRes.clients || [], payTerm);
    renderClientPaidTable(paidRes.clients || [], payTerm); // Fixed function name

  } catch (err) {
    console.error('Failed to load client invoices:', err);
    showToast('Failed to load invoices. Please try again.', 'danger');
    
    // Clear loading on error
    tables.forEach(id => {
      const tbody = document.querySelector(`#${id} tbody`);
      if (tbody) tbody.innerHTML = '<tr><td colspan="10" class="text-center text-danger">Error loading data</td></tr>';
    });
  }
}


// Render Unpaid / Current Invoices Table
function renderClientCurrentTable(invoices, payTerm) {
  const tbody = document.querySelector('#currentTableClient tbody');
  tbody.innerHTML = '';

  if (invoices.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No unpaid invoices</td></tr>';
    return;
  }

  invoices.forEach(inv => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${inv.invoice_date || '-'}</td>
      <td>${inv.ref_no || '-'}</td>
      <td>${inv.description || '-'}</td>
      <td>${fmt(inv.amount || 0)}</td>
      <td>${inv.bucket || 'Current'}</td>
      <td>
        <button class="btn btn-sm btn-primary hide" onclick="viewInvoice('${inv.ref_no}')">View</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Render Paid Invoices Table - Fixed function name & logic
function renderClientPaidTable(invoices) {
  const tbody = document.querySelector('#paidTable1Client tbody');
  tbody.innerHTML = '';

  if (invoices.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No paid invoices</td></tr>';
    return;
  }

  invoices.forEach(inv => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${inv.payment_date || inv.invoice_date || '-'}</td>
      <td>${inv.ref_no || '-'}</td>
      <td>${inv.description || '-'}</td>
      <td>${inv.debit_ref_no || '-'}</td>
      <td>${inv.debit_description || '-'}</td>
      <td>${fmt(inv.amount || inv.credit || 0)}</td>
      <td>${fmt(inv.debit || inv.paid_amount || 0)}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Helper: format currency (you probably already have this)
function fmt(num) {
  return new Intl.NumberFormat('en-US', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  }).format(num);
}



// Load aging on page load since it's active
// window.addEventListener('load', loadAging);
document.addEventListener("DOMContentLoaded", loadClientSummary);
