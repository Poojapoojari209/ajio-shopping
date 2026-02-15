/* =========================
   AJIO Address Book (JWT)
   File: static/js/address_book.js
========================= */

let editingAddressId = null;

/* ---------- Helpers ---------- */
function getToken() {
  return localStorage.getItem("access");
}

function setMsg(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text || "";
}

function escapeHtml(str) {
  return String(str || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

/* ---------- Panel open/close ---------- */
window.openAddressPanel = function () {
  document.getElementById("addressPanel")?.classList.add("open");
  document.getElementById("addressOverlay")?.classList.add("show");
};

window.closeAddressPanel = function () {
  document.getElementById("addressPanel")?.classList.remove("open");
  document.getElementById("addressOverlay")?.classList.remove("show");
  resetForm();
};

/* ---------- Reset form ---------- */
function resetForm() {
  const form = document.getElementById("addressForm");
  if (!form) return;

  editingAddressId = null;
  form.reset();

  // default radio HOME
  const home = form.querySelector('input[name="type"][value="HOME"]');
  if (home) home.checked = true;

  // title back to add
  const h2 = document.querySelector("#addressPanel .panel-header h2");
  if (h2) h2.textContent = "Add new address";

  setMsg("addrMsg", "");
}

/* ---------- Load & render addresses ---------- */
document.addEventListener("DOMContentLoaded", () => {
  loadAddresses();

  const form = document.getElementById("addressForm");
  if (form) form.addEventListener("submit", handleSubmit);
});

async function loadAddresses() {
  const token = getToken();
  const box = document.getElementById("addressCards");
  if (!box) return;

  setMsg("addrListMsg", "");
  box.innerHTML = "";

  if (!token) {
    setMsg("addrListMsg", "Please login to view saved addresses.");
    return;
  }

  try {
    const res = await fetch("/api/users/addresses/", {
      headers: { "Authorization": "Bearer " + token }
    });

    const data = await res.json().catch(() => []);

    if (!res.ok) {
      console.error(data);
      setMsg("addrListMsg", "Unable to load addresses.");
      return;
    }

    if (!Array.isArray(data) || data.length === 0) {
      // no cards: only add box will show
      return;
    }

    box.innerHTML = data.map(renderCard).join("");

  } catch (err) {
    console.error(err);
    setMsg("addrListMsg", "Network error. Check console.");
  }
}

function renderCard(a) {
  const isDefault = !!a.is_default;

  // NOTE: Use JSON stringify in onclick requires safe escaping, so we pass only id and fetch full object from dataset
  // Here we attach all fields as data-* so edit can read safely.
  return `
    <div class="mobaddr-box ${isDefault ? "active-address" : ""}"
         data-id="${a.id}"
         data-name="${escapeHtml(a.name)}"
         data-mobile="${escapeHtml(a.mobile)}"
         data-pincode="${escapeHtml(a.pincode)}"
         data-area="${escapeHtml(a.area)}"
         data-address_line="${escapeHtml(a.address_line)}"
         data-landmark="${escapeHtml(a.landmark || "")}"
         data-city="${escapeHtml(a.city)}"
         data-state="${escapeHtml(a.state)}"
         data-type="${escapeHtml(a.type || "OTHER")}"
         data-is_default="${isDefault}">
      
      <div class="address-info-wrapper">
        <div class="address-info-desk-name">
          <span class="address-book-user-name"><strong>${escapeHtml(a.name || "User")}</strong></span>
          <span class="address-book-addtype">${escapeHtml(a.type || "OTHER")}</span>
        </div>

        ${isDefault ? `<div class="default-address-tag"><strong>Default</strong></div>` : ""}

        <div class="address-info">
          <div class="address-first">${escapeHtml(a.address_line)}</div>
          <div class="address-third">${escapeHtml((a.city || "").toUpperCase())}, ${escapeHtml((a.state || "").toUpperCase())}</div>
          <div class="address-fifth"><strong>India - </strong>${escapeHtml(a.pincode)}</div>
        </div>

        <div class="address-mobile">
          <strong>Phone : </strong><span class="addFontWeight">${escapeHtml(a.mobile)}</span>
        </div>
      </div>

      <div class="edit-remove-button-container">
        <a href="javascript:void(0);" class="mobaddr-editc" onclick="editAddress(${a.id})">Edit</a>
        <a href="javascript:void(0);" class="mobaddr-icon-mar" onclick="deleteAddress(${a.id})">Delete</a>
        ${isDefault ? `<div class="mobaddr-selected-addr">Address Selected</div>` : ""}
      </div>
    </div>
  `;
}

/* ---------- Edit Address (open panel + prefill) ---------- */
window.editAddress = function (id) {
  const card = document.querySelector(`.mobaddr-box[data-id="${id}"]`);
  if (!card) return;

  const form = document.getElementById("addressForm");
  if (!form) return;

  editingAddressId = id;

  const h2 = document.querySelector("#addressPanel .panel-header h2");
  if (h2) h2.textContent = "Edit address";

  form.name.value = card.dataset.name || "";
  form.mobile.value = card.dataset.mobile || "";
  form.pincode.value = card.dataset.pincode || "";
  form.area.value = card.dataset.area || "";
  form.address_line.value = card.dataset.address_line || "";
  form.landmark.value = card.dataset.landmark || "";
  form.city.value = card.dataset.city || "";
  form.state.value = card.dataset.state || "";

  const type = (card.dataset.type || "OTHER").toUpperCase();
  const radio = form.querySelector(`input[name="type"][value="${type}"]`);
  if (radio) radio.checked = true;

  form.is_default.checked = (card.dataset.is_default === "true");

  setMsg("addrMsg", "");
  openAddressPanel();
};

/* ---------- Delete Address ---------- */
window.deleteAddress = async function (id) {
  if (!confirm("Delete this address?")) return;

  const token = getToken();
  if (!token) {
    alert("Please login first");
    return;
  }

  try {
    const res = await fetch(`/api/users/address/${id}/delete/`, {
      method: "DELETE",
      headers: { "Authorization": "Bearer " + token }
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      console.error(data);
      alert(data.error || "Delete failed");
      return;
    }

    // refresh list
    await loadAddresses();

  } catch (err) {
    console.error(err);
    alert("Network error. Check console.");
  }
};

/* ---------- Submit (Add or Update) ---------- */
async function handleSubmit(e) {
  e.preventDefault();

  const token = getToken();
  if (!token) {
    setMsg("addrMsg", "Please login first.");
    return;
  }

  const form = e.target;

  const payload = {
    name: form.name.value.trim(),
    mobile: form.mobile.value.trim(),
    pincode: form.pincode.value.trim(),
    area: form.area.value.trim(),
    address_line: form.address_line.value.trim(),
    landmark: form.landmark.value.trim(),
    city: form.city.value.trim(),
    state: form.state.value.trim(),
    type: form.querySelector('input[name="type"]:checked')?.value || "HOME",
    is_default: form.is_default.checked
  };

  const isEdit = editingAddressId !== null;
  const url = isEdit
    ? `/api/users/address/${editingAddressId}/update/`
    : `/api/users/address/add/`;

  const method = isEdit ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method,
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      console.error(data);
      setMsg("addrMsg", "Address not saved. Check all fields.");
      return;
    }

    setMsg("addrMsg", isEdit ? "Address updated successfully" : "Address added successfully");

    // refresh list & close panel
    setTimeout(async () => {
      closeAddressPanel();
      await loadAddresses();
    }, 500);

  } catch (err) {
    console.error(err);
    setMsg("addrMsg", "Network error. Check console.");
  }
}
