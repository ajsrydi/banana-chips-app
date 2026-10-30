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
        font-size: 1.4rem !important;
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
        "📦 Produksi & Stok",
        "🏪 Kelola Master Toko",
        "➕ Input & Kelola Penjualan",
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

  # Kartu Metrik Keuangan
  col1, col2, col3 = st.columns(3)
  col1.metric("Total Omset", f"Rp {total_omset:,.0f}")
  col2.metric("Total Biaya", f"Rp {total_biaya:,.0f}")
  col3.metric("Estimasi Profit", f"Rp {total_profit:,.0f}")

  # Kartu Metrik Stok
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
# MENU 2: PRODUKSI & STOK (BARU)
# -----------------------------------------------------------------------------
elif menu == "📦 Produksi & Stok":
  st.markdown("### 📦 Kelola Produksi & Stok Gudang")

  produksi_list = fetch_data("tabel_produksi")
  penjualan_list = fetch_data("tabel_penjualan")

  total_prod = sum(item.get("jumlah_produksi", 0) for item in produksi_list)
  total_terkirim = sum(item.get("dikirim", 0) for item in penjualan_list)
  stok_gudang = total_prod - total_terkirim

  # Ringkasan Stok
  c1, c2, c3 = st.columns(3)
  c1.metric("Akumulasi Produksi", f"{total_prod:,} pcs")
  c2.metric("Total Terkirim/Laku", f"{total_terkirim:,} pcs")
  c3.metric("Stok Tersedia", f"{stok_gudang:,} pcs")

  st.markdown("---")

  tab1, tab2 = st.tabs(["➕ Tambah Produksi", "📋 Riwayat & Hapus Produksi"])

  with tab1:
    with st.form("form_produksi", clear_on_submit=True):
      tanggal_prod = st.date_input("Tanggal Produksi", datetime.date.today())
      jumlah_prod = st.number_input(
          "Jumlah Produksi (Pcs)", min_value=1, step=1, value=50
      )
      keterangan = st.text_input(
          "Keterangan / Batch", placeholder="Contoh: Batch 1, Pisang Kepok"
      )

      submit_prod = st.form_submit_button("💾 Simpan Data Produksi")

      if submit_prod:
        try:
          data_prod = {
              "tanggal": str(tanggal_prod),
              "jumlah_produksi": jumlah_prod,
              "keterangan": keterangan,
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
      st.dataframe(df_prod, use_container_width=True)

      st.markdown("---")
      st.markdown("#### Hapus Catatan Produksi")
      opsi_hapus_prod = {
          f"ID {p['id']} | {p['tanggal']} | {p['jumlah_produksi']} pcs ({p['keterangan']})"
          : p['id']
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
# MENU 3: KELOLA MASTER TOKO
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
    df_toko = pd.DataFrame(list_toko)
    df_toko["Harga Bersih per Pcs (Rp)"] = df_toko["harga_jual"] - (
        df_toko["harga_jual"] * df_toko["potongan_persen"] / 100
    )
    st.dataframe(df_toko, use_container_width=True)
  else:
    st.info("Belum ada toko yang didaftarkan.")

# -----------------------------------------------------------------------------
# MENU 4: INPUT & KELOLA PENJUALAN
# -----------------------------------------------------------------------------
elif menu == "➕ Input & Kelola Penjualan":
  st.markdown("### 📝 Kelola Catatan Penjualan")

  tab1, tab2 = st.tabs(["➕ Tambah Baru", "✏️ Edit / Hapus Data"])

  data_toko = fetch_data("tabel_toko")
  opsi_toko = {t["nama_toko"]: t for t in data_toko} if data_toko else {}

  with tab1:
    if not data_toko:
      st.warning(
          "⚠️ Belum ada data toko. Silakan daftarkan toko di menu **🏪 Kelola"
          " Master Toko** terlebih dahulu!"
      )
    else:
      pilihan_toko_nama = st.selectbox(
          "Pilih Toko", list(opsi_toko.keys()), key="tambah_toko"
      )
      toko_terpilih = opsi_toko[pilihan_toko_nama]

      harga_jual = toko_terpilih.get("harga_jual", 0)
      potongan = toko_terpilih.get("potongan_persen", 0)
      harga_bersih_pcs = harga_jual - (harga_jual * potongan / 100)

      st.info(
          f"💡 **Harga Jual:** Rp {harga_jual:,.0f} | **Potongan:**"
          f" {potongan}% \n\n✨ **Harga Bersih per Pcs:** Rp"
          f" {harga_bersih_pcs:,.0f}"
      )

      with st.form("form_penjualan_baru", clear_on_submit=True):
        tanggal = st.date_input("Tanggal", datetime.date.today())
        dikirim = st.number_input(
            "Jumlah Dikirim / Laku", min_value=0, step=1, key="tambah_dikirim"
        )

        total_otomatis = dikirim * harga_bersih_pcs
        st.markdown(
            f"💰 **Total Penjualan Bersih (Otomatis):** Rp"
            f" {total_otomatis:,.0f}"
        )

        submit_penjualan = st.form_submit_button("💾 Simpan Data Penjualan")

        if submit_penjualan:
          try:
            data_baru = {
                "tanggal": str(tanggal),
                "toko": pilihan_toko_nama,
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
          f"ID {item['id']} | {item['tanggal']} | {item['toko']} (Dikirim: {item['dikirim']})"
          : item
          for item in penjualan_list
      }

      pilih_data = st.selectbox(
          "Pilih Data Penjualan yang ingin diubah/dihapus",
          list(opsi_penjualan.keys()),
      )
      data_terpilih = opsi_penjualan[pilih_data]

      current_id = data_terpilih["id"]
      current_tanggal = datetime.datetime.strptime(
          data_terpilih["tanggal"], "%Y-%m-%d"
      ).date()
      current_toko = data_terpilih["toko"]
      current_dikirim = data_terpilih["dikirim"]

      with st.form("form_edit_penjualan"):
        st.markdown(f"**Edit Data [ID: {current_id}]**")

        new_tanggal = st.date_input("Tanggal", value=current_tanggal)

        list_toko_nama = list(opsi_toko.keys()) if opsi_toko else [current_toko]
        default_idx = (
            list_toko_nama.index(current_toko)
            if current_toko in list_toko_nama
            else 0
        )
        new_toko = st.selectbox(
            "Pilih Toko", list_toko_nama, index=default_idx
        )

        new_dikirim = st.number_input(
            "Jumlah Dikirim / Laku",
            min_value=0,
            step=1,
            value=int(current_dikirim),
        )

        toko_edit_obj = opsi_toko.get(new_toko, {"harga_jual": 0, "potongan_persen": 0})
        h_jual = toko_edit_obj.get("harga_jual", 0)
        h_pot = toko_edit_obj.get("potongan_persen", 0)
        h_bersih_pcs = h_jual - (h_jual * h_pot / 100)

        new_total = new_dikirim * h_bersih_pcs
        st.markdown(
            f"💰 **Total Penjualan Bersih Baru (Otomatis):** Rp"
            f" {new_total:,.0f}"
        )

        col_update, col_delete = st.columns(2)
        update_btn = col_update.form_submit_button("🔄 Update Data")
        delete_btn = col_delete.form_submit_button("🗑️ Hapus Data")

        if update_btn:
          try:
            update_payload = {
                "tanggal": str(new_tanggal),
                "toko": new_toko,
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

        if delete_btn:
          try:
            supabase.table("tabel_penjualan").delete().eq(
                "id", current_id
            ).execute()
            st.success(f"🗑️ Data ID {current_id} berhasil dihapus!")
            st.rerun()
          except Exception as e:
            st.error(f"❌ Gagal menghapus data: {e}")

# -----------------------------------------------------------------------------
# MENU 5: INPUT PENGELUARAN
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
