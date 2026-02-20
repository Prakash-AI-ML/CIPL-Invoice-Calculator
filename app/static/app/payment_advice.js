   function canShowAction(ButtonName) {
    const advice = USER_MENUS.advice.buttons;

    if (!advice) return false;

    // If advice is an array
    if (Array.isArray(advice)) {
        const buttonNames = advice.map(item => item.button_name);
        return buttonNames.includes(ButtonName);
    }

    // If advice is a single object
    if (typeof advice === 'object' && 'button_name' in advice) {
        return advice.button_name === ButtonName;
    }

    return false;
}


// Load Payment Advice Summary
async function loadAdviceSummary() {
  const tbody = document.querySelector('#adviceTable tbody');
  const loading = document.getElementById('adviceLoading');
  const error = document.getElementById('adviceError');
  
  tbody.innerHTML = '';
  loading.classList.remove('d-none');
  error.classList.add('d-none');

  try {
    const res = await fetch(`${API_BASE}/v1/payment_/advice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
      },
      body: JSON.stringify({})
    });

    // Handle 401 Unauthorized
    if (res.status === 401) {
      console.error('apiFetch: 401 Unauthorized - clearing token & redirecting');
      document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      window.location.href = '/';
      return;
    }

    // Handle 403 Forbidden
    if (res.status === 403) {
      console.error("Access to menu clients denied");
      showToast("This user doesn’t have permission to access this menu right now.", 'danger');
      return;
    }

    if (!res.ok) throw new Error('Failed to fetch advice');

    const data = await res.json();
    const list = data.advice || [];

    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center">No customers with current due</td></tr>';
      return;
    }

    list.forEach(item => {
      const tr = document.createElement('tr');

      // Base columns (always shown)
      let rowHTML = `
        <td style="width:10%;">${item.customer_id}</td>
        <td style="width:40%;">${item.customer_name}</td>
        <td style="width:10%;">${item.pay_term_days}</td>
        <td style="width:25%;" class="fw-bold text-success">${parseFloat(item.current_due_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
        <td style="width:15%;">
      `;

      // Conditionally add the View Invoices button
      if (canShowAction('view')) {
        rowHTML += `
          <button class="btn btn-sm btn-primary view-detail" data-customer="${item.customer_id}">
            View Invoices <i class="bi bi-box-arrow-up-right"></i>
          </button>
        `;
      } else {
        rowHTML += '&nbsp;'; // Empty cell to maintain alignment
      }

      rowHTML += `</td>`;
      tr.innerHTML = rowHTML;

      tbody.appendChild(tr);
    });

    // Total footer row
    const tfoot = document.createElement('tfoot');
    const totalAmount = list.reduce((sum, item) => sum + (parseFloat(item.current_due_amount) || 0), 0);
    tbody.innerHTML += `
      <tr>
        
        <td style="width:20%;" colspan="3" class="text-end fw-bold">Total Current Due:</td>
        <td style="width:20%;text-align: left !important;" colspan="2" class="fw-bold text-primary ">${fmt(totalAmount)}</td>
     
      </tr>
    `;


    // Attach click events only to buttons that exist (i.e., when user has 'view' permission)
    if (canShowAction('view')) {
      document.querySelectorAll('.view-detail').forEach(btn => {
        btn.addEventListener('click', () => openDetailModal(btn.dataset.customer));
      });
    }

  } catch (err) {
    console.error(err);
    error.textContent = err.message || 'An error occurred while loading data.';
    error.classList.remove('d-none');
  } finally {
    loading.classList.add('d-none');
  }
}


// Open modal and load detailed invoices for a customer
// Open modal and load detailed invoices for a customer
async function openDetailModal(customerId) {
  const modal = new bootstrap.Modal(document.getElementById('detailModal'));
  const title = document.getElementById('modalCustomerName');
  const tbody = document.querySelector('#detailTable tbody');
  const loading = document.getElementById('detailLoading');
  tbody.innerHTML = '';
  loading.style.display = 'block';

  // Find customer name from advice table
  const row = Array.from(document.querySelectorAll('#adviceTable tbody tr')).find(r =>
    r.cells[0].textContent === customerId
  );
  title.textContent = row ? row.cells[1].textContent + ' - Invoices' : 'Invoices';

  modal.show();

  try {
    const res = await fetch(`${API_BASE}/v1/payment_/advice`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json',
                 'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
       },
      body: JSON.stringify({customer_id: customerId})
    });

    if (res.status === 401) {
                console.error('apiFetch: 401 Unauthorized - clearing token & redirecting');
                document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';  // Clear cookie
                window.location.href = '/';
            }

    if (!res.ok) throw new Error('Failed to load details');

    const data = await res.json();
    const invoices = data.advice || [];

    if (invoices.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center">No invoices found</td></tr>';
      return;
    }

    invoices.forEach(inv => {
      // for (let i = 0; i < 60; i++) {
        const tr = document.createElement("tr");
        const dateStr = inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString('en-GB') : '-';
        const duedateStr = inv.due_date ? new Date(inv.due_date).toLocaleDateString('en-GB') : '-';
    tr.innerHTML = `
        <td>${dateStr}</td>
        <td>${duedateStr}</td>
        <td>${inv.days_remaining_for_payment || 'Today'}</td>
        <td>${inv.ref_no || '-'}</td>
        <td>${inv.description || '-'}</td>
        <td>${fmt(inv.credit)}</td>
        <td>${fmt(inv.balance)}</td>
        <td>${inv.status == 0 ? 'Open' : 'Paid'}</td>
    `;
    tbody.appendChild(tr);
// }

      // const tr = document.createElement('tr');
      // // Only show date part
      // tr.innerHTML = `
      //   <td>${dateStr}</td>
      //   <td>${duedateStr}</td>
      //   <td>${inv.days_remaining_for_payment || 'Today'}</td>
      //   <td>${inv.ref_no || '-'}</td>
      //   <td>${inv.description || '-'}</td>
      //   <td>${fmt(inv.credit)}</td>
      //   <td>${fmt(inv.balance)}</td>
      //   <td>${inv.status == 0 ? 'Open' : 'Paid'}</td>
      // `;
      // tbody.appendChild(tr);
     
    });
tfoot=document.createElement('tr');
    tfoot.innerHTML=`
    
      <td colspan="5" class="text-end fw-bold">Total Amount:</td>
      <td class="fw-bold text-primary text-end">${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.credit) || 0), 0))}</td>
      <td class="fw-bold text-primary text-end">${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.balance) || 0), 0))}</td>
      <td></td>
    `;
    tbody.appendChild(tfoot);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-danger text-center">${err.message}</td></tr>`;
  } finally {
    loading.style.display = 'none';
  }
}




document.addEventListener("DOMContentLoaded", loadAdviceSummary);

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
