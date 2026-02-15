document.addEventListener("DOMContentLoaded", loadCart);

/* ---------------- Helpers ---------------- */

function getToken() {
  return localStorage.getItem("access");
}

function safeSetText(id, text) {
  const el = document.getElementById(id);
  if (el) el.innerText = text;
}

// escape strings for HTML attributes / safety
function escAttr(v) {
  return String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

/* =========================================================
   WISHLIST (LOCAL STORAGE) - FULL OBJECTS
========================================================= */
window.WISHLIST_KEY = window.WISHLIST_KEY || "wishlist_items";

function readWishlist() {
  try {
    const list = JSON.parse(localStorage.getItem(window.WISHLIST_KEY));
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
}

function saveWishlist(list) {
  localStorage.setItem(window.WISHLIST_KEY, JSON.stringify(list));
  if (window.updateWishlistBadge) window.updateWishlistBadge();
}

function addToWishlist(product) {
  let list = readWishlist();
  const pid = String(product.id);

  // ensure unique by id
  list = list.filter(x => String(x.id) !== pid);
  list.push(product);

  saveWishlist(list);
}

function wishlistCount() {
  return readWishlist().length;
}

/* ---------------- Load Cart ---------------- */

function loadCart() {
  const token = getToken();

  if (!token) {
    renderEmptyCart("Please login to view your cart.");
    return;
  }

  fetch("/api/cart/", {
    method: "GET",
    headers: {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json"
    }
  })
    .then(res => {
      if (res.status === 401) {
        renderEmptyCart("Please login to view your cart.");
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data || !Array.isArray(data.items) || data.items.length === 0) {
        renderEmptyCart("Your cart is empty.");
        return;
      }
      renderCart(data.items);
    })
    .catch(err => console.error("Cart error:", err));
}

/* ---------------- Render Cart ---------------- */

function renderCart(items) {
  const cartContainer = document.getElementById("cartItems");
  if (!cartContainer) return;

  cartContainer.innerHTML = "";

  let total = 0;
  let totalItems = 0;

  items.forEach(item => {
    if (!item || !item.product) return;

    const unitPrice = Number(item.product.discount_price || item.product.price || 0);
    const qty = Number(item.quantity || 1);
    const sizeText = item.size || "-";

    let sizes = Array.isArray(item.product.sizes) ? item.product.sizes : [];
    sizes = sizes.map(s => {
      if (typeof s === "string" || typeof s === "number") return String(s);
      if (s && typeof s === "object") return String(s.size || s.value || s.label || "");
      return "";
    }).filter(Boolean);

    total += unitPrice * qty;
    totalItems += qty;

    const brandName = item.product.brand || "";

    cartContainer.innerHTML += `
      <div class="ajio-cart-item"
        data-item-id="${item.id}"
        data-pid="${escAttr(item.product.id)}"
        data-name="${escAttr(item.product.name)}"
        data-brand="${escAttr(brandName)}"
        data-price="${escAttr(unitPrice)}"
        data-image="${escAttr(item.product.image)}"
      >

        <div class="ajio-ci-img">
          <img src="${item.product.image}" alt="${escAttr(item.product.name)}">
        </div>

        <div class="ajio-ci-mid">
          <div class="ajio-ci-name">${item.product.name}</div>

          <div class="ajio-ci-meta">

            <!-- SIZE DROPDOWN -->
            <div class="ajio-meta size-select">
              <span class="meta-label">Size</span>

              <button type="button" class="size-btn" data-item-id="${item.id}">
                <span class="meta-value" id="sizeVal-${item.id}">${sizeText}</span>
                <i class="fa-solid fa-chevron-down meta-down"></i>
              </button>

              <div class="size-menu" id="sizeMenu-${item.id}">
                ${
                  sizes.length
                    ? sizes.map(s => `
                      <div class="size-opt" data-item-id="${item.id}" data-size="${escAttr(s)}">
                        ${s}
                      </div>
                    `).join("")
                    : `<div class="size-opt disabled">No sizes</div>`
                }
              </div>
            </div>

            <!-- QTY -->
<div class="ajio-meta ajio-qty">
  <span class="meta-label">Qty</span>

  <button class="qty-btn qty-minus" type="button" onclick="changeQty(${item.id}, -1)">-</button>


  <span class="qty-val" id="qtyVal-${item.id}">${qty}</span>

  <button class="qty-btn qty-plus" type="button"
    onclick="changeQty(${item.id}, 1)">
    +
  </button>
</div>

          </div>

          <div class="ajio-ci-actions">
            <button class="link-btn" type="button" onclick="deleteCartItem(${item.id}, this)">Delete</button>
            <span class="sep">|</span>

            <button class="link-btn" type="button" onclick="moveToWishlist(${item.id}, this)">
              <i class="fa-regular fa-heart"></i> Move to Wishlist
            </button>
          </div>
        </div>

        <div class="ajio-ci-price">
          Rs. <span id="lineTotal-${item.id}">${(unitPrice * qty).toFixed(2)}</span>
        </div>

      </div>
    `;
  });

  safeSetText("bagTotal", `₹${total.toFixed(2)}`);
  safeSetText("orderTotal", `₹${(total + 29).toFixed(2)}`);

  const cartCountEl = document.getElementById("cartCount");
  if (cartCountEl) cartCountEl.innerText = totalItems;
}

function renderEmptyCart(message) {

  // Hide "My Bag" title
  const bagHeading = document.getElementById("bagHeading");
  if (bagHeading) bagHeading.style.display = "none";


  const cartContainer = document.getElementById("cartItems");
  const rightBox = document.querySelector(".cart-right");

  // Hide order summary
  if (rightBox) rightBox.style.display = "none";

  // Get wishlist preview
  const wishlist = readWishlist().slice(0, 3);

  let previewImages = wishlist.map(item => `
      <div class="empty-preview-item">
        <img src="${item.image}" alt="${item.name}">
      </div>
  `).join("");

  cartContainer.innerHTML = `
    <div class="empty-cart-wrapper">

      <h2 class="empty-title">Your Shopping Bag is Empty!!</h2>
      <p class="empty-subtitle">
        You have items in your wishlist waiting to be yours!
      </p>

      <div class="empty-preview">
        ${previewImages || ""}
      </div>

      <div class="empty-actions">
        <a href="/wishlist/" class="empty-btn">ADD FROM WISHLIST</a>
        <a href="/" class="continue-link">CONTINUE SHOPPING</a>
      </div>

    </div>
  `;

  safeSetText("bagTotal", "₹0");
  safeSetText("orderTotal", "₹0");

  const cartCountEl = document.getElementById("cartCount");
  if (cartCountEl) cartCountEl.innerText = 0;
}

/* ---------------- Qty Update ---------------- */

window.changeQty = function (cartItemId, delta) {
  const token = getToken();
  if (!token) return;

  const qtyEl = document.getElementById(`qtyVal-${cartItemId}`);
  if (!qtyEl) return;

  let currentQty = parseInt(qtyEl.innerText.trim(), 10);
  if (isNaN(currentQty)) currentQty = 1;

  let newQty = currentQty + delta;

  // ✅ If qty becomes 0 → remove item
  if (newQty === 0) {
    fetch(`/api/cart/remove/${cartItemId}/`, {
      method: "DELETE",
      headers: {
        "Authorization": "Bearer " + token
      }
    })
      .then(res => {
        if (!res.ok) throw new Error("Remove failed");
        return res.json().catch(() => ({}));
      })
      .then(() => {
        loadCart();
        if (window.loadHeaderCartPreview) window.loadHeaderCartPreview();
      })
      .catch(err => console.error(err));

    return;
  }

  // Prevent negative values
  if (newQty < 0) return;

  // Otherwise update quantity
  fetch(`/api/cart/item/${cartItemId}/`, {
    method: "PATCH",
    headers: {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ quantity: newQty })
  })
    .then(async res => {
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(data.error || data.detail || "Quantity update failed");
        return;
      }

      loadCart();
      if (window.loadHeaderCartPreview) window.loadHeaderCartPreview();
    })
    .catch(console.error);
};



/* ----------------  Move to Wishlist (NOW INCLUDES SIZE) ---------------- */

window.moveToWishlist = function (cartItemId, btnEl) {
  const row = btnEl.closest(".ajio-cart-item");
  if (!row) return;

  // get selected size from UI
  const sizeEl = document.getElementById(`sizeVal-${cartItemId}`);
  const selectedSize = sizeEl ? sizeEl.innerText.trim() : "-";

  // Save FULL product in wishlist_items including size
  addToWishlist({
    id: row.dataset.pid,
    name: row.dataset.name || "",
    brand: row.dataset.brand || "",
    price: row.dataset.price || "",
    image: row.dataset.image || "",
    size: selectedSize 
  });

  console.log("WISHLIST COUNT:", wishlistCount());

  // Remove from cart DB
  window.deleteCartItem(cartItemId, btnEl);

  // Redirect to wishlist page
  setTimeout(() => {
    window.location.href = "/wishlist/";
  }, 200);
};

/* ---------------- Size Dropdown + Update ---------------- */

document.addEventListener("click", (e) => {
  const sizeBtn = e.target.closest(".size-btn");
  if (sizeBtn) {
    const itemId = sizeBtn.dataset.itemId;

    document.querySelectorAll(".size-menu.show").forEach(m => m.classList.remove("show"));

    const menu = document.getElementById(`sizeMenu-${itemId}`);
    if (menu) menu.classList.toggle("show");
    return;
  }

  const opt = e.target.closest(".size-opt");
  if (opt && opt.dataset.size) {
    const itemId = opt.dataset.itemId;
    const newSize = opt.dataset.size;
    updateCartSize(itemId, newSize);
    return;
  }

  document.querySelectorAll(".size-menu.show").forEach(m => m.classList.remove("show"));
});

function updateCartSize(itemId, newSize) {
  const token = getToken();
  if (!token) return;

  fetch(`/api/cart/item/${itemId}/size/`, {
    method: "PATCH",
    headers: {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ size: newSize })
  })
    .then(async res => {
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(data.error || "Size update failed");
        return;
      }

      // update UI
      const sizeVal = document.getElementById(`sizeVal-${itemId}`);
      if (sizeVal) sizeVal.innerText = newSize;

      const menu = document.getElementById(`sizeMenu-${itemId}`);
      if (menu) menu.classList.remove("show");

      loadCart();
    })
    .catch(console.error);
}
