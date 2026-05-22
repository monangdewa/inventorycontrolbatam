import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# ==========================================
# 1. KONFIGURASI HALAMAN & PROTEKSI SEAMLESS
# ==========================================
st.set_page_config(page_title="MTP Dashboard System", layout="wide")

# Trik Javascript + CSS Kuat untuk Menghapus Paksa Ikon GitHub & Teks Share
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
# 2. DATABASE KREDENSIAL
# ==========================================
CREDENTIALS = {
    "Admin": {"user": "MTP", "pwd": "1712"},
    "IC Upload": {"user": "ICBTM", "pwd": "@ICBTM"},
    "Toko": {"user": "BTMJUARA", "pwd": "BTMJUARA"}
}

# ==========================================
# 3. INISIALISASI SESSION STATE
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None  
if "ic_uploads" not in st.session_state:
    st.session_state.ic_uploads = []  
# PENAMPUNGAN BARU UNTUK DATA RUSAK PABRIK
if "rusak_pabrik_uploads" not in st.session_state:
    st.session_state.rusak_pabrik_uploads = []

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# ==========================================
# 4. HALAMAN LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.title("🔒 MTP System Login")
    st.subheader("Silakan pilih jenis login dan masukkan akun Anda")
    
    role_choice = st.selectbox("Jenis Login", ["Admin", "IC Upload", "Toko"])
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

# ==========================================
# 5. HALAMAN DASHBOARD (JIKA SUDAH LOGIN)
# ==========================================
else:
    st.sidebar.title(f"👤 {st.session_state.role}")
    st.sidebar.write("Selamat Datang!")
    if st.sidebar.button("Log Out", type="secondary"):
        logout()

    # --- DASHBOARD ADMIN ---
    if st.session_state.role == "Admin":
        st.title("🖥️ Dashboard Admin")
        tab1, tab2, tab3 = st.tabs(["📁 Upload & Kelola CSV", "📸 Cek & Edit Bukti Foto IC", "⚠️ Cek Rusak Pabrik (Toko)"])
        
        with tab1:
            st.header("Upload Data CSV")
            delete_previous = st.radio("Hapus data sebelumnya sebelum upload baru?", ("Tidak", "YA"))
            uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
            
            if uploaded_file is not None:
                if st.button("Proses File CSV"):
                    try:
                        df = pd.read_csv(uploaded_file, sep='|')
                        if delete_previous == "YA":
                            st.session_state.uploaded_data = df
                            st.warning("Data sebelumnya telah dihapus.")
                        else:
                            if st.session_state.uploaded_data is not None:
                                st.session_state.uploaded_data = pd.concat([st.session_state.uploaded_data, df], ignore_index=True)
                                st.success("Data baru berhasil ditambahkan.")
                            else:
                                st.session_state.uploaded_data = df
                                st.success("Data berhasil diupload.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal membaca file. Error: {e}")
            
            if st.session_state.uploaded_data is not None:
                st.write("---")
                st.subheader("🔍 Filter & Tampilkan Data Saat Ini")
                nama_kolom_toko = st.session_state.uploaded_data.columns[0]
                list_toko = sorted(st.session_state.uploaded_data[nama_kolom_toko].dropna().unique().tolist())
                toko_terpilih = st.multiselect("Pilih Toko yang Ingin Ditampilkan:", options=list_toko, default=list_toko)
                df_filtered = st.session_state.uploaded_data[st.session_state.uploaded_data[nama_kolom_toko].isin(toko_terpilih)]
                st.dataframe(df_filtered, use_container_width=True)
            else:
                st.info("Belum ada data CSV yang diupload.")

        with tab2:
            st.header("Bukti Foto dari IC")
            if not st.session_state.ic_uploads:
                st.info("Belum ada bukti foto yang diupload oleh IC.")
            else:
                for idx, item in enumerate(st.session_state.ic_uploads):
                    with st.container(border=True):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"**NBH:** {item['nbh']} | **Status:** {item['status']}")
                            st.image(item['image'], width=300)
                        with col2:
                            new_nbh = st.text_input(f"Edit NBH ({idx})", value=item['nbh'], key=f"admin_edit_{idx}")
                            if st.button(f"Simpan Perubahan ({idx})", key=f"admin_save_{idx}"):
                                st.session_state.ic_uploads[idx]['nbh'] = new_nbh
                                st.success("Data NBH diperbarui!")
                                st.rerun()
                            if st.button(f"Hapus Foto ({idx})", key=f"admin_del_{idx}"):
                                st.session_state.ic_uploads.pop(idx)
                                st.error("Foto dihapus.")
                                st.rerun()

        # MENU BARU ADMIN: MELIHAT RUSAK PABRIK
        with tab3:
            st.header("Laporan Foto Rusak Pabrik dari Toko")
            if not st.session_state.rusak_pabrik_uploads:
                st.info("Belum ada laporan kerusakan pabrik dari toko.")
            else:
                for idx, rp in enumerate(st.session_state.rusak_pabrik_uploads):
                    with st.container(border=True):
                        st.write(f"### 🏪 Toko: {rp['toko']} | No NRB: {rp['no_nrb']} | Tgl NRB: {rp['tgl_nrb']}")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write("**1. Foto BA Toko:**")
                            st.image(rp['foto_ba'], width=300)
                        with c2:
                            st.write("**2. Foto Barang:**")
                            st.image(rp['foto_barang'], width=300)
                        
                        if st.button(f"Hapus Laporan Ini ({idx})", key=f"admin_del_rp_{idx}"):
                            st.session_state.rusak_pabrik_uploads.pop(idx)
                            st.error("Laporan Rusak Pabrik berhasil dihapus.")
                            st.rerun()

    # --- DASHBOARD IC UPLOAD ---
    elif st.session_state.role == "IC Upload":
        st.title("📤 Dashboard IC Upload")
        tab1, tab2 = st.tabs(["📌 Upload Bukti Kerja IC", "⚠️ Cek Rusak Pabrik (Toko)"])
        
        with tab1:
            st.subheader("Input Bukti Kerja")
            if st.session_state.uploaded_data is not None:
                kolom_nbh = [col for col in st.session_state.uploaded_data.columns if 'NBH' in col]
                if kolom_nbh:
                    nbh_options = st.session_state.uploaded_data[kolom_nbh[0]].dropna().unique().tolist()
                    nbh_choice = st.selectbox("Pilih NBH", nbh_options)
                else:
                    nbh_choice = st.text_input("Masukkan NBH (Ketik Manual)")
            else:
                nbh_choice = st.text_input("Masukkan NBH (Ketik Manual)")
                
            img_file = st.file_uploader("Upload Bukti Foto", type=["jpg", "jpeg", "png"])
            
            if st.button("Submit Upload", type="primary"):
                if nbh_choice and img_file:
                    st.session_state.ic_uploads.append({
                        "nbh": str(nbh_choice),
                        "image": img_file,
                        "status": "Selesai"
                    })
                    st.success("Bukti berhasil diupload!")
                    st.rerun()
                else:
                    st.error("Mohon isi NBH dan upload foto.")
                    
            st.write("---")
            st.subheader("Riwayat Upload Anda")
            if not st.session_state.ic_uploads:
                st.info("Anda belum mengupload foto apapun.")
            else:
                for idx, item in enumerate(st.session_state.ic_uploads):
                    with st.container(border=True):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"**NBH:** {item['nbh']} | **Status:** {item['status']}")
                            st.image(item['image'], width=200)
                        with col2:
                            edit_nbh_ic = st.text_input(f"Ubah NBH", value=item['nbh'], key=f"ic_edit_{idx}")
                            if st.button(f"Update NBH", key=f"ic_save_{idx}"):
                                st.session_state.ic_uploads[idx]['nbh'] = edit_nbh_ic
                                st.success("NBH diperbarui.")
                                st.rerun()
                            if st.button(f"Hapus", key=f"ic_del_{idx}"):
                                st.session_state.ic_uploads.pop(idx)
                                st.warning("Data dihapus.")
                                st.rerun()

        # MENU BARU IC: MELIHAT RUSAK PABRIK
        with tab2:
            st.header("Pantau Foto Rusak Pabrik dari Toko")
            if not st.session_state.rusak_pabrik_uploads:
                st.info("Belum ada laporan kerusakan pabrik dari toko.")
            else:
                for idx, rp in enumerate(st.session_state.rusak_pabrik_uploads):
                    with st.container(border=True):
                        st.write(f"### 🏪 Toko: {rp['toko']} | No NRB: {rp['no_nrb']} | Tgl NRB: {rp['tgl_nrb']}")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write("**1. Foto BA Toko:**")
                            st.image(rp['foto_ba'], width=200)
                        with c2:
                            st.write("**2. Foto Barang:**")
                            st.image(rp['foto_barang'], width=200)

    # --- DASHBOARD TOKO ---
    elif st.session_state.role == "Toko":
        st.title("🏪 Dashboard Toko")
        
        st.subheader("Pengaturan Akses Toko")
        kode_toko_anda = st.text_input("Masukkan Kode Toko Anda:", value="TWSU").strip().upper()
        
        tab1, tab2, tab3 = st.tabs(["📊 Data NBH", "💬 Bukti Chat", "⚠️ Rusak Pabrik"])
        
        with tab1:
            st.header(f"Melihat Data NBH - Toko {kode_toko_anda}")
            if st.session_state.uploaded_data is not None:
                nama_kolom_toko = st.session_state.uploaded_data.columns[0]
                data_toko_ini = st.session_state.uploaded_data[st.session_state.uploaded_data[nama_kolom_toko].astype(str).str.strip().str.upper() == kode_toko_anda]
                
                if not data_toko_ini.empty:
                    st.dataframe(data_toko_ini, use_container_width=True)
                else:
                    st.warning(f"Tidak ada data NBH untuk kode toko '{kode_toko_anda}'.")
            else:
                st.info("Belum ada data NBH utama dari Admin.")
                
            st.write("---")
            st.subheader("Status Foto dari IC")
            if st.session_state.ic_uploads:
                toko_view = [{"NBH": x["nbh"], "Status Dokumen": x["status"]} for x in st.session_state.ic_uploads]
                st.table(toko_view)
            else:
                st.info("Belum ada update bukti fisik dari IC.")
                
        with tab2:
            st.header("Bukti Chat")
            st.info("Fitur tampilan bukti chat toko.")
            st.text_area("Catatan/Pesan Toko ke Tim IC", placeholder="Tulis pesan di sini...")

        # MENU BARU TOKO: INPUT RUSAK PABRIK & UPLOAD 2 FOTO
        with tab3:
            st.header("Form Input Rusak Pabrik")
            
            with st.form("form_rusak_pabrik", clear_on_submit=True):
                # Input Teks Form sesuai request
                form_toko = st.text_input("Nama/Kode Toko", value=kode_toko_anda)
                form_no_nrb = st.text_input("Masukkan No NRB")
                form_tgl_nrb = st.text_input("Masukkan Tanggal NRB (DD/MM/YYYY)")
                
                st.write("---")
                # Upload Dua Bukti Foto sesuai request
                foto_ba = st.file_uploader("1. Upload Foto BA Toko", type=["jpg", "jpeg", "png"], key="ba_toko")
                foto_barang = st.file_uploader("2. Upload Foto Barang", type=["jpg", "jpeg", "png"], key="brg_toko")
                
                submit_rp = st.form_submit_button("Kirim Laporan Rusak Pabrik", type="primary")
                
                if submit_rp:
                    if form_toko and form_no_nrb and form_tgl_nrb and foto_ba and foto_barang:
                        st.session_state.rusak_pabrik_uploads.append({
                            "toko": form_toko.strip().upper(),
                            "no_nrb": form_no_nrb,
                            "tgl_nrb": form_tgl_nrb,
                            "foto_ba": foto_ba,
                            "foto_barang": foto_barang
                        })
                        st.success("Laporan Rusak Pabrik berhasil dikirim! Tim Admin dan IC sudah bisa melihat laporan ini.")
                    else:
                        st.error("Gagal kirim! Harap isi semua formulir teks dan pastikan kedua foto sudah di-upload.")
