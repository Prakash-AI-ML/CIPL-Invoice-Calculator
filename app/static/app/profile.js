// Profile Settings Logic
document.getElementById("edit_profile_image").addEventListener("change", e => {
    const file = e.target.files[0];
    if (file) {
        document.getElementById("edit_profile_image_preview").src =
            URL.createObjectURL(file);
    }
});

document.getElementById("edit_logo_image").addEventListener("change", e => {
    const file = e.target.files[0];
    if (file) {
        document.getElementById("edit_logo_image_preview").src =
            URL.createObjectURL(file);
    }
});


async function updateProfileImage(profile_image,logo_image,id){
    const profileImageInput = document.getElementById(profile_image);
    const logoImageInput = document.getElementById(logo_image);
    
    const formData = new FormData();
    
    if (profileImageInput.files.length > 0) {
        formData.append("profile_image", profileImageInput.files[0]);
    }
    
    if (logoImageInput.files.length > 0) {
        formData.append("company_logo", logoImageInput.files[0]);
    }
    if(profileImageInput.files.length > 0 ||
logoImageInput.files.length > 0){
    const res = await fetch(`${API_BASE}/v1/user/profile/${id}`, {
        method: "post",
        headers: {
            "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
        },
        body: formData
    });
    
    if (res.ok) {
        location.reload();
      } else {
        alert("Failed to delete user");
      }
    }else{
    location.reload();

  }
}

async function loadProfile() {
  const loading = document.getElementById('profileLoading');
  const errorEl = document.getElementById('profileError');
  const form = document.getElementById('profileForm');

  loading.classList.remove('d-none');
  errorEl.classList.add('d-none');

  try {

    const userId = getCookie('user_id') // Adjust based on your JWT claims

    const res = await fetch(`${API_BASE}/v1/users/read/${userId}`, {
      headers: { "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}` }
    });

    if (!res.ok) throw new Error("Failed to load profile");

    const data = await res.json();

    // Fill form
    document.getElementById('userId').value = data.id;
    document.getElementById('username').value = data.username || '';
    document.getElementById('email').value = data.email || '';
    document.getElementById('roleName').value = data.role?.role_name || 'User';
    document.getElementById('companyName').value = data.company;
    document.getElementById('phone').value = data.mobile;
        document.getElementById("edit_profile_image_preview").src = data.profile?"/static/app/images/profiles/"+data.profile:"/static/app/images/profiles/default-profile.png";
        document.getElementById("edit_logo_image_preview").src = data.logo?"/static/app/images/logos/"+data.logo:"/static/app/images/logos/default-profile.png";
  } catch (err) {
    errorEl.textContent = err.message || "Could not load profile";
    errorEl.classList.remove('d-none');
  } finally {
    loading.classList.add('d-none');
  }
}

// Toggle password visibility
document.querySelectorAll('.toggle-pwd').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = btn.previousElementSibling;
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
      input.type = 'text';
      icon.classList.replace('bi-eye', 'bi-eye-slash');
    } else {
      input.type = 'password';
      icon.classList.replace('bi-eye-slash', 'bi-eye');
    }
  });
});

// Handle form submit
document.getElementById('profileForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const successEl = document.getElementById('profileSuccess');
  const errorEl = document.getElementById('profileError');
  const saveText = document.getElementById('saveText');
  const saveSpinner = document.getElementById('saveSpinner');
  const passwordError = document.getElementById('passwordError');

  successEl.classList.add('d-none');
  errorEl.classList.add('d-none');
  passwordError.classList.add('d-none');

  const userId = document.getElementById('userId').value;
  const username = document.getElementById('username').value.trim();
  const newPassword = document.getElementById('newPassword').value;
  const confirmPassword = document.getElementById('confirmPassword').value;
  const company= document.getElementById('companyName').value;
  const phone=    Number(document.getElementById('phone').value)>0?Number(document.getElementById('phone').value):null ;
  // Validate password match if provided
  if (newPassword || confirmPassword) {
    if (newPassword !== confirmPassword) {
      passwordError.textContent = "Passwords do not match";
      passwordError.classList.remove('d-none');
      return;
    }
    if (newPassword.length < 6) {
      passwordError.textContent = "Password must be at least 6 characters";
      passwordError.classList.remove('d-none');
      return;
    }
  }

  const body = {
    username: username,
    company_name: company,
    mobile: phone,
    email: document.getElementById('email').value, // Read-only, but send as-is
    // role_id: 0,        // Not editable
    // group_id: 0,       // Not editable
    // status: 0,         // Not editable
    updated_by: userId // or current user
  };

  if (newPassword) {
    body.password = newPassword;
  }

  saveText.textContent = "Saving...";
  saveSpinner.classList.remove('d-none');

  try {
    const res = await fetch(`${API_BASE}/v1/users/update/${userId}`, {
      method: 'PUT', // or PUT if your API uses PUT
      headers: {
        'Content-Type': 'application/json',
        "Authorization": `Bearer ${localStorage.getItem("token") || getCookie("access_token")}`
      },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || "Update failed");
    }

    const result = await res.json();
    
        updateProfileImage("edit_profile_image","edit_logo_image",userId);
    successEl.textContent = "Profile updated successfully!";
    successEl.classList.remove('d-none');

  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('d-none');
  } finally {
    saveText.textContent = "Update Profile";
    saveSpinner.classList.add('d-none');
  }
});

// Load profile on page load
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('profileForm')) {
    loadProfile();
  }
});