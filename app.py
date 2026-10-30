import datetime
import pandas as pd
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
    .main {
        background-color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    h1 {
        color: #facc15 !important;
        font-weight: 800 !important;
        text-align: center;
        margin-bottom: 0px !important;
    }
    .stSubheader {
        color: #cbd5e1 !important;
        text-align: center;
        font-size: 1.1rem !important;
        margin-bottom: 1.5rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: bold !important;
        color: #38bdf8 !important;
    }
    div[data-testid="stForm"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
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
    div[data-testid="stDataFrame"] {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 8px;
        border: 1px solid #334155;
    }
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
    [
        "📊 Rekap & Dashboard",
        "🏪 Kelola Master Toko",
        "➕ Input Penjualan",
        "💸 Input Pengeluaran",
    ],
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

  total_omset = sum(item.get("total_penjualan", 0) for item in penjualan)
  total_biaya = sum(item.get("pengeluaran", 0) for item in pengeluaran)
  total_profit = total_omset - total_biaya

  col1, col2, col3 = st.columns(3)
  col1.metric("Total Omset", f"Rp {total_omset:,.0f}")
  col2.metric("Total Biaya", f"Rp {total_biaya:,.0f}")
  col3.metric("Estimasi Profit", f"Rp {total_profit:,.0f}")

  st.markdown("---")

  st.markdown("#### 📦 Data Penjualan")
  if penjualan:
    st.dataframe(penjualan, use_container_width=True)
  else:
    st.info("Belum ada data penjualan tercatat.")

  st.markdown("#### 💸 Data Pengeluaran")
  if pengeluaran:
    st.dataframe(pengeluaran, use_container_width=True)
  else:
    st.info("Belum ada data pengeluaran tercatat.")

# -----------------------------------------------------------------------------
# MENU 2: KELOLA MASTER TOKO (DENGAN KOLOM HARGA BERSIH)
# -----------------------------------------------------------------------------
elif menu == "🏪 Kelola Master Toko":
  st.markdown("### 🏪 Master Data Toko & Harga")

  with st.form("form_toko", clear_on_submit=True):
    nama_toko = st.text_input(
        "Nama Toko / Reseller", placeholder="Contoh: SBR2, Ajirasa1, AR 3"
    )
    harga_jual = st.number_input(
        "Harga Jual per Pcs (Rp)", min_value=0.0, step=500.0, format="%.2f"
    )
    potongan_persen = st.number_input(
        "Potongan / Komisi Toko (%)",
        min_value=0.0,
        max_value=100.0,
        step=0.5,
        format="%.1f",
    )

    submit_toko = st.form_submit_button("💾 Simpan / Update Toko")

    if submit_toko:
      if nama_toko.strip() == "":
        st.warning("⚠️ Nama toko tidak boleh kosong!")
      else:
        try:
          data_toko = {
              "nama_toko": nama_toko.strip(),
              "harga_jual": harga_jual,
              "potongan_persen": potongan_persen,
          }
          supabase.table("tabel_toko").upsert(
              data_toko, on_conflict="nama_toko"
          ).execute()
          st.success(f"✅ Data toko '{nama_toko}' berhasil disimpan!")
          st.rerun()
        except Exception as e:
          st.error(f"❌ Gagal menyimpan toko: {e}")

  st.markdown("---")
  st.markdown("#### 📋 Daftar Toko Terdaftar")
  list_toko = fetch_data("tabel_toko")
  if list_toko:
    # Buat DataFrame menggunakan Pandas untuk menambah kolom hitung otomatis
    df_toko = pd.DataFrame(list_toko)

    # Tambahkan kolom hitung: Harga Jual - Potongan (%)
    df_toko["Harga Bersih per Pcs (Rp)"] = df_toko["harga_jual"] - (
        df_toko["harga_jual"] * df_toko["potongan_persen"] / 100
    )

    st.dataframe(df_toko, use_container_width=True)
  else:
    st.info("Belum ada toko yang didaftarkan.")

# -----------------------------------------------------------------------------
# MENU 3: INPUT PENJUALAN
# -----------------------------------------------------------------------------
elif menu == "➕ Input Penjualan":
  st.markdown("### 📝 Input Penjualan Baru")

  data_toko = fetch_data("tabel_toko")

  if not data_toko:
    st.warning(
        "⚠️ Belum ada data toko. Silakan daftarkan toko di menu **🏪 Kelola"
        " Master Toko** terlebih dahulu!"
    )
  else:
    opsi_toko = {t["nama_toko"]: t for t in data_toko}
    pilihan_toko_nama = st.selectbox("Pilih Toko", list(opsi_toko.keys()))
    toko_terpilih = opsi_toko[pilihan_toko_nama]

    harga_jual = toko_terpilih.get("harga_jual", 0)
    potongan = toko_terpilih.get("potongan_persen", 0)
    harga_bersih_pcs = harga_jual - (harga_jual * potongan / 100)

    st.info(
        f"💡 **Harga Jual:** Rp {harga_jual:,.0f} | **Potongan:**"
        f" {potongan}% \n\n✨ **Harga Bersih per Pcs:** Rp"
        f" {harga_bersih_pcs:,.0f}"
    )

    with st.form("form_penjualan", clear_on_submit=True):
      tanggal = st.date_input("Tanggal", datetime.date.today())
      produksi = st.number_input("Jumlah Produksi / Titip", min_value=0, step=1)
      dikirim = st.number_input("Jumlah Dikirim / Laku", min_value=0, step=1)

      omset_bersih = dikirim * harga_bersih_pcs

      total_penjualan = st.number_input(
          "Total Penjualan Bersih (Rp)",
          value=float(omset_bersih),
          min_value=0.0,
          step=1000.0,
          format="%.2f",
          help="Otomatis dihitung dari (Dikirim × Harga Bersih per Pcs)",
      )

      submit_penjualan = st.form_submit_button("💾 Simpan Data Penjualan")

      if submit_penjualan:
        try:
          data_baru = {
              "tanggal": str(tanggal),
              "toko": pilihan_toko_nama,
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
# MENU 4: INPUT PENGELUARAN
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
