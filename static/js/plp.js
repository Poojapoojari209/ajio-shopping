
document.addEventListener("DOMContentLoaded", () => {
    loadProducts(apiUrl);
});

function loadProducts(url) {
    fetch(url)
        .then(res => res.json())
        .then(products => {
            const grid = document.getElementById("productGrid");
            grid.innerHTML = "";

            products.forEach(p => {

                // FIRST IMAGE
                const image = p.images && p.images.length > 0 
                    ? p.images[0].image 
                    : "";

                grid.innerHTML += `
                    <div class="product-card" onclick="openProduct(${p.id})">

                        ${p.discount_percentage > 0 ? `
                            <div class="discount-badge">
                                ${p.discount_percentage}% OFF
                            </div>
                        ` : ""}

                        <img src="${image}" alt="${p.name}">

                        <p class="brand">${p.brand.name}</p>
                        <p class="name">${p.name}</p>

                        <p class="price">
                            ₹${p.discount_price ?? p.price}
                            ${p.discount_price ? `<span class="original">₹${p.price}</span>` : ""}
                        </p>
                    </div>
                `;
            });
        })
        .catch(err => console.error("API ERROR:", err));
}

function openProduct(id) {
    window.location.href = `/products/page/${id}/`;
}
