 
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

async function refreshIframeFromCurrentContent(iframe,data) {
  
      if (!iframe || !iframe.parentNode) {
    console.error('Iframe not available');
    return iframe;
  }

  const parent = iframe.parentNode;

  // Capture current rendered HTML
//   const html = iframe.contentWindow.document.documentElement.outerHTML;

  // Remove iframe (kills JS context)
  iframe.remove();
  data.template_id = sessionStorage.getItem('selected_template') || 1;
  data.client_test="client_test";
  let htmlText = await fetch(`/static/app/7templates.html`).then(r => r.text());
    // let htmlText = await fetch(`/soa/soa/static/app/7templates.html`).then(r => r.text());
    
    // 2. Inject your JSON
    htmlText = await injectSampleData(htmlText, data);
  // Reinsert iframe in the same place
  const newIframe = document.createElement('iframe');
  newIframe.style.width = iframe.style.width || '100%';
  newIframe.style.border = iframe.style.border || '0';
  newIframe.style.minHeight = iframe.style.minHeight || '600px';

  parent.appendChild(newIframe);

  // Write content — scripts run cleanly
  const doc = newIframe.contentWindow.document;
  doc.open();
  doc.write(htmlText);
  doc.close();

  return newIframe;

  
}

async function saveStatement1(data, filename, modal_id_for_print="") {
    const pay_term_status = data.pay_term_status;
    const category_status = data.category_status;
    console.log(modal_id_for_print)
        $('.'+modal_id_for_print+'DownloadOPtion').removeClass('hide');
        $('.'+modal_id_for_print+'PreviewOPtion').removeClass('hide');
        // $('#'+modal_id_for_print+'PreviewBody').find('iframe')
        const $iframe = $('#' + modal_id_for_print + 'PreviewBody').find('iframe');
     
refreshIframeFromCurrentContent($iframe[0],data);

    // CASE 1: BOTH FALSE → modal required
    // if (!pay_term_status && !category_status) {
    
    //     const modalResult = await openExtractModal(data);
    
    //     if (modalResult.action === "cancel") {
    //         return { success: false, error: "User cancelled", filename };
    //     }
    
    //     data.term = modalResult.term;
    //     data.merchant_category = modalResult.cat;
    // }
    
    // // CASE 2: term true, category false
    // else if (pay_term_status && !category_status) {
    
    //     const modalResult = await openExtractModal(data, {
    //         term: Number.isInteger(data.term) ? data.term : "",
    //         category: ""
    //     });
    
    //     if (modalResult.action === "cancel") {
    //         return { success: false, error: "User cancelled", filename };
    //     }
    
    //     data.merchant_category = modalResult.cat;
    // }
    
    // // CASE 3: term false, category true
    // else if (!pay_term_status && category_status) {
    
    //     const modalResult = await openExtractModal(data, {
    //         term: "",
    //         category: data.merchant_category || ""
    //     });
    
    //     if (modalResult.action === "cancel") {
    //         return { success: false, error: "User cancelled", filename };
    //     }
    
    //     data.term = modalResult.term;
    // }
    
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

async function saveStatement(data, filename, modal_id_for_print = "") {
    try {
        // 1. Refresh preview if modal exists
        if (modal_id_for_print) {
            $('.' + modal_id_for_print + 'DownloadOPtion').removeClass('hide');
            $('.' + modal_id_for_print + 'PreviewOPtion').removeClass('hide');

            const $iframe = $('#' + modal_id_for_print + 'PreviewBody').find('iframe');
            if ($iframe.length) {
                await refreshIframeFromCurrentContent($iframe[0], data);
            }
        }

        // 2. Prepare payload (your existing code)
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
    

        const res = await fetch(`${API_BASE}/v1/extract/save-remittances`, {
            method: "PUT",
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
            },
            body: JSON.stringify(payload)
        });

        if (res.status === 403) {
            showToast("No permission to save", 'warning');
            return { success: false, error: "Forbidden", filename };
        }

        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Save failed");

        return { success: true, message: result.message || "Saved", filename };

    } catch (err) {
        console.error("Save statement error:", err);
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



async function ensureClientIsSaved(data, save_id, modal_id_for_print) {
    // If already has term & category → assume client is ok
    if (data.pay_term_status && data.category_status && data.merchant_category?.trim()) {
        return { success: true, skipped: true };
    }

    // Otherwise we need to save client details first
    const clientResult = await saveClientDetails(save_id, modal_id_for_print + "Preview", null);

    if (!clientResult.success) {
        return { success: false, error: clientResult.error || "Client save failed" };
    }

    // Update data object with latest values (important!)
    data.term = document.getElementById(`${save_id}payTerm`)?.value || data.term;
    data.merchant_category = document.getElementById(`${save_id}merchantCategory`)?.value || data.merchant_category;
    data.customer_name = document.getElementById(`${save_id}clientName`)?.value || data.customer_name;
    data.customer_address = document.getElementById(`${save_id}address`)?.value || data.customer_address;

    return { success: true, updated: true };
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

// async function createpreviewCard(data, filename,ele) {

//     // 1. Fetch template HTML
//     let htmlText = await fetch(`/soa/soa/static/app/7templates.html`).then(r => r.text());

//     // 2. Inject your JSON
//     htmlText = await injectSampleData(htmlText, data);

//     // 3. Create modal
//     const modalId = `pdfPreviewModal${data.customer_id}`;
//     const modal = document.createElement('div');
//     modal.className = 'modal fade';
//     modal.id = modalId;
//     modal.tabIndex = '-1';
//     modal.setAttribute('aria-labelledby', `${modalId}Label`);
//     modal.setAttribute('aria-hidden', 'true');
//     modal.innerHTML = `
//         <div class="modal-dialog modal-lg modal-dialog-scrollable">
//             <div class="modal-content">
//                 <div class="modal-header">
//                     <h5 class="modal-title" id="${modalId}Label">
//                         ${data.vendor_name || 'Invoice'} - Preview
//                     </h5>
//                                     <div class="d-flex gap-2">
//                     <button type="button" class="btn btn-sm btn-primary" id="${modalId}Download">
//                         Download PDF
//                     </button>
//                     <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
//                 </div>

//                 </div>
//                 <div class="modal-body" id="${modalId}Body">
//                     <!-- iframe will be inserted here -->
//                 </div>
//             </div>
//         </div>
//     `;

//     document.body.appendChild(modal);

//     // 4. Create iframe
//     const iframe = document.createElement('iframe');
//     iframe.style.width = '100%';
//     iframe.style.border = '0';
//     iframe.style.minHeight = '600px';

//     document.getElementById(`${modalId}Body`).appendChild(iframe);

//     // 5. Write HTML into iframe (scripts AUTO-RUN)
//     const iframeDoc = iframe.contentWindow.document;
//     iframeDoc.open();
//     iframeDoc.write(htmlText);
//     iframeDoc.close();

//     // 6. Auto-resize iframe height
//     iframe.onload = () => {
    //             iframe.style.height = iframe.contentDocument.body.scrollHeight + 'px';
//             const downloadBtn = document.getElementById(`${modalId}Download`);

//     downloadBtn.onclick = () => {
    //         generatePDFFromIframe(iframe, filename || 'Preview_Document');
//     };
//     };

//     return modal;
// }

 function saveClientDetails1(save_id,modalId,ele) { 
    const pkId = document.getElementById("clientPkId").value;
    if(!document.getElementById(`${save_id}clientId`).value || !document.getElementById(`${save_id}clientName`).value || !document.getElementById(`${save_id}payTerm`).value || !document.getElementById(`${save_id}merchantCategory`).value  || !document.getElementById(`${save_id}address`).value ){

    showToast('Merchant Category , Payterms, Client Name, Client Id,  Address are required ', 'danger');
        return false;
    }
    
    payload = {
        client_id: document.getElementById(`${save_id}clientId`).value,
        name: document.getElementById(`${save_id}clientName`).value,
        phone: document.getElementById(`${save_id}phone`).value,
        address: document.getElementById(`${save_id}address`).value,
        pay_term: parseInt(document.getElementById(`${save_id}payTerm`).value),
        merchant_category: document.getElementById(`${save_id}merchantCategory`).value,
        template: sessionStorage.getItem('selected_template') || 1,
        bank_name: document.getElementById(`${save_id}bankName`).value,
        bank_acc_number: document.getElementById(`${save_id}bankAcc`).value,
        bank_origin: document.getElementById(`${save_id}bankOrigin`).value,
        iban_no: document.getElementById(`${save_id}ibanNo`).value,
        swift_code: document.getElementById(`${save_id}shiftCode`).value,
        status: Number(document.getElementById(`${save_id}statuss`).value),
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
    const API_BASE_URL = API_BASE+"/v1/client-details";
    const url = pkId ? `${API_BASE_URL}/update/${pkId}` : `${API_BASE_URL}/create`;
    const method = pkId ? "PUT" : "POST";
    
     fetch(url, {
        method,
        headers,
        body: JSON.stringify(payload)
    });
    // fetch(`${API_BASE}/v1/client/insert`, {
    //     method: 'PUT',
    //     headers: {
    //         'accept': 'application/json',
            
    //         "Authorization": `Bearer ${localStorage.getItem("token") || getCookie('access_token')} `,
    //         'Content-Type': 'application/json'
    //     },
    //     body: JSON.stringify({
    //         "client_id": document.getElementById(`${save_id}clientId`).value,
    //         "name": document.getElementById(`${save_id}clientName`).value,
    //         "template": sessionStorage.getItem('selected_template') || 1
    //     })
    // })
    // .then(response => response.json())
    // .then(data => console.log('Template saved:', data))
    // .catch(error => console.error('Error:', error));
    // bootstrap.Modal.getInstance(document.getElementById(modalId)).hide();
    $('.btn-close')?.trigger('click');

    $(ele).hide();
    
}

async function saveClientDetails(save_id, modalId, ele) {
    const pkId = document.getElementById(`${save_id}clientPkId`).value;
    console.log(save_id, 'save id')

    // Validation
    const requiredFields = [
        `${save_id}clientId`,
        `${save_id}clientName`,
        `${save_id}payTerm`,
        `${save_id}merchantCategory`,
        `${save_id}address`
    ];

    for (const id of requiredFields) {
        if (!document.getElementById(id)?.value?.trim()) {
            showToast('Merchant Category, Payterms, Client Name, Client ID, Address are required', 'danger');
            return { success: false, error: "Missing required fields" };
        }
    }

    const payload = {
        client_id: document.getElementById(`${save_id}clientId`).value.trim(),
        name: document.getElementById(`${save_id}clientName`).value.trim(),
        phone: document.getElementById(`${save_id}phone`)?.value?.trim() || null,
        address: document.getElementById(`${save_id}address`).value.trim(),
        pay_term: parseInt(document.getElementById(`${save_id}payTerm`).value) || 0,
        merchant_category: document.getElementById(`${save_id}merchantCategory`).value.trim(),
        template: sessionStorage.getItem('selected_template') || 1,
        bank_name: document.getElementById(`${save_id}bankName`)?.value?.trim() || null,
        bank_acc_number: document.getElementById(`${save_id}bankAcc`)?.value?.trim() || null,
        bank_origin: document.getElementById(`${save_id}bankOrigin`)?.value?.trim() || null,
        iban_no: document.getElementById(`${save_id}ibanNo`)?.value?.trim() || null,
        swift_code: document.getElementById(`${save_id}shiftCode`)?.value?.trim() || null,
        status: Number(document.getElementById(`${save_id}statuss`)?.value || 1),
        created_by: Number(getCookie('user_id')),
        updated_by: Number(getCookie('user_id'))
    };

    // Clean payload
    Object.keys(payload).forEach(key => {
        if (payload[key] === null || payload[key] === undefined || payload[key] === "") {
            delete payload[key];
        }
    });

    const API_BASE_URL = `${API_BASE}/v1/client-details`;
    const url = pkId ? `${API_BASE_URL}/update/${pkId}` : `${API_BASE_URL}/create`;
    const method = pkId ? "PUT" : "POST";

    try {
        const response = await fetch(url, {
            method,
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`,
                "accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.message || `HTTP ${response.status}`);
        }

        const result = await response.json();

        // Optional: update pkId if newly created
        // if (!pkId && result?.id) {
        //     document.getElementById(`${save_id}clientPkId`).value = result.id;
        // }

        showToast("Client details saved successfully", "success");
        return { success: true, client_id: payload.client_id };

    } catch (err) {
        showToast(`Client save failed: ${err.message}`, "danger");
        console.error(err);
        return { success: false, error: err.message };
    } finally {
        // Clean up UI
        $('.btn-close')?.trigger('click');
        if (ele) $(ele).hide();
    }
}

const headers = {
    "Content-Type": "application/json",
    
    "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`,
    "accept": "application/json"
};

async function createpreviewCard(data, filename,ele,save_id,modal_id_for_print) {
    
    // 1. Fetch template HTML
    let htmlText = await fetch(`/static/app/7templates.html`).then(r => r.text());

    // 2. Inject your JSON
    htmlText = await injectSampleData(htmlText, data);
    
    // 3. Create modal
    // const modalId = `pdfPreviewModal${data.customer_id}`;
     const modalIdPreview = modal_id_for_print+"Preview";
    const modalPreview = document.createElement('div');
    modalPreview.className = 'modal fade';
    modalPreview.id = modalIdPreview;
    modalPreview.tabIndex = '-1';
    modalPreview.setAttribute('aria-labelledby', `${modalIdPreview}Label`);
    modalPreview.setAttribute('aria-hidden', 'true');
     modalPreview.innerHTML = `
     <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      
      <div class="modal-header">
        <h5 class="modal-title" id="${modalIdPreview}Label">
              ${data.vendor_name || 'Invoice'} - Preview
              </h5>
               <div class="d-flex gap-2">
                 
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
    
      </div>
      
      <div class="modal-body">
       
          <div class="col-md-12" id="${modalIdPreview}Body">
          </div>
          </div>
          
        </form>
      </div>
      
  
      
    </div>
  </div>
 
    `;
    document.body.appendChild(modalPreview);
      const iframePreview = document.createElement('iframe');
   
  iframePreview.style.width = '100%';
    iframePreview.style.border = '0';
    iframePreview.style.minHeight = '600px';
    
    document.getElementById(`${modalIdPreview}Body`).appendChild(iframePreview);
    
    // 5. Write HTML into iframe (scripts AUTO-RUN)
    const iframeDocP = iframePreview.contentWindow.document;
     const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlText;

    // Find all elements with class 'button-tab-container'
    const buttonTabs = tempDiv.querySelectorAll('.button-tab-container');

    // Add 'hide' class to each
buttonTabs.forEach(el => {
  el.classList.add('hide');
});


    iframeDocP.open();
    iframeDocP.write(tempDiv.innerHTML);
    iframeDocP.close();
    
    // 6. Auto-resize iframe height
   
    
    const modalId = modal_id_for_print;
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = modalId;
    modal.tabIndex = '-1';
    modal.setAttribute('aria-labelledby', `${modalId}Label`);
    modal.setAttribute('aria-hidden', 'true');
    customer_id_value= document.getElementById("modal_client_id").value = data.customer_id;
    customerName_value= document.getElementById("modal_client_name").value = data.customer_name;
    customerAddress_value= document.getElementById("modal_client_address").value = data.customer_address;
    
    // Prefill based on condition
    payterms_value= document.getElementById("modal_payment_term").value = data.term ?? "";
    category_value= document.getElementById("modal_merchant_category").value = data.merchant_category ?? "";
      const pay_term_status = data.pay_term_status;
    const category_status = data.category_status;
    
    modal.innerHTML = `
     <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      
      <div class="modal-header">
        <h5 class="modal-title" id="${modalId}Label">
              ${data.vendor_name || 'Invoice'} - Preview
              </h5>
               <div class="d-flex gap-2">
                    <button type="button" class="btn btn-sm btn-primary hide" id="${modalId}Download">
                        Download PDF
                    </button>
                    <button 
    class="btn btn-light btn-sm me-2" 
    onclick="if(saveClientDetails('${save_id}', 'pdfPreviewModal${modalId}',this)!=false) { $('.${save_id}').trigger('click');  }" 
    title="Save this statement">

      <i class="bi bi-cloud-check"></i> Save
    </button>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
    
      </div>
      
      <div class="modal-body">
        <form id="clientForm" class="${pay_term_status && category_status ? 'hide' : ''}">
          <input type="hidden" id="${save_id}clientPkId">
          
          <div class="row">
            <div class="col-md-12">
          <div class="row">
            <div class="col-md-12 mb-3">
            <h6 class="text-danger">

            Please Fill the Client Details Before Save
            </h6>
            </div>
            <div class="col-md-4 mb-3">
              <label class="form-label">Client ID<span style="color:red">*</span></label>
              <input type="text" class="form-control" id="${save_id}clientId" required value="${customer_id_value}">
            </div>
            
            <div class="col-md-4 mb-3">
              <label class="form-label">Client Name<span style="color:red">*</span></label>
              <input type="text" class="form-control" id="${save_id}clientName" required value="${customerName_value}">
            </div>
            
            <div class="col-md-4 mb-3">
              <label class="form-label">Phone</label>
              <input type="number" class="form-control" id="${save_id}phone">
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Merchant Category<span style="color:red">*</span></label>
                <select name="" id="${save_id}merchantCategory" class="form-select merchantCategory" required>
    
                </select>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Address<span style="color:red">*</span></label>
              <textarea class="form-control" id="${save_id}address" rows="2">${customerAddress_value}</textarea>
            </div>
            
            <div class="col-md-3 mb-3">
              <label class="form-label">Bank Name</label>
              <input type="text" class="form-control" id="${save_id}bankName" required>
            </div>
            
            <div class="col-md-3 mb-3">
              <label class="form-label">Bank Account No</label>
              <input type="number" class="form-control" id="${save_id}bankAcc" required>
            </div>
            
            <div class="col-md-3 mb-3">
              <label class="form-label">Currency</label>
              <input type="text" class="form-control" id="${save_id}bankOrigin" required>
            </div>
    
            <div class="col-md-3 mb-3">
              <label class="form-label">Shift Code</label>
              <input type="text" class="form-control" id="${save_id}shiftCode">
            </div>
            
            <div class="col-md-3 mb-3">
              <label class="form-label">Iban No</label>
              <input type="text" class="form-control" id="${save_id}ibanNo">
            </div>
            
            <div class="col-md-3 mb-3">
              <label class="form-label">Pay Term <span style="color:red">*</span> </label>
              <input type="number" class="form-control" id="${save_id}payTerm" required value="${payterms_value}">
            </div>
            
          
            <div class="col-md-4 mb-3 hide">
              <label class="form-label">Status</label>
              <select class="form-select" id="${save_id}statuss">
                <option value="1">Active</option>
                <option value="0">Inactive</option>
              </select>
            </div>
          </div>
          </div>
          <div class="col-md-12" id="${modalId}Body">
          </div>
          </div>
          
        </form>
      </div>
      
  
      
    </div>
  </div>
 
    `;
    
    document.body.appendChild(modal);
    console.log(modal)
    // 4. Create iframe
    const iframe = document.createElement('iframe');
    if (data.template_id && parseInt(data.template_id) > 0) {
    iframe.className = "hide";
}

    iframe.style.width = '100%';
    iframe.style.border = '0';
    iframe.style.minHeight = '600px';
    
    document.getElementById(`${modalId}Body`).appendChild(iframe);
    
    // 5. Write HTML into iframe (scripts AUTO-RUN)
    const iframeDoc = iframe.contentWindow.document;
    iframeDoc.open();
    iframeDoc.write(htmlText);
    iframeDoc.close();
    
    // 6. Auto-resize iframe height
    iframe.onload = () => {
        iframe.style.height = iframe.contentDocument.body.scrollHeight + 'px';
        document
        .getElementById(`${modalId}Download`)
        .addEventListener('click', () => {
            generatePDFFromIframe(iframe, filename || 'Preview_Document');
        });
        
    };
    
    return modalId;
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


function generatePDFFromIframe(iframe, filename) {
    const iframeDoc =
    iframe.contentDocument || iframe.contentWindow.document;
    
    if (!iframeDoc) {
        console.error('Iframe document not accessible');
        return;
    }
    
    const element =
    iframeDoc.getElementById('statement-content') ||
    iframeDoc.body;
    
    // ✅ FIX HERE
    const pdfButton = iframeDoc.getElementById('pdfButton');
    // OR: const pdfButton = element.querySelector('#pdfButton');
    
    if (!pdfButton) {
        console.error('❌ pdfButton not found inside iframe');
        return;
    }
    
    console.log('✅ Triggering PDF button click');
    pdfButton.click();
}

function injectSampleData(html, data) {
    const json = JSON.stringify(data, null, 2);
    
    return html.replace(
        /const\s+sampleData\s*=\s*\{[\s\S]*?\};/m,
        `const sampleData = ${json};`
    );
}
function uniqueText() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
}


// e.g. "lks9q3u8f4z1m2"

function createInvoiceCard(data, filename) {
    $id=uniqueText();
    const card = document.createElement('div');
    card.dataset.saveId = $id;
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
    modal_id_for_print= `pdfPreviewModal${$id}`;
    
createpreviewCard(data, filename,card,$id,modal_id_for_print);

 
    card.innerHTML = `
    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
      <h5 class="mb-0">
        <i class="bi bi-file-earmark-text"></i> ${data.vendor_name || 'Vendor Invoice'}
      </h5>
      <div>
  ${canShowAction('save') ? `
     <button class="btn btn-light btn-sm preview-pdf preview-pdf${modal_id_for_print} hide" data-bs-toggle="modal" data-bs-target="#${modal_id_for_print}">
      <i class="bi bi-eye"></i> Preview 
    </button>
    <button 
  class="btn btn-light btn-sm" 
  onclick='save_the_details(${JSON.stringify(data)}, "${modal_id_for_print}","${$id}",this)'>

      <i class="bi bi-eye"></i> Save 
    </button>
    <button class="btn btn-light btn-sm me-2 save-single hide ${$id}" title="Save this statement">
      <i class="bi bi-cloud-check"></i> Save
    </button>
   
  ` : ''}
    
 
  
    ${canShowAction('download') ? `
           <button class="btn btn-light btn-sm download-pdf hide " >
      <i class="bi bi-download"></i> Download
    </button>
  <button 
    class="btn btn-light btn-sm ${modal_id_for_print}DownloadOPtion ${(!data.template_id || parseInt(data.template_id) <= 0) ? 'hide' : ''}"
    onclick="document.getElementById('${modal_id_for_print}Download').click()"
    title="Download this statement">
    <i class="bi bi-download"></i> Download
  </button>
 
  <button 
    class="btn btn-light btn-sm ${modal_id_for_print}PreviewOPtion  ${(!data.template_id || parseInt(data.template_id) <= 0) ? 'hide' : ''}"
     data-bs-toggle="modal" data-bs-target="#${modal_id_for_print}Preview"
    title="Preview this statement">
    <i class="bi bi-eye"></i> Preview
  </button>

    <button class="btn btn-light btn-sm preview-pdf hide" data-bs-toggle="modal" data-bs-target="#pdfPreviewModal${data.customer_id}">
      <i class="bi bi-download"></i> Save 
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
          <div class="col border p-3 rounded bg-light">
            <small class="${data.current > 0 ? 'text-light' : ' text-dark'}">Current</small><br>
            <strong>${parseFloat(data.current || 0).toLocaleString()}</strong>
          </div>
          ${[2,3,4,5,6,7,8,9,10,11].map(i => `
            <div class="col border p-3 rounded ${data[`month_${i}`] > 0 ? 'bg-primary text-light' : 'bg-light text-dark'}">
              <small class="${data[`month_${i}`] > 0 ? 'text-light' : ' text-dark'}">Month ${i}</small><br>
              <strong>${parseFloat(data[`month_${i}`] || 0).toLocaleString()}</strong>
            </div>
          `).join('')}
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


// Save Button (permission-safe)
const saveBtn = card.querySelector('.save-single');
if (saveBtn) {
    

    saveBtn.addEventListener('click', async function () {
    const btn = this;
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';

    // const save_id = modal_id_for_prin;
    const save_id = card.dataset.saveId;
    const modal_id_for_print = `pdfPreviewModal${save_id}`;

    // Step 1: Ensure client details are saved/updated
    const clientResult = await saveClientDetails(save_id, modal_id_for_print + "Preview", null);

    if (!clientResult.success) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-check"></i> Save';
        showToast("Cannot save statement – client details invalid", "danger");
        return;
    }

    // Step 2: Now safe to save statement
    const result = await saveStatement(data, filename, modal_id_for_print);

    // Update UI
    const statusEl = card.querySelector('.save-status');
    if (result.success) {
        statusEl.innerHTML = '<i class="bi bi-check-circle text-success"></i> Saved';
        showToast("Statement saved", "success");

        // Show preview/download buttons only after success
        $(`.${modal_id_for_print}DownloadOPtion`).removeClass('hide');
        $(`.${modal_id_for_print}PreviewOPtion`).removeClass('hide');
    } else {
        statusEl.innerHTML = '<i class="bi bi-x-circle text-danger"></i> Failed';
        showToast(`Save failed: ${result.error}`, "danger");
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


function save_the_details(data11,modal_id_for_print,save_id,ele){
    // data11=JSON.parse(data11);
    const pay_term_status = data11.pay_term_status;
    const category_status = data11.category_status;
    const merchantCategory = data11.merchant_category;
    // return false;
    $(`#${save_id}merchantCategory`).val(merchantCategory);
    if(data11.template_id>0 && pay_term_status && category_status){
        console.log(pay_term_status,category_status,merchantCategory)
        $('.'+save_id).trigger('click');
        $(ele).hide();
        $('.'+modal_id_for_print+'DownloadOPtion').removeClass('hide');
        $('.'+modal_id_for_print+'PreviewOPtion').removeClass('hide');
    }else{
          $('.preview-pdf' + modal_id_for_print).trigger('click');
    }
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
        
        // document.getElementById('bulkSaveBtn').addEventListener('click', async () => {
        //     const cards = document.querySelectorAll('#resultsContainer .card');
            
        //     if (cards.length === 0) {
        //         showToast('No statements to save', 'info');
        //         return;
        //     }
            
        //     const btn = document.getElementById('bulkSaveBtn');
        //     const progress = document.getElementById('bulkProgress');
            
        //     btn.disabled = true;
        //     btn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Saving All...';
        //     progress.innerHTML = '';
            
        //     let success = 0, failed = 0;
            
        //     for (let i = 0; i < cards.length; i++) {
        //         const card = cards[i];
        //         const data = card.__extractedData;
        //         const filename = getFilenameFromCard(card);
                
        //         progress.innerHTML = `
        //       <div class="text-primary">
        //         Saving ${i + 1} of ${cards.length} →
        //         <strong>${data.customer_id || '??'}</strong>
        //         (${filename})
        //       </div>
        //     `;
                
        //         const result = await saveStatement(data, filename);
        //         const statusEl = card.querySelector('.save-status');
                
        //         if (result.success) {
        //             success++;
        //             if (statusEl) {
        //                 statusEl.innerHTML =
        //                 '<i class="bi bi-check-circle-fill text-success"></i> Saved';
        //             }
        //         } else {
        //             failed++;
        //             if (statusEl) {
        //                 statusEl.innerHTML =
        //                 '<i class="bi bi-x-circle-fill text-danger"></i> Failed';
        //             }
        //             console.error(`Save failed for ${data.customer_id}:`, result.error);
        //         }
        //     }
            
        //     progress.innerHTML = `
        //   <strong class="text-success">
        //     Completed! ${success} saved, ${failed} failed
        //   </strong>
        // `;
            
        //     btn.innerHTML = '<i class="bi bi-check2-all"></i> Save All Complete';
        //     btn.disabled = false;
            
        //     showToast(
        //         `Bulk save finished: ${success} succeeded${failed ? `, ${failed} failed` : ''}`,
        //         failed === 0 ? 'success' : 'warning'
        //     );
        // });
    
        document.getElementById('bulkSaveBtn').addEventListener('click', async () => {
            const cards = document.querySelectorAll('#resultsContainer .card');
            if (cards.length === 0) return showToast('No statements', 'info');

            const btn = document.getElementById('bulkSaveBtn');
            btn.disabled = true;
            btn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Processing...';

            let success = 0, failed = 0;

            for (const card of cards) {
                const data = card.__extractedData;
                const filename = getFilenameFromCard(card);

                // Extract unique identifiers from the card (very important!)
                const saveBtnInCard = card.querySelector('.save-single');
                const save_id1 = saveBtnInCard ? [...saveBtnInCard.classList].find(c => c !== 'save-single' && c !== 'hide') : null;
                const save_id = card.dataset.saveId;
                const modalBase = save_id ? `pdfPreviewModal${save_id}` : null;
                // console.log(save_id, 'bulk1')
                
                // console.log(save_id1, 'bulk2')
                if (!save_id || !modalBase) {
                    failed++;
                    card.querySelector('.save-status').innerHTML = '<i class="bi bi-x-octagon text-danger"></i> ID Error';
                    continue;
                }
              
                // Step 1: Force client details check/save
                const clientOk = await saveClientDetails(save_id, modalBase + "Preview", this);

                let result = { success: false, error: "Client step failed" };

                if (clientOk.success) {
                    // Step 2: Save statement
                    result = await saveStatement(data, filename, modalBase);
                }

                const statusEl = card.querySelector('.save-status');
                if (result.success) {
                    success++;
                    statusEl.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i> Saved';
                    // Show buttons only for this card
                    $(`.${modalBase}DownloadOPtion`).removeClass('hide');
                    $(`.${modalBase}PreviewOPtion`).removeClass('hide');
                } else {
                    failed++;
                    statusEl.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i> Failed';
                }
            }

            btn.innerHTML = '<i class="bi bi-check2-all"></i> Save All Done';
            btn.disabled = false;

            showToast(`Bulk: ${success} saved, ${failed} failed`, success === cards.length ? 'success' : 'warning');
        });    
    }
    

    function addBulkSaveButton3() {
    // Permission check
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
        btn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Checking...';
        progress.innerHTML = 'Validating client details...';

        // ─────────────────────────────────────────────────────────────
        // STEP 1: PRE-CHECK – Ensure all cards have required client info
        // ─────────────────────────────────────────────────────────────
        const incomplete = [];

        cards.forEach((card, index) => {
            const saveBtnElement = card.querySelector('.save-single');
            if (!saveBtnElement) {
                incomplete.push({ index: index + 1, reason: 'no save button' });
                return;
            }

            // Extract save_id from class names (your current method)
            const classes = Array.from(saveBtnElement.classList);
            let save_id = classes.find(cls => 
                cls !== 'save-single' && 
                cls !== 'hide' && 
                !cls.startsWith('btn') && 
                cls.length > 8 && 
                !cls.includes('-')
            );

            if (!save_id) {
                incomplete.push({ index: index + 1, reason: 'missing save_id' });
                return;
            }

            // Check required client fields
            const requiredFields = [
                `${save_id}clientId`,
                `${save_id}clientName`,
                `${save_id}payTerm`,
                `${save_id}merchantCategory`,
                `${save_id}address`
            ];

            let hasAllFields = true;
            for (const fieldId of requiredFields) {
                const input = document.getElementById(fieldId);
                if (!input || !input.value?.trim()) {
                    hasAllFields = false;
                    break;
                }
            }

            if (!hasAllFields) {
                incomplete.push({ 
                    index: index + 1, 
                    save_id,
                    cardElement: card 
                });
            }
        });

        // If any item is incomplete → block bulk save
        if (incomplete.length > 0) {
            let message = `Bulk save blocked: ${incomplete.length} of ${cards.length} statements missing required client details.<br><br>`;
            message += `Please use the <strong>Preview → Save</strong> flow on individual statements to fill in:<br>`;
            message += `• Client ID<br>• Client Name<br>• Address<br>• Payment Term<br>• Merchant Category`;

            showToast(message, 'warning', 12000); // longer duration

            // Highlight the first incomplete card
            if (incomplete[0]?.cardElement) {
                incomplete[0].cardElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                incomplete[0].cardElement.style.border = '3px solid #fd7e14';
                setTimeout(() => {
                    incomplete[0].cardElement.style.border = '';
                }, 4000);
            }

            // Reset button
            btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Save All Statements';
            btn.disabled = false;
            progress.innerHTML = '';
            return;
        }

        // ─────────────────────────────────────────────────────────────
        // STEP 2: All checks passed → proceed with actual saving
        // ─────────────────────────────────────────────────────────────
        btn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Saving All...';
        progress.innerHTML = '';

        let success = 0;
        let failed = 0;

        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            const data = card.__extractedData;
            const filename = getFilenameFromCard(card);

            // Extract save_id again for modal reference
            const saveBtnElement = card.querySelector('.save-single');
            const classes = Array.from(saveBtnElement.classList);
            const save_id = classes.find(cls => 
                cls !== 'save-single' && 
                cls !== 'hide' && 
                !cls.startsWith('btn') && 
                cls.length > 8 && 
                !cls.includes('-')
            );

            const modal_id_for_print = `pdfPreviewModal${save_id}`;

            progress.innerHTML = `
                <div class="text-primary">
                    Saving ${i + 1} of ${cards.length} →
                    <strong>${data.customer_id || '???'}</strong>
                    (${filename})
                </div>`;

            // Optional: refresh preview if needed
            // await refreshIframeFromCurrentContent(...)

            const result = await saveStatement(data, filename, modal_id_for_print);

            const statusEl = card.querySelector('.save-status');

            if (result.success) {
                success++;
                if (statusEl) {
                    statusEl.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i> Saved';
                }
                // Show download/preview buttons for this card
                $(`.${modal_id_for_print}DownloadOPtion`).removeClass('hide');
                $(`.${modal_id_for_print}PreviewOPtion`).removeClass('hide');
            } else {
                failed++;
                if (statusEl) {
                    statusEl.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i> Failed';
                }
                console.error(`Save failed for ${data.customer_id || filename}:`, result.error);
            }

            // Small delay to make progress visible
            await new Promise(resolve => setTimeout(resolve, 400));
        }

        progress.innerHTML = `
            <strong class="${failed === 0 ? 'text-success' : 'text-warning'}">
                Completed! ${success} saved successfully, ${failed} failed
            </strong>`;

        btn.innerHTML = '<i class="bi bi-check2-all"></i> Save All';
        btn.disabled = false;

        showToast(
            `Bulk save finished: ${success} succeeded${failed ? `, ${failed} failed` : ''}`,
            failed === 0 ? 'success' : 'warning'
        );
    });
}
    
    function loadCategoryList_new(select_id) {
        $(`.${select_id}`).empty()
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
            
            $(`.${select_id}`).append(
                `<option value=''>Select Category</option>
          `
            );
            rows.forEach(c => {
                $(`.${select_id}`).append(
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
                        loadCategoryList_new('merchantCategory');
                        if (outputData.length > 1)
                            { addBulkSaveButton();
                            }
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
            

//         document.getElementById('bulkSaveBtn')?.addEventListener('click', async () => {
//     const cards = document.querySelectorAll('#resultsContainer .card');
//     if (!cards.length) {
//         showToast('No statements to save', 'info');
//         return;
//     }

//     const btn = document.getElementById('bulkSaveBtn');
//     const progress = document.getElementById('bulkProgress');

//     btn.disabled = true;
//     btn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Saving All...';
//     progress.innerHTML = '';

//     let successCount = 0;
//     let failedCount = 0;

//     for (const [index, card] of Array.from(cards).entries()) {
//         const data = card.__extractedData;
//         const filename = getFilenameFromCard(card);
//         const save_id = card.querySelector('.save-single')?.classList[2] || ''; // e.g. "lks9q3u8f4z1m2"
//         const modal_id = `pdfPreviewModal${save_id}`;

//         progress.innerHTML = `
//             <div class="text-primary mb-1">
//                 ${index + 1}/${cards.length} — ${data.customer_id || '---'} (${filename})
//             </div>`;

//         // Step 1: Ensure client details are saved
//         const clientCheck = await ensureClientIsSaved(data, save_id, modal_id);

//         let result;

//         if (clientCheck.success) {
//             // Step 2: Save the actual statement
//             result = await saveStatement(data, filename, modal_id);

//             if (result.success) {
//                 successCount++;
//                 card.querySelector('.save-status').innerHTML =
//                     '<i class="bi bi-check-circle-fill text-success"></i> Saved';
//             } else {
//                 failedCount++;
//                 card.querySelector('.save-status').innerHTML =
//                     '<i class="bi bi-x-circle-fill text-danger"></i> Failed';
//             }
//         } else {
//             failedCount++;
//             card.querySelector('.save-status').innerHTML =
//                 '<i class="bi bi-x-circle-fill text-danger"></i> Client Error';
//         }

//         await new Promise(r => setTimeout(r, 300)); // small breathing room
//     }

//     progress.innerHTML = `
//         <strong class="${failedCount ? 'text-warning' : 'text-success'}">
//             Done • ${successCount} saved • ${failedCount} failed
//         </strong>`;

//     btn.innerHTML = '<i class="bi bi-check2-all"></i> Save All';
//     btn.disabled = false;

//     showToast(
//         `Bulk save: ${successCount} succeeded${failedCount ? `, ${failedCount} failed` : ''}`,
//         failedCount ? 'warning' : 'success'
//     );
// });    
            
            
            
            
            
            
            
            
            
            // Helper: format currency (you probably already have this)
            function fmt(num) {
                return new Intl.NumberFormat('en-US', { 
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: 2 
                }).format(num);
            }
            
            