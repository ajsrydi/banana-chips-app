import datetime
import streamlit as st
from supabase import Client, create_client

# Konfigurasi halaman agar optimal di layar HP
st.set_page_config(
    page_title="Wanna Be With U - Laporan", page_icon="🍌", layout="centered"
)


# Inisialisasi koneksi Supabase menggunakan st.secrets
@st.cache_resource
def init_connection():
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


supabase = init_connection()

# Judul Utama Aplikasi
st.title("🍌 Wanna Be With U")
st.subheader("Dashboard Laporan & Keuangan")

# Menu Navigasi Samping (Sidebar)
menu = st.sidebar.selectbox(
    "Pilih Menu",
    ["📊 Rekap & Dashboard", "➕ Input Penjualan", "💸 Input Pengeluaran"],
)


# Fungsi helper untuk mengambil data dari Supabase
def fetch_data(table_name):
  try:
    response = supabase.table(table_name).select("*").execute()
    return response.data
  except Exception as e:
    st.error(f"Gagal memuat data dari {table_name}: {e}")
    return []


# --- MENU 1: REKAP & DASHBOARD ---
if menu == "📊 Rekap & Dashboard":
  st.markdown("### Rekapitulasi Keuangan")

  # Ambil data dari kedua tabel
  penjualan = fetch_data("tabel_penjualan")
  pengeluaran = fetch_data("tabel_pengeluaran")

  # Tampilkan Tabel Penjualan
  st.markdown("---")
  st.markdown("#### 📦 Tabel Penjualan")
  if penjualan:
    st.dataframe(penjualan, use_container_width=True)
  else:
    st.info("Belum ada data penjualan tercatat.")

  # Tampilkan Tabel Pengeluaran
  st.markdown("---")
  st.markdown("#### 💸 Tabel Pengeluaran")
  if pengeluaran:
    st.dataframe(pengeluaran, use_container_width=True)
  else:
    st.info("Belum ada data pengeluaran tercatat.")

# --- MENU 2: INPUT PENJUALAN ---
elif menu == "➕ Input Penjualan":
  st.markdown("### Tambah Catatan Penjualan")

  with st.form("form_penjualan", clear_on_submit=True):
    tanggal = st.date_input("Tanggal", datetime.date.today())
    store = st.text_input(
        "Nama Toko / Reseller",
        placeholder="Contoh: SBR2, Ajirasa1, Reseller",
    )
    production = st.number_input(
        "Jumlah Produksi / Titip", min_value=0, step=1
    )
    sent = st.number_input("Jumlah Dikirim", min_value=0, step=1)
    total_penjualan = st.number_input(
        "Total Penjualan (Rp)", min_value=0.0, step=1000.0, format="%.2f"
    )

    submit_penjualan = st.form_submit_button("Simpan Data Penjualan")

    if submit_penjualan:
      try:
        data_baru = {
            "date": str(tanggal),
            "store": store,
            "production": production,
            "sent": sent,
            "total_penjualan": total_penjualan,
        }
        supabase.table("tabel_penjualan").insert(data_baru).execute()
        st.success("✅ Data penjualan berhasil disimpan ke Supabase!")
      except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")

# --- MENU 3: INPUT PENGELUARAN ---
elif menu == "💸 Input Pengeluaran":
  st.markdown("### Tambah Catatan Pengeluaran")

  with st.form("form_pengeluaran", clear_on_submit=True):
    tanggal = st.date_input("Tanggal Pengeluaran", datetime.date.today())
    nama_barang = st.text_input(
        "Nama Barang / Bahan", placeholder="Contoh: Pisang, Minyak, Plastik"
    )
    qty = st.number_input("Kuantitas (Qty)", min_value=0.0, step=0.5)
    satuan = st.text_input("Satuan", placeholder="Contoh: kg, pcs, liter, dus")
    pengeluaran = st.number_input(
        "Total Biaya Pengeluaran (Rp)", min_value=0.0, step=1000.0, format="%.2f"
    )

    submit_pengeluaran = st.form_submit_button("Simpan Data Pengeluaran")

    if submit_pengeluaran:
      try:
        data_baru = {
            "date": str(tanggal),
            "nama_barang": nama_barang,
            "qty": qty,
            "satuan": satuan,
            "pengeluaran": pengeluaran,
        }
        supabase.table("tabel_pengeluaran").insert(data_baru).execute()
        st.success("✅ Data pengeluaran berhasil disimpan ke Supabase!")
      except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")
