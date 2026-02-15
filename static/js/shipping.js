document.addEventListener("DOMContentLoaded", () => {
  loadShipping();
  document.getElementById("proceedPayment").addEventListener("click", proceedToPayment);
});

let selectedAddressId = null;

function token(){
  return localStorage.getItem("access");
}

async function loadShipping(){
  const t = token();
  if(!t){
    document.getElementById("shipMsg").innerText = "Please login to continue.";
    return;
  }

  await Promise.all([loadAddresses(), loadCartSummary()]);
}

async function loadAddresses(){
  const res = await fetch("/api/users/addresses/", {
    headers: { "Authorization": "Bearer " + token() }
  });

  const box = document.getElementById("addressList");
  box.innerHTML = "";

  if(!res.ok){
    document.getElementById("shipMsg").innerText = "Unable to load addresses.";
    return;
  }

  const addresses = await res.json();

  if(!addresses.length){
    box.innerHTML = `<p style="color:#666;font-size:14px;">No address found. Please add address in Address Book.</p>`;
    return;
  }

  const def = addresses.find(a => a.is_default) || addresses[0];
  selectedAddressId = def.id;

  addresses.forEach(a => {
    const checked = a.id === selectedAddressId ? "checked" : "";
    box.innerHTML += `
      <label class="addr-card">
        <input type="radio" name="addr" value="${a.id}" ${checked}
               onchange="window.__setAddr(${a.id})">
        <div>
          <strong>${a.name || "User"}</strong>
          <div class="mini">
            ${a.address_line}<br>
            ${a.city}, ${a.state} - ${a.pincode}<br>
            Phone: <b>${a.mobile || ""}</b>
          </div>
        </div>
      </label>
    `;
  });
}

window.__setAddr = (id) => { selectedAddressId = id; };

async function loadCartSummary(){
  const res = await fetch("/api/cart/", {
    headers: { "Authorization": "Bearer " + token() }
  });

  if(!res.ok) return;

  const data = await res.json();
  const items = data?.items || [];

  let bagTotal = 0;
  let bagDiscount = 0; // you can calculate if you have MRP vs discount_price

  items.forEach(it => {
    const p = it.product;
    const price = p.discount_price ?? p.price;
    bagTotal += price * it.quantity;
  });

  document.getElementById("bagTotal").innerText = `₹${bagTotal}`;
  document.getElementById("bagDiscount").innerText = `-₹${bagDiscount}`;
  document.getElementById("orderTotal").innerText = `₹${bagTotal + 29}`;
}

async function proceedToPayment(){
  const msg = document.getElementById("shipMsg");
  msg.innerText = "";

  if(!selectedAddressId){
    msg.innerText = "Please select an address.";
    return;
  }

  // Create order using API, then go to payment page
  const res = await fetch("/api/orders/create/", {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + token(),
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ address_id: selectedAddressId })
  });

  const data = await res.json();
  if(!res.ok){
    msg.innerText = data.error || "Order failed.";
    return;
  }

  // Save order id for payment step
  localStorage.setItem("last_order_id", data.order_id);

  // Next page 
  window.location.href = "/payment/";
}
