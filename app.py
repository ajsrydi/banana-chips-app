import pandas as pd
import streamlit as st
from supabase import Client, create_client

# Konfigurasi Tampilan Halaman
st.set_page_config(
    page_title="Wanna Be With U - Laporan", page_icon="🍌", layout="wide"
)

# Inisialisasi Koneksi ke Supabase
@st.cache_resource
def init_supabase():
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


supabase: Client = init_supabase()

st.title("🍌 Wanna Be With U - Dashboard Laporan")
st.markdown("Kelola penjualan, pengeluaran, dan profit usaha dengan mudah dari HP.")

# Menu Navigasi di Sidebar
menu = st.sidebar.selectbox(
    "Pilih Menu",
    [
        "📊 Rekap Keuangan Otomatis",
        "🍫 Catat Penjualan",
        "💸 Catat Pengeluaran",
    ],
)

# ==========================================
# 1. REKAP KEUANGAN OTOMATIS
# ==========================================
if menu == "📊 Rekap Keuangan Otomatis":
  st.header("📊 Rekap Keuangan & Profit")

  try:
    # Ambil data penjualan & pengeluaran dari Supabase
    res_penjualan = supabase.table("tabel_penjualan").select("*").execute()
    res_pengeluaran = supabase.table("tabel_pengeluaran").select("*").execute()

    df_penjualan = (
        pd.DataFrame(res_penjualan.data)
        if res_penjualan.data
        else pd.DataFrame()
    )
    df_pengeluaran = (
        pd.DataFrame(res_pengeluaran.data)
        if res_pengeluaran.data
        else pd.DataFrame()
    )

    # Hitung total omset dan pengeluaran
    total_omset = (
        df_penjualan["total_penjualan"].sum()
        if not df_penjualan.empty and "total_penjualan" in df_penjualan.columns
        else 0
    )
    total_keluar = (
        df_pengeluaran["pengeluaran"].sum()
        if not df_pengeluaran.empty and "pengeluaran" in df_pengeluaran.columns
        else 0
    )
    profit_bersih = total_omset - total_keluar

    # Tampilkan Ringkasan Metrik
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Omset Penjualan", f"Rp {total_omset:,.0f}")
    col2.metric("Total Pengeluaran", f"Rp {total_keluar:,.0f}")
    col3.metric("Estimasi Profit Bersih", f"Rp {profit_bersih:,.0f}")

    st.markdown("---")
    st.subheader("📋 Daftar Transaksi Penjualan")
    if not df_penjualan.empty:
      st.dataframe(df_penjualan, use_container_width=True)
    else:
      st.info("Belum ada data penjualan.")

    st.subheader("📋 Daftar Transaksi Pengeluaran")
    if not df_pengeluaran.empty:
      st.dataframe(df_pengeluaran, use_container_width=True)
    else:
      st.info("Belum ada data pengeluaran.")

  except Exception as e:
    st.error(f"Gagal memuat rekap keuangan: {e}")

# ==========================================
# 2. CATAT PENJUALAN
# ==========================================
elif menu == "🍫 Catat Penjualan":
  st.header("🍫 Form Input Penjualan")

  with st.form("form_penjualan"):
    tanggal = st.date_input("Tanggal")
    toko = st.text_input("Nama Toko / Reseller (Contoh: SBR, AR1, resell)")
    produksi = st.number_input("Jumlah Produksi", value=0, step=1)
    dikirim = st.number_input("Jumlah Dikirim", value=0, step=1)
    total_penjualan = st.number_input("Total Nilai Penjualan (Rp)", value=0.0)

    submit_penj = st.form_submit_button("Simpan Penjualan")

    if submit_penj:
      try:
        supabase.table("tabel_penjualan").insert({
            "tanggal": str(tanggal),
            "toko": toko,
            "produksi": produksi,
            "dikirim": dikirim,
            "total_penjualan": total_penjualan,
        }).execute()
        st.success("Data penjualan berhasil disimpan ke Supabase! 🎉")
      except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

# ==========================================
# 3. CATAT PENGELUARAN
# ==========================================
elif menu == "💸 Catat Pengeluaran":
  st.header("💸 Form Input Pengeluaran / Belanja")

  with st.form("form_pengeluaran"):
    tanggal_keluar = st.date_input("Tanggal Belanja")
    nama_barang = st.text_input(
        "Nama Barang (Contoh: Kemasan Coklat, Minyak, Keresek)"
    )
    qty = st.number_input(
        "Jumlah Barang (Qty)", value=1.0, step=0.1, format="%.2f"
    )
    satuan = st.text_input("Satuan (Contoh: pcs, liter, bal, kg)")
    total_biaya = st.number_input("Total Harga / Pengeluaran (Rp)", value=0.0)

    submit_keluar = st.form_submit_button("Simpan Pengeluaran")

    if submit_keluar:
      try:
        supabase.table("tabel_pengeluaran").insert({
            "tanggal": str(tanggal_keluar),
            "nama_barang": nama_barang,
            "qty": qty,
            "satuan": satuan,
            "pengeluaran": total_biaya,
        }).execute()
        st.success("Data pengeluaran berhasil disimpan ke Supabase! 🎉")
      except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
