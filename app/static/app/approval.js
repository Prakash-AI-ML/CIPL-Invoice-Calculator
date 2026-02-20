function canShowAction(ButtonName) {
    const approval = USER_MENUS.approval.buttons;

    if (!approval) return false;

    if (Array.isArray(approval)) {
        const buttonNames = approval.map(item => item.button_name);
        return buttonNames.includes(ButtonName);
    }

    if (typeof approval === 'object' && 'button_name' in approval) {
        return approval.button_name === ButtonName;
    }

    return false;
}

let currentCustomerId = "";
let currentTabStatus = "pending";

/* =============================
   LOAD OVERALL APPROVAL LIST
============================= */
function loadOverallApprovalList() {
  $("#approvalLoading").removeClass("d-none");
  $("#approvalError").addClass("d-none");
  $("#approvalTable tbody").empty();
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
   Object.keys(filters).forEach(key => {
    if (filters[key] === null || filters[key] === '') delete filters[key];
  });

  fetch(`${API_BASE}/v1/approval/lists`, {
    method: "POST",
    headers: {
      "accept": "application/json",
      "Content-Type": "application/json",
      'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    },
    
      body: JSON.stringify(filters)  // Send filters!
  })
    .then(res => res.json())
    .then(res => {
      $("#approvalLoading").addClass("d-none");

      if (res.status === 403) {
        showToast("This user doesn’t have permission to access this menu right now.", 'danger');
        return;
      }

      const rows = res.clients || [];
      const hasViewPermission = canShowAction('view');
      const colspan = hasViewPermission ? 6 : 5;

      if (!rows.length) {
        $("#approvalTable tbody").html(`
          <tr><td colspan="${colspan}" class="text-center">No records found</td></tr>
        `);
        return;
      }

      rows.forEach(r => {
        let actionCell = '';
        if (hasViewPermission) {
          actionCell = `
            <button class="btn btn-sm btn-primary"
                    onclick="openApprovalModal('${r.client_id}')">
              View
            </button>
          `;
        }

        $("#approvalTable tbody").append(`
          <tr>
            <td>${r.client_id}</td>
            <td>${r.customer_name}</td>
            <td>${r.approved_payments}</td>
            <td>${r.pending_payments}</td>
            <td class="fw-bold">${r.total_payments}</td>
            <td>${actionCell}</td>
          </tr>
        `);
      });
    })
    .catch(err => {
      $("#approvalLoading").addClass("d-none");
      $("#approvalError").removeClass("d-none").text("Failed to load approval list");
      console.error(err);
    });
}

loadCategoryList('category_name')

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
/* =============================
   OPEN MODAL & TAB SWITCH
============================= */
function openApprovalModal(customerId) {
  currentCustomerId = customerId;
  $("#modalCustomerId").text(customerId);
  $("#approvalModal").modal("show");

  currentTabStatus = "pending";
  loadApprovalByClient("pending");
}

// $(document).on("shown.bs.tab", "#approvalTabs a", function () {
//   currentTabStatus = $(this).data("status");
//   loadApprovalByClient(currentTabStatus);
// });

$(document).on("shown.bs.tab", "#approvalTabs a", function () {
  const status = $(this).data("status");

  // Hide both tables first
  $("#clientApprovalTable").closest(".table-responsive").addClass("d-none");
  $("#clientRejectedTable").closest(".table-responsive").addClass("d-none");

  // Hide action bar by default
  $("#approvalActions").addClass("d-none");
  $("#pendingActions").addClass("d-none");

  if (status === "rejected") {
    // Show rejected table
    $("#clientRejectedTable").closest(".table-responsive").removeClass("d-none");
    loadRejectedByClient(status);

  } else {
    // Show approval table
    $("#clientApprovalTable").closest(".table-responsive").removeClass("d-none");
    loadApprovalByClient(status);

    // Show actions only for pending
    // if (status === "pending") {
    //   $("#approvalActions").removeClass("d-none");
    //   $("#pendingActions").removeClass("d-none");
    // }
  }
});
$(document).ready(function () {
  $("#clientRejectedTable").closest(".table-responsive").addClass("d-none");
});


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


/* =============================
   LOAD APPROVAL BY CLIENT
============================= */
function loadApprovalByClient(status) {
  $("#modalLoading").removeClass("d-none");
  $("#clientApprovalTable tbody").empty();
  hideActions();
currentTabStatus=status;
  const hasCheckboxPermission = canShowAction('checkbox');
const getFilterValue = (id) => document.getElementById(id)?.value.trim() || null;

  const filters = {
    from_date: getFilterValue('filterFromDate'),
    to_date: getFilterValue('filterToDate'),
    supplier_name: getFilterValue('filterSupplier'),
    min_amount: getFilterValue('filterMinAmount') ? parseFloat(getFilterValue('filterMinAmount')) : null,
    max_amount: getFilterValue('filterMaxAmount') ? parseFloat(getFilterValue('filterMaxAmount')) : null,
    category_name: getFilterValue('category_name') || null,
    quick_filter: getFilterValue('filterQuick') || null,
     customer_id: currentCustomerId,
      status: status,
  };
   Object.keys(filters).forEach(key => {
    if (filters[key] === null || filters[key] === '') delete filters[key];
  });

  fetch(`${API_BASE}/v1/approval/lists`, {
    method: "POST",
    headers: {
      "accept": "application/json",
      "Content-Type": "application/json",
      'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    },
    body: JSON.stringify(
     
      filters
    )
  })
    .then(res => res.json())
    .then(res => {
      $("#modalLoading").addClass("d-none");

      const rows = res.clients || [];
      const showCheckboxColumn =hasCheckboxPermission && (status === "pending" || status==="approved");
      const colspan = showCheckboxColumn ? 13 : 12;

      if (!rows.length) {
        $("#clientApprovalTable tbody").html(`
          <tr><td colspan="${colspan}" class="text-center">No records</td></tr>
        `);
        return;
      }

      rows.forEach(r => {
        let checkbox = '';
        if (showCheckboxColumn) {
          checkbox = `<input type="checkbox" class="row-check" data-ref="${r.debit_ref_no}">`;
        }

        $("#clientApprovalTable tbody").append(`
          <tr>
            <td>${checkbox}</td>
            <td>${r.invoice_date}</td>
            <td>${r.invoice_ref_no}</td>
            <td>${r.debit_ref_no || "-"}</td>
            <td>${r.description}</td>
            <td>${r.debit_description}</td>
            <td>${fmt(r.credit)}</td>
            <td>${fmt(r.prev_debit)}</td>
            <td>${fmt(r.current_credit)}</td>
            <td>${fmt(r.debit)}</td>
            <td>${fmt(r.balance)}</td>
            <td>${r.payment_by || '-'}</td>
            <td>${formatDateTime(r.payment_at) || '-'}</td>

            <td>${r.approval_status}</td>
          </tr>
        `);
      });

      toggleCheckboxColumn(showCheckboxColumn);
      toggleActions(); // Refresh action buttons visibility
    })
    .catch(err => {
      $("#modalLoading").addClass("d-none");
      console.error(err);
    });
}


/* =============================
   LOAD Rejected BY CLIENT
============================= */
function loadRejectedByClient(status) {
  $("#modalLoading").removeClass("d-none");
  $("#clientRejectedTable tbody").empty();
  hideActions();
const getFilterValue = (id) => document.getElementById(id)?.value.trim() || null;

  const filters = {
    from_date: getFilterValue('filterFromDate'),
    to_date: getFilterValue('filterToDate'),
    supplier_name: getFilterValue('filterSupplier'),
    min_amount: getFilterValue('filterMinAmount') ? parseFloat(getFilterValue('filterMinAmount')) : null,
    max_amount: getFilterValue('filterMaxAmount') ? parseFloat(getFilterValue('filterMaxAmount')) : null,
    category_name: getFilterValue('category_name') || null,
    quick_filter: getFilterValue('filterQuick') || null,
     customer_id: currentCustomerId,
      status: status,
  };
   Object.keys(filters).forEach(key => {
    if (filters[key] === null || filters[key] === '') delete filters[key];
  });

  const hasCheckboxPermission = canShowAction('checkbox');

  fetch(`${API_BASE}/v1/approval/lists`, {
    method: "POST",
    headers: {
      "accept": "application/json",
      "Content-Type": "application/json",
      'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
    },
    body: JSON.stringify(
     
      filters
    )
  })
    .then(res => res.json())
    .then(res => {
      $("#modalLoading").addClass("d-none");

      const rows = res.clients || [];
      const showCheckboxColumn =hasCheckboxPermission && status === "pending";
      const colspan = showCheckboxColumn ? 13 : 12;

      if (!rows.length) {
        $("#clientRejectedTable tbody").html(`
          <tr><td colspan="${colspan}" class="text-center">No records</td></tr>
        `);
        return;
      }

      rows.forEach(r => {
        let checkbox = '';
        if (showCheckboxColumn) {
          checkbox = `<input type="checkbox" class="row-check" data-ref="${r.debit_ref_no}">`;
        }
        $("#clientRejectedTable tbody").append(`
          <tr>
            <td>${r.invoice_date}</td>
            <td>${r.invoice_ref_no}</td>
            <td>${r.debit_ref_no || "-"}</td>
            <td>${r.description}</td>
            <td>${r.debit_description}</td>
            <td>${fmt(r.credit)}</td>
            <td>${fmt(r.prev_debit)}</td>
            <td>${fmt(r.current_credit)}</td>
            <td>${fmt(r.debit)}</td>
            <td>${fmt(r.balance)}</td>
            <td>${r.rejected_by || '-'}</td>
            <td>${formatDateTime(r.rejected_at) || '-'}</td>
            <td>${r.approval_status}</td>
          </tr>
        `);
      });

      toggleCheckboxColumn(showCheckboxColumn);
      toggleActions(); // Refresh action buttons visibility
    })
    .catch(err => {
      $("#modalLoading").addClass("d-none");
      console.error(err);
    });
}
function fmt(val) {
  const num = parseFloat(val);
  return isNaN(num) || num === 0 ? '-' : parseFloat(num.toFixed(2)).toLocaleString();
}

/* =============================
   CHECKBOX COLUMN VISIBILITY
============================= */
function toggleCheckboxColumn(show) {
  const $checkboxHeader = $("#clientApprovalTable thead th.checkbox-col"); // Make sure your <th> has class="checkbox-col"
  const $checkboxCells = $("#clientApprovalTable td:first-child");

  if (show) {
    $checkboxHeader.show();
    $checkboxCells.show();
    $("#selectAllRows").prop("checked", false).show();
  } else {
    $checkboxHeader.hide();
    $checkboxCells.hide();
    $("#selectAllRows").hide();
  }
}

/* =============================
   CHECKBOX HANDLING
============================= */
$(document).on("change", ".row-check, #selectAllRows", function () {
  if (this.id === "selectAllRows") {
    $(".row-check").prop("checked", this.checked);
  }
  toggleActions();
});

/* =============================
   ACTION BUTTONS VISIBILITY
============================= */
function toggleActions() {
  const hasChecked = $(".row-check:checked").length > 0;
  const hasCheckboxPermission = canShowAction('checkbox');
  const hasApprove = canShowAction('approve');
  const hasReject = canShowAction('reject');

  // Always hide all action containers first
  $("#approvalActions, #pendingActions, #draftActions").addClass("d-none");

  if (!hasChecked || !hasCheckboxPermission) {
    return; // No actions if nothing selected or no checkbox permission
  }
  
  if (currentTabStatus === "pending") {
    const anyPendingAction = hasApprove || hasReject;

    if (anyPendingAction) {
      $("#approvalActions").removeClass("d-none");
      $("#pendingActions").removeClass("d-none");

      // Show only permitted buttons
      $("#btnApprove").toggle(hasApprove);
      $("#btnReject").toggle(hasReject);
      $("#btnRevoke").toggle(false);
    }
    // If no approve/reject permission → entire pendingActions stays hidden
  } else if (currentTabStatus === "draft") {
    $("#approvalActions").removeClass("d-none");
    $("#draftActions").removeClass("d-none");
    $("#btnRevoke").toggle(false);
  }else if( currentTabStatus === "approved") {
    
    const anyApprovedAction = hasApprove || hasReject;
    if (anyApprovedAction) {
      $("#approvalActions").removeClass("d-none");
      $("#pendingActions").removeClass("d-none");
      
      $("#btnApprove").toggle(false);
      $("#btnReject").toggle(false);
      $("#btnRevoke").toggle(true);
      
    }
  }
}

function hideActions() {
  $("#approvalActions, #pendingActions, #draftActions").addClass("d-none");
}

function toFloat(value, defaultValue = 0) {
  if (value === null || value === undefined) return defaultValue;
  const num = parseFloat(String(value).replace(/,/g, "").trim());
  return Number.isNaN(num) ? defaultValue : num;
}

/* =============================
   BULK STATUS UPDATE
============================= */
function bulkUpdateStatus(status) {
  const selectedRows = $(".row-check:checked");
  if (!selectedRows.length) return;

  // ... (your existing bulkUpdateStatus logic remains unchanged)
  if (status === "REJECTED") {
    // Reject API
    const payload = {
      payments: selectedRows.map(function () {
        const $row = $(this).closest("tr");
        return {
          debit_ref_no: $(this).data("ref"),
          invoice_ref_no: $row.find("td:eq(2)").text(),
          debit_description: $row.find("td:eq(5)").text(),
          debit: toFloat($row.find("td:eq(9)").text()) || 0,
          balance: toFloat($row.find("td:eq(10)").text()) || 0,
          approval_status: "rejected",
          updated_by: getCookie('user_id')
        };
      }).get()
    };

    fetch(`${API_BASE}/v1/payments/revert`, {
      method: "PUT",
      headers: {
        "accept": "application/json",
        "Content-Type": "application/json",
        'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
      },
      body: JSON.stringify(payload)
    })
      .then(() => {
        loadApprovalByClient(currentTabStatus);
        loadOverallApprovalList();
        showToast("Payments rejected successfully", "success");
      })
      .catch(err => showToast("Reject failed", "danger"));
  } else {
    const payload = {
      payments: selectedRows.map(function () {
        const $row = $(this).closest("tr");
        return {
          invoice_ref_no: $row.find("td:eq(2)").text(),
          debit_ref_no: $(this).data("ref"),
          approval_status: status,
          approved_by: getCookie('user_id')
        };
      }).get()
    };

    fetch(`${API_BASE}/v1/approval/update`, {
      method: "PUT",
      headers: {
        "accept": "application/json",
        "Content-Type": "application/json",
        'Authorization': `Bearer ${localStorage.getItem('token') || getCookie('access_token')}`
      },
      body: JSON.stringify(payload)
    })
      .then(() => {
        loadApprovalByClient(currentTabStatus);
        loadOverallApprovalList();
        showToast("Status updated successfully", "success");
      })
      .catch(err => showToast("Update failed", "danger"));
  }
}

/* =============================
   INIT
============================= */
$(document).ready(function () {
  loadOverallApprovalList();
});
 document.getElementById('applyFilters')?.addEventListener('click', loadOverallApprovalList);
    document.getElementById('clearFilters')?.addEventListener('click', () => {
      document.querySelectorAll('#filterCard input, #filterCard select').forEach(el => {
        if (el.type === 'date' || el.type === 'text' || el.type === 'number') el.value = '';
        if (el.tagName === 'SELECT') el.selectedIndex = 0;
      });
      loadOverallApprovalList();
    });
    
    $(function () {


  $('#dateRangeTrigger').daterangepicker({
    autoUpdateInput: false,
    opens: 'right',
    drops: 'down',  
    showDropdowns: true,   
    minYear:2018,
    maxYear: moment().year(),   
    ranges: {
      'Today': [moment(), moment()],
      'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
      'This Week': [moment().startOf('week'), moment().endOf('week')],
      'This Month': [moment().startOf('month'), moment().endOf('month')],
      'This Year': [moment().startOf('year'), moment().endOf('year')]
    }
  });

  // Open range picker when clicking either date input
  $('#filterFromDate, #filterToDate').on('click focus', function () {
    $('#dateRangeTrigger').trigger('click');
  });

  // Apply selected range to two inputs
  $('#dateRangeTrigger').on('apply.daterangepicker', function (ev, picker) {
    $('#filterFromDate').val(picker.startDate.format('YYYY-MM-DD'));
    $('#filterToDate').val(picker.endDate.format('YYYY-MM-DD'));
  });

});