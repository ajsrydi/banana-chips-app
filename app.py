import datetime
import pandas as pd
import streamlit as st
from supabase import Client, create_client

# Konfigurasi halaman agar optimal di layar HP
st.set_page_config(
    page_title="Wanna Be With U - Laporan", page_icon="🍌", layout="centered"
)


# Fungsi untuk memuat file CSS eksternal
def load_css(file_name):
  try:
    with open(file_name) as f:
      st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
  except FileNotFoundError:
    st.warning(
        f"File {file_name} tidak ditemukan. Pastikan file berada di direktori"
        " yang sama."
    )


# Muat styling dari file style.css
load_css("style.css")


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

# -----------------------------------------------------------------------------
# NAVIGASI SIDEBAR BERBASIS 2 KATEGORI DROPDOWN
# -----------------------------------------------------------------------------
st.sidebar.markdown("### 📌 Navigasi Menu")

kategori_utama = st.sidebar.selectbox(
    "Pilih Kategori",
    [
        "📦 Menu Operasional",
        "📊 Dashboard & Rekap",
        "🏪 Master Data Toko",
    ],
)

if kategori_utama == "📦 Menu Operasional":
  menu = st.sidebar.selectbox(
      "Pilih Menu",
      [
          "📦 Produksi & Stok",
          "🛒 Kelola Penjualan",
          "💸 Kelola Pengeluaran",
      ],
  )
elif kategori_utama == "📊 Dashboard & Rekap":
  menu = st.sidebar.selectbox(
      "Pilih Menu",
      [
          "📈 Dashboard Utama",
          "📊 Rekap Harian, Bulanan, Tahunan",
      ],
  )
else:
  menu = st.sidebar.selectbox("Pilih Master", ["🏪 Kelola Master Toko"])


def fetch_data(table_name):
  try:
    response = supabase.table(table_name).select("*").execute()
    return response.data
  except Exception as e:
    st.error(f"Gagal memuat data dari {table_name}: {e}")
    return []


# -----------------------------------------------------------------------------
# MENU 1: DASHBOARD UTAMA
# -----------------------------------------------------------------------------
if menu == "📈 Dashboard Utama":
  st.markdown("### 📈 Ringkasan Keuangan & Stok")

  penjualan = fetch_data("tabel_penjualan")
  pengeluaran = fetch_data("tabel_pengeluaran")
  produksi = fetch_data("tabel_produksi")

  total_omset = sum(item.get("total_penjualan", 0) for item in penjualan)
  total_biaya = sum(item.get("pengeluaran", 0) for item in pengeluaran)
  total_profit = total_omset - total_biaya

  total_prod_qty = sum(item.get("jumlah_produksi", 0) for item in produksi)
  total_kirim_qty = sum(item.get("dikirim", 0) for item in penjualan)
  sisa_stok = total_prod_qty - total_kirim_qty

  col1, col2, col3 = st.columns(3)
  col1.metric("Total Omset", f"Rp {total_omset:,.0f}")
  col2.metric("Total Biaya", f"Rp {total_biaya:,.0f}")
  col3.metric("Estimasi Profit", f"Rp {total_profit:,.0f}")

  col4, col5, col6 = st.columns(3)
  col4.metric("Total Produksi", f"{total_prod_qty:,} pcs")
  col5.metric("Total Terkirim", f"{total_kirim_qty:,} pcs")
  col6.metric("Sisa Stok Gudang", f"{sisa_stok:,} pcs")

  st.markdown("---")

  st.markdown("#### 📦 Data Penjualan Terakhir")
  if penjualan:
    st.dataframe(penjualan, use_container_width=True)
  else:
    st.info("Belum ada data penjualan tercatat.")

  st.markdown("#### 💸 Data Pengeluaran Terakhir")
  if pengeluaran:
    st.dataframe(pengeluaran, use_container_width=True)
  else:
    st.info("Belum ada data pengeluaran tercatat.")

# -----------------------------------------------------------------------------
# MENU 2: REKAP HARIAN, BULANAN, TAHUNAN
# -----------------------------------------------------------------------------
elif menu == "📊 Rekap Harian, Bulanan, Tahunan":
  st.markdown("### 📊 Rekap Harian, Bulanan & Tahunan")

  penjualan = fetch_data("tabel_penjualan")
  pengeluaran = fetch_data("tabel_pengeluaran")

  df_penjualan = pd.DataFrame(penjualan) if penjualan else pd.DataFrame()
  df_pengeluaran = (
      pd.DataFrame(pengeluaran) if pengeluaran else pd.DataFrame()
  )

  tab_harian, tab_bulanan, tab_tahunan = st.tabs(
      ["📅 Harian", "📆 Bulanan", "🗓️ Tahunan"]
  )

  with tab_harian:
    st.markdown("#### Rekap Berdasarkan Tanggal")
    if not df_penjualan.empty or not df_pengeluaran.empty:
      df_p_harian = (
          df_penjualan.groupby("tanggal")["total_penjualan"]
          .sum()
          .reset_index()
          if not df_penjualan.empty
          else pd.DataFrame(columns=["tanggal", "total_penjualan"])
      )
      df_exp_harian = (
          df_pengeluaran.groupby("tanggal")["pengeluaran"].sum().reset_index()
          if not df_pengeluaran.empty
          else pd.DataFrame(columns=["tanggal", "pengeluaran"])
      )

      df_harian = pd.merge(
          df_p_harian, df_exp_harian, on="tanggal", how="outer"
      ).fillna(0)
      df_harian = df_harian.sort_values(by="tanggal", ascending=False)
      df_harian["Profit Bersih"] = (
          df_harian["total_penjualan"] - df_harian["pengeluaran"]
      )

      st.dataframe(df_harian, use_container_width=True)
    else:
      st.info("Belum ada data transaksi untuk rekap harian.")

  with tab_bulanan:
    st.markdown("#### Rekap Berdasarkan Bulan")
    if not df_penjualan.empty or not df_pengeluaran.empty:
      if not df_penjualan.empty:
        df_penjualan["bulan"] = (
            pd.to_datetime(df_penjualan["tanggal"])
            .dt.to_period("M")
            .astype(str)
        )
        df_p_bulan = (
            df_penjualan.groupby("bulan")["total_penjualan"].sum().reset_index()
        )
      else:
        df_p_bulan = pd.DataFrame(columns=["bulan", "total_penjualan"])

      if not df_pengeluaran.empty:
        df_pengeluaran["bulan"] = (
            pd.to_datetime(df_pengeluaran["tanggal"])
            .dt.to_period("M")
            .astype(str)
        )
        df_exp_bulan = (
            df_pengeluaran.groupby("bulan")["pengeluaran"].sum().reset_index()
        )
      else:
        df_exp_bulan = pd.DataFrame(columns=["bulan", "pengeluaran"])

      df_bulanan = pd.merge(
          df_p_bulan, df_exp_bulan, on="bulan", how="outer"
      ).fillna(0)
      df_bulanan = df_bulanan.sort_values(by="bulan", ascending=False)
      df_bulanan["Profit Bersih"] = (
          df_bulanan["total_penjualan"] - df_bulanan["pengeluaran"]
      )

      st.dataframe(df_bulanan, use_container_width=True)
    else:
      st.info("Belum ada data transaksi untuk rekap bulanan.")

  with tab_tahunan:
    st.markdown("#### Rekap Berdasarkan Tahun")
    if not df_penjualan.empty or not df_pengeluaran.empty:
      if not df_penjualan.empty:
        df_penjualan["tahun"] = (
            pd.to_datetime(df_penjualan["tanggal"]).dt.year.astype(str)
        )
        df_p_tahun = (
            df_penjualan.groupby("tahun")["total_penjualan"].sum().reset_index()
        )
      else:
        df_p_tahun = pd.DataFrame(columns=["tahun", "total_penjualan"])

      if not df_pengeluaran.empty:
