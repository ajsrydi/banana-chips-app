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
# NAVIGASI SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.markdown("### 📌 Navigasi Menu")

menu = st.sidebar.selectbox(
    "Pilih Menu",
    [
        "📦 Produksi & Stok",
        "🛒 Kelola Penjualan",
        "💸 Kelola Pengeluaran",
        "📈 Dashboard Utama",
        "📊 Rekap Harian, Bulanan, Tahunan",
        "🏪 Kelola Master Toko",
    ],
)


def fetch_data(table_name):
  try:
    response = supabase.table(table_name).select("*").execute()
    return response.data
  except Exception as e:
    st.error(f"Gagal memuat data dari {table_name}: {e}")
    return []


# Pilihan Varian Produk
LIST_PRODUK = ["Coklat", "Matcha"]

# -----------------------------------------------------------------------------
# MENU 1: PRODUKSI & STOK
# -----------------------------------------------------------------------------
if menu == "📦 Produksi & Stok":
  st.markdown("### 📦 Kelola Produksi & Stok Gudang")

  produksi_list = fetch_data("tabel_produksi")
  penjualan_list = fetch_data("tabel_penjualan")

  total_prod_coklat = sum(
      item.get("jumlah_produksi", 0)
      for item in produksi_list
      if item.get("produk", "Coklat") == "Coklat"
  )
  total_kirim_coklat = sum(
      item.get("dikirim", 0)
      for item in penjualan_list
      if item.get("produk", "Coklat") == "Coklat"
  )
  stok_coklat = total_prod_coklat - total_kirim_coklat

  total_prod_matcha = sum(
      item.get("jumlah_produksi", 0)
      for item in produksi_list
      if item.get("produk") == "Matcha"
  )
  total_kirim_matcha = sum(
      item.get("dikirim", 0)
      for item in penjualan_list
      if item.get("produk") == "Matcha"
  )
  stok_matcha = total_prod_matcha - total_kirim_matcha

  st.markdown("#### 📊 Sisa Stok Gudang per Varian")
  c1, c2 = st.columns(2)
  c1.metric(
      "Stok Coklat",
      f"{stok_coklat:,} pcs",
      f"Prod: {total_prod_coklat} | Terkirim: {total_kirim_coklat}",
  )
  c2.metric(
      "Stok Matcha",
      f"{stok_matcha:,} pcs",
      f"Prod: {total_prod_matcha} | Terkirim: {total_kirim_matcha}",
  )

  st.markdown("---")

  tab1, tab2 = st.tabs(["➕ Tambah Produksi", "📋 Riwayat & Hapus Produksi"])

  with tab1:
    with st.form("form_produksi", clear_on_submit=True):
      tanggal_prod = st.date_input("Tanggal Produksi", datetime.date.today())
      pilih_produk = st.selectbox("Varian Produk", LIST_PRODUK)
      jumlah_prod = st.number_input(
          "Jumlah Produksi (Pcs)", min_value=1, step=1, value=50
      )

      submit_prod = st.form_submit_button("💾 Simpan Data Produksi")

      if submit_prod:
        try:
          data_prod = {
              "tanggal": str(tanggal_prod),
              "produk": pilih_produk,
              "jumlah_produksi": jumlah_prod,
          }
          supabase.table("tabel_produksi").insert(data_prod).execute()
          st.success("✅ Data produksi berhasil disimpan!")
          st.rerun()
        except Exception as e:
          st.error(f"❌ Gagal menyimpan produksi: {e}")

  with tab2:
    if not produksi_list:
      st.info("Belum ada catatan produksi.")
    else:
      st.markdown("#### Daftar Riwayat Produksi")
      df_prod = pd.DataFrame(produksi_list)
      if "keterangan" in df_prod.columns:
        df_prod = df_prod.drop(columns=["keterangan"])
      st.dataframe(df_prod, use_container_width=True)

      st.markdown("---")
      st.markdown("#### Hapus Catatan Produksi")
      opsi_hapus_prod = {
          f"ID {p['id']} | {p.get('tanggal')} | [{p.get('produk', 'Coklat')}] {p.get('jumlah_produksi')} pcs"
          : p["id"]
          for p in produksi_list
      }
      pilih_hapus = st.selectbox(
          "Pilih data produksi yang ingin dihapus", list(opsi_hapus_prod.keys())
      )
      id_dihapus = opsi_hapus_prod[pilih_hapus]

      if st.button("🗑️ Hapus Data Produksi Ini"):
        try:
          supabase.table("tabel_produksi").delete().eq(
              "id", id_dihapus
          ).execute()
          st.success("🗑️ Data produksi berhasil dihapus!")
          st.rerun()
        except Exception as e:
          st.error(f"❌ Gagal menghapus: {e}")

# -----------------------------------------------------------------------------
# MENU 2: KELOLA PENJUALAN
# -----------------------------------------------------------------------------
elif menu == "🛒 Kelola Penjualan":
  st.markdown("### 📝 Kelola Catatan Penjualan")

  tab1, tab2, tab3 = st.tabs(
      ["➕ Tambah Baru", "✏️ Edit / Hapus Data", "📦 Data Penjualan"]
  )

  data_toko = fetch_data("tabel_toko")

  with tab1:
    if not data_toko:
      st.warning(
          "⚠️ Belum ada data toko. Silakan daftarkan toko di menu **🏪 Kelola"
          " Master Toko** terlebih dahulu!"
      )
    else:
      tanggal = st.date_input("Tanggal", datetime.date.today(), key="tgl_jual")
      pilihan_produk_jual = st.selectbox(
          "Pilih Varian Produk", LIST_PRODUK, key="jual_prod"
      )

      toko_filtered = [
          t for t in data_toko if t.get("produk", "Coklat") == pilihan_produk_jual
      ]

      if not toko_filtered:
        st.warning(
            f"⚠️ Belum ada harga terdaftar untuk varian"
            f" **{pilihan_produk_jual}**. Silakan daftarkan di Master Toko."
        )
      else:
        opsi_toko = {t["nama_toko"]: t for t in toko_filtered}
        pilihan_toko_nama = st.selectbox(
            "Pilih Toko", list(opsi_toko.keys()), key="tambah_toko"
        )
        toko_terpilih = opsi_toko[pilihan_toko_nama]

        harga_jual = toko_terpilih.get("harga_jual", 0)
        potongan = toko_terpilih.get("potongan_persen", 0)
        harga_bersih_pcs = harga_jual - (harga_jual * potongan / 100)

        dikirim = st.number_input(
            "Jumlah Dikirim / Laku", min_value=0, step=1, key="tambah_dikirim"
        )

        st.info(
            f"💡 **Varian:** {pilihan_produk_jual} | **Harga Jual:** Rp"
            f" {harga_jual:,.0f} | **Potongan:** {potongan}% \n\n✨ **Harga"
            f" Bersih per Pcs:** Rp {harga_bersih_pcs:,.0f}"
        )

        total_otomatis = dikirim * harga_bersih_pcs
        st.markdown(f"💰 **Total Penjualan:** Rp {total_otomatis:,.0f}")

        if st.button("💾 Simpan Data Penjualan", use_container_width=True):
          try:
            data_baru = {
                "tanggal": str(tanggal),
                "toko": pilihan_toko_nama,
                "produk": pilihan_produk_jual,
                "dikirim": dikirim,
                "total_penjualan": total_otomatis,
            }
            supabase.table("tabel_penjualan").insert(data_baru).execute()
            st.success("✅ Data penjualan berhasil disimpan!")
            st.rerun()
          except Exception as e:
            st.error(f"❌ Gagal menyimpan data: {e}")

  with tab2:
    penjualan_list = fetch_data("tabel_penjualan")
    if not penjualan_list:
      st.info("Belum ada data penjualan untuk diedit atau dihapus.")
    else:
      opsi_penjualan = {
          f"ID {item['id']} | {item['tanggal']} | {item.get('toko')} [{item.get('produk', 'Coklat')}] (Dikirim: {item['dikirim']})"
          : item
          for item in penjualan_list
      }

      pilih_data = st.selectbox(
          "Pilih Data Penjualan yang ingin diubah/dihapus",
          list(opsi_penjualan.keys()),
          key="pilih_data_edit",
      )
      data_terpilih = opsi_penjualan[pilih_data]

      current_id = data_terpilih["id"]
      current_tanggal = datetime.datetime.strptime(
          data_terpilih["tanggal"], "%Y-%m-%d"
      ).date()
      current_toko = data_terpilih["toko"]
      current_produk = data_terpilih.get("produk", "Coklat")
      current_dikirim = data_terpilih["dikirim"]

      st.markdown(f"**Edit Data [ID: {current_id}]**")

      new_tanggal = st.date_input(
          "Tanggal", value=current_tanggal, key=f"edit_tgl_{current_id}"
      )
      new_produk = st.selectbox(
          "Varian Produk",
          LIST_PRODUK,
          index=(
              LIST_PRODUK.index(current_produk)
              if current_produk in LIST_PRODUK
              else 0
          ),
          key=f"edit_prod_{current_id}",
      )

      toko_filtered_edit = [
          t for t in data_toko if t.get("produk", "Coklat") == new_produk
      ]
      list_toko_nama = (
          [t["nama_toko"] for t in toko_filtered_edit]
          if toko_filtered_edit
          else [current_toko]
      )

      default_idx = (
          list_toko_nama.index(current_toko)
          if current_toko in list_toko_nama
          else 0
      )
      new_toko = st.selectbox(
          "Pilih Toko",
          list_toko_nama,
          index=default_idx,
          key=f"edit_toko_{current_id}",
      )

      new_dikirim = st.number_input(
          "Jumlah Dikirim / Laku",
          min_value=0,
          step=1,
          value=int(current_dikirim),
          key=f"edit_dikirim_{current_id}",
      )

      toko_edit_obj = next(
          (
              t
              for t in data_toko
              if t["nama_toko"] == new_toko
              and t.get("produk", "Coklat") == new_produk
          ),
          {"harga_jual": 0, "potongan_persen": 0},
      )
      h_jual = toko_edit_obj.get("harga_jual", 0)
      h_pot = toko_edit_obj.get("potongan_persen", 0)
      h_bersih_pcs = h_jual - (h_jual * h_pot / 100)

      st.info(
          f"💡 **Harga Jual:** Rp {h_jual:,.0f} | **Potongan:** {h_pot}% \n\n✨"
          f" **Harga Bersih per Pcs:** Rp {h_bersih_pcs:,.0f}"
      )

      new_total = new_dikirim * h_bersih_pcs
      st.
