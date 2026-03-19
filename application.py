import streamlit as st
import requests
from datetime import date

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Invoice Generator", layout="centered")

# ---------- STATE INIT ----------
if "step" not in st.session_state:
    st.session_state.step = 1

if "invoice" not in st.session_state:
    st.session_state.invoice = {
        "business": {},
        "customer": {},
        "items": [],
        "tax": {"sgst": 0, "cgst": 0},
        "discount": 0
    }

# ---------- HELPERS ----------
def calculate_totals(inv):
    subtotal = sum(i["quantity"] * i["price"] for i in inv["items"])
    tax = subtotal * (inv["tax"]["sgst"] + inv["tax"]["cgst"]) / 100
    discount = subtotal * inv["discount"] / 100
    total = subtotal + tax - discount
    return subtotal, tax, total

def go_next(step):
    st.session_state.step = step
    st.rerun()

def go_back():
    st.session_state.step -= 1
    st.rerun()

# ---------- PROGRESS ----------
st.progress(st.session_state.step / 5)

# ---------- STEP 1: BUSINESS ----------
if st.session_state.step == 1:
    st.title("🏢 Business Details")

    name = st.text_input("Business Name")
    gst = st.text_input("GST Number")

    col1, col2 = st.columns(2)
    with col2:
        if st.button("Next ➡"):
            if name and gst:
                st.session_state.invoice["business"] = {
                    "business_name": name,
                    "gst": gst
                }
                go_next(2)
            else:
                st.warning("Fill all fields")

# ---------- STEP 2: CUSTOMER ----------
elif st.session_state.step == 2:
    st.title("👤 Customer Details")

    cname = st.text_input("Customer Name")
    address = st.text_area("Address")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Back"):
            go_back()
    with col2:
        if st.button("Next ➡"):
            if cname and address:
                st.session_state.invoice["customer"] = {
                    "customer_name": cname,
                    "address": address
                }
                go_next(3)
            else:
                st.warning("Fill all fields")

# ---------- STEP 3: ITEMS ----------
elif st.session_state.step == 3:
    st.title("🛒 Add Items")

    col1, col2, col3 = st.columns(3)
    with col1:
        product = st.text_input("Product")
    with col2:
        qty = st.number_input("Qty", min_value=1, step=1)
    with col3:
        price = st.number_input("Price", min_value=0.0)

    if st.button("➕ Add Item"):
        if product:
            st.session_state.invoice["items"].append({
                "product_name": product,
                "quantity": qty,
                "price": price
            })
            st.rerun()

    st.subheader("📦 Items")

    # show items with delete option
    for i, item in enumerate(st.session_state.invoice["items"]):
        c1, c2, c3, c4 = st.columns([3,1,1,1])
        c1.write(item["product_name"])
        c2.write(item["quantity"])
        c3.write(item["price"])
        if c4.button("❌", key=f"del_{i}"):
            st.session_state.invoice["items"].pop(i)
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Back"):
            go_back()
    with col2:
        if st.button("Next ➡"):
            if st.session_state.invoice["items"]:
                go_next(4)
            else:
                st.warning("Add at least one item")

# ---------- STEP 4: TAX ----------
elif st.session_state.step == 4:
    st.title("💰 Tax & Discount")

    col1, col2 = st.columns(2)
    with col1:
        sgst = st.number_input("SGST (%)", min_value=0.0)
    with col2:
        cgst = st.number_input("CGST (%)", min_value=0.0)

    discount = st.number_input("Discount (%)", min_value=0.0)

    # update state
    st.session_state.invoice["tax"] = {"sgst": sgst, "cgst": cgst}
    st.session_state.invoice["discount"] = discount

    # live preview
    subtotal, tax, total = calculate_totals(st.session_state.invoice)

    st.info(f"Subtotal: ₹{subtotal:.2f}")
    st.info(f"Tax: ₹{tax:.2f}")
    st.success(f"Total: ₹{total:.2f}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Back"):
            go_back()
    with col2:
        if st.button("Next ➡"):
            go_next(5)

# ---------- STEP 5: PREVIEW ----------
elif st.session_state.step == 5:
    st.title("📄 Invoice Preview")

    inv = st.session_state.invoice

    # auto invoice number
    invoice_no = f"INV-{len(inv['items'])}{date.today().strftime('%d%m')}"
    invoice_id = st.text_input("Invoice ID")

    st.write("### 🏢 Business", inv["business"])
    st.write("### 👤 Customer", inv["customer"])
    st.write("### 🛒 Items", inv["items"])

    subtotal, tax, total = calculate_totals(inv)

    st.write(f"Subtotal: ₹{subtotal}")
    st.write(f"Tax: ₹{tax}")
    st.write(f"Total: ₹{total}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Back"):
            go_back()
    with col2:
        if st.button("✅ Create Invoice"):
            payload = {
                "invoice_id": invoice_id,
                "invoice_no": invoice_no,
                "date": str(date.today()),
                **inv
            }

            try:
                res = requests.post(f"{API_URL}/create", json=payload)

                if res.status_code == 201:
                    st.success("🎉 Invoice Created!")

                    # reset state
                    st.session_state.step = 1
                    st.session_state.invoice = {
                        "business": {},
                        "customer": {},
                        "items": [],
                        "tax": {"sgst": 0, "cgst": 0},
                        "discount": 0
                    }
                    st.rerun()
                else:
                    st.error(res.text)

            except Exception as e:
                st.error(f"Error: {e}")