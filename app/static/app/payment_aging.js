
      // Helper: Format amount or show "-"
      function fmt(val) {
        const num = parseFloat(val);
        return isNaN(num) || num === 0 ? '-' : parseFloat(num.toFixed(2)).toLocaleString();
      }
      
      function canShowAction(ButtonName) {
    const aging = USER_MENUS.aging.buttons;

    if (!aging) return false;

    // If aging is an array
    if (Array.isArray(aging)) {
        const buttonNames = aging.map(item => item.button_name);
        return buttonNames.includes(ButtonName);
    }

    // If aging is a single object
    if (typeof aging === 'object' && 'button_name' in aging) {
        return aging.button_name === ButtonName;
    }

    return false;
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
      
      function fmt(val) {
      const num = parseFloat(val);
      return isNaN(num) || num === 0 ? '-' : parseFloat(num.toFixed(2)).toLocaleString();
    }
    
    // function fmt(amount) {
    //     // 1. Convert the input to a number, handling null/undefined/non-numeric input safely
    //     const numericAmount = parseFloat(amount) || 0; 
    
    //     // 2. Use toFixed(2) to ensure exactly two decimal places
    //     const fixedAmount = numericAmount.toFixed(2);
    
    //     // 3. (Optional) Add currency formatting (e.g., thousands separators, currency symbol)
    //     // For this example, we'll use a simple locale-specific format
    //     return new Intl.NumberFormat('en-US', {
    //         style: 'currency',
    //         currency: 'MYR', // Change 'USD' to your required currency code
    //         minimumFractionDigits: 2, // Explicitly set 2 fraction digits
    //         maximumFractionDigits: 2,
    //     }).format(numericAmount); 
    
    //     // Simpler option if you don't need the currency symbol:
    //     // return fixedAmount; 
    // }
    
    // Helper: Apply class based on bucket

  

    function getOverdueClass(bucket) {
      const map = {
        '1-30 days overdue': 'overdue-1-30',
        '31-60 days overdue': 'overdue-31-60',
        '61-90 days overdue': 'overdue-61-90',
        '91-120 days overdue': 'overdue-91-120',
        '121-150 days overdue': 'overdue-121-150',
        '150+ days overdue': 'overdue-150'
      };
      return map[bucket] || '';
    }
   
loadCategoryList('category_name')
async function loadAging() {
  const tbody = document.querySelector('#agingTable tbody');
  const loading = document.getElementById('agingLoading');
  const error = document.getElementById('agingError');
  
  // Collect filter values
  const getFilterValue = (id) => document.getElementById(id)?.value.trim() || null;

  const filters = {
    from_date: getFilterValue('filterFromDate'),
    to_date: getFilterValue('filterToDate'),
    supplier_name: getFilterValue('filterSupplier'),
    min_amount: getFilterValue('filterMinAmount') ? parseFloat(getFilterValue('filterMinAmount')) : null,
    max_amount: getFilterValue('filterMaxAmount') ? parseFloat(getFilterValue('filterMaxAmount')) : null,
    category_name: getFilterValue('category_name') || null,
    quick_filter: getFilterValue('filterQuick') || null
  };

  // Clean null/empty values
  Object.keys(filters).forEach(key => {
    if (filters[key] === null || filters[key] === '') delete filters[key];
  });

  tbody.innerHTML = '';
  loading.classList.remove('d-none');
  error.classList.add('d-none');

  try {
    const res = await fetch(`${API_BASE}/v1/payment/aging`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
      
      },
      body: JSON.stringify(filters)  // Send filters!
    });

    if (res.status === 403) {
          showToast(message = "This user doesn’t have permission to access this menu right now.", type = 'danger')
            }

    if (res.status === 401) {
                console.error('apiFetch: 401 Unauthorized - clearing token & redirecting');
                document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';  // Clear cookie
                window.location.href = '/';
            }

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`HTTP ${res.status}: ${err}`);
    }

    const data = await res.json();
    // const aging = data.supply_aging || data || [];
    const aging = Array.isArray(data.supply_aging) ? data.supply_aging : [];

    // Update Summary Badges
    const totalCustomers = aging.length;
    let totalpayment = 0;
    let totalOutstanding = 0;
    let overdueCount = 0;
    let notCurrentDue = 0;
    let totalCurrentDue = 0;
    let total1to30 = 0;
    let total31to60 = 0;
    let total61to90 = 0;
    let total91to120 = 0;
    let total121to150 = 0;
    let total150plus = 0;
    let totalOutstandingSum = 0;
    let totalPaid = 0;
    let totalUnpaid = 0;

    const tfoot = document.querySelector('#agingTable tfoot');
    if (aging.length === 0) {
      tbody.innerHTML = '<tr><td colspan="15" class="text-center text-muted py-4">No records match your filters</td></tr>';
      tfoot.innerHTML='<tr><td></td><td class="text-end fw-bold">Total</td><td></td><td class="fw-semibold  text-success">0</td><td class="fw-semibold text-danger" style = "color: #3b86d1!important">0</td><td class="fw-semibold" style = "color: #008C75!important">0</td><td class="fw-semibold text-danger">0</td><td class="fw-semibold text-danger">0</td><td class="fw-semibold text-danger">0</td><td class="fw-semibold text-danger">0</td><td class="fw-semibold text-danger">0</td><td class="fw-bold text-primary">0</td><td class="text-center">0</td><td class="text-center">0</td><td></td></tr>';
    } else {
      

      aging.forEach(item => {
        const tr = document.createElement('tr');

        const cols = [
          item.customer_id || '',
          item.customer_name || 'Unknown',
          item.pay_term_days || '30',
          item.current_month_payment || 0,
          item.not_due_amount || 0,
          item['1-30 days overdue'] || 0,
          item['31-60 days overdue'] || 0,
          item['61-90 days overdue'] || 0,
          item['91-120 days overdue'] || 0,
          item['121-150 days overdue'] || 0,
          item['150+ days overdue'] || 0,
          item.total_outstanding || 0,
          item['Paid Invoices'] || 0,
          item['Unpaid Invoices'] || 0
        ];
totalpayment += parseFloat(item.current_month_payment || 0);
notCurrentDue += parseFloat(item.not_due_amount || 0);
// totalCurrentDue += parseFloat(item.current_due_amount || 0);
total1to30 += parseFloat(item['1-30 days overdue'] || 0);
total31to60 += parseFloat(item['31-60 days overdue'] || 0);
total61to90 += parseFloat(item['61-90 days overdue'] || 0);
total91to120 += parseFloat(item['91-120 days overdue'] || 0);
total121to150 += parseFloat(item['121-150 days overdue'] || 0);
total150plus += parseFloat(item['150+ days overdue'] || 0);
totalOutstandingSum += parseFloat(item.total_outstanding || 0);
totalPaid += parseInt(item['Paid Invoices'] || 0);
totalUnpaid += parseInt(item['Unpaid Invoices'] || 0);

        cols.forEach((val, i) => {
          const td = document.createElement('td');
          const num = parseFloat(val);

          if ([3,4,5,6,7,8,9,10, 11].includes(i)) {
            if (num === 0) {
              td.textContent = '-';
              td.classList.add('text-muted');
            } else {
              td.textContent = num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
              if (i >= 4 && i <= 10) td.classList.add('text-danger', 'fw-semibold');
              if (i === 3) td.classList.add('text-success', 'fw-semibold');
              if (i === 4) td.style= 'color: #3b86d1!important', 'fw-semibold';
              if (i === 5) td.style= 'color: #008C75!important', 'fw-semibold';
              if (i === 11) {
                td.classList.add('fw-bold', 'text-primary');
                totalOutstanding += num;
              }
            }
          } else if (i === 10 || i === 11) {
            td.textContent = num === 0 ? '-' : num;
            td.classList.add('text-center');
          } else {
            td.textContent = val;
          }

          tr.appendChild(td);
        });

        // Count overdue customers
        if (parseFloat(item['1-30 days overdue'] || 0) > 0 ||
            parseFloat(item['31-60 days overdue'] || 0) > 0 ||
            parseFloat(item['61-90 days overdue'] || 0) > 0 ||
            parseFloat(item['91-120 days overdue'] || 0) > 0 ||
            parseFloat(item['121-150 days overdue'] || 0) > 0 ||
            parseFloat(item['150+ days overdue'] || 0) > 0) {
          overdueCount++;
        }

        if (canShowAction('view')) {
        const actionTd = document.createElement('td');
        const btn = document.createElement('i');
        btn.className = 'mdi mdi-eye';
        btn.style ='font-size: 20px;color: #844fc1;'
        btn.textContent = '';
        btn.onclick = () => openInvoiceModal(
          item.customer_id,
          item.customer_name || 'Unknown',
          item.pay_term_days ?? 30,
          item.debit_ref_prefix || "PC"
        );
        actionTd.style ='text-align:center;'
        actionTd.appendChild(btn);
        tr.appendChild(actionTd);


      }
        tbody.appendChild(tr);

        tbody.appendChild(tr);
        const tfoot = document.querySelector('#agingTable tfoot');
tfoot.innerHTML = ''; // clear existing footer

const footRow = document.createElement('tr');

const blankCols = 3; // customer id + name
for (let i = 0; i < blankCols; i++) {
  const td = document.createElement('td');
  if(i == 1) {
    td.textContent = 'Total';
    td.classList.add('text-end', 'fw-bold');
    
  } else{
  td.textContent = '';
}
footRow.appendChild(td);
      }

const totals = [
  totalpayment,
  notCurrentDue,
  // totalCurrentDue,

  total1to30,
  total31to60,
  total61to90,
  total91to120,
  total121to150,
  total150plus,
  totalOutstandingSum,
  totalPaid,
  totalUnpaid
];

totals.forEach((val, index) => {
  const td = document.createElement('td');

  
  if (index === 0) td.classList.add('fw-semibold', 'text-success'); // current due
  if (index <= 7) td.classList.add('fw-semibold', 'text-danger'); // overdue
  if (index === 1) td.style= 'color: #3b86d1!important', 'fw-semibold';
  if (index === 2) td.style= 'color: #008C75!important', 'fw-semibold';
  if (index === 0) td.style= 'color: #21bf06!important', 'fw-semibold';
              
  if (index === 8) td.classList.add('fw-bold', 'text-primary'); // total outstanding
  if (index >= 8) td.classList.add('text-center'); // paid/unpaid
if(index < 9 ){
  
  td.textContent = val === 0 ? '-' :
    parseFloat(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }else{
  td.textContent = val === 0 ? '-' :
    parseInt(val);
}

  footRow.appendChild(td);
});
const tdFinal = document.createElement('td');
tdFinal.textContent = '';
footRow.appendChild(tdFinal);

tfoot.appendChild(footRow);

      });
    }

    // Update badges
    document.getElementById('totalRecords').textContent = totalCustomers;
    document.getElementById('totalOverdue').textContent = overdueCount;
    document.getElementById('totalOutstanding').textContent = totalOutstanding.toLocaleString('en-MY', {style: 'currency',currency: 'MYR'});
    document.getElementById('totalPayment').textContent = totalpayment.toLocaleString('en-MY', {style: 'currency',currency: 'MYR'});

  } catch (err) {
    console.error('Aging load error:', err);
    error.textContent = err.message || 'Failed to load aging report';
    error.classList.remove('d-none');
  } finally {
    loading.classList.add('d-none');
  }
}


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

    
    // Event Listeners
    // document.getElementById('applyFilters')?.addEventListener('click', loadAging);
    // document.getElementById('clearFilters')?.addEventListener('click', () => {
    //   document.querySelectorAll('#aging input, #aging select').forEach(el => {
    //     if (el.type === 'date' || el.type === 'text' || el.type === 'number') el.value = '';
    //     if (el.tagName === 'SELECT') el.selectedIndex = 0;
    //   });
    //   loadAging();
    // });
    document.getElementById('applyFilters')?.addEventListener('click', () => {
      const toDate = document.getElementById('filterToDate')?.value || null;

      updateMonthUI(toDate);
      loadAging();
    });
    document.getElementById('clearFilters')?.addEventListener('click', () => {
      document.querySelectorAll('#aging input, #aging select').forEach(el => {
        if (el.type === 'date' || el.type === 'text' || el.type === 'number') {
          el.value = '';
        }
        if (el.tagName === 'SELECT') {
          el.selectedIndex = 0;
        }
      });

      // Reset to current month
      updateMonthUI();
      loadAging();
    });

    
    // Auto-load on tab switch (if using Bootstrap tabs)
    document.querySelector('[data-bs-target="#aging"]')?.addEventListener('shown.bs.tab', loadAging);
    
  

async function openInvoiceModal(customerId, customerName, payTerm, debit_ref_prefix) {
  sessionStorage.setItem("customerId", customerId);
  sessionStorage.setItem("customerName", customerName);
  sessionStorage.setItem("payTerm", payTerm);
  sessionStorage.setItem("debitPrefix", debit_ref_prefix);
//  const modalElement = document.getElementById('invoiceModal');
 $('#invoiceModal').modal('hide');
// let modal = bootstrap.Modal.getInstance(modalElement);

// if (!modal) {
//     modal = new bootstrap.Modal(modalElement);
// }

// modalElement.addEventListener('hidden.bs.modal', () => {
//     modal.show();  
// }, { once: true });
setTimeout(() => {
    $('#invoiceModal').modal('show');
}, 500);
// modal.hide();

  document.getElementById('modalCustomerName').textContent = customerName;
  document.getElementById('modalCustomerId').textContent = customerId;

  // Show loading in all tables
  const tables = ['currentTable', 'overdueTable', 'partialTable', 'paidTable', 'notoverdueTable', "pendingTable", "paymentTable", 'allTable'];
  tables.forEach(id => {
    const tbody = document.querySelector(`#${id} tbody`);
    const colspan = document.querySelector(`#${id} thead th`).parentElement.children.length;
    tbody.innerHTML = `<tr><td colspan="${colspan}" class="text-center">Loading...</td></tr>`;
  });

  // modal.show();

  // Collect filter values
    const getFilterValue = (id) => document.getElementById(id)?.value.trim() || null;

    

  try {
    // Fetch all statuses at once (you can optimize backend to accept "all" or multiple)
    const statuses = ['unpaid', 'overdue', 'partial', 'paid', 'notoverdue', 'all'];
    // const promises = statuses.map(status =>
    //   fetch(`${API_BASE}/v1/payment/invoices`, {
    //     method: 'POST',
    //     headers: { 
    //       'Content-Type': 'application/json',
    //       'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    //     },
    //     body: JSON.stringify({ customer_id: customerId, status, payment_term: payTerm })
    //   }).then(r => r.json())
    // );

    const promises = statuses.map(status => {
        const filters = {
          from_date: getFilterValue('filterFromDate'),
          to_date: getFilterValue('filterToDate'),
          supplier_name: getFilterValue('filterSupplier'),
          min_amount: getFilterValue('filterMinAmount')
            ? parseFloat(getFilterValue('filterMinAmount'))
            : null,
          max_amount: getFilterValue('filterMaxAmount')
            ? parseFloat(getFilterValue('filterMaxAmount'))
            : null,
          category_name: getFilterValue('category_name') || null,
          quick_filter: getFilterValue('filterQuick') || null,
          customer_id: customerId,
          payment_term: payTerm,
          status: status,
          debit_ref_prefix: debit_ref_prefix
        };

        // Remove null or empty values
        Object.keys(filters).forEach(key => {
          if (filters[key] === null || filters[key] === '') {
            delete filters[key];
          }
        });

        return fetch(`${API_BASE}/v1/payment/invoices`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${
              localStorage.getItem('token') || getCookie('access_token')
            }`
          },
          body: JSON.stringify(filters)
        }).then(r => r.json());
      });
    
      const filters = {
          from_date: getFilterValue('filterFromDate'),
          to_date: getFilterValue('filterToDate'),
          supplier_name: getFilterValue('filterSupplier'),
          min_amount: getFilterValue('filterMinAmount')
            ? parseFloat(getFilterValue('filterMinAmount'))
            : null,
          max_amount: getFilterValue('filterMaxAmount')
            ? parseFloat(getFilterValue('filterMaxAmount'))
            : null,
          category_name: getFilterValue('category_name') || null,
          quick_filter: getFilterValue('filterQuick') || null,
          customer_id: customerId,
          payment_term: payTerm,
          debit_ref_prefix: debit_ref_prefix,
          status: 'all'
        };
        // Remove null or empty values
        Object.keys(filters).forEach(key => {
          if (filters[key] === null || filters[key] === '') {
            delete filters[key];
          }
        });

    const Res = await fetch(`${API_BASE}/v1/payment/approvals`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`

                // Add any necessary authentication headers (e.g., 'Authorization')
            },
            body: JSON.stringify(filters)
        });
        const pendingRes = await Res.json();

        const filters1 = {
          from_date: getFilterValue('filterFromDate'),
          to_date: getFilterValue('filterToDate'),
          supplier_name: getFilterValue('filterSupplier'),
          min_amount: getFilterValue('filterMinAmount')
            ? parseFloat(getFilterValue('filterMinAmount'))
            : null,
          max_amount: getFilterValue('filterMaxAmount')
            ? parseFloat(getFilterValue('filterMaxAmount'))
            : null,
          category_name: getFilterValue('category_name') || null,
          quick_filter: getFilterValue('filterQuick') || null,
          customer_id: customerId,
          payment_term: payTerm,
          status: "payment",
          debit_ref_prefix: debit_ref_prefix
        };
        // Remove null or empty values
        Object.keys(filters1).forEach(key => {
          if (filters1[key] === null || filters1[key] === '') {
            delete filters1[key];
          }
        });

      const payRes = await fetch(`${API_BASE}/v1/payment/invoices`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`

                // Add any necessary authentication headers (e.g., 'Authorization')
            },
            body: JSON.stringify(filters1)
        });
        const paymentRes = await payRes.json();
    

    const [unpaidRes, overdueRes, partialRes, paidRes, notoverdueRes, allRes] = await Promise.all(promises);

    renderCurrentTable(unpaidRes.invoices || [], payTerm);
    renderOverdueTable(overdueRes.invoices || [], payTerm);
    rendernotOverdueTable(notoverdueRes.invoices || [], payTerm);
    renderPartialTable(partialRes.invoices || [], payTerm);
    renderPaidTable(paidRes.invoices || [], payTerm);
    renderPendingTable(pendingRes.clients || [], payTerm);
    renderPaymentTable(paymentRes.invoices || [], payTerm);
    renderAllTable(allRes.invoices || [], payTerm);

  } catch (err) {
    showToast('Failed to load invoices', 'danger');
    console.error(err);
  }
}


function renderCurrentTable1(invoices, payTerm) {
    const table = document.querySelector('#currentTable');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = invoices.length === 0
        ? '<tr><td colspan="10" class="text-center text-muted py-3">No current due invoices</td></tr>'
        : '';

    const selectAllCheckbox = document.getElementById('selectAllCurrent');

    // Remove previous listener to prevent duplicates
    // selectAllCheckbox.removeEventListener('change', handleSelectAll);
    // const selectAllCheckbox = document.getElementById('selectAllCurrent');

      if (selectAllCheckbox) {
          selectAllCheckbox.removeEventListener('change', handleSelectAll);
          selectAllCheckbox.addEventListener('change', handleSelectAll);
      }

    let selectedInvoiceAmount = 0;

    // --- Bulk Action Row ---
    const bulkActionRow = document.createElement('tr');
    bulkActionRow.id = 'currentBulkActionRow';
    bulkActionRow.className = 'table-info d-none';
    bulkActionRow.innerHTML = `
        <td colspan="10" class="p-3">
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center">
                    <span class="fw-bold me-3">Selected Total: <span id="selectedCurrentTotal" class="text-primary">${fmt(0)}</span></span>
                    <label for="paymentActionSelect" class="me-2">Action:</label>
                    <select id="paymentActionSelect" class="form-select form-select-sm w-auto me-3">
                        <option value="" disabled selected>Select Action</option>
                    </select>
                    <div id="partialPaymentGroup" class="input-group input-group-sm w-auto d-none">
                        <span class="input-group-text">Amount</span>
                        <input type="number" id="partialPaymentAmount" class="form-control" placeholder="0.00" min="0" step="0.01">
                    </div>
                </div>
                <button id="confirmPaymentBtn" class="btn btn-sm btn-success" disabled>Confirm Payment</button>
            </div>
        </td>
    `;
      
    // --- Populate Dropdown based on permissions ---
    const paymentActionSelect = bulkActionRow.querySelector('#paymentActionSelect');
    const partialPaymentGroup = bulkActionRow.querySelector('#partialPaymentGroup');
    const partialPaymentAmountInput = bulkActionRow.querySelector('#partialPaymentAmount');
    const confirmPaymentBtn = bulkActionRow.querySelector('#confirmPaymentBtn');

    // Add dropdown options dynamically
    paymentActionSelect.innerHTML = '<option value="" disabled selected>Select Action</option>';
    if (canShowAction('full_payment')) {
        const opt = document.createElement('option');
        opt.value = 'full';
        opt.textContent = 'Full Payment';
        paymentActionSelect.appendChild(opt);
    }
    if (canShowAction('partial_payment')) {
        const opt = document.createElement('option');
        opt.value = 'partial';
        opt.textContent = 'Partial Payment';
        paymentActionSelect.appendChild(opt);
    }

    // Initially disable confirm button if no permission
    confirmPaymentBtn.disabled = !canShowAction('confirm_payment');

    // --- Render invoice rows ---
    invoices.forEach(inv => {
        const tr = document.createElement('tr');
        const isOverdue = inv.updated_date_status === 1;
        const amountValue = parseFloat(inv.amount || inv.credit || 0) || 0;
        const amountBalance = parseFloat(inv.balance || 0) || 0;

        tr.innerHTML = `
            <td>${inv.invoice_date || '-'}</td>
            <td>${inv.ref_no || '-'}</td>
            <td>${inv.description || '-'}</td>
            <td>${fmt(amountValue)}</td>
            <td>${fmt(inv.debit || 0)}</td>
            <td>${fmt(amountBalance)}</td>
            <td>${isOverdue ? 'Overdue' : 'Current'}</td>
            <td>${inv.payment_status || '-'}</td>
            <td></td>
            <td></td>
        `;

        // 1️⃣ Revoke Button
        if (isOverdue && canShowAction('revoke')) {
            const revokeTd = tr.children[8];
            const revokeBtn = document.createElement('button');
            revokeBtn.className = 'btn btn-danger btn-sm revoke-btn';
            revokeBtn.dataset.ref = inv.ref_no;
            revokeBtn.textContent = 'Revoke';
            revokeBtn.addEventListener('click', () => handleRevoke(inv.ref_no, payTerm, tr));
            revokeTd.appendChild(revokeBtn);
        }

        // 2️⃣ Select Checkbox
        if (canShowAction('checkbox')) {
            const checkboxTd = tr.children[9];
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'current-row-checkbox';
            checkbox.dataset.amount = amountValue;
            checkbox.dataset.balance = amountBalance;
            checkbox.dataset.ref = inv.ref_no;

            checkbox.addEventListener('change', e => {
                const amt = parseFloat(e.target.dataset.balance) || 0;
                selectedInvoiceAmount += e.target.checked ? amt : -amt;
                updateSelectedTotalDisplay();
                checkPaymentValidity(); // Re-validate on selection change
            });

            checkboxTd.appendChild(checkbox);
        }

        tbody.appendChild(tr);
    });

    // Append bulk action row once (after all invoice rows)
    if (invoices.length > 0 && canShowAction('checkbox')) {
        tbody.appendChild(bulkActionRow);
    }

    // --- Update selected total display and validation ---
    function updateSelectedTotalDisplay() {
        const selectedCount = tbody.querySelectorAll('.current-row-checkbox:checked').length;
        bulkActionRow.querySelector('#selectedCurrentTotal').textContent = fmt(selectedInvoiceAmount);

        if (selectedCount > 0) {
            bulkActionRow.classList.remove('d-none');
            partialPaymentAmountInput.max = selectedInvoiceAmount;
            checkPaymentValidity(); // Important: recheck validity
        } else {
            bulkActionRow.classList.add('d-none');
            partialPaymentGroup.classList.add('d-none');
            partialPaymentAmountInput.value = '';
            confirmPaymentBtn.disabled = true;
            paymentActionSelect.value = '';
        }

        // Update Select All checkbox state
        if (selectedCount === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (selectedCount === invoices.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
    }

    // --- Validation for partial payment ---
    function checkPaymentValidity() {
        const action = paymentActionSelect.value;
        const amountInputValue = partialPaymentAmountInput.value.trim();
        const amount = parseFloat(amountInputValue);

        // Remove any previous invalid state
        partialPaymentAmountInput.classList.remove('is-invalid');

        if (action === 'full') {
            partialPaymentGroup.classList.add('d-none');
            confirmPaymentBtn.disabled = !canShowAction('confirm_payment');
            return;
        }

        if (action === 'partial') {
            partialPaymentGroup.classList.remove('d-none');

            if (isNaN(amount) || amount <= 0 || amount > selectedInvoiceAmount) {
                partialPaymentAmountInput.classList.add('is-invalid');
                confirmPaymentBtn.disabled = true;
            } else {
                partialPaymentAmountInput.classList.remove('is-invalid');
                confirmPaymentBtn.disabled = !canShowAction('confirm_payment');
            }
            return;
        }

        // No action selected
        confirmPaymentBtn.disabled = true;
    }

    // --- Action select change ---
    paymentActionSelect.addEventListener('change', () => {
        partialPaymentAmountInput.value = '';
        partialPaymentAmountInput.classList.remove('is-invalid');
        checkPaymentValidity();
    });

    // --- Real-time input validation for partial amount ---
    partialPaymentAmountInput.addEventListener('input', checkPaymentValidity);
    partialPaymentAmountInput.addEventListener('change', checkPaymentValidity);

    // --- Handle Select All ---
    function handleSelectAll(e) {
        const isChecked = e.target.checked;
        const checkboxes = tbody.querySelectorAll('.current-row-checkbox');
        selectedInvoiceAmount = 0;

        checkboxes.forEach(cb => {
            cb.checked = isChecked;
            if (isChecked) {
                selectedInvoiceAmount += parseFloat(cb.dataset.balance) || 0;
            }
        });

        updateSelectedTotalDisplay();
        checkPaymentValidity();
    }

    selectAllCheckbox.addEventListener('change', handleSelectAll);

    // --- Footer total row ---
    if (invoices.length > 0) {
        const tfoot = document.createElement('tr');
        const totalAmount = invoices.reduce((sum, inv) => sum + (parseFloat(inv.balance || 0) || 0), 0);
        tfoot.innerHTML = `
            <td colspan="7" class="text-end fw-bold">Total Current Due:</td>
            <td colspan="3" class="fw-bold text-primary text-end">${fmt(totalAmount)}</td>
        `;
        tbody.appendChild(tfoot);
    }
}


function renderCurrentTable(invoices, payTerm) {
    const table = document.querySelector('#currentTable');
    const tbody = table.querySelector('tbody');
    const selectAllCheckbox = document.getElementById('selectAllCurrent');

    // Clear previous rows
    tbody.innerHTML = invoices.length === 0
        ? '<tr><td colspan="10" class="text-center text-muted py-3">No current due invoices</td></tr>'
        : '';

    let selectedInvoiceAmount = 0;

    // ---------------- Bulk Action Row ----------------
    const bulkActionRow = document.createElement('tr');
    bulkActionRow.id = 'currentBulkActionRow';
    bulkActionRow.className = 'table-info d-none';
    bulkActionRow.innerHTML = `
        <td colspan="10" class="p-3">
            <div class="d-flex flex-column gap-2">

                <div class="d-flex align-items-center justify-content-between">
                    <div class="d-flex align-items-center">
                        <span class="fw-bold me-3">
                            Selected Total:
                            <span id="selectedCurrentTotal" class="text-primary">${fmt(0)}</span>
                        </span>

                        <label for="paymentActionSelect" class="me-2">Action:</label>
                        <select id="paymentActionSelect" class="form-select form-select-sm w-auto me-3">
                            <option value="" disabled selected>Select Action</option>
                        </select>

                        <div id="partialPaymentGroup" class="input-group input-group-sm w-auto d-none">
                            <span class="input-group-text">Amount</span>
                            <input type="number" id="partialPaymentAmount"
                                   class="form-control"
                                   placeholder="0.00"
                                   min="0"
                                   step="0.01">
                        </div>
                    </div>

                    <button id="confirmPaymentBtn"
                            class="btn btn-sm btn-success"
                            disabled>
                        Confirm Payment
                    </button>
                </div>

                <!-- Warning message -->
                <div id="paymentWarning" class="alert alert-warning py-2 mb-0 d-none">
                    <strong>Warning:</strong> You do not have permission to make payment.
                    Please contact your administrator.
                </div>

            </div>
        </td>
    `;

    const paymentActionSelect = bulkActionRow.querySelector('#paymentActionSelect');
    const partialPaymentGroup = bulkActionRow.querySelector('#partialPaymentGroup');
    const partialPaymentAmountInput = bulkActionRow.querySelector('#partialPaymentAmount');
    const confirmPaymentBtn = bulkActionRow.querySelector('#confirmPaymentBtn');
    const paymentWarning = bulkActionRow.querySelector('#paymentWarning');

    // ---------------- Helper: Warning Toggle ----------------
    function updatePaymentWarning() {
        if (confirmPaymentBtn.disabled) {
            paymentWarning.classList.remove('d-none');
        } else {
            paymentWarning.classList.add('d-none');
        }
    }

    // ---------------- Populate Dropdown ----------------
    if (canShowAction('full_payment')) {
        paymentActionSelect.appendChild(new Option('Full Payment', 'full'));
    }
    if (canShowAction('partial_payment')) {
        paymentActionSelect.appendChild(new Option('Partial Payment', 'partial'));
    }

    confirmPaymentBtn.disabled = !canShowAction('confirm_payment');
    updatePaymentWarning();

    // ---------------- Render Invoice Rows ----------------
    invoices.forEach(inv => {
        const tr = document.createElement('tr');
        const isOverdue = inv.updated_date_status === 1;
        const amountValue = parseFloat(inv.amount || inv.credit || 0) || 0;
        const balance = parseFloat(inv.balance || 0) || 0;

        tr.innerHTML = `
            <td>${inv.invoice_date || '-'}</td>
            <td>${inv.ref_no || '-'}</td>
            <td>${inv.description || '-'}</td>
            <td>${fmt(amountValue)}</td>
            <td>${fmt(inv.debit || 0)}</td>
            <td>${fmt(balance)}</td>
            <td>${inv.aging_bucket || '-'}</td>
            <td>${inv.payment_status || '-'}</td>
        `;

        // Revoke Button
        if (isOverdue && canShowAction('revoke')) {
            const actionTd = document.createElement('td');
            const btn = document.createElement('button');
            btn.className = 'btn btn-danger btn-sm revoke-btn';
            btn.textContent = 'Revoke';
            btn.onclick = () => handleRevoke(inv.ref_no, payTerm, tr);
            actionTd.appendChild(btn);
            tr.appendChild(actionTd);
        } else{
           const actionTd = document.createElement('td');
        
            tr.appendChild(actionTd);
        }

        // Checkbox
        if (canShowAction('checkbox')) {
            const cbTd = document.createElement('td');
            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.className = 'current-row-checkbox';
            cb.dataset.ref = inv.ref_no;
            cb.dataset.balance = balance;

            cb.addEventListener('change', () => {
                selectedInvoiceAmount += cb.checked ? balance : -balance;
                updateSelectedTotalDisplay();
                checkPaymentValidity();
            });

            cbTd.appendChild(cb);
            tr.appendChild(cbTd);
        }

        tbody.appendChild(tr);
    });

    if (invoices.length && canShowAction('checkbox')) {
        tbody.appendChild(bulkActionRow);
    }

    // ---------------- Helpers ----------------
    function updateSelectedTotalDisplay() {
        const checkboxes = tbody.querySelectorAll('.current-row-checkbox');
        const checked = tbody.querySelectorAll('.current-row-checkbox:checked').length;

        bulkActionRow.querySelector('#selectedCurrentTotal').textContent =
            fmt(selectedInvoiceAmount);

        if (checked > 0) {
            bulkActionRow.classList.remove('d-none');
            partialPaymentAmountInput.max = selectedInvoiceAmount;
        } else {
            bulkActionRow.classList.add('d-none');
            paymentActionSelect.value = '';
            partialPaymentGroup.classList.add('d-none');
            partialPaymentAmountInput.value = '';
            confirmPaymentBtn.disabled = true;
            // updatePaymentWarning();
        }

        // Select All sync
        if (selectAllCheckbox) {
            if (checked === 0) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            } else if (checked === checkboxes.length) {
                selectAllCheckbox.checked = true;
                selectAllCheckbox.indeterminate = false;
            } else {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = true;
            }
        }
    }

    function checkPaymentValidity() {
        const action = paymentActionSelect.value;
        const amount = parseFloat(partialPaymentAmountInput.value);

        partialPaymentAmountInput.classList.remove('is-invalid');

        if (action === 'full') {
            partialPaymentGroup.classList.add('d-none');
            confirmPaymentBtn.disabled = !canShowAction('confirm_payment');

            return;
        }

        if (action === 'partial') {
            partialPaymentGroup.classList.remove('d-none');

            if (!amount || amount <= 0 || amount > selectedInvoiceAmount) {
                partialPaymentAmountInput.classList.add('is-invalid');
                confirmPaymentBtn.disabled = true;
            } else {
                confirmPaymentBtn.disabled = !canShowAction('confirm_payment');
            }


            return;
        }

        confirmPaymentBtn.disabled = true;

    }

    paymentActionSelect.onchange = () => {
        partialPaymentAmountInput.value = '';
        checkPaymentValidity();
    };

    partialPaymentAmountInput.oninput = checkPaymentValidity;

    // ---------------- Select All ----------------
    function handleSelectAll(e) {
        const checked = e.target.checked;
        selectedInvoiceAmount = 0;

        tbody.querySelectorAll('.current-row-checkbox').forEach(cb => {
            cb.checked = checked;
            if (checked) {
                selectedInvoiceAmount += parseFloat(cb.dataset.balance) || 0;
            }
        });

        updateSelectedTotalDisplay();
        checkPaymentValidity();
    }

    if (selectAllCheckbox) {
        selectAllCheckbox.removeEventListener('change', handleSelectAll);
        selectAllCheckbox.addEventListener('change', handleSelectAll);
    }

    // ---------------- Footer Total ----------------
    if (invoices.length) {
        const total = invoices.reduce(
            (s, i) => s + (parseFloat(i.balance) || 0), 0
        );

        tbody.insertAdjacentHTML('beforeend', `
            <tr>
                <td colspan="7" class="text-end fw-bold">Total Current Due:</td>
                <td colspan="3" class="fw-bold text-primary text-end">
                    ${fmt(total)}
                </td>
            </tr>
        `);
    }
}


    // ⚠️ IMPORTANT: You must define a function to execute the payment logic
    // --- Event Delegation (Run this once, globally) ---
    document.addEventListener('click', function(e) {
      // Check if the clicked element has the ID 'confirmPaymentBtn'
      if (e.target.id === 'confirmPaymentBtn') {
        // Prevent the default button action
        e.preventDefault(); 
        
        // Call your handler function
        handleUpdatePaymentsofCurrentdue(e); 
      }
    });
    
    // Overdue Invoices
    function renderOverdueTable(invoices, payTerm) {
    const tbody = document.querySelector('#overdueTable tbody');
    tbody.innerHTML = invoices.length === 0
        ? '<tr><td colspan="7" class="text-center text-muted py-3">No overdue invoices</td></tr>'
        : '';

    invoices.forEach(inv => {
        const tr = document.createElement('tr');

        // Add standard columns
        tr.innerHTML = `
            <td>${inv.invoice_date || '-'}</td>
            <td>${inv.ref_no || '-'}</td>
            <td>${inv.description || '-'}</td>
            <td>${fmt(inv.amount || inv.credit || 0)}</td>
            <td>${inv.aging_bucket || '-'}</td>
            ${
              inv.days_overdue === 0
  ? 'Today'
  : inv.days_overdue < 0
    ? `${Math.abs(inv.days_overdue)} days left`
    : `${Math.abs(inv.days_overdue)} days overdue`

            }
        `;

        // Conditionally add Action button
        if (canShowAction('current_due')) {  // or whatever button you want
            const td = document.createElement('td');
            const btn = document.createElement('button');
            btn.className = 'btn btn-success btn-sm mark-overdue-btn';
            btn.dataset.ref = inv.ref_no;
            btn.textContent = 'Mark as Current Due';
            btn.addEventListener('click', () => handleUpdateAging(inv.ref_no, payTerm, tr));

            td.appendChild(btn);
            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    });

    // Add footer row for total
    const tfoot = document.createElement('tr');
    tfoot.innerHTML = `
        <td colspan="3" class="text-end fw-bold">Total Overdue:</td>
        <td colspan="3" class="fw-bold text-primary text-end">
            ${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.amount || inv.credit || 0) || 0), 0))}
        </td>
        <td colspan="1"</td>
    `;
    tbody.appendChild(tfoot);
}

    // Overdue Invoices
    function rendernotOverdueTable(invoices, payTerm) {
    const tbody = document.querySelector('#notoverdueTable tbody');
    tbody.innerHTML = invoices.length === 0
        ? '<tr><td colspan="9" class="text-center text-muted py-3">No not in overdue invoices</td></tr>'
        : '';

    invoices.forEach(inv => {
        const tr = document.createElement('tr');

        // Add standard columns
        tr.innerHTML = `
            <td>${inv.invoice_date || '-'}</td>
            <td>${inv.ref_no || '-'}</td>
            <td>${inv.description || '-'}</td>
            <td>${fmt(inv.amount || inv.credit || 0)}</td>
            <td>${fmt(inv.debit || 0)}</td>
          <td>${fmt(inv.balance || 0)}</td>
            <td>${inv.aging_bucket || '-'}</td>
            <td>
            ${
              inv.days_overdue === 0
  ? 'Today'
  : inv.days_overdue < 0
    ? `${Math.abs(inv.days_overdue)} days left`
    : `${Math.abs(inv.days_overdue)} days overdue`

            }
          </td>
          

        `;

        // Conditionally add Action button
        if (canShowAction('current_due')) {  // or whatever button you want
            const td = document.createElement('td');
            const btn = document.createElement('button');
            btn.className = 'btn btn-success btn-sm mark-overdue-btn';
            btn.dataset.ref = inv.ref_no;
            btn.textContent = 'Mark as Current Due';
            btn.addEventListener('click', () => handleUpdateAgingNew(inv.ref_no, payTerm, tr, inv.invoice_date, inv.days_overdue));

            td.appendChild(btn);
            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    });

    // Add footer row for total
    const tfoot = document.createElement('tr');
    tfoot.innerHTML = `
        <td colspan="2" class="text-end fw-bold">Total:</td>
        <td colspan="2" class="fw-bold text-primary text-end">
            ${fmt(invoices.reduce((sum, inv) => sum + (parseFloat( inv.credit || 0) || 0), 0))}
</td>
            <td colspan="1" class="fw-bold text-primary text-end">
            ${fmt(invoices.reduce((sum, inv) => sum + (parseFloat( inv.debit || 0) || 0), 0))}
</td>
            <td colspan="1" class="fw-bold text-primary text-end">
            ${fmt(invoices.reduce((sum, inv) => sum + (parseFloat( inv.balance || 0) || 0), 0))}
        </td>
        <td colspan="4"</td>
    `;
    tbody.appendChild(tfoot);
}


function renderPartialTable(invoices, payTerm) {
    const tbody = document.querySelector('#partialTable tbody');
    tbody.innerHTML = invoices.length === 0
        ? '<tr><td colspan="10" class="text-center text-muted py-3">No partially paid invoices</td></tr>'
        : '';

    invoices.forEach(inv => {
        const tr = document.createElement('tr');

        // Add standard columns
        tr.innerHTML = `
            <td>${inv.invoice_date || '-'}</td>
            <td>${inv.ref_no || '-'}</td>
            <td>${inv.description || '-'}</td>
            <td>${inv.debit_ref_no || '-'}</td>
            <td>${inv.debit_description || '-'}</td>
            <td>${fmt(inv.amount || inv.credit || 0)}</td>
            <td>${fmt(inv.debit || 0)}</td>
            <td>${fmt(inv.balance || 0)}</td>
            <td>${inv.aging_bucket || '-'}</td>
        `;

        // Conditionally add Action button
        if (canShowAction('current_due')) {  // Check the permission using your function
            const td = document.createElement('td');
            const btn = document.createElement('button');
            btn.className = 'btn btn-warning btn-sm mark-overdue-btn';
            btn.dataset.ref = inv.ref_no;
            btn.textContent = 'Mark as Current Due';
            btn.addEventListener('click', () => handleUpdateAging(inv.ref_no, payTerm, tr));

            td.appendChild(btn);
            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    });

    // Footer row for total balance
    const tfoot = document.createElement('tr');
    tfoot.innerHTML = `
        <td colspan="5" class="text-end fw-bold">Total Balance:</td>
        <td colspan="5" class="fw-bold text-primary text-end">
            ${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.balance || 0) || 0), 0))}
        </td>
    `;
    tbody.appendChild(tfoot);
}

    
    // Paid Invoices
    function renderPaidTable(invoices) {
      const tbody = document.querySelector('#paidTable tbody');
      tbody.innerHTML = invoices.length === 0
      ? '<tr><td colspan="7" class="text-center text-muted py-3">No paid invoices</td></tr>'
      : '';
      
      invoices.forEach(inv => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
      <td>${inv.payment_date || inv.invoice_date || '-'}</td>
      <td>${inv.ref_no || '-'}</td>
      <td>${inv.description || '-'}</td>
      <td>${inv.debit_ref_no || '-'}</td>
      <td>${inv.debit_description || '-'}</td>
      <td>${fmt(inv.amount || inv.credit || 0)}</td>
      <td>${fmt(inv.debit || inv.amount || 0)}</td>
      
    `;
        tbody.appendChild(tr);
      });
      tfoot=document.createElement('tr');
      tfoot.innerHTML=`
  <td colspan="3" class="text-end fw-bold">Total Paid:</td>
  <td colspan="4" class="fw-bold text-primary text-end">${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.debit || inv.amount || 0) || 0), 0))}</td>
`;
      tbody.appendChild(tfoot);
    }



function formatDateTime(dateTimeStr) {
  if (!dateTimeStr) return '-'; // handle null/undefined

  const dt = new Date(dateTimeStr);

  const year = dt.getFullYear();
  const month = String(dt.getMonth() + 1).padStart(2, '0');
  const day = String(dt.getDate()).padStart(2, '0');
  const hours = String(dt.getHours()).padStart(2, '0');
  const minutes = String(dt.getMinutes()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

      // Paid Invoices
    function renderPendingTable(invoices) {
      const tbody = document.querySelector('#pendingTable tbody');
      tbody.innerHTML = invoices.length === 0
      ? '<tr><td colspan="12" class="text-center text-muted py-3">No paid invoices</td></tr>'
      : '';
      
      invoices.forEach(inv => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
      <td>${inv.payment_date || inv.invoice_date || '-'}</td>
      <td>${inv.invoice_ref_no || '-'}</td>
      <td>${inv.description || '-'}</td>
      <td>${inv.debit_ref_no || '-'}</td>
      <td>${inv.debit_description || '-'}</td>
      <td>${fmt(inv.amount || inv.credit || 0)}</td>
      <td>${fmt(inv.debit || inv.amount || 0)}</td>
      <td>${fmt(inv.balance || 0)}</td>
      <td>${inv.payment_by || '-'}</td>
      <td>${formatDateTime(inv.payment_at) || '-'}</td>
      <td>${inv.approval_status || '-'}</td>
      <td>${inv.approved_by || '-'}</td>
      
    `;
        tbody.appendChild(tr);
      });
      tfoot=document.createElement('tr');
      tfoot.innerHTML=`
  <td colspan="5" class="text-end fw-bold">Total Paid:</td>
  <td colspan="2" class="fw-bold text-primary text-end">${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.debit || inv.amount || 0) || 0), 0))}</td>
  <td colspan="5"></td>
`;
      tbody.appendChild(tfoot);
    }
    

    function renderPaymentTable(invoices) {
      const tbody = document.querySelector('#paymentTable tbody');
      tbody.innerHTML = invoices.length === 0
      ? '<tr><td colspan="12" class="text-center text-muted py-3">No paid invoices</td></tr>'
      : '';
      
      invoices.forEach(inv => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
      <td>${inv.debit_date || inv.invoice_date || '-'}</td>
      <td>${inv.invoice_ref_no || '-'}</td>
      <td>${inv.debit_ref_no || '-'}</td>
      <td>${inv.debit_description || '-'}</td>
      <td>${fmt(inv.current_credit || inv.credit || 0)}</td>
      <td>${fmt(inv.debit || inv.amount || 0)}</td>
      <td>${fmt(inv.balance || 0)}</td>
      <td>${inv.payment_by || '-'}</td>
      <td>${formatDateTime(inv.created_at) || '-'}</td>
      <td>${inv.approval_status || '-'}</td>
      <td>${inv.approved_by || '-'}</td>
      
    `;
        tbody.appendChild(tr);
      });
      tfoot=document.createElement('tr');
      tfoot.innerHTML=`
  <td colspan="5" class="text-end fw-bold">Total Paid:</td>
  <td colspan="2" class="fw-bold text-primary text-end">${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.debit || inv.amount || 0) || 0), 0))}</td>
  <td colspan="5"></td>
`;
      tbody.appendChild(tfoot);
    }
    
function renderAllTable(invoices, payTerm) {
    const tbody = document.querySelector('#allTable tbody');
    tbody.innerHTML = invoices.length === 0
        ? '<tr><td colspan="10" class="text-center text-muted py-3">No invoices</td></tr>'
        : '';

    invoices.forEach(inv => {
        const tr = document.createElement('tr');
        const hasDebit = inv.debit_ref_no || inv.debit_description;

        // Add standard columns
        tr.innerHTML = `
            <td>${inv.invoice_date || inv.payment_date || '-'}</td>
            <td>${inv.ref_no || '-'}</td>
            <td>${inv.description || '-'}</td>
            <td>${hasDebit ? inv.debit_ref_no : '-'}</td>
            <td>${hasDebit ? inv.debit_description : '-'}</td>
            <td>${fmt(inv.amount || inv.credit || 0)}</td>
            <td>${inv.debit ? fmt(inv.debit) : '-'}</td>
            <td>${inv.balance !== undefined ? fmt(inv.balance) : '-'}</td>
            <td>${inv.aging_bucket || inv.updated_date_status || '-'}</td>
        `;

        // Conditionally add Action button
        if (inv.status !== 'paid' && inv.balance > 0 && canShowAction('current_due')) {
            const td = document.createElement('td');
            const btn = document.createElement('button');
            btn.className = 'btn btn-success btn-sm mark-overdue-btn';
            btn.dataset.ref = inv.ref_no;
            btn.textContent = 'Mark as Current Due';
            btn.addEventListener('click', () => handleUpdateAging(inv.ref_no, payTerm, tr));
            td.appendChild(btn);
            tr.appendChild(td);
        } else {
            // Append empty td to keep column alignment
            const td = document.createElement('td');
            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    });

    // Footer row for total
    const tfoot = document.createElement('tr');
    tfoot.innerHTML = `
        <td colspan="5" class="text-end fw-bold">Total Invoices:</td>
        <td colspan="5" class="fw-bold text-primary text-end">
            ${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.balance || 0) || 0), 0))}
        </td>
    `;
    tbody.appendChild(tfoot);
}

  // Shared: Mark as Current Due (calls /update-aging)
async function handleUpdateAging(refNo, payTerm, rowElement) {
  const btn = rowElement.querySelector('.mark-overdue-btn');
  btn.disabled = true;
  btn.textContent = 'Processing...';

  try {
    const res = await fetch(`${API_BASE}/v1/payment/update-aging`, {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
      },
      body: JSON.stringify({ reference_no: refNo, payment_term: payTerm, updated_by: getCookie('user_id') })
    });

    if (res.status === 401) {
              console.error('apiFetch: 401 Unauthorized - clearing token & redirecting');
              document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';  // Clear cookie
              window.location.href = '/';
          }
    const result = await res.json();

    if (result.success) {
      showToast(`Invoice ${refNo} updated to Overdue`, 'success');
      rowElement.remove();
      setTimeout(loadAging, 1200);
      customerId = sessionStorage.getItem("customerId");
      customerName = sessionStorage.getItem("customerName"); 
      payTerm = sessionStorage.getItem("payTerm");
      debitprefix = sessionStorage.getItem("debitPrefix");
      openInvoiceModal(customerId, customerName, payTerm, debitprefix);
    } else {
      showToast(result.message || 'Update failed', 'danger');
    }
  } catch (err) {
    showToast('Network error', 'danger');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Mark as Current Due';
  }
}

  // Shared: Mark as Current Due (calls /update-aging)
async function handleUpdateAgingNew(refNo, payTerm, rowElement, invoice_date, days_overdue) {
  const btn = rowElement.querySelector('.mark-overdue-btn');
  btn.disabled = true;
  btn.textContent = 'Processing...';

  try {
    const res = await fetch(`${API_BASE}/v1/payment/update-aging`, {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
      },
      body: JSON.stringify({ reference_no: refNo, payment_term: payTerm, updated_by: getCookie('user_id'),
        invoice_date: invoice_date, days_overdue: days_overdue
       })
    });

    if (res.status === 401) {
              console.error('apiFetch: 401 Unauthorized - clearing token & redirecting');
              document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';  // Clear cookie
              window.location.href = '/';
          }
    const result = await res.json();

    if (result.success) {
      showToast(`Invoice ${refNo} updated to Overdue`, 'success');
      rowElement.remove();
      setTimeout(loadAging, 1200);
      customerId = sessionStorage.getItem("customerId");
      customerName = sessionStorage.getItem("customerName"); 
      payTerm = sessionStorage.getItem("payTerm");
      debitprefix = sessionStorage.getItem("debitPrefix");
      openInvoiceModal(customerId, customerName, payTerm, debitprefix);
    } else {
      showToast(result.message || 'Update failed', 'danger');
    }
  } catch (err) {
    showToast('Network error', 'danger');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Mark as Current Due';
  }
}

    /**
    * Executes the payment clearance API call for selected current due invoices.
    *
    * NOTE: This function assumes it is triggered by the "Confirm Payment" button click
    * and retrieves the necessary data (selected invoices, payment action, amount)
    * directly from the DOM elements.
    * * @param {HTMLButtonElement} confirmBtn The button element that triggered the action.
    * @param {HTMLTableElement} tableElement The table containing the invoices.
  */
async function handleUpdatePaymentsofCurrentdue1() {
    // --- 1. Get DOM Elements and Payment Data ---
    const tableElement = document.getElementById('currentTable');
    const confirmBtn = document.getElementById('confirmPaymentBtn');
    const paymentActionSelect = document.getElementById('paymentActionSelect');
    const partialPaymentAmountInput = document.getElementById('partialPaymentAmount');
    
    // Check if the button exists and disable it immediately to prevent double-clicks
    if (!confirmBtn) return;
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Processing...';

    const selectedCheckboxes = tableElement.querySelectorAll('.current-row-checkbox:checked');
    const selectedAction = paymentActionSelect.value;
    
    // Safety check for selected invoices
    if (selectedCheckboxes.length === 0 || !selectedAction) {
        alert('Please select invoices and a payment action.');
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirm Payment';
        return;
    }
    
    // --- 2. Build the Request Payload ---
    const invoices = Array.from(selectedCheckboxes).map(cb => {
        // You'll need access to the client_id here, 
        // which might require adding a data-client-id attribute to your checkbox 
        // or retrieving it from a hidden field. For now, we use a placeholder.
        return {
            client_id: sessionStorage.getItem("customerId"), // Placeholder: Update this to retrieve actual client_id
            ref_no: cb.dataset.ref,
            balance: parseFloat(cb.dataset.amount) // The current balance/amount being paid
        };
    });

    let totalDebit = 0;
    let isPartial = false;

    if (selectedAction === 'full') {
        // Calculate total amount for full payment
        totalDebit = invoices.reduce((sum, inv) => sum + inv.balance, 0);
        isPartial = false;
    } else if (selectedAction === 'partial') {
        // Use the amount entered in the partial payment input
        totalDebit = parseFloat(partialPaymentAmountInput.value) || 0;
        isPartial = true;
        
        // Basic validation check
        if (totalDebit <= 0) {
            alert('Partial payment amount must be greater than zero.');
            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Confirm Payment';
            return;
        }
    }
    
    // The final payload structure
    const payload = {
        invoices: invoices,
        partial: isPartial,
        total_debit: totalDebit
    };
    
    console.log('API Payload:', payload); // Debugging: Check the data being sent

    // --- 3. Execute the API Call ---
    try {
        const res = await fetch(`${API_BASE}/v1/payments/clearance`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`

                // Add any necessary authentication headers (e.g., 'Authorization')
            },
            body: JSON.stringify(payload)
        });

        // Check for non-200 responses
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.message || `API call failed with status: ${res.status}`);
        }

        const result = await res.json();

      setTimeout(loadAging, 1200);
      customerId = sessionStorage.getItem("customerId");
      customerName = sessionStorage.getItem("customerName"); 
      payTerm = sessionStorage.getItem("payTerm");
      debitprefix = sessionStorage.getItem("debitPrefix");
      openInvoiceModal(customerId, customerName, payTerm, debitprefix);
      showToast(`Payment successful! `);
        // --- 4. Success Handling ---
        // Refresh the table or remove cleared rows based on the API response
        // e.g., location.reload() or renderCurrentTable(newInvoices, payTerm); 

    } catch (error) {
        // --- 5. Error Handling ---
        console.error('Payment clearance error:', error);
        showToast(`Payment failed: ${error.message}`);
    } finally {
        // Re-enable the button and reset text
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirm Payment';
    }
}


    async function handleUpdatePaymentsofCurrentdue() {
      // --- 1. Get DOM Elements and Payment Data ---
      const tableElement = document.getElementById('currentTable');
      const confirmBtn = document.getElementById('confirmPaymentBtn');
      const paymentActionSelect = document.getElementById('paymentActionSelect');
      const partialPaymentAmountInput = document.getElementById('partialPaymentAmount');
      
      // Check if the button exists and disable it immediately to prevent double-clicks
      if (!confirmBtn) return;
      confirmBtn.disabled = true;
      confirmBtn.textContent = 'Processing...';
      
      const selectedCheckboxes = tableElement.querySelectorAll('.current-row-checkbox:checked');
      const selectedAction = paymentActionSelect.value;
      
      // Safety check for selected invoices
      if (selectedCheckboxes.length === 0 || !selectedAction) {
        alert('Please select invoices and a payment action.');
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirm Payment';
        return;
      }
      
      // --- 2. Build the Request Payload ---
      const invoices = Array.from(selectedCheckboxes).map(cb => {
        // You'll need access to the client_id here, 
        // which might require adding a data-client-id attribute to your checkbox 
        // or retrieving it from a hidden field. For now, we use a placeholder.
        return {
          client_id: sessionStorage.getItem("customerId"), // Placeholder: Update this to retrieve actual client_id
          ref_no: cb.dataset.ref,
          balance: parseFloat(cb.dataset.balance) // The current balance/amount being paid
        };
      });
      
      let totalDebit = 0;
      let isPartial = false;
      
      if (selectedAction === 'full') {
        // Calculate total amount for full payment
        totalDebit = invoices.reduce((sum, inv) => sum + inv.balance, 0);
        isPartial = false;
      } else if (selectedAction === 'partial') {
        // Use the amount entered in the partial payment input
        totalDebit = parseFloat(partialPaymentAmountInput.value) || 0;
        isPartial = true;
        
        // Basic validation check
        if (totalDebit <= 0) {
          alert('Partial payment amount must be greater than zero.');
          confirmBtn.disabled = false;
          confirmBtn.textContent = 'Confirm Payment';
          return;
        }
      }
      console.log(sessionStorage.getItem("debitPrefix"))
      const debitprefix = sessionStorage.getItem("debitPrefix");
      console.log(debitprefix)
      // The final payload structure
      const payload = {
        invoices: invoices,
        partial: isPartial,
        total_debit: totalDebit,
        debit_ref_prefix: debitprefix,
        payment_by: getCookie('user_id'),
        created_by: getCookie('user_id'),
        updated_by: getCookie('user_id')
      };
      
      console.log('API Payload:', payload); // Debugging: Check the data being sent
      
      // --- 3. Execute the API Call ---
      try {
        const res = await fetch(`${API_BASE}/v1/payments/clearance`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`

                // Add any necessary authentication headers (e.g., 'Authorization')
            },
            body: JSON.stringify(payload)
        });

        
        // Check for non-200 responses
        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.message || `API call failed with status: ${res.status}`);
        }
        
        const result = await res.json();
        flagRevokeAlert = false;
        selectedCheckboxes.forEach(checkbox => {
  // go up to the row
          const row = checkbox.closest('tr');

          // get the td that contains the checkbox
          const checkboxTd = checkbox.closest('td');

          // get the previous td
          const buttonTd = checkboxTd.previousElementSibling;

          // find the button inside that td
          const button = buttonTd?.querySelector('button');

          // trigger it
          button?.click();
        });
        flagRevokeAlert = true;
        // handleRevoke(inv.ref_no, payTerm, tr)
        setTimeout(loadAging, 1200);
        customerId = sessionStorage.getItem("customerId");
        customerName = sessionStorage.getItem("customerName"); 
        payTerm = sessionStorage.getItem("payTerm");
        debitprefix1 = sessionStorage.getItem("debitPrefix");
        openInvoiceModal(customerId, customerName, payTerm, debitprefix1);
        showToast(`Payment successful! `);
        // --- 4. Success Handling ---
        // Refresh the table or remove cleared rows based on the API response
        // e.g., location.reload() or renderCurrentTable(newInvoices, payTerm); 
        
      } catch (error) {
        // --- 5. Error Handling ---
        console.error('Payment clearance error:', error);
        showToast(`Payment failed: ${error.message}`);
      } finally {
        // Re-enable the button and reset text
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirm Payment';
      }
    }
    
    
    // --- 6. Integration with Confirm Button (Necessary step) ---
    // This part ensures the function is called when the user confirms. 
    // You need to ensure this listener is attached AFTER the button is created 
    // (which happens in your renderCurrentTable function).
    
    
    
    // Example of how the fmt function should look (if not provided)
    /*
    function fmt(amount) {
    const numericAmount = parseFloat(amount) || 0;
    return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    }).format(numericAmount);
    }
    */
    // Shared: Revoke Overdue Status (calls /revoke-aging)
// Shared: Revoke Overdue Status (calls /revoke-aging)
flagRevokeAlert = true;
async function handleRevoke(refNo, payTerm, rowElement) {
  if (flagRevokeAlert) {
  if (!confirm(`Revoke overdue status for ${refNo}?`)) return;
  }

  const btn = rowElement.querySelector('.revoke-btn');
  btn.disabled = true;
  btn.textContent = 'Revoking...';

  try {
    const res = await fetch(`${API_BASE}/v1/payment/revoke-aging`, {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
       },
      body: JSON.stringify({ reference_no: refNo, payment_term: payTerm, updated_by: getCookie('user_id') })
    });
    if (res.status === 401) {
              console.error('apiFetch: 401 Unauthorized - clearing token & redirecting');
              document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';  // Clear cookie
              window.location.href = '/';
          }
    const result = await res.json();

    if (result.success) {
      showToast(`Overdue status revoked for ${refNo}`, 'info');
      rowElement.remove();
        customerId = sessionStorage.getItem("customerId");
      customerName = sessionStorage.getItem("customerName"); 
      payTerm = sessionStorage.getItem("payTerm");
      debitprefix = sessionStorage.getItem("debitPrefix");

      openInvoiceModal(customerId, customerName, payTerm, debitprefix);
      setTimeout(loadAging, 1200);
    } else {
      showToast(result.message || 'Revoke failed', 'danger');
    }
  } catch (err) {
    showToast('Network error', 'danger');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Revoke';
  }
}

    
      
  
      document.addEventListener("DOMContentLoaded", loadAging);
      
      
      
   
      // Helper: format currency (you probably already have this)
      function fmt(num) {
        return new Intl.NumberFormat('en-US', { 
          minimumFractionDigits: 2, 
          maximumFractionDigits: 2 
        }).format(num);
      }
      
      $(document).on('hidden.bs.modal', '.modal', function () {
    $(this).find('input[type="checkbox"]').prop('checked', false);
});


  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  function updateMonthUI(dateValue = null) {
    let dateObj;

    if (dateValue) {
      // Expecting format YYYY-MM-DD
      dateObj = new Date(dateValue);
    } else {
      // Default to current date
      dateObj = new Date();
    }

    const monthName = months[dateObj.getMonth()];

    // Update all UI elements
    document.getElementById("monthPayment").textContent =
      `${monthName} Payment`;
    document.getElementById("monthPayment").setAttribute(
      "title",
      `Client’s total payable for ${monthName}.`
    );

    document.getElementById("paymentTabLink").textContent =
      `${monthName} Payment`;

    document.getElementById("currentMonthLabel").textContent =
      `${monthName} Payment:`;

    document.getElementById("currentMonthTooltip").textContent =
      `Client’s total payable for ${monthName}.`;

    document.getElementById("totalPaymentText").textContent =
      `Total ${monthName} Payments`;
  }

  // Initial load → current month
  updateMonthUI();

