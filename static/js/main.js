/* ==========================
   GLOBALS
========================== */
let qvSelectedSize = null;
let qvProductId = null;

const QV_FALLBACK_IMG = window.QV_FALLBACK_IMG || "/static/images/no-image.png";

/* ==========================
   AUTH HELPERS (JWT)
========================== */
function decodeJwtPayload(token) {
  try {
    const base64Url = token.split(".")[1];
    if (!base64Url) return null;

    let base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");

    //  add padding
    while (base64.length % 4 !== 0) {
      base64 += "=";
    }

    const jsonPayload = atob(base64);
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

async function isLoggedInServer() {
  try {
    const res = await fetch("/api/users/me/", { credentials: "include" });
    if (!res.ok) return false;

    const p = await res.json().catch(() => ({}));
    if (p.first_name) localStorage.setItem("first_name", p.first_name);
    if (p.screen_name) localStorage.setItem("screen_name", p.screen_name);
    if (p.phone) localStorage.setItem("phone", p.phone);

    return true;
  } catch {
    return false;
  }
}

function isTokenValid(token) {
  if (!token) return false;
  const payload = decodeJwtPayload(token);
  if (!payload || !payload.exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return payload.exp > now;
}

function clearAuth() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("username");
  localStorage.removeItem("user_id");
  localStorage.removeItem("first_name");
  localStorage.removeItem("screen_name");
  localStorage.removeItem("phone");
}

/* ==========================
   SMALL HELPERS
========================== */
function normalizeImgUrl(url) {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  if (url.startsWith("/")) return url;
  return "/" + url; // "media/.." -> "/media/.."
}

function extractImages(p) {
  const list = [];

  // p.images can be ["..",".."] OR [{image:".."}]
  if (Array.isArray(p.images)) {
    p.images.forEach(item => {
      if (!item) return;
      if (typeof item === "string") list.push(item);
      else if (typeof item === "object") list.push(item.image || item.url || item.src || "");
    });
  }

  // fallback single
  if (list.length === 0 && p.image) list.push(p.image);

  return list.map(normalizeImgUrl).filter(Boolean);
}


/* ==========================
   QUICK VIEW COLOR HELPERS
========================== */
function pickBaseColorName(p) {
  return (
    p?.color_name ||
    p?.base_color?.name ||
    p?.color?.name ||
    p?.colour_name ||
    (typeof p?.color === "string" ? p.color : "") ||
    "-"
  );
}

function pickBaseColorHex(p) {
  return (
    p?.base_color?.hex_code ||
    p?.color?.hex_code ||
    p?.base_color_hex ||
    p?.hex_code ||
    p?.color_hex ||
    "#f0f0f0"
  );
}

function pickVariants(p) {
  return (
    p?.variants ||
    p?.color_variants ||
    p?.variant_colors ||
    p?.variant_list ||
    []
  );
}

function renderQuickViewImages(images, mainImg, thumbs) {
  let imgs = (images || []).map(normalizeImgUrl).filter(Boolean);
  if (!imgs.length) imgs = [QV_FALLBACK_IMG];

  mainImg.onerror = () => { mainImg.src = QV_FALLBACK_IMG; };
  mainImg.src = imgs[0];

  thumbs.innerHTML = "";

  imgs.forEach((url, idx) => {
    const t = document.createElement("img");
    t.src = url;
    t.className = "qv-thumb" + (idx === 0 ? " active" : "");
    t.onerror = () => t.remove();

    t.addEventListener("click", () => {
      mainImg.src = url;
      thumbs.querySelectorAll(".qv-thumb").forEach(x => x.classList.remove("active"));
      t.classList.add("active");
    });

    thumbs.appendChild(t);
  });
}

function renderQuickViewColors(p, mainImg, thumbs) {
  //  these IDs MUST exist in your quick view modal HTML
  // <b id="qvColorName">-</b>
  // <a id="qvMoreColors" style="display:none;">+ More</a>
  // <div id="qvColorSwatches"></div>

  const colorNameEl = document.getElementById("qvColorName");
  const swatchesEl  = document.getElementById("qvColorSwatches");
  const moreColors  = document.getElementById("qvMoreColors");

  if (!colorNameEl || !swatchesEl) return;

  swatchesEl.innerHTML = "";
  if (moreColors) {
    moreColors.style.display = "none";
    moreColors.onclick = null;
  }

  const baseName = pickBaseColorName(p);
  const baseHex  = pickBaseColorHex(p);
  colorNameEl.innerText = baseName;

  const baseImages = extractImages(p);

  // BASE swatch
  const baseBtn = document.createElement("button");
  baseBtn.type = "button";
  baseBtn.className = "qv-swatch active";
  baseBtn.title = baseName;
  baseBtn.style.background = baseHex;

  baseBtn.addEventListener("click", () => {
    swatchesEl.querySelectorAll(".qv-swatch").forEach(x => x.classList.remove("active"));
    baseBtn.classList.add("active");
    colorNameEl.innerText = baseName;
    renderQuickViewImages(baseImages, mainImg, thumbs);
  });

  swatchesEl.appendChild(baseBtn);

  const variants = pickVariants(p);
  if (!Array.isArray(variants) || variants.length === 0) return;

  const maxVisible = 3;
  const extra = [];

  variants.forEach((v, idx) => {
    const vName = v?.color?.name || v?.name || "-";
    const vHex  = v?.color?.hex_code || v?.hex_code || "#ccc";
    const vImgs = v?.images || v?.variant_images || [];

    const b = document.createElement("button");
    b.type = "button";
    b.className = "qv-swatch";
    b.title = vName;
    b.style.background = vHex;

    b.addEventListener("click", () => {
      swatchesEl.querySelectorAll(".qv-swatch").forEach(x => x.classList.remove("active"));
      b.classList.add("active");
      colorNameEl.innerText = vName;
      renderQuickViewImages(vImgs, mainImg, thumbs);
    });

    if (idx < maxVisible) swatchesEl.appendChild(b);
    else extra.push(b);
  });

  if (moreColors && extra.length) {
    moreColors.style.display = "inline";
    moreColors.onclick = () => {
      extra.forEach(btn => swatchesEl.appendChild(btn));
      moreColors.style.display = "none";
    };
  }
}

/* ==========================
   DOM READY (ONE TIME)
========================== */
document.addEventListener("DOMContentLoaded", function () {

  // HOME product fetch (skip listing page)
  const container = document.getElementById("productContainer");
  const isProductsPage = window.location.pathname.includes("/products-page/");
  if (container && !isProductsPage) {
    fetch("/api/products/")
      .then(res => res.json())
      .then(data => {
        container.innerHTML = "";
        (data || []).forEach(product => {
          const img = normalizeImgUrl(product.image) || QV_FALLBACK_IMG;
          container.innerHTML += `
            <div class="product-card">
              <img src="${img}" alt="${product.name || ""}" onerror="this.src='${QV_FALLBACK_IMG}'">
              <h4>${product.brand || ""}</h4>
              <p>${product.name || ""}</p>
              <div class="price">₹${product.price || ""}</div>
            </div>
          `;
        });
      })
      .catch(err => console.error("Home product fetch error:", err));
  }

  // sliders (only if elements exist)
  initSlider({
    rootSelector: ".main-slider",
    slideSelector: ".slide",
    prevSelector: ".prev",
    nextSelector: ".next",
    dotsSelector: ".dots",
    dotClass: "dot",
    activeClass: "active",
    interval: 4000
  });

  initSlider({
    rootSelector: ".sub-slider",
    slideSelector: ".sub-slide",
    prevSelector: ".sub-prev",
    nextSelector: ".sub-next",
    dotsSelector: ".sub-dots",
    dotClass: "sub-dot",
    activeClass: "active",
    interval: 5000
  });

  // topbar + cart badge
  updateTopbar();
  updateCartCount();

  // hover bag dropdown
  const wrap = document.querySelector(".cart-hover-wrap");
  if (wrap) wrap.addEventListener("mouseenter", loadHeaderCartPreview);

  // QUICK VIEW OPEN (event delegation)
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".quick-view-btn");
    if (!btn) return;

    e.preventDefault();
    e.stopPropagation();

    const productId = btn.dataset.id;
    if (!productId) return;

    openQuickView(productId);
  });

  // quick view close
  document.getElementById("qvClose")?.addEventListener("click", closeQuickView);
  document.getElementById("qvOverlay")?.addEventListener("click", closeQuickView);

  // ESC close
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeQuickView();
  });

  //  quick view add to bag
  document.getElementById("qvAddBtn")?.addEventListener("click", () => {
    const err = document.getElementById("qvSizeError");
    if (!qvSelectedSize) {
      if (err) err.style.display = "block";
      return;
    }
    addToCartFromQuickView(qvProductId, qvSelectedSize);
  });

  // wishlist init (product detail only)
  initWishlistButton();

  // nav search
  initNavSearch();
});

/* ==========================
   SLIDER (Reusable)
========================== */
function initSlider({
  rootSelector,
  slideSelector,
  prevSelector,
  nextSelector,
  dotsSelector,
  dotClass,
  activeClass,
  interval
}) {
  const root = document.querySelector(rootSelector);
  if (!root) return;

  const slides = root.querySelectorAll(slideSelector);
  const prev = root.querySelector(prevSelector);
  const next = root.querySelector(nextSelector);
  const dotsContainer = root.querySelector(dotsSelector);

  if (!slides.length || !prev || !next || !dotsContainer) return;

  let index = 0;
  let timer = null;

  dotsContainer.innerHTML = "";

  slides.forEach((_, i) => {
    const dot = document.createElement("span");
    dot.classList.add(dotClass);
    if (i === 0) dot.classList.add(activeClass);
    dot.addEventListener("click", () => {
      show(i);
      restart();
    });
    dotsContainer.appendChild(dot);
  });

  const dots = dotsContainer.querySelectorAll("." + dotClass);

  function show(i) {
    slides.forEach(s => s.classList.remove(activeClass));
    dots.forEach(d => d.classList.remove(activeClass));
    slides[i].classList.add(activeClass);
    dots[i].classList.add(activeClass);
    index = i;
  }

  function nextSlide() { show((index + 1) % slides.length); }
  function prevSlide() { show((index - 1 + slides.length) % slides.length); }

  prev.addEventListener("click", () => { prevSlide(); restart(); });
  next.addEventListener("click", () => { nextSlide(); restart(); });

  function start() { stop(); timer = setInterval(nextSlide, interval); }
  function stop() { if (timer) clearInterval(timer); timer = null; }
  function restart() { start(); }

  root.addEventListener("mouseenter", stop);
  root.addEventListener("mouseleave", start);

  show(0);
  start();
}

// horizontal scroll sections
function slideRight(id) { document.getElementById(id).scrollLeft += 300; }
function slideLeft(id) { document.getElementById(id).scrollLeft -= 300; }


/* ==========================
   AJIO LOGIN MODAL FLOW 
========================== */
const API_CHECK_MOBILE = "/api/users/check-mobile/";
const API_SEND_OTP = "/api/users/send-otp/";
const API_VERIFY_OTP = "/api/users/verify-otp/";

// orrect backend endpoint
const API_PROFILE = "/api/users/me/";

let otpMobile = "";
let isNewUserFlow = false;
let resendInterval = null;
let resendSeconds = 54;

//  in-memory temp data for new user setup
let pendingProfilePayload = null;

function openLogin() {
  const modal = document.getElementById("loginModal");
  if (modal) modal.style.display = "block";
  showStep("mobile");
}

function closeLogin() {
  const modal = document.getElementById("loginModal");
  if (modal) modal.style.display = "none";
  stopResendTimer();
  resetLogin();
}

function resetLogin() {
  otpMobile = "";
  isNewUserFlow = false;
  pendingProfilePayload = null;
  stopResendTimer();

  const m = document.getElementById("mobileInput");
  const otp = document.getElementById("otpInput");
  if (m) m.value = "";
  if (otp) otp.value = "";

  // clear setup fields
  const name = document.getElementById("setupName");
  const email = document.getElementById("setupEmail");
  const inv = document.getElementById("setupInvite");
  const agree = document.getElementById("setupAgree");
  if (name) name.value = "";
  if (email) email.value = "";
  if (inv) inv.value = "";
  if (agree) agree.checked = false;

  document.querySelectorAll("input[name='setupGender']").forEach(r => (r.checked = false));
  setStartShoppingEnabled(false);
}

function showStep(step) {
  const mobileStep = document.getElementById("mobileStep");
  const signupStep = document.getElementById("signupStep");
  const otpStep = document.getElementById("otpStep");
  const backBtn = document.getElementById("loginBackBtn");
  if (!mobileStep || !signupStep || !otpStep || !backBtn) return;

  mobileStep.classList.add("hidden");
  signupStep.classList.add("hidden");
  otpStep.classList.add("hidden");

  if (step === "mobile") {
    mobileStep.classList.remove("hidden");
    backBtn.style.display = "none";
  } else if (step === "signup") {
    signupStep.classList.remove("hidden");
    backBtn.style.display = "inline-block";
  } else if (step === "otp") {
    otpStep.classList.remove("hidden");
    backBtn.style.display = "inline-block";
  }
}

function loginBack() {
  const otpStep = document.getElementById("otpStep");
  if (otpStep && !otpStep.classList.contains("hidden")) {
    stopResendTimer();
    if (isNewUserFlow) showStep("signup");
    else showStep("mobile");
    return;
  }
  showStep("mobile");
}

function editMobile() {
  showStep("mobile");
}

async function continueLogin() {
  const mobileEl = document.getElementById("mobileInput");
  if (!mobileEl) return;

  const mobile = (mobileEl.value || "").trim();
  if (!/^\d{10}$/.test(mobile)) {
    alert("Enter valid 10 digit mobile number");
    return;
  }

  otpMobile = mobile;

  // check if exists
  let exists = false;
  try {
    const res = await fetch(`${API_CHECK_MOBILE}?mobile=${encodeURIComponent(mobile)}`);
    const data = await res.json().catch(() => ({}));
    exists = !!data.exists;
  } catch (e) {
    console.log("check-mobile error", e);
  }

  if (exists) {
    isNewUserFlow = false;
    pendingProfilePayload = null;
    await sendOtp();
    showOtpScreen();
  } else {
    isNewUserFlow = true;
    const setupMobileText = document.getElementById("setupMobileText");
    if (setupMobileText) setupMobileText.innerText = mobile;
    showStep("signup");
  }
}

async function sendOtpFromSetup() {
  const agree = document.getElementById("setupAgree");
  const name = document.getElementById("setupName");
  const email = document.getElementById("setupEmail");
  const invite = document.getElementById("setupInvite");

  const gender = document.querySelector("input[name='setupGender']:checked")?.value || "";

  if (!agree?.checked) return alert("Please accept Terms and Conditions");
  if (!gender) return alert("Please select gender");
  if (!name?.value.trim()) return alert("Please enter name");
  if (!email?.value.trim()) return alert("Please enter email");

  // backend expects first_name, email, gender
  pendingProfilePayload = {
    first_name: name.value.trim(),
    email: email.value.trim(),
    gender: gender,
    invite_code: (invite?.value || "").trim() // backend ignores if not used
  };

  await sendOtp();
  showOtpScreen();
}

async function sendOtp() {
  if (!otpMobile) return;
  try {
    await fetch(`${API_SEND_OTP}?mobile=${encodeURIComponent(otpMobile)}`);
  } catch (e) {
    console.log("send otp error", e);
  }
}

function showOtpScreen() {
  const masked = `+91 ${otpMobile.slice(0, 2)}XXXXXX${otpMobile.slice(-3)}`;
  const show = document.getElementById("showMobile");
  if (show) show.innerText = masked;

  const otpInput = document.getElementById("otpInput");
  if (otpInput) otpInput.value = "";

  setStartShoppingEnabled(false);
  showStep("otp");
  startResendTimer(54);
}

function setStartShoppingEnabled(enabled) {
  const btn = document.getElementById("startShoppingBtn");
  if (!btn) return;
  btn.disabled = !enabled;
}

// resend timer
function startResendTimer(seconds) {
  stopResendTimer();
  resendSeconds = seconds;

  const resendBtn = document.getElementById("resendOtpBtn");
  const timerEl = document.getElementById("resendTimer");

  if (resendBtn) resendBtn.classList.add("disabled");
  if (timerEl) timerEl.innerText = String(resendSeconds);

  resendInterval = setInterval(() => {
    resendSeconds -= 1;
    if (timerEl) timerEl.innerText = String(resendSeconds);

    if (resendSeconds <= 0) {
      stopResendTimer();
      if (resendBtn) resendBtn.classList.remove("disabled");
      if (resendBtn) resendBtn.innerHTML = `Resend OTP`;
    }
  }, 1000);
}

function stopResendTimer() {
  if (resendInterval) clearInterval(resendInterval);
  resendInterval = null;
}

async function resendOtp() {
  const resendBtn = document.getElementById("resendOtpBtn");
  if (resendBtn && resendBtn.classList.contains("disabled")) return;

  await sendOtp();

  if (resendBtn) {
    resendBtn.innerHTML = `Resend OTP in <span id="resendTimer">54</span>s`;
    resendBtn.classList.add("disabled");
  }
  startResendTimer(54);
}

// OTP auto verify (6 digits)
document.addEventListener("input", async (e) => {
  if (!e.target || e.target.id !== "otpInput") return;

  const otp = (e.target.value || "").trim();
  if (otp.length !== 6) {
    setStartShoppingEnabled(false);
    return;
  }

  try {
    const res = await fetch(API_VERIFY_OTP, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ mobile: otpMobile, otp })
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok || !data.success) {
      alert(data.message || "Invalid OTP");
      setStartShoppingEnabled(false);
      return;
    }

    // store tokens
    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    localStorage.setItem("username", data.username);
    localStorage.setItem("user_id", data.user_id);

    //  save immediately if returned (faster topbar)
    if (data.first_name) localStorage.setItem("first_name", data.first_name);
    if (data.screen_name) localStorage.setItem("screen_name", data.screen_name);
    if (data.phone) localStorage.setItem("phone", data.phone);

    // new user setup -> save profile now
    if (isNewUserFlow && pendingProfilePayload) {
      await saveSetupProfile(data.access, pendingProfilePayload);
      pendingProfilePayload = null;
    }

    // load profile & cache (ensures topbar correct)
    await syncProfileNameToLocalStorage(data.access);
    updateTopbar();

    setStartShoppingEnabled(true);
  } catch (err) {
    console.log("verify error", err);
    alert("OTP verification failed");
    setStartShoppingEnabled(false);
  }
});

async function saveSetupProfile(accessToken, payload) {
  try {
    await fetch(API_PROFILE, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + accessToken
      },
      body: JSON.stringify(payload)
    });
  } catch (e) {
    console.log("save profile error", e);
  }
}

async function syncProfileNameToLocalStorage(accessToken) {
   const token = accessToken || localStorage.getItem("access");
  if (!token) return false;

  try {
    const res = await fetch(API_PROFILE, {
      headers: { "Authorization": "Bearer " + token }
    });

    if (!res.ok) return false;

    const p = await res.json().catch(() => ({}));

    if (p.first_name) localStorage.setItem("first_name", p.first_name);
    if (p.screen_name) localStorage.setItem("screen_name", p.screen_name);
    if (p.phone) localStorage.setItem("phone", p.phone);

    return true;
  } catch (e) {
    return false;
  }
}

function startShopping() {
  closeLogin();
  updateTopbar();
  updateCartCount();
  window.location.href = "/";
}

/* ==========================
   TOPBAR UI
========================== */
function getUserDisplayName() {
  const firstName = localStorage.getItem("first_name");
  const screenName = localStorage.getItem("screen_name");
  const username = localStorage.getItem("username");
  const phone = localStorage.getItem("phone");

  if (firstName && firstName.trim()) return firstName.trim();
  if (screenName && screenName.trim()) return screenName.trim();
  if (username && username.trim()) return username.trim();
  if (phone && phone.trim()) return phone.trim();

  return "User";
}

function renderGuestTopbar(topbar) {
  topbar.innerHTML = `
    <a href="javascript:void(0)" onclick="openLogin()">Sign In / Join AJIO</a>
    <a href="/customer-care/">Customer Care</a>
    <button class="luxe-btn">Visit AJIOLUXE</button>
  `;
}

function renderLoggedInTopbar(topbar) {
  const name = getUserDisplayName();
  topbar.innerHTML = `
    <span>${name}</span>
    <a href="/account/orders/">My Account</a>
    <a href="javascript:void(0)" onclick="logout()">Sign Out</a>
    <a href="/customer-care/">Customer Care</a>
    <button class="luxe-btn">Visit AJIOLUXE</button>
  `;
}

async function updateTopbar() {
  const topbar = document.querySelector(".topbar-right");
  if (!topbar) return;

  // If we have any access token, try loading profile with Bearer
  const ok = await syncProfileNameToLocalStorage();

  if (ok) {
    renderLoggedInTopbar(topbar);
  } else {
    renderGuestTopbar(topbar);
  }
}

function logout() {
  clearAuth();
  updateTopbar();
  updateCartCount();
}

/* ==========================
   CART COUNT BADGE
========================== */
function updateCartCount() {
  const cartCountEl = document.getElementById("cartCount");
  if (!cartCountEl) return;

  const token = localStorage.getItem("access");

  if (!isTokenValid(token)) {
    cartCountEl.innerText = "0";
    return;
  }

  fetch("/api/cart/", { headers: { "Authorization": "Bearer " + token } })
    .then(async (res) => {
      if (res.status === 401) {
        clearAuth();
        cartCountEl.innerText = "0";
        updateTopbar();
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data) return;
      cartCountEl.innerText = (data && data.items) ? data.items.length : 0;
    })
    .catch(() => {
      cartCountEl.innerText = "0";
    });
}

/* ==========================
   HOVER BAG PREVIEW
========================== */
function loadHeaderCartPreview() {
  const token = localStorage.getItem("access");
  const itemsBox = document.getElementById("headerCartItems");
  const totalEl = document.getElementById("headerCartTotal");
  const countEl = document.getElementById("cartCount");

  if (!itemsBox || !totalEl || !countEl) return;

  if (!isTokenValid(token)) {
    clearAuth();
    updateTopbar();
    itemsBox.innerHTML = `<div class="cart-dd-empty">Your bag is empty</div>`;
    totalEl.innerText = "Rs.0";
    countEl.innerText = "0";
    return;
  }

  fetch("/api/cart/", {
    method: "GET",
    headers: {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json"
    }
  })
    .then(async (res) => {
      const data = await res.json().catch(() => ({}));

      if (res.status === 401) {
        clearAuth();
        updateTopbar();
        itemsBox.innerHTML = `<div class="cart-dd-empty">Your bag is empty</div>`;
        totalEl.innerText = "Rs.0";
        countEl.innerText = "0";
        return null;
      }

      if (!res.ok) throw new Error(data.detail || "Cart fetch failed");
      return data;
    })
    .then((data) => {
      if (!data) return;

      let items = data.items || data.cart_items || (data.cart && data.cart.items) || [];
      if (!Array.isArray(items)) items = [];

      if (items.length === 0) {
        itemsBox.innerHTML = `<div class="cart-dd-empty">Your bag is empty</div>`;
        totalEl.innerText = "Rs.0";
        countEl.innerText = "0";
        return;
      }

      let total = 0;
      itemsBox.innerHTML = "";

      items.forEach(item => {
        const p = item.product || item.product_data || {};
        const unit =
          Number(p.discount_price || item.discount_price || 0) > 0
            ? Number(p.discount_price || item.discount_price || 0)
            : Number(p.price || item.price || 0);

        const qty = Number(item.quantity || 0);
        total += unit * qty;

        const sizeText =
          (typeof item.size === "string") ? item.size :
          (item.size && item.size.size) ? item.size.size :
          (item.size && item.size.label) ? item.size.label :
          (item.size ? String(item.size) : "-");

        const img = normalizeImgUrl(p.image || p.image_url) || QV_FALLBACK_IMG;
        const name = p.name || item.product_name || "";

        itemsBox.innerHTML += `
          <div class="cart-dd-item">
            <img class="cart-dd-img" src="${img}" alt="" onerror="this.src='${QV_FALLBACK_IMG}'">
            <div class="cart-dd-info">
              <div class="cart-dd-price">Rs.${unit}</div>
              <div class="cart-dd-name">${name}</div>
              <div class="cart-dd-meta">
                Size <b>${sizeText}</b><br>
                Qty <b>${qty}</b>
              </div>
            </div>
          </div>
        `;
      });

      totalEl.innerText = `Rs.${total.toFixed(2)}`;
      countEl.innerText = String(items.length);
    })
    .catch(() => {
      itemsBox.innerHTML = `<div class="cart-dd-empty">Your bag is empty</div>`;
      totalEl.innerText = "Rs.0";
      countEl.innerText = "0";
    });
}

/* ==========================
   QUICK VIEW
========================== */
function openQuickView(productId) {
  qvProductId = String(productId);
  qvSelectedSize = null;

  const overlay = document.getElementById("qvOverlay");
  const modal = document.getElementById("qvModal");
  const thumbs = document.getElementById("qvThumbs");
  const sizesBox = document.getElementById("qvSizes");
  const err = document.getElementById("qvSizeError");
  const mainImg = document.getElementById("qvMainImg");

  if (!overlay || !modal || !thumbs || !sizesBox || !mainImg) return;

  thumbs.innerHTML = "";
  sizesBox.innerHTML = "";
  if (err) err.style.display = "none";

  mainImg.onerror = () => { mainImg.src = QV_FALLBACK_IMG; };
  mainImg.src = QV_FALLBACK_IMG;

  overlay.style.display = "block";
  modal.style.display = "block";
  document.body.style.overflow = "hidden";

  fetch(`/api/products/${encodeURIComponent(qvProductId)}/`)
    .then(async (res) => {
      const text = await res.text();
      let data = {};
      try { data = JSON.parse(text); } catch {}
      if (!res.ok) throw new Error(data.detail || data.error || `API error (${res.status})`);
      return data;
    })
    .then((p) => {
      const brandEl = document.getElementById("qvBrand");
      const nameEl = document.getElementById("qvName");
      const finalEl = document.getElementById("qvFinal");
      const mrpEl = document.getElementById("qvMrp");

      if (brandEl) brandEl.innerText = p.brand || "";
      if (nameEl) nameEl.innerText = p.name || "";

      const hasDisc = p.discount_price && Number(p.discount_price) > 0;
      const finalPrice = hasDisc ? p.discount_price : p.price;

      if (finalEl) finalEl.innerText = finalPrice ? `₹${finalPrice}` : "";

      if (mrpEl) {
        if (hasDisc) {
          mrpEl.style.display = "inline";
          mrpEl.innerText = p.price ? `₹${p.price}` : "";
        } else {
          mrpEl.style.display = "none";
          mrpEl.innerText = "";
        }
      }

      //  images
      renderQuickViewImages(extractImages(p), mainImg, thumbs);

      //  colors + swatches (+More)
      renderQuickViewColors(p, mainImg, thumbs);

      //  sizes
      const SIZE_ORDER = [
        "XS", "S", "M", "L", "XL", "XXL", "FZ",
        "28", "30", "32", "34", "36",
        "5", "6", "7", "8", "9", "10", "11", "12",
        "0-2", "3-5", "6-7", "8-10", "11-14",
      ];

      let sizes = Array.isArray(p.sizes) ? p.sizes : [];

      // sort by our order list; unknowns go last
      sizes.sort((a, b) => {
        const sa = String(a?.size ?? "");
        const sb = String(b?.size ?? "");
        const ia = SIZE_ORDER.indexOf(sa);
        const ib = SIZE_ORDER.indexOf(sb);

        const ra = ia === -1 ? 999 : ia;
        const rb = ib === -1 ? 999 : ib;

        if (ra === rb) return sa.localeCompare(sb);
        return ra - rb;
      });

      sizesBox.innerHTML = "";

      sizes.forEach((s) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "qv-size-btn";
        b.innerText = s.size;

        if (Number(s.stock) <= 0) {
          b.classList.add("disabled");
          b.disabled = true;
        } else {
          b.addEventListener("click", () => {
            sizesBox.querySelectorAll(".qv-size-btn").forEach(x => x.classList.remove("active"));
            b.classList.add("active");
            qvSelectedSize = s.size;
            if (err) err.style.display = "none";
          });
        }

        sizesBox.appendChild(b);
      });

      // details link (your real url is /detail/<id>/)
      const details = document.getElementById("qvDetailsBtn");
      if (details) details.href = `/detail/${qvProductId}/`;
    })
    .catch((e) => {
      console.error("Quick view error:", e);
      closeQuickView();
      alert("Unable to load quick view");
    });
}



function closeQuickView() {
  const overlay = document.getElementById("qvOverlay");
  const modal = document.getElementById("qvModal");
  if (overlay) overlay.style.display = "none";
  if (modal) modal.style.display = "none";
  document.body.style.overflow = "";
  qvSelectedSize = null;
  qvProductId = null;
}

function addToCartFromQuickView(productId, size) {
  const token = localStorage.getItem("access");

  if (!isTokenValid(token)) {
    // clearAuth();
    // updateTopbar();
    // alert("Please login first");
    openLogin();
    return;
  }

  fetch("/api/cart/add/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ product_id: productId, size, quantity: 1 })
  })
    .then(async (res) => {
      const data = await res.json().catch(() => ({}));
      if (res.status === 401) {
        clearAuth();
        updateTopbar();
        alert("Session expired. Please login again.");
        openLogin();
        return;
      }
      if (!res.ok) {
        alert(data.error || data.detail || "Failed to add to cart");
        return;
      }
      loadHeaderCartPreview();
      updateCartCount();

      closeQuickView();
      window.location.href = "/cart/";
    })
    .catch(err => console.log("Add to cart error:", err));
}

/* ==========================
   COMMON ADD TO CART
========================== */
window.addToCartCommon = async function ({ productId, size, quantity = 1, redirectToCart = false }) {
  const token = localStorage.getItem("access");

  if (!isTokenValid(token)) {
    clearAuth();
    updateTopbar();
    alert("Please login first");
    openLogin();
    return;
  }

  if (!size) {
    alert("Please select size");
    return;
  }

  const res = await fetch("/api/cart/add/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ product_id: productId, size, quantity })
  });

  const data = await res.json().catch(() => ({}));

  if (res.status === 401) {
    clearAuth();
    updateTopbar();
    alert("Session expired. Please login again.");
    openLogin();
    return;
  }

  if (!res.ok) {
    alert(data.error || data.detail || "Add to cart failed");
    return;
  }

  loadHeaderCartPreview();
  updateCartCount();

  if (redirectToCart) window.location.href = "/cart/";
  else alert("Added to bag");
};

/* ==========================
   WISHLIST (LOCALSTORAGE)
========================== */
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

function isInWishlist(id) {
  const pid = String(id);
  return readWishlist().some(item => String(item.id) === pid);
}

function addToWishlist(product) {
  let list = readWishlist();
  const pid = String(product.id);
  list = list.filter(x => String(x.id) !== pid);
  list.push(product);
  saveWishlist(list);
}

function removeFromWishlist(id) {
  const pid = String(id);
  const list = readWishlist().filter(x => String(x.id) !== pid);
  saveWishlist(list);
}

function setWishUI(saved) {
  const wishBtn = document.getElementById("wishBtn");
  const wishIcon = document.getElementById("wishIcon");
  const wishText = document.getElementById("wishText");

  if (!wishBtn || !wishIcon || !wishText) return;

  if (saved) {
    wishBtn.classList.add("active");
    wishIcon.className = "fa-solid fa-heart";
    wishText.innerText = "REMOVE FROM WISHLIST";
  } else {
    wishBtn.classList.remove("active");
    wishIcon.className = "fa-regular fa-heart";
    wishText.innerText = "SAVE TO WISHLIST";
  }
}

/* ✅ AJIO style popup message */
function showAjioToast(message) {
  const toast = document.getElementById("ajioToast");
  if (!toast) return;

  toast.textContent = message;
  toast.classList.add("show");

  clearTimeout(window.__ajioToastTimer);
  window.__ajioToastTimer = setTimeout(() => {
    toast.classList.remove("show");
    toast.style.display = "none";
  }, 1500);

  toast.style.display = "block";
}

function initWishlistButton() {
  const wishBtn = document.getElementById("wishBtn");
  if (!wishBtn) return;

  const product = {
    id: wishBtn.dataset.id,
    name: wishBtn.dataset.name || "",
    brand: wishBtn.dataset.brand || "",
    price: wishBtn.dataset.price || "",
    image: wishBtn.dataset.image || ""
  };

  setWishUI(isInWishlist(product.id));

  wishBtn.addEventListener("click", () => {
    const saved = isInWishlist(product.id);

    if (saved) {
      removeFromWishlist(product.id);
      setWishUI(false);
      showAjioToast("Item removed from wishlist");
      return;
    }

    const size = window.selectedSize || null;
    if (!size) {
      const sizeError = document.getElementById("sizeError");
      if (sizeError) sizeError.style.display = "block";
      
      showAjioToast("Please select a size");
      return;
    }

    const productToSave = { ...product, size };
    addToWishlist(productToSave);
    setWishUI(true);
    showAjioToast("Item saved in my wishlist");


    setTimeout(() => {
      window.location.href = "/wishlist/";
    }, 700);
  });
}

/* ==========================
   NAV SEARCH (Dropdown)
========================== */
function initNavSearch() {
  const input = document.getElementById("searchInput");
  const btn = document.getElementById("searchBtn");
  const dd = document.getElementById("searchDropdown");
  if (!input || !btn || !dd) return;

  const LISTING_PAGE = "/products-page/";
  let timer = null;

  function hideDropdown() {
    dd.style.display = "none";
    dd.innerHTML = "";
  }

  function goSearch() {
    const q = (input.value || "").trim();
    window.location.href = q ? `${LISTING_PAGE}?search=${encodeURIComponent(q)}` : LISTING_PAGE;
  }

  btn.addEventListener("click", goSearch);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") goSearch();
  });

  input.addEventListener("input", () => {
    const q = (input.value || "").trim();
    clearTimeout(timer);

    if (q.length < 2) {
      hideDropdown();
      return;
    }

    timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/products/?search=${encodeURIComponent(q)}`);
        const data = await res.json();

        dd.innerHTML = "";

        if (!Array.isArray(data) || data.length === 0) {
          dd.innerHTML = `<div class="search-empty">No results found</div>`;
          dd.style.display = "block";
          return;
        }

        data.slice(0, 6).forEach(p => {
          const img = normalizeImgUrl(p.image) || QV_FALLBACK_IMG;
          const row = document.createElement("div");
          row.className = "search-item";
          row.innerHTML = `
            <img src="${img}" alt="" onerror="this.src='${QV_FALLBACK_IMG}'">
            <div class="search-meta">
              <div class="search-brand">${p.brand || ""}</div>
              <div class="search-name">${p.name || ""}</div>
            </div>
          `;
          row.addEventListener("click", () => {
            window.location.href = `/product/${p.id}/`;
          });
          dd.appendChild(row);
        });

        dd.style.display = "block";
      } catch (err) {
        console.log("Nav search error:", err);
        hideDropdown();
      }
    }, 300);
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".ajio-search")) hideDropdown();
  });
}



// quick view color varient

/* ==========================
   QUICK VIEW COLOR HELPERS (ADD THIS)
========================== */

function qvBrandName(p) {
  if (!p) return "";
  if (typeof p.brand === "string") return p.brand;
  if (p.brand && typeof p.brand === "object") return p.brand.name || "";
  return "";
}

function pickBaseColorName(p) {
  return (
    p.color_name ||
    p.base_color?.name ||
    p.color?.name ||
    p.colour_name ||
    p.colour ||
    p.color ||
    "-"
  );
}

function pickBaseColorHex(p) {
  return (
    p.base_color?.hex_code ||
    p.color?.hex_code ||
    p.base_color_hex ||
    p.hex_code ||
    p.color_hex ||
    "#f0f0f0"
  );
}

function pickVariants(p) {
  // support different API keys
  return (
    p.variants ||
    p.color_variants ||
    p.variant_colors ||
    p.variant_list ||
    []
  );
}

function renderQuickViewImages(images, mainImg, thumbs) {
  let imgs = (images || []).map(normalizeImgUrl).filter(Boolean);
  if (!imgs.length) imgs = [QV_FALLBACK_IMG];

  mainImg.onerror = () => { mainImg.src = QV_FALLBACK_IMG; };
  mainImg.src = imgs[0];

  thumbs.innerHTML = "";

  imgs.forEach((url, idx) => {
    const t = document.createElement("img");
    t.src = url;
    t.className = "qv-thumb" + (idx === 0 ? " active" : "");
    t.onerror = () => t.remove();

    t.addEventListener("click", () => {
      mainImg.src = url;
      thumbs.querySelectorAll(".qv-thumb").forEach(x => x.classList.remove("active"));
      t.classList.add("active");
    });

    thumbs.appendChild(t);
  });
}


