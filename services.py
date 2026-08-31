def add_to_cart(cart, product, qty):
    qty = int(qty)
    if qty <= 0:
        raise ValueError("Quantity must be greater than zero.")
    old = next((x for x in cart if x["id"] == product["id"]), None)
    current = old["qty"] if old else 0
    if current + qty > product["stock"]:
        raise ValueError(f"Only {product['stock']} units are available.")
    if old:
        old["qty"] += qty
        old["line_total"] = old["qty"] * old["price"]
    else:
        cart.append({
            "id": product["id"], "code": product["code"], "name": product["name"],
            "price": float(product["price"]), "tax": float(product["tax"]),
            "qty": qty, "line_total": float(product["price"]) * qty
        })


def remove_from_cart(cart, index):
    if 0 <= index < len(cart):
        cart.pop(index)


def calculate_totals(cart, discount):
    subtotal = sum(x["price"] * x["qty"] for x in cart)
    tax = sum(x["price"] * x["qty"] * x["tax"] / 100 for x in cart)
    discount = max(0, float(discount))
    total = max(0, subtotal + tax - discount)
    for x in cart:
        x["line_total"] = x["price"] * x["qty"]
    return round(subtotal,2), round(tax,2), round(total,2)
