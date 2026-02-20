 
 // Helper: Format amount or show "-"
 function fmt(val) {
    const num = parseFloat(val);
    return isNaN(num) || num === 0 ? '-' : parseFloat(num.toFixed(2)).toLocaleString();
}

function canShowAction(ButtonName) {
    const extract = USER_MENUS.extract.buttons;

    if (!extract) return false;

    if (Array.isArray(extract)) {
        const buttonNames = extract.map(item => item.button_name);
        return buttonNames.includes(ButtonName);
    }

    if (typeof extract === 'object' && 'button_name' in extract) {
        return extract.button_name === ButtonName;
    }

    return false;
}

$(document).ready(function (){
    $('.btn-close,.btn-close1').on('click',function(){
      console.log('test')

      const statusEll = document.querySelector('.save-single');
    statusEll.disabled = false;
    statusEll.innerHTML = '<i class="bi bi-cloud-check"></i> Save';
  })

})
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


async function saveStatement(data, filename) {
  const pay_term_status = data.pay_term_status;
  const category_status = data.category_status;

  // CASE 1: BOTH FALSE → modal required
  if (!pay_term_status && !category_status) {

    const modalResult = await openExtractModal(data);

    if (modalResult.action === "cancel") {
      return { success: false, error: "User cancelled", filename };
    }

    data.term = modalResult.term;
    data.merchant_category = modalResult.cat;
  }

  // CASE 2: term true, category false
  else if (pay_term_status && !category_status) {

    const modalResult = await openExtractModal(data, {
      term: Number.isInteger(data.term) ? data.term : "",
      category: ""
    });

    if (modalResult.action === "cancel") {
      return { success: false, error: "User cancelled", filename };
    }

    data.merchant_category = modalResult.cat;
  }

  // CASE 3: term false, category true
  else if (!pay_term_status && category_status) {

    const modalResult = await openExtractModal(data, {
      term: "",
      category: data.merchant_category || ""
    });

    if (modalResult.action === "cancel") {
      return { success: false, error: "User cancelled", filename };
    }

    data.term = modalResult.term;
  }

  // ---------- ORIGINAL SAVE STATEMENT PAYLOAD ----------
  const payload = {
    invoice: {
      customer_id: data.customer_id,
      vendor_name: data.vendor_name || null,
      vendor_address: data.vendor_address || null,
      customer_name: data.customer_name || null,
      customer_address: data.customer_address || null,
      term: data.term || null,
      merchant_category: data.merchant_category,
      total_amount: parseFloat(data.total_amount) || 0,
      total_amount_text: data.total_amount_text || null,
      current: parseFloat(data.current) || 0,
      month_2: parseFloat(data.month_2) || 0,
      month_3: parseFloat(data.month_3) || 0,
      month_4: parseFloat(data.month_4) || 0,
      month_5: parseFloat(data.month_5) || 0,
      month_6: parseFloat(data.month_6) || 0,
      month_7: parseFloat(data.month_7) || 0,
      month_8: parseFloat(data.month_8) || 0,
      month_9: parseFloat(data.month_9) || 0,
      month_10: parseFloat(data.month_10) || 0,
      month_11: parseFloat(data.month_11) || 0,
      created_by: getCookie('user_id'),
      updated_by: getCookie('user_id')
    },
    items: (data.table || []).map(row => ({
      customer_id: data.customer_id,
      transaction_date: row.DATE ? parseDate(row.DATE).toISOString().split("T")[0] : null,
      ref_no: row["REF NO"] || row.ref_no || null,
      description: row.DESCRIPTION || null,
      debit: parseFloat(row.DEBIT) || 0,
      credit: parseFloat(row.CREDIT) || 0,
      balance: parseFloat(row.BALANCE) || 0
    })).filter(i => i.ref_no),
    payable_aging: (data.payable_data || []).map(p => ({
      customer_id: data.customer_id,
      invoice_date: p.DATE ? parseDate(p.DATE).toISOString().split("T")[0] : null,
      ref_no: p["REF NO"] || null,
      description: p.DESCRIPTION || null,
      credit: parseFloat(p.CREDIT) || 0,
      debit: parseFloat(p.DEBIT) || 0,
      debit_description: p.DEBIT_DESCRIPTION || null,
      debit_ref_no: p.DEBIT_REF_NO || null,
      debit_date: p.DEBIT_DATE ? parseDate(p.DEBIT_DATE).toISOString().split("T")[0] : null,
      paid_amount: parseFloat(p.PAID_AMOUNT) || 0,
      balance: parseFloat(p.BALANCE) || 0,
      status: p.STATUS || 0,
      approval_status: p.APPROVAL_STATUS || "PENDING",
      approved_by: p.APPROVED_BY,
      payment_by: p.PAYMENT_BY
    })).filter(p => p.ref_no)
  };

  try {
    const res = await fetch(`${API_BASE}/v1/extract/save-remittances`, {
      method: "PUT",
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
      },
      body: JSON.stringify(payload)
    });

    if (res.status === 403) {
          showToast(message = "This user doesn’t have permission to access the Save right now.", type = 'warning')
            }
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Save failed");

    return { success: true, message: result.message || "Saved", filename };

  } catch (err) {
    return { success: false, error: err.message, filename };
  }
}

function openExtractModal(data, prefill = {}) {
  loadCategoryList('modal_merchant_category')
  return new Promise((resolve) => {

    // Fill static data
    document.getElementById("modal_client_id").value = data.customer_id;
    document.getElementById("modal_client_name").value = data.customer_name;
    document.getElementById("modal_client_address").value = data.customer_address;

    // Prefill based on condition
    document.getElementById("modal_payment_term").value = prefill.term ?? "";
    document.getElementById("modal_merchant_category").value = prefill.category ?? "";

    const modalEl = document.getElementById("extractModal");
    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();

    // CANCEL button
    document.getElementById("modal_cancel_btn").onclick = () => {
      resolve({ action: "cancel" });
    };

    // SAVE button
    document.getElementById("modal_save_btn").onclick = async () => {

      const term = document.getElementById("modal_payment_term").value.trim();
      const cat = document.getElementById("modal_merchant_category").value.trim();
      const address_ = document.getElementById("modal_client_address").value.trim();
      const customer_id = document.getElementById("modal_client_id").value.trim();
      const client_name = document.getElementById("modal_client_name").value.trim();

      if (!term || !cat || !address_ || !customer_id || !client_name ) {
        alert("All fields are required!");
        return;
      }

      const payload = {
        client_id: customer_id,
        name: client_name,
        address: address_,
        pay_term: Number(term),
        merchant_category: cat
      };

      try {
    const res = await fetch(`${API_BASE}/v1/client/insert`, {
      method: "PUT",
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
      },
      body: JSON.stringify(payload)
    });

        const result = await res.json();
        if (!res.ok) throw new Error(result.error || "Insert failed");

        alert("Client saved successfully!");

        bsModal.hide();
        resolve({ action: "save", term, cat });

      } catch (err) {
        alert("Error: " + err.message);
      }
    };
  });
}



// ======================== CREATE INVOICE CARD WITH SAVE BUTTON ========================
// Smart date parser — handles DD/MM/YYYY, DD-MM-YYYY, and ISO
function parseDate(dateStr) {
    if (!dateStr) return null;
    const s = dateStr.toString().trim();
    
    // If already ISO or valid JS date, return as-is
    const isoDate = new Date(s);
    if (!isNaN(isoDate.getTime())) return isoDate;
    
    // Try DD/MM/YYYY or DD-MM-YYYY
    const parts = s.match(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/);
    if (parts) {
        // parts[1] = day, parts[2] = month, parts[3] = year
        return new Date(parts[3], parts[2] - 1, parts[1]); // month is 0-indexed
    }
    
    return null; // fallback
}

function createInvoiceCard(data, filename) {
    const card = document.createElement('div');
    card.className = 'card shadow-sm mb-4 border-0';
    card.dataset.customerId = data.customer_id || '';
    card.__extractedData = data; // For bulk save

    var totalCredit_Payable = 0;
    var totalDebit_Payable = 0;
    var totalPaidAmount_Payable = 0;
    var totalBalance_Payable = 0;

    var totalDebit=0;
    var totalCredit=0;
    var lastBalance=0;
    
    card.innerHTML = `
    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
      <h5 class="mb-0">
        <i class="bi bi-file-earmark-text"></i> ${data.vendor_name || 'Vendor Invoice'}
      </h5>
      <div>
  ${canShowAction('save') ? `
    <button class="btn btn-light btn-sm me-2 save-single" title="Save this statement">
      <i class="bi bi-cloud-check"></i> Save
    </button>
  ` : ''}

  ${canShowAction('download') ? `
    <button class="btn btn-light btn-sm download-pdf">
      <i class="bi bi-download"></i> PDF
    </button>
  ` : ''}
</div>

      
    </div>
    <div class="card-body invoice-content" style="font-size: 14px;">
      <div class="row mb-4">
        <div class="col-md-6">
          <strong>From:</strong><br>
          <strong>${data.vendor_name || ''}</strong><br>
          ${data.vendor_address?.replace(/\n/g, '<br>') || ''}
        </div>
        <div class="col-md-6 text-md-end">
          <strong>To:</strong><br>
          <strong>${data.customer_name || ''} (${data.customer_id || 'N/A'})</strong><br>
          ${data.customer_address?.replace(/\n/g, '<br>') || ''}
        </div>
      </div>
      <div class="row mb-4">
        <div class="col-md-6">
          <strong>Payment Terms:</strong> ${data.term || 'N/A'} days<br>
          <strong>Statement Period:</strong> ${data.period || 'N/A'}
        </div>
        <div class="col-md-6 text-md-end">
          <h4 class="text-primary">Total Payable: <strong>${parseFloat(data.total_amount || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}</strong></h4>
          <p class="text-muted">${data.total_amount_text || ''}</p>
          </div>
      </div>
    
      <div class="row text-center mb-4">
        <div class="col border p-3 rounded bg-light"><small class="text-muted">Current</small><br><strong>${parseFloat(data.current || 0).toLocaleString()}</strong></div>
        ${[2,3,4,5,6,7,8,9,10,11].map(i => `
          <div class="col border p-3 rounded ${data[`month_${i}`] > 0 ? 'bg-warning text-dark' : 'bg-light'}">
            <small class="text-muted">Month ${i}</small><br>
            <strong>${parseFloat(data[`month_${i}`] || 0).toLocaleString()}</strong>
          </div>`).join('')}
      </div>
    </div>
      <h6 class="border-bottom pb-2">Transaction Details</h6>
     
      <div class="table-responsive" class="fixed-table-wrapper" style="width:101.2%;max-height: 450px;">
        <table class="table table-sm table-bordered">
         <thead class="table-light"><tr><th style="width:10%">Date</th><th style="width:10%">Ref No</th><th style="width:50%">Description</th><th style="width:10%">Debit</th><th style="width:10%">Credit</th><th style="width:10%">Balance</th></tr></thead>
       
             <tbody>
            ${data.table?.map(row => `
              <tr>
       
                <td style="width:10%">${row.DATE ? parseDate(row.DATE).toLocaleDateString('en-GB') : '-'}</td>               
                <td style="width:10%">${row['REF NO'] || '-'}</td>
                <td style="width:50%">${row.DESCRIPTION || '-'}</td>
                <td style="width:10%" class="text-end">${fmt(row.DEBIT)}</td>
                <td style="width:10%" class="text-end text-success">${fmt(row.CREDIT)}</td>
                <td style="width:10%" class="text-end fw-bold">${fmt(row.BALANCE)}</td>
              </tr>`).join('') || '<tr><td colspan="6" class="text-center text-muted">No transactions</td></tr>'}
          </tbody>
          ${(() => {
       
                 totalDebit = data.table?.reduce((sum, r) => sum + (parseFloat(r.DEBIT) || 0), 0) || 0;
                 totalCredit = data.table?.reduce((sum, r) => sum + (parseFloat(r.CREDIT) || 0), 0) || 0;
                 lastBalance =
                data.table?.length
                  ? parseFloat(data.table[data.table.length - 1].BALANCE) || 0
                  : 0;


                  return `
                    
                  `;
                })()}

                <tfoot>
                            <tr class="table-light fw-bold">
                              
                              <td style="width:70%;" colspan="3" class="text-end">Total</td>
                              <td style="width:10%;" class="text-end">${fmt(totalDebit)}</td>
                              <td style="width:10%;" class="text-end text-success">${fmt(totalCredit)}</td>
                              <td style="width:10%;" class="text-end">${fmt(lastBalance)}</td>

                             
                            </tr>
                          </tfoot>
        </table>

   
           
       </div>
    
  <!-- Payable Details -->
        ${data.payable_data && data.payable_data.length > 0 ? `
          <h6 class="border-bottom pb-2 mt-5">Outstanding Invoices</h6>

      
          <div class="table-responsive" class="fixed-table-wrapper" style="width:101.2%;max-height: 450px;">
            <table class="table table-sm table-bordered">
              <thead class="table-warning">
                <tr>
                  <th style="width:10%;">Date</th>
                  <th  style="width:10%;">Ref No</th>
                  <th  style="width:30%;">Description</th>
                  <th  style="width:10%;">Credit</th>
                  <th  style="width:10%;">Debit</th>
                  <th  style="width:10%;">Paid</th>
                  <th  style="width:10%;">Balance</th>
                  <th  style="width:10%;">Status</th>
                </tr>
              </thead>

              <tbody>
                ${data.payable_data.map(p => `
                  <tr class="${p.STATUS === 'Open' ? 'table-danger' : ''}">
                    <td style="width:10%;">${p.DATE ? new Date(p.DATE).toLocaleDateString('en-GB') : '-'}</td>
                    <td style="width:10%;">${p['REF NO'] || p.DEBIT_REF_NO || '-'}</td>
                    <td style="width:30%;">${p.DESCRIPTION || p.DEBIT_DESCRIPTION || '-'}</td>
                    <td style="width:10%;" class="text-end">${fmt(p.CREDIT)}</td>
                    <td style="width:10%;" class="text-end">${fmt(p.DEBIT)}</td>
                    <td style="width:10%;" class="text-end">${fmt(p.PAID_AMOUNT)}</td>
                    <td style="width:10%;" class="text-end fw-bold">${fmt(p.BALANCE)}</td>
                    <td style="width:10%;text-align: center;">
    <span class="badge ${p.STATUS ? 'bg-success' : 'bg-danger'}">
        ${p.STATUS ? 'Paid' : 'Open'}
    </span>
</td>                  </tr>
                `).join('')}
              </tbody>
              ${(() => {
                
                       totalCredit_Payable      = data.payable_data?.reduce((s,p) => s + (parseFloat(p.CREDIT) || 0), 0) || 0;
                       totalDebit_Payable         = data.payable_data?.reduce((s,p) => s + (parseFloat(p.DEBIT) || 0), 0) || 0;
                       totalPaidAmount_Payable    = data.payable_data?.reduce((s,p) => s + (parseFloat(p.PAID_AMOUNT) || 0), 0) || 0;
                       totalBalance_Payable       = data.payable_data?.reduce((s,p) => s + (parseFloat(p.BALANCE) || 0), 0) || 0;

                        return `
                          
                        `;
                      })()}

                       <tfoot> 
                           <tr class="table-light fw-bold">
                              <td style="width:50%;" colspan="3" class="text-end">Total</td>

                              <td style="width:10%;" class="text-end">${fmt(totalCredit_Payable)}</td>
                              <td  style="width:10%;" class="text-end">${fmt(totalDebit_Payable )}</td>
                              <td style="width:10%;" class="text-end">${fmt(totalPaidAmount_Payable )}</td>
                              <td style="width:10%;" class="text-end">${fmt(totalBalance_Payable)}</td>

                              <td style="width:10%;"></td>
                            </tr>
                          </tfoot>
            </table>
          </div>
        ` : ''}
  
    
      
      <strong>Customer ID:</strong> ${data.customer_id || 'N/A'} | File: ${filename}
      <span class="save-status float-end"></span>
    </div>
    `;
    
    // Save Button
//     card.querySelector('.save-single').addEventListener('click', async function () {
//         const btn = this;
//         const statusEl = card.querySelector('.save-status');
//         btn.disabled = true;
//         btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';
//         const result = await saveStatement(data, filename);
//         if (result.success) {
//             statusEl.innerHTML = '<i class="bi bi-check-circle text-success"></i> Saved';
//             showToast(`Saved: ${data.vendor_name || filename}`, 'success');
//         } else {
//             statusEl.innerHTML = '<i class="bi bi-x-circle text-danger"></i> Failed';
//             showToast(`Save failed: ${result.error}`, 'danger');
//         }
//         btn.disabled = false;
//         btn.innerHTML = '<i class="bi bi-cloud-check"></i> Save';
//     });
    
//     // PDF Button
//     card.querySelector('.download-pdf').addEventListener('click', function () {
//         const element = card.querySelector('.invoice-content');
//         html2pdf().set({
//             margin: 0.5,
//             filename: `${data.customer_id || 'Invoice'}_${data.vendor_name || 'Vendor'}.pdf`,
//             image: { type: 'jpeg', quality: 0.98 },
//             html2canvas: { scale: 2 },
//             jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
//         }).from(element).save();
//     });
  // Save Button (permission-safe)
const saveBtn = card.querySelector('.save-single');
if (saveBtn) {
  saveBtn.addEventListener('click', async function () {
    const btn = this;
    const statusEl = card.querySelector('.save-status');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';

    const result = await saveStatement(data, filename);

    if (result.success) {
      statusEl.innerHTML = '<i class="bi bi-check-circle text-success"></i> Saved';
      showToast(`Saved: ${data.vendor_name || filename}`, 'success');
    } else {
      statusEl.innerHTML = '<i class="bi bi-x-circle text-danger"></i> Failed';
      showToast(`Save failed: ${result.error}`, 'danger');
    }

    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-cloud-check"></i> Save';
  });
}

// PDF Button (permission-safe)
const pdfBtn = card.querySelector('.download-pdf');
if (pdfBtn) {
  pdfBtn.addEventListener('click', function () {
    const element = card.querySelector('.invoice-content');
    html2pdf().set({
      margin: 0.5,
      filename: `${data.customer_id || 'Invoice'}_${data.vendor_name || 'Vendor'}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    }).from(element).save();
  });
}

    
    return card;
}



function getFilenameFromCard(card) {
    const footer = card.querySelector('.card-footer');
    if (!footer) return 'Unknown File';
    const match = footer.textContent.match(/File:\s*([^|]+?)\s*(?:\||$)/);
    return match ? match[1].trim() : 'Unknown File';
}


function addBulkSaveButton1() {
    // Prevent duplicate button
    if (document.getElementById('bulkSaveBtn')) return;
    
    const div = document.createElement('div');
    div.className = 'text-center mb-4';
    div.innerHTML = `
    <button id="bulkSaveBtn" class="btn btn-success btn-lg px-5">
      <i class="bi bi-cloud-upload"></i> Save All Statements
    </button>
    <div id="bulkProgress" class="mt-3 fw-bold"></div>
  `;
    document.getElementById('resultsContainer').before(div);
    
    document.getElementById('bulkSaveBtn').addEventListener('click', async () => {
        const cards = document.querySelectorAll('#resultsContainer .card');
        if (cards.length === 0) {
            showToast('No statements to save', 'info');
            return;
        }
        
        const btn = document.getElementById('bulkSaveBtn');
        const progress = document.getElementById('bulkProgress');
        btn.disabled = true;
        btn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Saving All...';
        progress.innerHTML = '';
        
        let success = 0, failed = 0;
        
        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            const data = card.__extractedData;           // ← stored when card created
            const filename = getFilenameFromCard(card);  // ← fixed extraction
            
            progress.innerHTML = `
        <div class="text-primary">
          Saving ${i + 1} of ${cards.length} → 
          <strong>${data.customer_id || '??'}</strong> 
          (${filename})
        </div>`;
            
            const result = await saveStatement(data, filename);
            
            const statusEl = card.querySelector('.save-status');
            if (result.success) {
                success++;
                statusEl.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i> Saved';
            } else {
                failed++;
                statusEl.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i> Failed';
                console.error(`Save failed for ${data.customer_id}:`, result.error);
            }
        }
        
        progress.innerHTML = `<strong class="text-success">Completed! ${success} saved, ${failed} failed</strong>`;
        btn.innerHTML = '<i class="bi bi-check2-all"></i> Save All Complete';
        btn.disabled = false;
        
        showToast(`Bulk save finished: ${success} succeeded${failed ? `, ${failed} failed` : ''}`, 
            failed === 0 ? 'success' : 'warning');
        });
    }
    
function addBulkSaveButton() {
    // 🔐 Permission check
    if (!canShowAction('save')) return;

    // Prevent duplicate button
    if (document.getElementById('bulkSaveBtn')) return;

    const div = document.createElement('div');
    div.className = 'text-center mb-4';
    div.innerHTML = `
      <button id="bulkSaveBtn" class="btn btn-success btn-lg px-5">
        <i class="bi bi-cloud-upload"></i> Save All Statements
      </button>
      <div id="bulkProgress" class="mt-3 fw-bold"></div>
    `;

    document.getElementById('resultsContainer').before(div);

    document.getElementById('bulkSaveBtn').addEventListener('click', async () => {
        const cards = document.querySelectorAll('#resultsContainer .card');

        if (cards.length === 0) {
            showToast('No statements to save', 'info');
            return;
        }

        const btn = document.getElementById('bulkSaveBtn');
        const progress = document.getElementById('bulkProgress');

        btn.disabled = true;
        btn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Saving All...';
        progress.innerHTML = '';

        let success = 0, failed = 0;

        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            const data = card.__extractedData;
            const filename = getFilenameFromCard(card);

            progress.innerHTML = `
              <div class="text-primary">
                Saving ${i + 1} of ${cards.length} →
                <strong>${data.customer_id || '??'}</strong>
                (${filename})
              </div>
            `;

            const result = await saveStatement(data, filename);
            const statusEl = card.querySelector('.save-status');

            if (result.success) {
                success++;
                if (statusEl) {
                    statusEl.innerHTML =
                        '<i class="bi bi-check-circle-fill text-success"></i> Saved';
                }
            } else {
                failed++;
                if (statusEl) {
                    statusEl.innerHTML =
                        '<i class="bi bi-x-circle-fill text-danger"></i> Failed';
                }
                console.error(`Save failed for ${data.customer_id}:`, result.error);
            }
        }

        progress.innerHTML = `
          <strong class="text-success">
            Completed! ${success} saved, ${failed} failed
          </strong>
        `;

        btn.innerHTML = '<i class="bi bi-check2-all"></i> Save All Complete';
        btn.disabled = false;

        showToast(
            `Bulk save finished: ${success} succeeded${failed ? `, ${failed} failed` : ''}`,
            failed === 0 ? 'success' : 'warning'
        );
    });
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

  

    // Extract Tab Logic
    document.addEventListener('DOMContentLoaded', function () {
        const fileInput = document.getElementById('fileInput');
        const selectFilesBtn = document.getElementById('selectFiles');
        const dropZone = document.getElementById('dropZone');
        const resultsContainer = document.getElementById('resultsContainer');
        const uploadProgress = document.getElementById('uploadProgress');
        
        selectFilesBtn.addEventListener('click', () => fileInput.click());
        
        ['dragover', 'dragenter'].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('border-primary', 'bg-light'); }));
        ['dragleave', 'dragend'].forEach(e => dropZone.addEventListener(e, () => dropZone.classList.remove('border-primary', 'bg-light')));
        dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('border-primary', 'bg-light'); if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files); });
        fileInput.addEventListener('change', () => { if (fileInput.files.length) handleFiles(fileInput.files); });
        
        window.handleFiles = async function(files) {
            const validFiles = Array.from(files).filter(f => f.name.match(/\.(xlsx|xls)$/i));
            if (validFiles.length === 0) return alert('Please upload Excel files only');
            
            uploadProgress.classList.remove('d-none');
            resultsContainer.innerHTML = '';
            
            const formData = new FormData();
            validFiles.forEach((f, i) => formData.append(`file${i + 1}`, f));
            
            try {
              const response = await fetch(`${API_BASE}/v1/extract/remittances`,
              { 
                method: 'POST', 
                headers: {
                'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
              },
                body: formData});

              if (response.status === 403) {
                showToast(message = "This user doesn’t have permission to access this menu right now.", type = 'danger')
            }
              if (response.status === 401) {
                        console.error('apiFetch: 401 Unauthorized - clearing token & redirecting');
                        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';  // Clear cookie
                        window.location.href = '/';
                    }
                if (!response.ok) throw new Error(`Server error: ${response.status}`);
                const outputData = await response.json();
                
                outputData.forEach(item => {
                    const result = item.response;
                    const filename = item.filename || 'Unknown File';
                    const card = createInvoiceCard(result, filename);
                    card.__extractedData = result;
                    resultsContainer.appendChild(card);
                });
                
                if (outputData.length > 0) addBulkSaveButton();
                showToast(`${outputData.length} statement(s) processed successfully`, 'success');
            } catch (err) {
                resultsContainer.innerHTML = `<div class="alert alert-danger">Upload Failed: ${err.message}</div>`;
            } finally {
                uploadProgress.classList.add('d-none');
                fileInput.value = '';
            }
        };
        
        
        
        function createInvoiceCard1(data, filename) {
            const card = document.createElement('div');
            card.className = 'card shadow-sm mb-4 border-0';
            card.innerHTML = `
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
          <i class="bi bi-file-earmark-text"></i> ${data.vendor_name || 'Vendor Invoice'}
        </h5>
        <button class="btn btn-light btn-sm download-pdf" data-filename="${filename.replace('.xlsx', 'pdf')}">
          <i class="bi bi-download"></i> Download PDF
        </button>
      </div>
      <div class="card-body invoice-content" style="font-size: 14px;">
        <div class="row mb-4">
          <div class="col-md-6">
            <strong>From:</strong><br>
            <strong>${data.vendor_name}</strong><br>
            ${data.vendor_address?.replace(/\n/g, '<br>') || ''}
          </div>
          <div class="col-md-6 text-md-end">
            <strong>To:</strong><br>
            <strong>${data.customer_name} (${data.customer_id})</strong><br>
            ${data.customer_address?.replace(/\n/g, '<br>') || ''}
          </div>
        </div>
            
        <div class="row mb-4">
          <div class="col-md-6">
            <strong>Payment Terms:</strong> ${data.term || 'N/A'} days<br>
            <strong>Statement Period:</strong> ${data.period || 'N/A'}
          </div>
          <div class="col-md-6 text-md-end">
            <h4 class="text-primary">Total Payable: <strong>${parseFloat(data.total_amount || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}</strong></h4>
            <p class="text-muted">${data.total_amount_text || ''}</p>
          </div>
        </div>
            
        <!-- Summary Boxes -->
        <div class="row text-center mb-4">
          <div class="col border p-3 rounded bg-light">
            <small class="text-muted">Current</small><br>
            <strong>${parseFloat(data.current || 0).toLocaleString()}</strong>
          </div>
          ${[2,3,4,5,6,7,8,9,10,11].map(i => `
            <div class="col border p-3 rounded ${data[`month_${i}`] > 0 ? 'bg-warning text-dark' : 'bg-light'}">
              <small class="text-muted">Month ${i}</small><br>
              <strong>${parseFloat(data[`month_${i}`] || 0).toLocaleString()}</strong>
            </div>
          `).join('')}
        </div>
            
        <!-- Transactions Table -->
        <h6 class="border-bottom pb-2">Transaction Details</h6>
        <div class="table-responsive">
          <table class="table table-sm table-bordered">
            <thead class="table-light">
              <tr>
                <th>Date</th>
                <th>Ref No</th>
                <th>Description</th>
                <th>Debit</th>
                <th>Credit</th>
                <th>Balance</th>
              </tr>
            </thead>
            <tbody>
              ${data.table?.map(row => `
                <tr>
                  <td>${row.DATE ? new Date(row.DATE).toLocaleDateString('en-GB') : '-'}</td>
                  <td>${row['REF NO'] || '-'}</td>
                  <td>${row.DESCRIPTION || '-'}</td>
                  <td class="text-end">${fmt(row.DEBIT)}</td>
                  <td class="text-end text-success">${fmt(row.CREDIT)}</td>
                  <td class="text-end fw-bold">${fmt(row.BALANCE)}</td>
                </tr>
              `).join('') || '<tr><td colspan="6" class="text-center text-muted">No transactions</td></tr>'}
            </tbody>
          </table>
        </div>
            
        <!-- Payable Details -->
        ${data.payable_data && data.payable_data.length > 0 ? `
          <h6 class="border-bottom pb-2 mt-5">Outstanding Invoices</h6>
          <div class="table-responsive">
            <table class="table table-sm table-bordered">
              <thead class="table-warning">
                <tr>
                  <th>Date</th>
                  <th>Ref No</th>
                  <th>Description</th>
                  <th>Credit</th>
                  <th>Debit</th>
                  <th>Paid</th>
                  <th>Balance</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${data.payable_data.map(p => `
                  <tr class="${p.STATUS === 'Open' ? 'table-danger' : ''}">
                    <td>${p.DATE ? new Date(p.DATE).toLocaleDateString('en-GB') : '-'}</td>
                    <td>${p['REF NO'] || p.DEBIT_REF_NO || '-'}</td>
                    <td>${p.DESCRIPTION || p.DEBIT_DESCRIPTION || '-'}</td>
                    <td class="text-end">${fmt(p.CREDIT)}</td>
                    <td class="text-end">${fmt(p.DEBIT)}</td>
                    <td class="text-end">${fmt(p.PAID_AMOUNT)}</td>
                    <td class="text-end fw-bold">${fmt(p.BALANCE)}</td>
                    <td>
    <span class="badge ${p.STATUS ? 'bg-success' : 'bg-danger'}">
        ${p.STATUS ? 'Paid' : 'Open'}
    </span>
</td>                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        ` : ''}
      </div>
    `;
            
            // Download PDF Button
            card.querySelector('.download-pdf').addEventListener('click', function () {
                const element = card.querySelector('.invoice-content');
                const opt = {
                    margin: 0.5,
                    filename: `${data.customer_id || 'Invoice'}_${data.vendor_name || 'Vendor'}.pdf`,
                    image: { type: 'jpeg', quality: 0.98 },
                    html2canvas: { scale: 2 },
                    jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
                };
                html2pdf().set(opt).from(element).save();
            });
            
            return card;
        }
    });
     function fmt(val) {
      const num = parseFloat(val);
      return isNaN(num) || num === 0 ? '-' : parseFloat(num.toFixed(2)).toLocaleString();
    }
    
  
    
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
    
     
    async function openInvoiceModal1(customerId, customerName, payTerm) {
      const modal = new bootstrap.Modal(document.getElementById('invoiceModal'));
      document.getElementById('modalCustomerName').textContent = customerName;
      document.getElementById('modalCustomerId').textContent = customerId;
      
      // Show loading
      document.querySelector('#unpaidTable tbody').innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';
      document.querySelector('#paidTable tbody').innerHTML = '<tr><td colspan="5" class="text-center">Loading...</td></tr>';
      
      modal.show();
      
      try {
        // Unpaid Invoices
        const unpaidRes = await fetch(`${API_BASE}/get-invoices`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ customer_id: customerId, status: false, payment_term: payTerm })
        });
        const unpaidData = await unpaidRes.json();
        renderInvoiceTable(unpaidData.invoices || [], 'unpaidTable', true, payTerm);
        
        // Paid Invoices
        const paidRes = await fetch(`${API_BASE}/get-invoices`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ customer_id: customerId, status: true, payment_term: payTerm })
        });
        const paidData = await paidRes.json();
        renderInvoiceTable(paidData.invoices || [], 'paidTable', false, payTerm);
        
      } catch (err) {
        showToast('Failed to load invoices', 'danger');
        console.error(err);
      }
    }
    
    
    async function openInvoiceModal(customerId, customerName, payTerm) {
      sessionStorage.setItem("customerId", customerId);
      sessionStorage.setItem("customerName", customerName);
      sessionStorage.setItem("payTerm", payTerm);
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
      const tables = ['currentTable', 'overdueTable', 'partialTable', 'paidTable', 'allTable'];
      tables.forEach(id => {
        const tbody = document.querySelector(`#${id} tbody`);
        const colspan = document.querySelector(`#${id} thead th`).parentElement.children.length;
        tbody.innerHTML = `<tr><td colspan="${colspan}" class="text-center">Loading...</td></tr>`;
      });
      
      // modal.show();
      
      try {
        // Fetch all statuses at once (you can optimize backend to accept "all" or multiple)
        const statuses = ['unpaid', 'overdue', 'partial', 'paid', 'all'];
        const promises = statuses.map(status =>
        fetch(`${API_BASE}/get-invoices`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ customer_id: customerId, status, payment_term: payTerm })
        }).then(r => r.json())
        );
        
        const [unpaidRes, overdueRes, partialRes, paidRes, allRes] = await Promise.all(promises);
        
        renderCurrentTable(unpaidRes.invoices || [], payTerm);
        renderOverdueTable(overdueRes.invoices || [], payTerm);
        renderPartialTable(partialRes.invoices || [], payTerm);
        renderPaidTable(paidRes.invoices || [], payTerm);
        renderAllTable(allRes.invoices || [], payTerm);
        
      } catch (err) {
        showToast('Failed to load invoices', 'danger');
        console.error(err);
      }
    }
    
    function renderCurrentTable(invoices, payTerm) {
      const table = document.querySelector('#currentTable');
      const tbody = table.querySelector('tbody');
      
      // Clear existing body (and implicitly the bulk action row/footer)
      tbody.innerHTML = invoices.length === 0
      ? '<tr><td colspan="10" class="text-center text-muted py-3">No current due invoices</td></tr>'
      : '';
      
      const selectAllCheckbox = document.getElementById('selectAllCurrent');
      
      // --- Clear previous listener to prevent duplication ---
      selectAllCheckbox.removeEventListener('change', handleSelectAll);
      // ------------------------------------------------------
      
      let selectedInvoiceAmount = 0;
      
      // 1. ADD NEW PAYMENT ACTION/INPUT ROW
      const bulkActionRow = document.createElement('tr');
      bulkActionRow.id = 'currentBulkActionRow';
      // Use 'd-none' initially to hide it when nothing is selected
      bulkActionRow.className = 'table-info d-none'; 
      bulkActionRow.innerHTML = `
    <td colspan="10" class="p-3">
        <div class="d-flex align-items-center justify-content-between">
            <div class="d-flex align-items-center">
                <span class="fw-bold me-3">Selected Total: <span id="selectedCurrentTotal" class="text-primary">${fmt(0)}</span></span>

                <label for="paymentActionSelect" class="me-2">Action:</label>
                <select id="paymentActionSelect" class="form-select form-select-sm w-auto me-3">
                    <option value="" disabled selected>Select Action</option>
                    <option value="full">Full Payment</option>
                    <option value="partial">Partial Payment</option>
                </select>

                <div id="partialPaymentGroup" class="input-group input-group-sm w-auto d-none">
                    <span class="input-group-text">Amount</span>
                    <input type="number" id="partialPaymentAmount" class="form-control" placeholder="0.00" min="0">
                </div>
            </div>

            <button id="confirmPaymentBtn" class="btn btn-sm btn-success" disabled>
                Confirm Payment
            </button>
        </div>
    </td>
  `;
      
      
      
      invoices.forEach(inv => {
        const tr = document.createElement('tr');
        const isOverdue = inv.updated_date_status === 1;
        const amountValue = parseFloat(inv.amount || inv.credit || 0) || 0; 
        const amountdebitValue = parseFloat(inv.debit) || 0; 
        const amountbalanceValue = parseFloat(inv.balance) || 0; 
        
        tr.innerHTML = `
      
      <td>${inv.invoice_date || '-'}</td>
      <td>${inv.ref_no || '-'}</td>
      <td>${inv.description || '-'}</td>
      <td>${fmt(amountValue)}</td>
      <td>${fmt(amountdebitValue)}</td>
      <td>${fmt(amountbalanceValue)}</td>
      <td>${inv.updated_date_status === 1 ? 'Overdue' : 'Current'}</td>
      <td>${inv.payment_status}</td>
      <td>
        ${isOverdue ? `<button class="btn btn-danger btn-sm revoke-btn" data-ref="${inv.ref_no}">Revoke</button>` : ''}
      </td>
      <td><input type="checkbox" class="current-row-checkbox" data-amount="${amountValue}"  data-balance="${amountbalanceValue}" data-ref="${inv.ref_no}"></td>
    `;
        
        // Overdue/Revoke button listener (kept from original)
        if (isOverdue) {
          tr.querySelector('.revoke-btn').addEventListener('click', () => handleRevoke(inv.ref_no, payTerm, tr));
        }
        
        // Checkbox listener to update the running total
        tr.querySelector('.current-row-checkbox').addEventListener('change', (e) => {
          const amount = parseFloat(e.target.dataset.balance);
          
          if (e.target.checked) {
            selectedInvoiceAmount += amount;
          } else {
            selectedInvoiceAmount -= amount;
          }
          updateSelectedTotalDisplay();
        });
        
        tbody.appendChild(tr);
      });
      tbody.appendChild(bulkActionRow);
      
      // --- Bulk Action Logic ---
      const paymentActionSelect = document.getElementById('paymentActionSelect');
      const partialPaymentGroup = document.getElementById('partialPaymentGroup');
      const partialPaymentAmountInput = document.getElementById('partialPaymentAmount');
      const confirmPaymentBtn = document.getElementById('confirmPaymentBtn');
      
      // Listener for the Action dropdown (Full/Partial)
      paymentActionSelect.addEventListener('change', handlePaymentAction);
      
      // Listener for the Partial Payment input field
      partialPaymentAmountInput.addEventListener('input', checkPaymentValidity);
      
      function handlePaymentAction() {
        const action = paymentActionSelect.value;
        
        // Reset input field and validation for new selection
        partialPaymentAmountInput.value = '';
        partialPaymentAmountInput.classList.remove('is-invalid');
        
        if (action === 'partial') {
          // Show the input field for partial payment
          partialPaymentGroup.classList.remove('d-none');
          // Set the max limit for the input field
          partialPaymentAmountInput.max = selectedInvoiceAmount; 
          // Check validity right away (will disable button if field is empty)
          checkPaymentValidity();
        } else if (action === 'full') {
          // Hide the input field for full payment
          partialPaymentGroup.classList.add('d-none');
          // Full payment is always valid if selected
          confirmPaymentBtn.disabled = false;
        } else {
          // No action selected
          partialPaymentGroup.classList.add('d-none');
          confirmPaymentBtn.disabled = true;
        }
      }
      
      
      
      function checkPaymentValidity() {
        const amount = parseFloat(partialPaymentAmountInput.value);
        const isPartial = paymentActionSelect.value === 'partial';
        const maxAmount = selectedInvoiceAmount;
        
        if (!isPartial) {
          return; // Skip validation if not partial payment
        }
        
        if (isNaN(amount) || amount <= 0 || amount > maxAmount) {
          partialPaymentAmountInput.classList.add('is-invalid');
          confirmPaymentBtn.disabled = true;
        } else {
          partialPaymentAmountInput.classList.remove('is-invalid');
          confirmPaymentBtn.disabled = false;
        }
      }
      
      function updateSelectedTotalDisplay() {
        const selectedCount = tbody.querySelectorAll('.current-row-checkbox:checked').length;
        document.getElementById('selectedCurrentTotal').textContent = fmt(selectedInvoiceAmount);
        
        const bulkActionRow = document.getElementById('currentBulkActionRow');
        
        if (selectedCount > 0) {
          bulkActionRow.classList.remove('d-none');
          // Also update the max amount for the partial payment field
          partialPaymentAmountInput.max = selectedInvoiceAmount;
          // Re-check validity when total changes
          checkPaymentValidity(); 
        } else {
          bulkActionRow.classList.add('d-none');
          confirmPaymentBtn.disabled = true;
          paymentActionSelect.value = ''; // Reset dropdown
        }
        
        if (selectedCount < invoices.length) {
          selectAllCheckbox.checked = false;
        } else if (invoices.length > 0) {
          selectAllCheckbox.checked = true;
        }
      }
      
      // Handle "Select All"
      function handleSelectAll(e) {
        const isChecked = e.target.checked;
        const checkboxes = tbody.querySelectorAll('.current-row-checkbox');
        selectedInvoiceAmount = 0; 
        
        checkboxes.forEach(cb => {
          cb.checked = isChecked;
          if (isChecked) {
            selectedInvoiceAmount += parseFloat(cb.dataset.balance);
          }
        });
        updateSelectedTotalDisplay();
      }
      selectAllCheckbox.addEventListener('change', handleSelectAll);
      
      // Total Due row
      const tfoot = document.createElement('tr');
      const totalAmount = invoices.reduce((sum, inv) => sum + (parseFloat(inv.balance || 0) || 0), 0);
      tfoot.innerHTML = `
    <td colspan="7" class="text-end fw-bold">Total Current Due:</td>
    <td colspan="3" class="fw-bold text-primary text-end">${fmt(totalAmount)}</td>
  `;
      tbody.appendChild(tfoot);
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
      ? '<tr><td colspan="6" class="text-center text-muted py-3">No overdue invoices</td></tr>'
      : '';
      
      invoices.forEach(inv => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
      <td>${inv.invoice_date || '-'}</td>
      <td>${inv.ref_no || '-'}</td>
      <td>${inv.description || '-'}</td>
      <td>${fmt(inv.amount || inv.credit || 0)}</td>
      <td>${inv.aging_bucket || '-'}</td>
      <td><button class="btn btn-success btn-sm mark-overdue-btn" data-ref="${inv.ref_no}">Mark as Current Due</button></td>
    `;
        tr.querySelector('.mark-overdue-btn').addEventListener('click', () => handleUpdateAging(inv.ref_no, payTerm, tr));
        tbody.appendChild(tr);
      });
      tfoot=document.createElement('tr');
      tfoot.innerHTML=`
  <td colspan="3" class="text-end fw-bold">Total Overdue:</td>
  <td colspan="3" class="fw-bold text-primary  text-end">${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.amount || inv.credit || 0) || 0), 0))}</td>
`;
      tbody.appendChild(tfoot);
    }
    
    // Partially Paid
    function renderPartialTable(invoices, payTerm) {
      const tbody = document.querySelector('#partialTable tbody');
      tbody.innerHTML = invoices.length === 0
      ? '<tr><td colspan="10" class="text-center text-muted py-3">No partially paid invoices</td></tr>'
      : '';
      
      invoices.forEach(inv => {
        const tr = document.createElement('tr');
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
      <td><button class="btn btn-warning btn-sm mark-overdue-btn" data-ref="${inv.ref_no}">Mark as Current Due</button></td>
    `;
        tr.querySelector('.mark-overdue-btn').addEventListener('click', () => handleUpdateAging(inv.ref_no, payTerm, tr));
        tbody.appendChild(tr);
      });
      tfoot=document.createElement('tr');
      tfoot.innerHTML=`
  <td colspan="5" class="text-end fw-bold">Total Balance:</td>
  <td colspan="5" class="fw-bold text-primary text-end">${fmt(invoices.reduce((sum, inv) => sum + (parseFloat( inv.balance || 0) || 0), 0))}</td>
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
    
    // All Invoices
    function renderAllTable(invoices, payTerm) {
      const tbody = document.querySelector('#allTable tbody');
      tbody.innerHTML = invoices.length === 0
      ? '<tr><td colspan="10" class="text-center text-muted py-3">No invoices</td></tr>'
      : '';
      
      invoices.forEach(inv => {
        const tr = document.createElement('tr');
        const hasDebit = inv.debit_ref_no || inv.debit_description;
        
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
      <td>${inv.status !== 'paid' && inv.balance > 0 ? `<button class="btn btn-success btn-sm mark-overdue-btn" data-ref="${inv.ref_no}">Mark as Current Due</button>` : ''}</td>
    `;
        
        if (inv.status !== 'paid' && inv.balance > 0) {
          tr.querySelector('.mark-overdue-btn')?.addEventListener('click', () => handleUpdateAging(inv.ref_no, payTerm, tr));
        }
        tbody.appendChild(tr);
      });
      tfoot=document.createElement('tr');
      tfoot.innerHTML=`
  <td colspan="5" class="text-end fw-bold">Total Invoices:</td>
  <td colspan="5" class="fw-bold text-primary text-end">${fmt(invoices.reduce((sum, inv) => sum + (parseFloat(inv.balance || 0) || 0), 0))}</td>
`;
      tbody.appendChild(tfoot);
    }
    
    // Shared: Mark as Current Due (calls /update-aging)
    async function handleUpdateAging(refNo, payTerm, rowElement) {
      const btn = rowElement.querySelector('.mark-overdue-btn');
      btn.disabled = true;
      btn.textContent = 'Processing...';
      
      try {
        const res = await fetch(`${API_BASE}/update-aging`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reference_no: refNo, payment_term: payTerm })
        });
        const result = await res.json();
        
        if (result.success) {
          showToast(`Invoice ${refNo} updated to Overdue`, 'success');
          rowElement.remove();
          setTimeout(loadAging, 1200);
          customerId = sessionStorage.getItem("customerId");
          customerName = sessionStorage.getItem("customerName"); 
          payTerm = sessionStorage.getItem("payTerm");
          openInvoiceModal(customerId, customerName, payTerm);
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
        const res = await fetch(`${API_BASE}/payment-clearance`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
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
        openInvoiceModal(customerId, customerName, payTerm);
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
    async function handleRevoke(refNo, payTerm, rowElement) {
      if (!confirm(`Revoke overdue status for ${refNo}?`)) return;
      
      const btn = rowElement.querySelector('.revoke-btn');
      btn.disabled = true;
      btn.textContent = 'Revoking...';
      
      try {
        const res = await fetch(`${API_BASE}/revoke-aging`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reference_no: refNo, payment_term: payTerm })
        });
        const result = await res.json();
        
        if (result.success) {
          showToast(`Overdue status revoked for ${refNo}`, 'info');
          rowElement.remove();
          customerId = sessionStorage.getItem("customerId");
          customerName = sessionStorage.getItem("customerName"); 
          payTerm = sessionStorage.getItem("payTerm");
          openInvoiceModal(customerId, customerName, payTerm);
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
          const res = await fetch(`${API_BASE}/advice`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ customer_id: customerId })
          });
          
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
      
     
      
      
    
      
      
   
      
  
 
      
      // Helper: format currency (you probably already have this)
      function fmt(num) {
        return new Intl.NumberFormat('en-US', { 
          minimumFractionDigits: 2, 
          maximumFractionDigits: 2 
        }).format(num);
      }
      
    