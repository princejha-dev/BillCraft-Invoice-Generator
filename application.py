import streamlit as st
import requests
from datetime import date
import uuid
import pandas as pd

API_URL = "http://127.0.0.1:8000"  # change after deploy

st.set_page_config(page_title="Invoice Studio", layout="wide")

# ---------- STATE ----------
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
def generate_invoice_id():
    return str(uuid.uuid4())[:8]

def totals(inv):
    subtotal = sum(i["quantity"] * i["price"] for i in inv["items"])
    tax = subtotal * (inv["tax"]["sgst"] + inv["tax"]["cgst"]) / 100
    discount = subtotal * inv["discount"] / 100
    return subtotal, tax, subtotal + tax - discount

def next_step(step):
    st.session_state.step = step
    st.rerun()

def prev_step():
    st.session_state.step -= 1
    st.rerun()

def display_invoice(data):
    st.subheader("📄 Invoice Details")

    st.write("### 🏢 Business")
    st.table(pd.DataFrame([data["business"]]))

    st.write("### 👤 Customer")
    st.table(pd.DataFrame([data["customer"]]))

    st.write("### 🛒 Items")
    st.table(pd.DataFrame(data["items"]))

    st.write("### 💰 Summary")
    summary = {
        "Subtotal": data.get("subtotal"),
        "Tax": data.get("tax_amount"),
        "Total": data.get("total"),
        "Discount": data.get("discount")
    }
    st.table(pd.DataFrame([summary]))

# ---------- SIDEBAR ----------
st.sidebar.title("⚙️ Menu")
menu = st.sidebar.radio("Go to", ["Create Invoice", "View Invoice", "Update Invoice", "Delete Invoice"])

# =========================================================
# 🧾 CREATE INVOICE
# =========================================================
if menu == "Create Invoice":

    st.title("🧾 Create Invoice")
    st.progress(st.session_state.step / 5)

    # STEP 1
    if st.session_state.step == 1:
        st.subheader("🏢 Business Details")
        name = st.text_input("Business Name")
        gst = st.text_input("GST")

        if st.button("Next ➡"):
            if name and gst:
                st.session_state.invoice["business"] = {"business_name": name, "gst": gst}
                next_step(2)
            else:
                st.warning("Fill all fields")

    # STEP 2
    elif st.session_state.step == 2:
        st.subheader("👤 Customer Details")
        cname = st.text_input("Customer Name")
        address = st.text_area("Address")

        col1, col2 = st.columns(2)
        if col1.button("⬅ Back"):
            prev_step()
        if col2.button("Next ➡"):
            if cname and address:
                st.session_state.invoice["customer"] = {
                    "customer_name": cname,
                    "address": address
                }
                next_step(3)

    # STEP 3
    elif st.session_state.step == 3:
        st.subheader("🛒 Items")

        col1, col2, col3 = st.columns(3)
        product = col1.text_input("Product")
        qty = col2.number_input("Qty", 1)
        price = col3.number_input("Price", 0.0)

        if st.button("➕ Add Item"):
            if product:
                st.session_state.invoice["items"].append({
                    "product_name": product,
                    "quantity": qty,
                    "price": price
                })
                st.rerun()

        for i, item in enumerate(st.session_state.invoice["items"]):
            c1, c2, c3, c4 = st.columns([3,1,1,1])
            c1.write(item["product_name"])
            c2.write(item["quantity"])
            c3.write(item["price"])
            if c4.button("❌", key=i):
                st.session_state.invoice["items"].pop(i)
                st.rerun()

        col1, col2 = st.columns(2)
        if col1.button("⬅ Back"):
            prev_step()
        if col2.button("Next ➡"):
            if st.session_state.invoice["items"]:
                next_step(4)

    # STEP 4
    elif st.session_state.step == 4:
        st.subheader("💰 Tax & Discount")

        sgst = st.number_input("SGST %", 0.0)
        cgst = st.number_input("CGST %", 0.0)
        discount = st.number_input("Discount %", 0.0)

        st.session_state.invoice["tax"] = {"sgst": sgst, "cgst": cgst}
        st.session_state.invoice["discount"] = discount

        sub, tax, total = totals(st.session_state.invoice)

        st.info(f"Subtotal: ₹{sub:.2f}")
        st.info(f"Tax: ₹{tax:.2f}")
        st.success(f"Total: ₹{total:.2f}")

        col1, col2 = st.columns(2)
        if col1.button("⬅ Back"):
            prev_step()
        if col2.button("Next ➡"):
            next_step(5)

    # STEP 5
    elif st.session_state.step == 5:
        st.subheader("📄 Preview")

        inv = st.session_state.invoice

        invoice_id = generate_invoice_id()
        invoice_no = f"INV-{date.today().strftime('%d%m%y')}"

        st.success(f"Invoice ID: {invoice_id}")
        st.info(f"Invoice No: {invoice_no}")

        sub, tax, total = totals(inv)
        st.success(f"Total Payable: ₹{total:.2f}")

        col1, col2 = st.columns(2)
        if col1.button("⬅ Back"):
            prev_step()

        if col2.button("✅ Create Invoice"):
            payload = {
                "invoice_id": invoice_id,
                "invoice_no": invoice_no,
                "date": str(date.today()),
                **inv
            }

            res = requests.post(f"{API_URL}/create", json=payload)

            if res.status_code == 201:
                st.success("🎉 Invoice Created!")
                display_invoice(payload)

                # reset
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

# =========================================================
# 🔍 VIEW
# =========================================================
elif menu == "View Invoice":
    st.title("🔍 View Invoice")

    invoice_id = st.text_input("Invoice ID")

    if st.button("Fetch"):
        res = requests.get(f"{API_URL}/get_invoice/{invoice_id}")

        if res.status_code == 200:
            display_invoice(res.json())
        else:
            st.error(res.text)

# =========================================================
# ✏️ UPDATE
# =========================================================
elif menu == "Update Invoice":
    st.title("✏️ Update Invoice")

    invoice_id = st.text_input("Invoice ID")

    if st.button("Load Invoice"):
        res = requests.get(f"{API_URL}/get_invoice/{invoice_id}")

        if res.status_code == 200:
            st.session_state.update_data = res.json()
        else:
            st.error("Invoice not found")

    if "update_data" in st.session_state:
        data = st.session_state.update_data

        st.subheader("Edit Invoice")

        bname = st.text_input("Business Name", data["business"]["business_name"])
        gst = st.text_input("GST", data["business"]["gst"])

        cname = st.text_input("Customer Name", data["customer"]["customer_name"])
        address = st.text_area("Address", data["customer"]["address"])

        discount = st.number_input("Discount", value=data["discount"])

        if st.button("Update"):
            payload = {
                "business": {"business_name": bname, "gst": gst},
                "customer": {"customer_name": cname, "address": address},
                "discount": discount
            }

            res = requests.put(f"{API_URL}/update/{invoice_id}", json=payload)

            if res.status_code == 200:
                st.success("Updated successfully")
                display_invoice(res.json()["invoice"])
            else:
                st.error(res.text)

# =========================================================
# ❌ DELETE
# =========================================================
elif menu == "Delete Invoice":
    st.title("❌ Delete Invoice")

    invoice_id = st.text_input("Invoice ID")

    if st.button("Delete"):
        res = requests.delete(f"{API_URL}/delete/{invoice_id}")

        if res.status_code == 200:
            st.success("Invoice deleted successfully")
        else:
            st.error(res.text)