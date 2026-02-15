function addToCart(el) {
    const productId = el.dataset.productId;

    if (!productId) {
        console.error("Product ID missing");
        return;
    }

    fetch("/api/cart/add/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + localStorage.getItem("access")
        },
        body: JSON.stringify({
            product_id: productId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Added to cart");
            el.closest(".wishlist-card").remove();
            updateCartCount(); // if exists
        } else {
            alert(data.message || "Failed to add to cart");
        }
    })
    .catch(err => {
        console.error("Add to cart error:", err);
    });
}

function deleteWishlist(el) {
    const productId = el.dataset.productId;

    if (!productId) {
        console.error("Product ID not found");
        return;
    }

    fetch("/api/wishlist/remove/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + localStorage.getItem("access")
        },
        body: JSON.stringify({
            product_id: productId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Remove card from UI
            el.closest(".wishlist-card").remove();
        } else {
            alert(data.message || "Unable to remove from wishlist");
        }
    })
    .catch(err => {
        console.error("Delete wishlist error:", err);
    });
}
