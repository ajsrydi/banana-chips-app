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
      st.markdown(f"💰 **Total Penjualan:** Rp {new_total:,.0f}")

      col_update, col_delete = st.columns(2)
      if col_update.button(
          "🔄 Update Data",
          key=f"btn_update_{current_id}",
          use_container_width=True,
      ):
        try:
          update_payload = {
              "tanggal": str(new_tanggal),
              "toko": new_toko,
              "produk": new_produk,
              "dikirim": new_dikirim,
              "total_penjualan": new_total,
          }
          supabase.table("tabel_penjualan").update(update_payload).eq(
              "id", current_id
          ).execute()
          st.success(f"✅ Data ID {current_id} berhasil diperbarui!")
          st.rerun()
        except Exception as e:
          st.error(f"❌ Gagal memperbarui data: {e}")

      if col_delete.button(
          "🗑️ Hapus Data",
          key=f"btn_delete_{current_id}",
          use_container_width=True,
      ):
        try:
          supabase.table("tabel_penjualan").delete().eq(
              "id", current_id
          ).execute()
          st.success(f"🗑️ Data ID {current_id} berhasil dihapus!")
          st.rerun()
        except Exception as e:
          st.error(f"❌ Gagal menghapus data: {e}")

  with tab3:
    st.markdown("#### 📦 Keseluruhan Data Penjualan")
    penjualan_list = fetch_data("tabel_penjualan")
    if penjualan_list:
      df_penjualan = pd.DataFrame(penjualan_list)
      if "produksi" in df_penjualan.columns:
        df_penjualan = df_penjualan.drop(columns=["produksi"])
      st.dataframe(df_penjualan, use_container_width=True)
    else:
      st.info("Belum ada data penjualan tercatat.")

# -----------------------------------------------------------------------------
# MENU 3: KELOLA PENGELUARAN
# -----------------------------------------------------------------------------
elif menu == "💸 Kelola Pengeluaran":
  st.markdown("### 📝 Kelola Catatan Pengeluaran")

  tab1, tab2, tab3 = st.tabs(
      ["➕ Tambah Baru", "🗑️ Hapus Data", "💸 Data Pengeluaran"]
  )

  with tab1:
    with st.form("form_pengeluaran", clear_on_submit=True):
      tanggal = st.date_input("Tanggal Pengeluaran", datetime.date.today())
      nama_barang = st.text_input(
          "Nama Barang / Bahan",
          placeholder="Contoh: Pisang, Matcha Powder, Minyak",
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

  with tab2:
    pengeluaran_list = fetch_data("tabel_pengeluaran")
    if not pengeluaran_list:
      st.info("Belum ada data pengeluaran untuk dihapus.")
    else:
      opsi_keluar = {
          f"ID {item['id']} | {item['tanggal']} | {item['nama_barang']} (Rp {item['pengeluaran']:,.0f})"
          : item["id"]
          for item in pengeluaran_list
      }
      pilih_hapus_keluar = st.selectbox(
          "Pilih Pengeluaran yang ingin dihapus", list(opsi_keluar.keys())
      )
      id_keluar_dihapus = opsi_keluar[pilih_hapus_keluar]

      if st.button("🗑️ Hapus Pengeluaran Ini"):
        try:
          supabase.table("tabel_pengeluaran").delete().eq(
              "id", id_keluar_dihapus
          ).execute()
          st.success("🗑️ Data pengeluaran berhasil dihapus!")
          st.rerun()
        except Exception as e:
          st.error(f"❌ Gagal menghapus: {e}")

  with tab3:
    st.markdown("#### 💸 Keseluruhan Data Pengeluaran")
    pengeluaran_list = fetch_data("tabel_pengeluaran")
    if pengeluaran_list:
      st.dataframe(pengeluaran_list, use_container_width=True)
    else:
      st.info("Belum ada data pengeluaran tercatat.")

# -----------------------------------------------------------------------------
# MENU 4: DASHBOARD UTAMA
# -----------------------------------------------------------------------------
elif menu == "📈 Dashboard Utama":
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
  col6.metric("Stok Gudang", f"{sisa_stok:,} pcs")

  st.markdown("---")
  st.info(
      "💡 **Catatan:** Rincian data transaksi penjualan dan pengeluaran dapat"
      " dilihat langsung melalui tab di menu **Kelola Penjualan** dan **Kelola"
      " Pengeluaran**."
  )

# -----------------------------------------------------------------------------
# MENU 5: REKAP HARIAN, BULANAN, TAHUNAN
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
    st.markdown("#### Rekap Berdasarkan Tahunan")
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
        df_pengeluaran["tahun"] = (
            pd.to_datetime(df_pengeluaran["tanggal"]).dt.year.astype(str)
        )
        df_exp_tahun = (
            df_pengeluaran.groupby("tahun")["pengeluaran"].sum().reset_index()
        )
      else:
        df_exp_tahun = pd.DataFrame(columns=["tahun", "pengeluaran"])

      df_tahunan = pd.merge(
          df_p_tahun, df_exp_tahun, on="tahun", how="outer"
      ).fillna(0)
      df_tahunan = df_tahunan.sort_values(by="tahun", ascending=False)
      df_tahunan["Profit Bersih"] = (
          df_tahunan["total_penjualan"] - df_tahunan["pengeluaran"]
      )

      st.dataframe(df_tahunan, use_container_width=True)
    else:
      st.info("Belum ada data transaksi untuk rekap tahunan.")

# -----------------------------------------------------------------------------
# MENU 6: KELOLA MASTER TOKO (DENGAN INPUT KENAIKAN HARGA)
# -----------------------------------------------------------------------------
elif menu == "🏪 Kelola Master Toko":
  st.markdown("### 🏪 Master Data Toko & Harga")

  tab1, tab2, tab3 = st.tabs(
      ["➕ Tambah / Edit Toko", "📈 Adjust Kenaikan Harga", "📋 Daftar Toko"]
  )

  list_toko = fetch_data("tabel_toko")

  with tab1:
    with st.form("form_toko", clear_on_submit=True):
      nama_toko = st.text_input(
          "Nama Toko / Reseller", placeholder="Contoh: SBR2, Ajirasa1, AR 3"
      )
      pilih_produk_toko = st.selectbox("Varian Produk", LIST_PRODUK)
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
                "produk": pilih_produk_toko,
                "harga_jual": harga_jual,
                "potongan_persen": potongan_persen,
            }
            supabase.table("tabel_toko").upsert(
                data_toko, on_conflict="nama_toko,produk"
            ).execute()
            st.success(
                f"✅ Data toko '{nama_toko}' untuk produk"
                f" '{pilih_produk_toko}' berhasil disimpan!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"❌ Gagal menyimpan toko: {e}")

  with tab2:
    st.markdown("#### 📈 Penyesuaian Kenaikan Harga")
    if not list_toko:
      st.info("Belum ada data toko terdaftar.")
    else:
      mode_adjust = st.radio(
          "Pilih Skop Kenaikan Harga",
          ["Satu Toko Spesifik", "Massal per Varian Produk"],
      )

      if mode_adjust == "Satu Toko Spesifik":
        opsi_toko_adj = {
            f"{t['nama_toko']} [{t.get('produk', 'Coklat')}] (Harga Lama: Rp {t.get('harga_jual', 0):,.0f})"
            : t
            for t in list_toko
        }
        pilih_toko_adj = st.selectbox(
            "Pilih Toko & Produk", list(opsi_toko_adj.keys())
        )
        obj_toko = opsi_toko_adj[pilih_toko_adj]

        harga_lama = obj_toko.get("harga_jual", 0)
        nominal_kenaikan = st.number_input(
            "Nominal Kenaikan Harga (Rp)",
            min_value=0.0,
            step=500.0,
            value=1000.0,
            format="%.2f",
        )

        harga_baru = harga_lama + nominal_kenaikan
        st.info(
            f"💡 **Harga Lama:** Rp {harga_lama:,.0f} ➡️ **Harga Baru:** Rp"
            f" {harga_baru:,.0f}"
        )

        if st.button("🚀 Terapkan Kenaikan Harga", use_container_width=True):
          try:
            supabase.table("tabel_toko").update(
                {"harga_jual": harga_baru}
            ).eq("id", obj_toko["id"]).execute()
            st.success(
                f"✅ Harga jual {obj_toko['nama_toko']} [{obj_toko.get('produk')}]"
                f" berhasil dinaikkan menjadi Rp {harga_baru:,.0f}!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"❌ Gagal memperbarui harga: {e}")

      else:
        produk_massal = st.selectbox("Pilih Varian Produk", LIST_PRODUK)
        nominal_kenaikan_massal = st.number_input(
            "Nominal Kenaikan Harga untuk Semua Toko (Rp)",
            min_value=0.0,
            step=500.0,
            value=1000.0,
            format="%.2f",
            key="kenaikan_massal",
        )

        toko_produk_terkait = [
            t for t in list_toko if t.get("produk", "Coklat") == produk_massal
        ]
        st.warning(
            f"⚠️ Kenaikan harga Rp {nominal_kenaikan_massal:,.0f} akan"
            f" diterapkan ke **{len(toko_produk_terkait)} toko** untuk varian"
            f" **{produk_massal}**."
        )

        if st.button("🚀 Terapkan Kenaikan Massal", use_container_width=True):
          try:
            for t in toko_produk_terkait:
              h_baru = t.get("harga_jual", 0) + nominal_kenaikan_massal
              supabase.table("tabel_toko").update({"harga_jual": h_baru}).eq(
                  "id", t["id"]
              ).execute()
            st.success(
                f"✅ Kenaikan harga berhasil diterapkan ke semua toko untuk"
                f" varian {produk_massal}!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"❌ Gagal memperbarui harga massal: {e}")

  with tab3:
    st.markdown("#### 📋 Daftar Toko Terdaftar")
    if list_toko:
      df_toko = pd.DataFrame(list_toko)
      df_toko["Harga Bersih per Pcs (Rp)"] = df_toko["harga_jual"] - (
          df_toko["harga_jual"] * df_toko["potongan_persen"] / 100
      )
      st.dataframe(df_toko, use_container_width=True)
    else:
      st.info("Belum ada toko yang didaftarkan.")
