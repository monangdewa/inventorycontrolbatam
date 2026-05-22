import streamlit as st
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# ==========================================
# 1. KONFIGURASI HALAMAN & PROTECTIONS
# ==========================================
st.set_page_config(page_title="IC BATAM", layout="wide")

components.html(
    """
    <script>
        const removeElements = () => {
            const selectors = ['.stAppDeployButton', '[data-testid="stActionButton"]', 'header', '.stAppHeader', '[data-testid="stIconMaterial"]'];
            selectors.forEach(selector => {
                const elements = parent.document.querySelectorAll(selector);
                elements.forEach(el => { el.style.display = 'none'; el.style.visibility = 'hidden'; });
            });
        };
        setInterval(removeElements, 500);
    </script>
    """, height=0, width=0
)
st.markdown("<style>footer {visibility: hidden !important;}</style>", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE KREDENSIAL & INITIALIZATION
# ==========================================
CREDENTIALS = {
    "Adm_ICBTM": {"user": "MTP", "pwd": "1712"},
    "IC_Batam": {"user": "ICBTM", "pwd": "@ICBTM"},
    "Toko_Kepri": {"user": "BTMJUARA", "pwd": "@BTMJUARA"}
}

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("Koneksi Google Sheets belum dikonfigurasi.")

# Fungsi Kirim Data ke Google Sheets via Apps Script (Anti-Error)
def simpan_ke_gsheets_via_api(sheet_name, row_dict):
    try:
        api_url = st.secrets["GSHEETS_API_URL"]
        payload = {
            "sheet_name": sheet_name,
            "row_data": row_dict
        }
        res = requests.post(api_url, json=payload)
        if res.status_code == 200 and res.json().get("status") == "success":
            return True
        else:
            st.error(f"Gagal simpan ke GSheets: {res.text}")
            return False
    except Exception as e:
        st.error(f"Error Database API: {e}")
        return False

# Fungsi untuk upload foto langsung ke Cloud Storage (ImgBB)
def upload_ke_imgbb(file_foto):
    try:
        api_key = st.secrets["IMGBB_API_KEY"]
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": api_key}
        files = {"image": file_foto.getvalue()}
        response = requests.post(url, data=payload, files=files)
        if response.status_code == 200:
            return response.json()["data"]["url"]
        return None
    except Exception as e:
        st.error(f"Error Cloud Upload: {e}")
        return None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None  

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# ==========================================
# 3. HALAMAN LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.title("💻 IC BATAM")
    st.write("Rekap Rusak Pabrik dan NBH (Online Cloud Version)")
    role_choice = st.selectbox("Jenis Login", ["Adm_ICBTM", "IC_Batam", "Toko_Kepri"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login", type="primary"):
        target = CREDENTIALS[role_choice]
        if username == target["user"] and password == target["pwd"]:
            st.session_state.logged_in = True
            st.session_state.role = role_choice
            st.success(f"Login berhasil sebagai {role_choice}!")
            st.rerun()
        else:
            st.error("Username atau Password salah.")
    st.write("---")
    st.markdown("<p style='text-align: center; color: gray; font-size: 13px;'>👮 Inventory Control - Batam 🥇</p>", unsafe_allow_html=True)

# ==========================================
# 4. HALAMAN DASHBOARD (JIKA SUDAH LOGIN)
# ==========================================
else:
    st.sidebar.title(f"👤 {st.session_state.role}")
    if st.sidebar.button("Log Out", type="secondary"):
        logout()

    # --- INTERFACE ADMIN ---
    if st.session_state.role == "Adm_ICBTM":
        st.title("🖥️ Dashboard Admin - IC BATAM")
        tab1, tab2, tab3 = st.tabs(["📁 Kelola CSV Induk", "📸 Cek Bukti Foto NBH (IC)", "🔆 Cek Rusak Pabrik (Toko)"])
        
        with tab1:
            st.header("Upload Master Data CSV NBH")
            uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
            if uploaded_file is not None:
                if st.button("Proses & Simpan CSV di Sesi"):
                    st.session_state.uploaded_data = pd.read_csv(uploaded_file, sep='|')
                    st.success("Data CSV Induk berhasil dimuat!")

        with tab2:
            st.header("Bukti Foto NBH dari Database Cloud (Live)")
            try:
                df_nbh = conn.read(worksheet="nbh_uploads", ttl="1s")
                if df_nbh.empty:
                    st.info("Belum ada bukti foto NBH di cloud database.")
                else:
                    st.dataframe(df_nbh, use_container_width=True)
                    st.write("---")
                    for idx, row in df_nbh.iterrows():
                        with st.container(border=True):
                            st.write(f"**NBH:** {row['nbh']} | **Status:** {row['status']}")
                            st.image(row['image_url'], width=350)
            except Exception:
                st.info("Menunggu data masuk atau periksa tab 'nbh_uploads'.")

        with tab3:
            st.header("Laporan Foto Rusak Pabrik dari Toko (Live)")
            try:
                df_rp = conn.read(worksheet="rusak_pabrik_uploads", ttl="1s")
                if df_rp.empty:
                    st.info("Belum ada laporan kerusakan pabrik dari toko.")
                else:
                    for idx, row in df_rp.iterrows():
                        with st.container(border=True):
                            st.write(f"### 🏪 Toko: {row['toko']} | No NRB: {row['no_nrb']} | Tgl: {row['tgl_nrb']}")
                            c1, c2 = st.columns(2)
                            with c1:
                                st.write("**1. Foto BA Toko:**")
                                st.image(row['foto_ba_url'], width=300)
                            with c2:
                                st.write("**2. Foto Barang:**")
                                st.image(row['foto_barang_url'], width=300)
            except Exception:
                st.info("Menunggu data masuk atau periksa tab 'rusak_pabrik_uploads'.")

    # --- INTERFACE IC ---
    elif st.session_state.role == "IC_Batam":
        st.title("📤 Dashboard Lapangan - IC BATAM")
        tab1, tab2 = st.tabs(["📌 Upload FU NBH", "🔆 Pantau Rusak Pabrik (Toko)"])
        
        with tab1:
            st.subheader("Upload FU NBH ke Cloud System")
            nbh_choice = st.text_input("Input Manual NBH (KodeToko-NoNRB-Tgl NRB)", key="ic_input_nbh")
            img_file = st.file_uploader("Upload Bukti Foto Fisik", type=["jpg", "jpeg", "png"], key="ic_foto_nbh")
            
            if st.button("Kirim ke Database Admin", type="primary"):
                if nbh_choice and img_file:
                    with st.spinner("Mengunggah gambar ke cloud storage..."):
                        cloud_url = upload_ke_imgbb(img_file)
                    if cloud_url:
                        row_data = {"nbh": str(nbh_choice), "image_url": cloud_url, "status": "Selesai"}
                        if simpan_ke_gsheets_via_api("nbh_uploads", row_data):
                            st.success("🔥 Berhasil disimpan online dan langsung tersinkronisasi!")
                else:
                    st.error("Mohon lengkapi data teks dan foto.")

        with tab2:
            st.header("Pantau Laporan Rusak Pabrik dari Toko (Live)")
            try:
                df_rp = conn.read(worksheet="rusak_pabrik_uploads", ttl="5s")
                if df_rp.empty:
                    st.info("Belum ada laporan kerusakan pabrik dari toko.")
                else:
                    for idx, row in df_rp.iterrows():
                        with st.container(border=True):
                            st.write(f"### 🏪 Toko: {row['toko']} | No NRB: {row['no_nrb']}")
                            c1, c2 = st.columns(2)
                            with c1: st.image(row['foto_ba_url'], width=200, caption="BA Toko")
                            with c2: st.image(row['foto_barang_url'], width=200, caption="Fisik Barang")
            except Exception:
                st.info("Sinkronisasi database...")

    # --- INTERFACE TOKO ---
    elif st.session_state.role == "Toko_Kepri":
        st.title("🏪 Portal Toko - KEPRI")
        kode_toko_anda = st.text_input("Masukkan Kode Toko Anda:", value="TWSU").strip().upper()
        tab1, tab2 = st.tabs(["🔆 Form Rusak Pabrik", "📊 Cek Status NBH"])
        
        with tab2:
            st.header("Status NBH Toko Anda di Cloud")
            try:
                df_nbh = conn.read(worksheet="nbh_uploads", ttl="5s")
                st.dataframe(df_nbh, use_container_width=True)
            except Exception:
                st.info("Belum ada pembaruan data dari database cloud.")

        with tab1:
            st.header("Form Input Rusak Pabrik Online")
            with st.form("form_toko_cloud", clear_on_submit=True):
                form_toko = st.text_input("Nama/Kode Toko", value=kode_toko_anda)
                form_no_nrb = st.text_input("Masukkan No NRB")
                form_tgl_nrb = st.text_input("Masukkan Tanggal NRB (DD/MM/YYYY)")
                st.write("---")
                foto_ba = st.file_uploader("1. Upload Foto BA Toko", type=["jpg", "jpeg", "png"])
                foto_barang = st.file_uploader("2. Upload Foto Barang", type=["jpg", "jpeg", "png"])
                submit_rp = st.form_submit_button("Kirim Laporan Online", type="primary")
                
                if submit_rp:
                    if form_toko and form_no_nrb and form_tgl_nrb and foto_ba and foto_barang:
                        with st.spinner("Memproses konversi cloud & mengirim data..."):
                            url_ba = upload_ke_imgbb(foto_ba)
                            url_barang = upload_ke_imgbb(foto_barang)
                        if url_ba and url_barang:
                            row_data = {
                                "toko": form_toko.strip().upper(),
                                "no_nrb": form_no_nrb,
                                "tgl_nrb": form_tgl_nrb,
                                "foto_ba_url": url_ba,
                                "foto_barang_url": url_barang
                            }
                            if simpan_ke_gsheets_via_api("rusak_pabrik_uploads", row_data):
                                st.success("🚀 Sukses Terkirim! Laporan Anda sudah tersimpan aman di cloud.")
                    else:
                        st.error("Gagal mengirim! Harap isi semua kolom teks dan lampirkan kedua gambar.")
