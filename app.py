import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="IC BATAM SYSTEM", layout="wide")

# ===============================
# FILE STORAGE (SHARED DATA)
# ===============================
IC_FILE = "ic_uploads.json"
RP_FILE = "rusak_pabrik.json"
CSV_FILE = "csv_data.json"

# ===============================
# LOAD / SAVE FUNCTIONS
# ===============================
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# ===============================
# INIT DATA
# ===============================
if "ic_uploads" not in st.session_state:
    st.session_state.ic_uploads = load_json(IC_FILE)

if "rusak_pabrik" not in st.session_state:
    st.session_state.rusak_pabrik = load_json(RP_FILE)

if "csv_data" not in st.session_state:
    st.session_state.csv_data = load_json(CSV_FILE)

# ===============================
# LOGIN DATA
# ===============================
CREDENTIALS = {
    "ADMIN": {"user": "MTP", "pwd": "1712"},
    "IC": {"user": "ICBTM", "pwd": "@ICBTM"},
    "TOKO": {"user": "BTMJUARA", "pwd": "BTMJUARA"}
}

# ===============================
# SESSION LOGIN
# ===============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# ===============================
# LOGIN PAGE
# ===============================
if not st.session_state.logged_in:
    st.title("💻 IC BATAM SYSTEM")

    role_choice = st.selectbox("Jenis Login", list(CREDENTIALS.keys()))
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        target = CREDENTIALS[role_choice]
        if username == target["user"] and password == target["pwd"]:
            st.session_state.logged_in = True
            st.session_state.role = role_choice
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Login gagal")

# ===============================
# DASHBOARD
# ===============================
else:
    st.sidebar.title(f"Role: {st.session_state.role}")
    if st.sidebar.button("Logout"):
        logout()

    # ===========================
    # ADMIN
    # ===========================
    if st.session_state.role == "ADMIN":
        st.title("🖥️ ADMIN DASHBOARD")

        tab1, tab2, tab3 = st.tabs(["CSV DATA", "IC UPLOAD", "RUSAK PABRIK"])

        # -------------------
        # CSV UPLOAD
        # -------------------
        with tab1:
            uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

            if uploaded_file:
                df = pd.read_csv(uploaded_file, sep=None, engine="python")
                st.dataframe(df)

                if st.button("Simpan CSV"):
                    st.session_state.csv_data = df.to_dict(orient="records")
                    save_json(CSV_FILE, st.session_state.csv_data)
                    st.success("CSV tersimpan")

        # -------------------
        # IC UPLOAD VIEW
        # -------------------
        with tab2:
            st.subheader("Data IC Upload")

            for i, item in enumerate(st.session_state.ic_uploads):
                st.write(f"NBH: {item['nbh']}")
                st.image(item["image"])

        # -------------------
        # RUSAK PABRIK VIEW
        # -------------------
        with tab3:
            st.subheader("Rusak Pabrik")

            for i, item in enumerate(st.session_state.rusak_pabrik):
                st.write(f"Toko: {item['toko']} | NRB: {item['no_nrb']}")
                st.image(item["foto_ba"])
                st.image(item["foto_barang"])

    # ===========================
    # IC USER
    # ===========================
    elif st.session_state.role == "IC":
        st.title("📤 IC UPLOAD")

        nbh = st.text_input("NBH")

        img = st.file_uploader("Upload Bukti", type=["jpg", "png", "jpeg"])

        if st.button("Submit"):
            if nbh and img:
                file_path = f"img_{len(st.session_state.ic_uploads)}.jpg"

                with open(file_path, "wb") as f:
                    f.write(img.getbuffer())

                data = {
                    "nbh": nbh,
                    "image": file_path,
                    "status": "SELESAI"
                }

                st.session_state.ic_uploads.append(data)
                save_json(IC_FILE, st.session_state.ic_uploads)

                st.success("Upload berhasil & masuk ke ADMIN + TOKO")

        st.divider()

        st.subheader("Riwayat Upload")
        for item in st.session_state.ic_uploads:
            st.write(item["nbh"])
            st.image(item["image"])

    # ===========================
    # TOKO
    # ===========================
    elif st.session_state.role == "TOKO":
        st.title("🏪 TOKO DASHBOARD")

        kode = st.text_input("Kode Toko").strip().upper()

        st.subheader("Data NBH")
        for item in st.session_state.csv_data:
            if str(item.get("TOKO", "")).strip().upper() == kode:
                st.write(item)

        st.divider()

        st.subheader("Status IC Upload")
        for item in st.session_state.ic_uploads:
            st.write(item["nbh"], "-", item["status"])

        st.divider()

        st.subheader("Upload Rusak Pabrik")

        toko = st.text_input("Toko", value=kode)
        no_nrb = st.text_input("No NRB")

        ba = st.file_uploader("Foto BA")
        barang = st.file_uploader("Foto Barang")

        if st.button("Kirim"):
            if toko and no_nrb and ba and barang:

                ba_path = f"ba_{len(st.session_state.rusak_pabrik)}.jpg"
                br_path = f"br_{len(st.session_state.rusak_pabrik)}.jpg"

                with open(ba_path, "wb") as f:
                    f.write(ba.getbuffer())

                with open(br_path, "wb") as f:
                    f.write(barang.getbuffer())

                data = {
                    "toko": toko,
                    "no_nrb": no_nrb,
                    "foto_ba": ba_path,
                    "foto_barang": br_path
                }

                st.session_state.rusak_pabrik.append(data)
                save_json(RP_FILE, st.session_state.rusak_pabrik)

                st.success("Laporan masuk ke ADMIN & IC")
