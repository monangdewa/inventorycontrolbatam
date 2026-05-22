import streamlit as st
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# ==========================================
# 1. KONFIGURASI HALAMAN & PROTECTIONS
# ==========================================
st.set_page_config(page_title="IC BATAM", layout="wide")

# JavaScript untuk menghilangkan header bawaan Streamlit secara paksa
components.html(
    """
    <script>
        const removeElements = () => {
            const selectors = [
                '.stAppDeployButton', 
                '[data-testid="stActionButton"]', 
                'header', 
                '.stAppHeader',
                '[data-testid="stIconMaterial"]'
            ];
            selectors.forEach(selector => {
                const elements = parent.document.querySelectorAll(selector);
                elements.forEach(el => {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                });
            });
        };
        setInterval(removeElements, 500);
    </script>
    """,
    height=0,
    width=0
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

# Hubungkan ke Google Sheets Connection bawaan Streamlit
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Koneksi Google Sheets belum dikonfigurasi di Secrets Streamlit.")

# Fungsi untuk upload foto langsung ke Cloud Storage (ImgBB)
def upload_ke_imgbb(file_foto):
    try:
        api_key = st.secrets["IMGBB_API_KEY"]
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": api_key}
        files = {"image": file_foto.getvalue()}
        
        response = requests.post(url, data=payload, files=files)
        if response.status_code == 200:
            return response.json()["data"]["url"]  # Mengembalikan link URL foto online
        else:
            st.error("Gagal mengunggah foto ke Cloud Server ImgBB.")
            return None
    except Exception as e:
        st.error(f"Error Konfigurasi Cloud Upload: {e}")
        return None

# Inisialisasi Session State dasar untuk Login & Master CSV
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
            st.error("Username atau Password salah. Silakan coba lagi.")
            
    st.write("---")
    st.markdown("<p style='text-align: center; color: gray; font-size: 13px;'>👮 Inventory Control - Batam 🥇</p>", unsafe_allow_html=True)

# ==========================================
# 4. HALAMAN DASHBOARD (JIKA SUDAH LOGIN)
# ==========================================
else:
    st.sidebar.title(f"👤 {st.session_state.role}")
    st.sidebar.write("Selamat Datang!")
    if st.sidebar.button("Log Out", type="secondary"):
        logout()

    # ------------------------------------------
    # A. INTERFACE ADMIN (Adm_ICBTM)
    # ------------------------------------------
    if st.session_state.role == "Adm_ICBTM":
        st.title("🖥️ Dashboard Admin - IC BATAM")
        tab1, tab2, tab3 = st.tabs(["📁 Kelola CSV Induk", "📸 Cek Bukti Foto NBH (IC)", "🔆 Cek Rusak Pabrik (Toko)"])
        
        with tab1:
            st.header("Upload Master Data CSV NBH")
            uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
            if uploaded_file is not None:
                if st.button("Proses & Simpan CSV di Sesi"):
                    df = pd.read_csv(uploaded_file, sep='|')
                    st.session_state.uploaded_data = df
                    st.success("Data CSV Induk berhasil dimuat untuk sesi ini!")

        with tab2:
            st.header("Bukti Foto NBH dari Database Cloud (Live)")
            try:
                df_nbh = conn.read(worksheet="nbh_uploads", ttl="1s")
                if df_nbh.empty:
                    st.info("Belum ada bukti foto NBH yang masuk ke database cloud.")
                else:
                    st.dataframe(df_nbh, use_container_width=True)
                    st.write("---")
                    for idx, row in df_nbh.iterrows():
                        with st.container(border=True):
                            st.write(f"**NBH:** {row['nbh']} | **Status:** {row['status']}")
                            st.image(row['image_url'], width=350, caption="Foto Bukti IC")
            except Exception:
                st.info("Menunggu data masuk atau periksa nama worksheet 'nbh_uploads' Anda.")

        with tab3:
            st.header("Laporan Foto Rusak Pabrik dari Toko (Live)")
            try:
                df_rp = conn.read(worksheet="rusak_pabrik_uploads", ttl="1s")
                if df_rp.empty:
                    st.info("Belum ada laporan kerusakan pabrik dari toko di database cloud.")
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
                st.info("Menunggu data masuk atau periksa nama worksheet 'rusak_pabrik_uploads' Anda.")

    # ------------------------------------------
    # B. INTERFACE IC (IC_Batam)
    # ------------------------------------------
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
                        try:
                            df_existing = conn.read(worksheet="nbh_uploads", ttl="0s")
                        except Exception:
                            df_existing = pd.DataFrame(columns=["nbh", "image_url", "status"])
                            
                        new_data = pd.DataFrame([{"nbh": str(nbh_choice), "image_url": cloud_url, "status": "Selesai"}])
                        df_updated = pd.concat([df_existing, new_data], ignore_index=True)
                        
                        conn.update(worksheet="nbh_uploads", data=df_updated)
                        st.success("🔥 Berhasil! Data dan foto tersimpan online dan langsung bisa dilihat Admin.")
                else:
                    st.error("Mohon isi teks NBH dan pilih fotonya terlebih dahulu.")

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
                            with c1:
                                st.image(row['foto_ba_url'], width=200, caption="BA Toko")
                            with c2:
                                st.image(row['foto_barang_url'], width=200, caption="Fisik Barang")
            except Exception:
                st.info("Sinkronisasi database...")

    # ------------------------------------------
    # C. INTERFACE TOKO (Toko_Kepri)
    # ------------------------------------------
    elif st.session_state.role == "Toko_Kepri":
        st.title("🏪 Portal Toko - KEPRI HITS")
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
                            try:
                                df_existing = conn.read(worksheet="rusak_pabrik_uploads", ttl="0s")
                            except Exception:
                                df_existing = pd.DataFrame(columns=["toko", "no_nrb", "tgl_nrb", "foto_ba_url", "foto_barang_url"])
                            
                            new_row = pd.DataFrame([{
                                "toko": form_toko.strip().upper(),
                                "no_nrb": form_no_nrb,
                                "tgl_nrb": form_tgl_nrb,
                                "foto_ba_url": url_ba,
                                "foto_barang_url": url_barang
                            }])
                            
                            df_updated = pd.concat([df_existing, new_row], ignore_index=True)
                            conn.update(worksheet="rusak_pabrik_uploads", data=df_updated)
                            st.success("🚀 Sukses Terkirim! Laporan Anda sudah tersimpan di cloud database Admin & IC.")
                    else:
                        st.error("Gagal mengirim! Harap isi semua kolom teks dan lampirkan kedua gambar.")
