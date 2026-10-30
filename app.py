import datetime
import streamlit as st
from supabase import Client, create_client

# Konfigurasi halaman agar optimal di layar HP
st.set_page_config(
    page_title="Wanna Be With U - Laporan", page_icon="🍌", layout="centered"
)

# -----------------------------------------------------------------------------
# CUSTOM CSS FOR STYLING
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Latar belakang utama & penyesuaian font */
    .main {
        background-color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Judul Utama */
    h1 {
        color: #facc15 !important;
        font-weight: 800 !important;
        text-align: center;
        margin-bottom: 0px !important;
    }
    
    /* Subtitle */
    .stSubheader {
        color: #cbd5e1 !important;
        text-align: center;
        font-size: 1.1rem !important;
        margin-bottom: 1.5rem !important;
    }

    /* Container Kartu Metric / Summary */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: bold !important;
        color: #38bdf8 !important;
    }

    /* Kustomisasi Form & Input */
    div[data-testid="stForm"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }

    /* Tombol Submit */
    div[data-testid="stForm"] button {
        background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        width: 100% !important;
        transition: transform 0.2s, opacity 0.2s;
    }
    div[data-testid="stForm"] button:active {
        transform: scale(0.98);
    }

    /* Styling Tabel Dataframe */
    div[data-testid="stDataFrame"] {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 8px;
        border: 1px solid #334155;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #334155;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# SUPABASE CONNECTION
# -----------------------------------------------------------------------------
@st.cache_resource
def init_connection():
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


supabase = init_connection()

# Header Utama
st.title("🍌 Wanna Be With U")
st.subheader("Dashboard Laporan & Keuangan")

# Menu Navigasi Samping
menu = st.sidebar.selectbox(
    "📌 Pilih Menu",
    ["📊 Rekap & Dashboard", "➕ Input Penjualan", "💸 Input Pengeluaran"],
)


def fetch_data(table_name):
  try:
    response = supabase.table(table_name).select("*").execute()
    return response.data
  except Exception as e:
    st.error(f"Gagal memuat data dari {table_name}: {e}")
    return []


# -----------------------------------------------------------------------------
# MENU 1: REKAP & DASHBOARD
# -----------------------------------------------------------------------------
if menu == "📊 Rekap & Dashboard":
  st.markdown("### 📈 Ringkasan Keuangan")

  penjualan = fetch_data("tabel_penjualan")
  pengeluaran = fetch_data("tabel_pengeluaran")

  # Hitung Total
  total_omset = sum(item.get("total_penjualan", 0) for item in penjualan)
  total_biaya = sum(item.get("pengeluaran", 0) for item in pengeluaran)
  total_profit = total_omset - total_biaya

  # Tampilkan Ringkasan Kartu (Metrics)
  col1, col2, col3 = st.columns(3)
  col1.metric("Total Omset", f"Rp {total_omset:,.0f}")
  col2.metric("Total Biaya", f"Rp {total_biaya:,.0f}")
  col3.metric("Estimasi Profit", f"Rp {total_profit:,.0f}")

  st.markdown("---")

  # Tabel Penjualan
  st.markdown("#### 📦 Data Penjualan")
  if penjualan:
    st.dataframe(penjualan, use_container_width=True)
  else:
    st.info("Belum ada data penjualan tercatat.")

  # Tabel Pengeluaran
  st.markdown("#### 💸 Data Pengeluaran")
  if pengeluaran:
    st.dataframe(pengeluaran, use_container_width=True)
  else:
    st.info("Belum ada data pengeluaran tercatat.")

# -----------------------------------------------------------------------------
# MENU 2: INPUT PENJUALAN
# -----------------------------------------------------------------------------
elif menu == "➕ Input Penjualan":
  st.markdown("### 📝 Input Penjualan Baru")

  with st.form("form_penjualan", clear_on_submit=True):
    tanggal = st.date_input("Tanggal", datetime.date.today())
    toko = st.text_input(
        "Nama Toko / Reseller",
        placeholder="Contoh: SBR2, Ajirasa1, Reseller",
    )
    produksi = st.number_input(
        "Jumlah Produksi / Titip", min_value=0, step=1
    )
    dikirim = st.number_input("Jumlah Dikirim", min_value=0, step=1)
    total_penjualan = st.number_input(
        "Total Penjualan (Rp)", min_value=0.0, step=1000.0, format="%.2f"
    )

    submit_penjualan = st.form_submit_button("💾 Simpan Data Penjualan")

    if submit_penjualan:
      try:
        data_baru = {
            "tanggal": str(tanggal),
            "toko": toko,
            "produksi": produksi,
            "dikirim": dikirim,
            "total_penjualan": total_penjualan,
        }
        supabase.table("tabel_penjualan").insert(data_baru).execute()
        st.success("✅ Data penjualan berhasil disimpan!")
        st.rerun()
      except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")

# -----------------------------------------------------------------------------
# MENU 3: INPUT PENGELUARAN
# -----------------------------------------------------------------------------
elif menu == "💸 Input Pengeluaran":
  st.markdown("### 📝 Input Pengeluaran Baru")

  with st.form("form_pengeluaran", clear_on_submit=True):
    tanggal = st.date_input("Tanggal Pengeluaran", datetime.date.today())
    nama_barang = st.text_input(
        "Nama Barang / Bahan", placeholder="Contoh: Pisang, Minyak, Plastik"
    )
    qty = st.number_input("Kuantitas (Qty)", min_value=0.0, step=0.5)
    pengeluaran = st.number_input(
        "Total Biaya Pengeluaran (Rp)", min_value=0.0, step=1000.0, format="%.2f"
    )

    submit_pengeluaran = st.form_submit_button("💾 Simpan Data Pengeluaran")

    if submit_pengeluaran:
      try:
        data_baru = {
            "tanggal": str(tanggal),
            "nama_barang": nama_barang,
            "qty": qty,
            "pengeluaran": pengeluaran,
        }
        supabase.table("tabel_pengeluaran").insert(data_baru).execute()
        st.success("✅ Data pengeluaran berhasil disimpan!")
        st.rerun()
      except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")
