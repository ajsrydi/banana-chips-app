import datetime
import io
import pandas as pd
import plotly.express as px
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

# Header Utama (Subheader telah dihapus)
st.title("🍌 Wanna Be With U")

# -----------------------------------------------------------------------------
# NAVIGASI SIDEBAR (HOME DI POSISI PALING ATAS)
# -----------------------------------------------------------------------------
st.sidebar.markdown("### 📌 Navigasi Menu")

menu = st.sidebar.selectbox(
    "Pilih Menu",
    [
        "🏠 Home",
        "📦 Produksi & Stok",
        "🛒 Kelola Penjualan",
        "💸 Kelola Pengeluaran",
        "📊 Rekap Laporan & Stok",
        "📈 Pantau Harga Bahan",
        "📥 Download Rekap Excel",
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

# Daftar Pilihan Barang / Bahan Pengeluaran
LIST_BARANG_PENGELUARAN = [
    "keripik pisang",
    "kemasan coklat",
    "kemasan matcha",
    "coklat",
    "matcha",
    "perisa matcha",
    "minyak",
    "keresek",
    "keripik singkong",
    "bawang putih",
    "bawang merah",
    "cabai kering",
    "cabai rawit",
    "gula",
    "garam",
    "jeruk",
    "daun jeruk",
    "buruh",
    "ongkos",
    "amplop",
]

# -----------------------------------------------------------------------------
# MENU 1: HOME (EKS DASHBOARD UTAMA)
# -----------------------------------------------------------------------------
if menu == "🏠 Home":
  st.markdown("### 📈 Ringkasan Keuangan & Stok")

  penjualan = fetch_data("tabel_penjualan")
  pengeluaran = fetch_data("tabel_pengeluaran")
  produksi = fetch_data("tabel_produksi")

  total_omset = sum(item.get("total_penjualan", 0) for item in penjualan)
  parse_piutang = sum(
      item.get("total_penjualan", 0)
      for item in penjualan
      if "Belum" in str(item.get("status", ""))
  )
  total_biaya = sum(item.get("pengeluaran", 0) for item in pengeluaran)
  
  bulan_ini = str(datetime.date.today())[:7]
  biaya_bulan_ini = sum(
      item.get("pengeluaran", 0)
      for item in pengeluaran
      if str(item.get("tanggal", "")).startswith(bulan_ini)
  )

  total_profit = total_omset - total_biaya

  total_prod_coklat = sum(
      item.get("jumlah_produksi", 0)
      for item in produksi
      if item.get("produk", "Coklat") == "Coklat"
  )
  total_kirim_coklat = sum(
      item.get("dikirim", 0)
      for item in penjualan
      if item.get("produk", "Coklat") == "Coklat"
  )
  stok_coklat = total_prod_coklat - total_kirim_coklat

  total_prod_matcha = sum(
      item.get("jumlah_produksi", 0)
      for item in produksi
      if item.get("produk") == "Matcha"
  )
  total_kirim_matcha = sum(
      item.get("dikirim", 0)
      for item in penjualan
      if item.get("produk") == "Matcha"
  )
  stok_matcha = total_prod_matcha - total_kirim_matcha

  if stok_coklat < 20 or stok_matcha < 20:
    st.warning(
        f"⚠️ **Peringatan Stok Menipis!** Stok Coklat: **{stok_coklat} pcs** | Stok Matcha: **{stok_matcha} pcs**. Segera jadwalkan produksi!"
    )

  col1, col2, col3 = st.columns(3)
  col1.metric("Total Omset", f"Rp {total_omset:,.0f}")
  col2.metric("Total Piutang (Kontrabon)", f"Rp {parse_piutang:,.0f}")
  col3.metric("Estimasi Profit Bersih", f"Rp {total_profit:,.0f}")

  col4, col5, col6 = st.columns(3)
  col4.metric("Pengeluaran Bulan Ini", f"Rp {biaya_bulan_ini:,.0f}")
  col5.metric("Stok Gudang Coklat", f"{stok_coklat:,} pcs")
  col6.metric("Stok Gudang Matcha", f"{stok_matcha:,} pcs")

  st.markdown("---")

  st.markdown("#### 📊 Grafik Kinerja Keuangan Bulanan")
  
  df_p = pd.DataFrame(penjualan) if penjualan else pd.DataFrame()
  df_e = pd.DataFrame(pengeluaran) if pengeluaran else pd.DataFrame()

  if not df_p.empty or not df_e.empty:
    if not df_p.empty:
      df_p["bulan"] = pd.to_datetime(df_p["tanggal"]).dt.to_period("M").astype(str)
      df_p_bulan = df_p.groupby("bulan")["total_penjualan"].sum().reset_index()
    else:
      df_p_bulan = pd.DataFrame(columns=["bulan", "total_penjualan"])

    if not df_e.empty:
      df_e["bulan"] = pd.to_datetime(df_e["tanggal"]).dt.to_period("M").astype(str)
      df_exp_bulan = df_e.groupby("bulan")["pengeluaran"].sum().reset_index()
    else:
      df_exp_bulan = pd.DataFrame(columns=["bulan", "pengeluaran"])

    df_chart_bulanan = pd.merge(df_p_bulan, df_exp_bulan, on="bulan", how="outer").fillna(0)
    df_chart_bulanan = df_chart_bulanan.sort_values("bulan")
    df_chart_bulanan["Profit Bersih"] = (
        df_chart_bulanan["total_penjualan"] - df_chart_bulanan["pengeluaran"]
    )

    df_chart_melted = df_chart_bulanan.rename(columns={
        "bulan": "Bulan",
        "total_penjualan": "Pemasukan",
        "pengeluaran": "Pengeluaran",
        "Profit Bersih": "Profit Bersih"
    }).melt(id_vars=["Bulan"], value_vars=["Pemasukan", "Pengeluaran", "Profit Bersih"], var_name="Kategori", value_name="Jumlah (Rp)")

    fig = px.line(
        df_chart_melted,
        x="Bulan",
        y="Jumlah (Rp)",
        color="Kategori",
        markers=True,
        labels={"Bulan": "Bulan", "Jumlah (Rp)": "Nominal (Rp)"},
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="",
        yaxis_title="Nominal (Rp)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
  else:
    st.info("Belum ada data transaksi untuk ditampilkan pada grafik bulanan.")

# -----------------------------------------------------------------------------
# MENU 2: PRODUKSI & STOK
# -----------------------------------------------------------------------------
elif menu == "📦 Produksi & Stok":
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
# MENU 3: KELOLA PENJUALAN
# -----------------------------------------------------------------------------
elif menu == "🛒 Kelola Penjualan":
  st.markdown("#### 🚨 Rekap Toko Belum Lunas (Kontrabon Aktif)")
  penjualan_all = fetch_data("tabel_penjualan")
  piutang_all = [
      item
      for item in penjualan_all
      if "Belum" in str(item.get("status", ""))
  ]

  if piutang_all:
    for item in piutang_all:
      tgl_trx = item.get("tanggal", "-")
      nm_toko = item.get("toko", "-")
      prd_toko = item.get("produk", "Coklat")
      jml_kirim = item.get("dikirim", 0)
      tot_rp = item.get("total_penjualan", 0)
      st.warning(
          f"📅 `{tgl_trx}` | 🏪 **{nm_toko}** [{prd_toko}] ➡️ **{jml_kirim:,}"
          f" pcs** (Rp {tot_rp:,.0f})"
      )
  else:
    st.success("🎉 Mantap! Semua toko sudah lunas (tidak ada kontrabon aktif).")

  st.markdown("---")

  st.markdown("### 📝 Kelola Catatan Penjualan & Kontrabon")

  tab1, tab2, tab3 = st.tabs(
      ["➕ Tambah Baru", "✏️ Edit / Pelunasan", "📦 Data Penjualan"]
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

        status_bayar = st.selectbox(
            "Status Pembayaran", ["Belum Lunas (Kontrabon)", "Lunas"], key="tambah_status"
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
                "status": status_bayar,
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
      st.info("Belum ada data penjualan untuk diedit atau dilunasi.")
    else:
      daftar_bulan = sorted(
          list(
              set(
                  str(item["tanggal"])[:7]
                  for item in penjualan_list
                  if "tanggal" in item
              )
          ),
          reverse=True,
      )

      if not daftar_bulan:
        st.info("Belum ada data bulan transaksi.")
      else:
        pilih_bulan = st.selectbox(
            "📅 Pilih Bulan Transaksi", daftar_bulan, key="filter_bulan_edit"
        )

        penjualan_filtered_bulan = [
            item
            for item in penjualan_list
            if str(item["tanggal"]).startswith(pilih_bulan)
        ]

        if not penjualan_filtered_bulan:
          st.info(f"Tidak ada data penjualan pada bulan {pilih_bulan}.")
        else:
          opsi_penjualan = {
              f"ID {item['id']} | {item['tanggal']} | {item.get('toko')} [{item.get('produk', 'Coklat')}] - Status: {item.get('status', 'Belum Lunas (Kontrabon)')}"
              : item
              for item in penjualan_filtered_bulan
          }

          pilih_data = st.selectbox(
              "Pilih Data Penjualan yang ingin diubah / dilunasi",
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
          current_status = data_terpilih.get("status", "Belum Lunas (Kontrabon)")

          st.markdown(f"**Edit / Pelunasan Data [ID: {current_id}]**")

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

          idx_status = (
              ["Belum Lunas (Kontrabon)", "Lunas"].index(current_status)
              if current_status in ["Belum Lunas (Kontrabon)", "Lunas"]
              else 0
          )
          new_status = st.selectbox(
              "Status Pembayaran",
              ["Belum Lunas (Kontrabon)", "Lunas"],
              index=idx_status,
              key=f"edit_status_{current_id}",
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
              "🔄 Update / Lunasi Data",
              key=f"btn_update_{current_id}",
              use_container_width=True,
          ):
            try:
              update_payload = {
                  "tanggal": str(new_tanggal),
                  "toko": new_toko,
                  "produk": new_produk,
                  "dikirim": new_dikirim,
                  "status": new_status,
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
    st.markdown("#### 📦 Keseluruhan Data Penjualan & Kontrabon")
    penjualan_list = fetch_data("tabel_penjualan")
    if penjualan_list:
      df_penjualan = pd.DataFrame(penjualan_list)
      if "produksi" in df_penjualan.columns:
        df_penjualan = df_penjualan.drop(columns=["produksi"])
      
      def highlight_status(row):
        status = row.get("status", "Belum Lunas (Kontrabon)")
        if "Belum" in str(status):
          return ["background-color: rgba(255, 75, 75, 0.15)"] * len(row)
        return [""] * len(row)

      st.dataframe(
          df_penjualan.style.apply(highlight_status, axis=1),
          use_container_width=True,
      )
    else:
      st.info("Belum ada data penjualan tercatat.")

# -----------------------------------------------------------------------------
# MENU 4: KELOLA PENGELUARAN
# -----------------------------------------------------------------------------
elif menu == "💸 Kelola Pengeluaran":
  st.markdown("### 📝 Kelola Catatan Pengeluaran")

  tab1, tab2, tab3 = st.tabs(
      ["➕ Tambah Baru", "✏️ Edit & Hapus", "💸 Data Pengeluaran"]
  )

  with tab1:
    with st.form("form_pengeluaran", clear_on_submit=True):
      tanggal = st.date_input("Tanggal Pengeluaran", datetime.date.today())
      nama_barang = st.selectbox("Nama Barang / Bahan", LIST_BARANG_PENGELUARAN)
      pengeluaran = st.number_input(
          "Total Biaya Pengeluaran (Rp)", min_value=0.0, step=1000.0, format="%.2f"
      )
      qty = st.number_input("Banyak Barang", min_value=0.0, step=0.5)

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
      st.info("Belum ada data pengeluaran untuk diedit atau dihapus.")
    else:
      daftar_bulan_keluar = sorted(
          list(
              set(
                  str(item["tanggal"])[:7]
                  for item in pengeluaran_list
                  if "tanggal" in item
              )
          ),
          reverse=True,
      )

      if not daftar_bulan_keluar:
        st.info("Belum ada data bulan pengeluaran.")
      else:
        pilih_bulan_keluar = st.selectbox(
            "📅 Pilih Bulan Pengeluaran", daftar_bulan_keluar, key="filter_bulan_edit_keluar"
        )

        pengeluaran_filtered_bulan = [
            item
            for item in pengeluaran_list
            if str(item["tanggal"]).startswith(pilih_bulan_keluar)
        ]

        if not pengeluaran_filtered_bulan:
          st.info(f"Tidak ada data pengeluaran pada bulan {pilih_bulan_keluar}.")
        else:
          opsi_keluar_edit = {
              f"ID {item['id']} | {item['tanggal']} | {item['nama_barang']} (Rp {item.get('pengeluaran', 0):,.0f})"
              : item
              for item in pengeluaran_filtered_bulan
          }

          pilih_data_keluar = st.selectbox(
              "Pilih Data Pengeluaran yang ingin diubah atau dihapus",
              list(opsi_keluar_edit.keys()),
              key="pilih_data_edit_keluar",
          )
          data_terpilih_keluar = opsi_keluar_edit[pilih_data_keluar]

          curr_id_k = data_terpilih_keluar["id"]
          curr_tgl_k = datetime.datetime.strptime(
              data_terpilih_keluar["tanggal"], "%Y-%m-%d"
          ).date()
          curr_barang_k = data_terpilih_keluar.get("nama_barang", LIST_BARANG_PENGELUARAN[0])
          curr_biaya_k = data_terpilih_keluar.get("pengeluaran", 0.0)
          curr_qty_k = data_terpilih_keluar.get("qty", 0.0)

          st.markdown(f"**Edit / Hapus Data Pengeluaran [ID: {curr_id_k}]**")

          new_tgl_k = st.date_input(
              "Tanggal Pengeluaran", value=curr_tgl_k, key=f"edit_tgl_k_{curr_id_k}"
          )
          
          idx_barang = (
              LIST_BARANG_PENGELUARAN.index(curr_barang_k)
              if curr_barang_k in LIST_BARANG_PENGELUARAN
              else 0
          )
          new_barang_k = st.selectbox(
              "Nama Barang / Bahan",
              LIST_BARANG_PENGELUARAN,
              index=idx_barang,
              key=f"edit_barang_k_{curr_id_k}",
          )

          new_biaya_k = st.number_input(
              "Total Biaya Pengeluaran (Rp)",
              min_value=0.0,
              step=1000.0,
              value=float(curr_biaya_k),
              format="%.2f",
              key=f"edit_biaya_k_{curr_id_k}",
          )
          
          new_qty_k = st.number_input(
              "Banyak Barang",
              min_value=0.0,
              step=0.5,
              value=float(curr_qty_k),
              key=f"edit_qty_k_{curr_id_k}",
          )

          col_update_k, col_delete_k = st.columns(2)
          if col_update_k.button(
              "🔄 Update Data",
              key=f"btn_update_k_{curr_id_k}",
              use_container_width=True,
          ):
            try:
              update_payload_k = {
                  "tanggal": str(new_tgl_k),
                  "nama_barang": new_barang_k,
                  "pengeluaran": new_biaya_k,
                  "qty": new_qty_k,
              }
              supabase.table("tabel_pengeluaran").update(update_payload_k).eq(
                  "id", curr_id_k
              ).execute()
              st.success(f"✅ Data Pengeluaran ID {curr_id_k} berhasil diperbarui!")
              st.rerun()
            except Exception as e:
              st.error(f"❌ Gagal memperbarui data: {e}")

          if col_delete_k.button(
              "🗑️ Hapus Data",
              key=f"btn_delete_k_{curr_id_k}",
              use_container_width=True,
          ):
            try:
              supabase.table("tabel_pengeluaran").delete().eq(
                  "id", curr_id_k
              ).execute()
              st.success(f"🗑️ Data Pengeluaran ID {curr_id_k} berhasil dihapus!")
              st.rerun()
            except Exception as e:
              st.error(f"❌ Gagal menghapus data: {e}")

  with tab3:
    st.markdown("#### 💸 Keseluruhan Data Pengeluaran")
    pengeluaran_list = fetch_data("tabel_pengeluaran")
    if pengeluaran_list:
      st.dataframe(pengeluaran_list, use_container_width=True)
    else:
      st.info("Belum ada data pengeluaran tercatat.")

# -----------------------------------------------------------------------------
# MENU 5: REKAP LAPORAN & STOK
# -----------------------------------------------------------------------------
elif menu == "📊 Rekap Laporan & Stok":
  st.markdown("### 📊 Rekap Laporan, Stok & Keuangan")

  penjualan = fetch_data("tabel_penjualan")
  produksi = fetch_data("tabel_produksi")
  pengeluaran = fetch_data("tabel_pengeluaran")

  tab_stok, tab_keuangan = st.tabs(
      ["📦 Tabel Stok & Penjualan Toko", "💰 Tabel Keuangan"]
  )

  with tab_stok:
    st.markdown("#### 📦 Rekap Stok, Terbuang & Penjualan per Toko (Bulanan)")
    
    months = set()
    if penjualan:
      for item in penjualan:
        if "tanggal" in item and item["tanggal"]:
          months.add(str(item["tanggal"])[:7])
    if produksi:
      for item in produksi:
        if "tanggal" in item and item["tanggal"]:
          months.add(str(item["tanggal"])[:7])
    
    months = sorted(list(months), reverse=True)

    if months:
      rekap_stok_data = []
      for m in months:
        prod_m = sum(
            item.get("jumlah_produksi", 0)
            for item in produksi
            if str(item.get("tanggal", "")).startswith(m)
        )
        terbuang_m = sum(
            item.get("sisa", 0)
            for item in penjualan
            if str(item.get("tanggal", "")).startswith(m)
        )
        sbr2_m = sum(
            item.get("dikirim", 0)
            for item in penjualan
            if str(item.get("tanggal", "")).startswith(m) and str(item.get("toko", "")).strip().lower() == "sbr2"
        )
        ajirasa3_m = sum(
            item.get("dikirim", 0)
            for item in penjualan
            if str(item.get("tanggal", "")).startswith(m) and str(item.get("toko", "")).strip().lower() == "ajirasa3"
        )
        ajirasa2_m = sum(
            item.get("dikirim", 0)
            for item in penjualan
            if str(item.get("tanggal", "")).startswith(m) and str(item.get("toko", "")).strip().lower() == "ajirasa2"
        )
        ajirasa1_m = sum(
            item.get("dikirim", 0)
            for item in penjualan
            if str(item.get("tanggal", "")).startswith(m) and str(item.get("toko", "")).strip().lower() == "ajirasa1"
        )
        reseller_m = sum(
            item.get("dikirim", 0)
            for item in penjualan
            if str(item.get("tanggal", "")).startswith(m) and ("reseller" in str(item.get("toko", "")).strip().lower() or str(item.get("toko", "")).strip().lower() not in ["sbr2", "ajirasa3", "ajirasa2", "ajirasa1"])
        )

        rekap_stok_data.append({
            "Bulan": m,
            "Produksi": prod_m,
            "Terbuang": terbuang_m,
            "SBR2": sbr2_m,
            "Ajirasa3": ajirasa3_m,
            "Ajirasa2": ajirasa2_m,
            "Ajirasa1": ajirasa1_m,
            "Reseller": reseller_m,
        })
      
      df_stok_rekap = pd.DataFrame(rekap_stok_data)
      st.dataframe(df_stok_rekap, use_container_width=True)
    else:
      st.info("Belum ada data produksi atau penjualan untuk rekap stok.")

  with tab_keuangan:
    st.markdown("#### 💰 Rekap Keuangan (Omset, Pengeluaran & Profit)")
    df_p = pd.DataFrame(penjualan) if penjualan else pd.DataFrame()
    df_e = pd.DataFrame(pengeluaran) if pengeluaran else pd.DataFrame()

    if not df_p.empty or not df_e.empty:
      if not df_p.empty:
        df_p["bulan"] = pd.to_datetime(df_p["tanggal"]).dt.to_period("M").astype(str)
        df_p_bulan = df_p.groupby("bulan")["total_penjualan"].sum().reset_index()
      else:
        df_p_bulan = pd.DataFrame(columns=["bulan", "total_penjualan"])

      if not df_e.empty:
        df_e["bulan"] = pd.to_datetime(df_e["tanggal"]).dt.to_period("M").astype(str)
        df_exp_bulan = df_e.groupby("bulan")["pengeluaran"].sum().reset_index()
      else:
        df_exp_bulan = pd.DataFrame(columns=["bulan", "pengeluaran"])

      df_keuangan = pd.merge(df_p_bulan, df_exp_bulan, on="bulan", how="outer").fillna(0)
      df_keuangan = df_keuangan.sort_values(by="bulan", ascending=False)
      df_keuangan["profit_bersih"] = df_keuangan["total_penjualan"] - df_keuangan["pengeluaran"]

      df_keuangan = df_keuangan.rename(columns={
          "bulan": "Bulan",
          "total_penjualan": "Total Omset (Rp)",
          "pengeluaran": "Total Pengeluaran (Rp)",
          "profit_bersih": "Profit Bersih (Rp)"
      })

      st.dataframe(
          df_keuangan.style.format({
              "Total Omset (Rp)": "Rp {:,.0f}",
              "Total Pengeluaran (Rp)": "Rp {:,.0f}",
              "Profit Bersih (Rp)": "Rp {:,.0f}"
          }),
          use_container_width=True,
      )
    else:
      st.info("Belum ada data keuangan tercatat.")

# -----------------------------------------------------------------------------
# MENU 6: PANTAU HARGA BAHAN (MATRIKS SEDERHANA)
# -----------------------------------------------------------------------------
elif menu == "📈 Pantau Harga Bahan":
  st.markdown("### 📈 Perkembangan Harga Satuan")
  st.markdown("Memantau pergerakan harga satuan bahan dan pengeluaran dari waktu ke waktu.")

  pengeluaran_list = fetch_data("tabel_pengeluaran")

  if not pengeluaran_list:
    st.info("Belum ada data pengeluaran yang tercatat.")
  else:
    df_bahan = pd.DataFrame(pengeluaran_list)
    
    if "nama_barang" in df_bahan.columns and "pengeluaran" in df_bahan.columns and "qty" in df_bahan.columns and "tanggal" in df_bahan.columns:
      df_bahan["qty"] = pd.to_numeric(df_bahan["qty"], errors="coerce").fillna(0)
      df_bahan["pengeluaran"] = pd.to_numeric(df_bahan["pengeluaran"], errors="coerce").fillna(0)
      
      df_bahan["harga_satuan"] = df_bahan.apply(
          lambda row: row["pengeluaran"] / row["qty"] if row["qty"] > 0 else row["pengeluaran"], axis=1
      )
      
      df_pivot = df_bahan.pivot_table(
          index="tanggal",
          columns="nama_barang",
          values="harga_satuan",
          aggfunc="mean"
      ).reset_index()

      df_pivot = df_pivot.sort_values("tanggal", ascending=False)
      df_pivot["tanggal"] = pd.to_datetime(df_pivot["tanggal"]).dt.strftime("%d %B %Y")
      df_pivot = df_pivot.rename(columns={"tanggal": "tanggal"})

      df_display = df_pivot.copy()
      for col in df_display.columns:
        if col != "tanggal":
          df_display[col] = df_display[col].apply(lambda x: f"Rp {x:,.0f}" if pd.notnull(x) and x > 0 else "")

      st.dataframe(df_display, use_container_width=True)
    else:
      st.error("Struktur data pengeluaran tidak sesuai.")

# -----------------------------------------------------------------------------
# MENU 7: DOWNLOAD REKAP EXCEL (BARU)
# -----------------------------------------------------------------------------
elif menu == "📥 Download Rekap Excel":
  st.markdown("### 📥 Download Rekap Excel")
  st.markdown("Unduh laporan lengkap dalam format Excel yang rapi dengan pembagian 3 sheet: **Stok & Penjualan**, **Keuangan**, dan **Harga Bahan**.")

  if st.button("📥 Unduh File Excel Sekarang", use_container_width=True):
    penjualan = fetch_data("tabel_penjualan")
    produksi = fetch_data("tabel_produksi")
    pengeluaran = fetch_data("tabel_pengeluaran")

    # Siapkan Data Sheet 1: Stok & Penjualan Bulanan
    months = set()
    if penjualan:
      for item in penjualan:
        if "tanggal" in item and item["tanggal"]:
          months.add(str(item["tanggal"])[:7])
    if produksi:
      for item in produksi:
        if "tanggal" in item and item["tanggal"]:
          months.add(str(item["tanggal"])[:7])
    months = sorted(list(months), reverse=True)

    rekap_stok_data = []
    for m in months:
      prod_m = sum(item.get("jumlah_produksi", 0) for item in produksi if str(item.get("tanggal", "")).startswith(m))
      terbuang_m = sum(item.get("sisa", 0) for item in penjualan if str(item.get("tanggal", "")).startswith(m))
      sbr2_m = sum(item.get("dikirim", 0) for item in penjualan if str(item.get("tanggal", "")).startswith(m) and str(item.get("toko", "")).strip().lower() == "sbr2")
      ajirasa3_m = sum(item.get("dikirim", 0) for item in penjualan if str(item.get("tanggal", "")).startswith(m) and str(item.get("toko", "")).strip().lower() == "ajirasa3")
      ajirasa2_m = sum(item.get("dikirim", 0) for item in penjualan if str(item.get("tanggal", "")).startswith(m) and str(item.get("toko", "")).strip().lower() == "ajirasa2")
      ajirasa1_m = sum(item.get("dikirim", 0) for item in penjualan if str(item.get("tanggal", "")).startswith(m) and str(item.get("toko", "")).strip().lower() == "ajirasa1")
      reseller_m = sum(item.get("dikirim", 0) for item in penjualan if str(item.get("tanggal", "")).startswith(m) and ("reseller" in str(item.get("toko", "")).strip().lower() or str(item.get("toko", "")).strip().lower() not in ["sbr2", "ajirasa3", "ajirasa2", "ajirasa1"]))

      rekap_stok_data.append({
          "Bulan": m,
          "Produksi": prod_m,
          "Terbuang": terbuang_m,
          "SBR2": sbr2_m,
          "Ajirasa3": ajirasa3_m,
          "Ajirasa2": ajirasa2_m,
          "Ajirasa1": ajirasa1_m,
          "Reseller": reseller_m,
      })
    df_sheet1 = pd.DataFrame(rekap_stok_data) if rekap_stok_data else pd.DataFrame(columns=["Bulan", "Produksi", "Terbuang", "SBR2", "Ajirasa3", "Ajirasa2", "Ajirasa1", "Reseller"])

    # Siapkan Data Sheet 2: Keuangan
    df_p = pd.DataFrame(penjualan) if penjualan else pd.DataFrame()
    df_e = pd.DataFrame(pengeluaran) if pengeluaran else pd.DataFrame()
    if not df_p.empty:
      df_p["bulan"] = pd.to_datetime(df_p["tanggal"]).dt.to_period("M").astype(str)
      df_p_b = df_p.groupby("bulan")["total_penjualan"].sum().reset_index()
    else:
      df_p_b = pd.DataFrame(columns=["bulan", "total_penjualan"])

    if not df_e.empty:
      df_e["bulan"] = pd.to_datetime(df_e["tanggal"]).dt.to_period("M").astype(str)
      df_e_b = df_e.groupby("bulan")["pengeluaran"].sum().reset_index()
    else:
      df_e_b = pd.DataFrame(columns=["bulan", "pengeluaran"])

    df_sheet2 = pd.merge(df_p_b, df_e_b, on="bulan", how="outer").fillna(0)
    df_sheet2 = df_sheet2.sort_values(by="bulan", ascending=False)
    df_sheet2["profit_bersih"] = df_sheet2["total_penjualan"] - df_sheet2["pengeluaran"]
    df_sheet2 = df_sheet2.rename(columns={
        "bulan": "Bulan",
        "total_penjualan": "Total Omset (Rp)",
        "pengeluaran": "Total Pengeluaran (Rp)",
        "profit_bersih": "Profit Bersih (Rp)"
    })

    # Siapkan Data Sheet 3: Harga Bahan
    if pengeluaran:
      df_b = pd.DataFrame(pengeluaran)
      df_b["qty"] = pd.to_numeric(df_b["qty"], errors="coerce").fillna(0)
      df_b["pengeluaran"] = pd.to_numeric(df_b["pengeluaran"], errors="coerce").fillna(0)
      df_b["harga_satuan"] = df_b.apply(lambda row: row["pengeluaran"] / row["qty"] if row["qty"] > 0 else row["pengeluaran"], axis=1)
      
      df_sheet3 = df_b.pivot_table(
          index="tanggal",
          columns="nama_barang",
          values="harga_satuan",
          aggfunc="mean"
      ).reset_index()
      df_sheet3 = df_sheet3.sort_values("tanggal", ascending=False)
      df_sheet3["tanggal"] = pd.to_datetime(df_sheet3["tanggal"]).dt.strftime("%d %B %Y")
      df_sheet3 = df_sheet3.rename(columns={"tanggal": "Tanggal"})
    else:
      df_sheet3 = pd.DataFrame(columns=["Tanggal"])

    # Tulis ke file Excel in-memory menggunakan pandas & openpyxl
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      df_sheet1.to_excel(writer, sheet_name="Stok dan Penjualan", index=False)
      df_sheet2.to_excel(writer, sheet_name="Keuangan", index=False)
      df_sheet3.to_excel(writer, sheet_name="Harga Bahan", index=False)
    processed_data = output.getvalue()

    st.download_button(
        label="📥 Klik di Sini untuk Unduh File Excel",
        data=processed_data,
        file_name=f"Rekap_WannaBeWithU_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.success("✅ File Excel berhasil disiapkan! Silakan klik tombol unduh di atas.")

# -----------------------------------------------------------------------------
# MENU 8: KELOLA MASTER TOKO
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
      pilih_varian_adj = st.selectbox(
          "Pilih Varian Produk", LIST_PRODUK, key="varian_adjust"
      )
      
      toko_filtered_adj = [
          t for t in list_toko if t.get("produk", "Coklat") == pilih_varian_adj
      ]

      if not toko_filtered_adj:
        st.info(f"Belum ada data toko untuk varian {pilih_varian_adj}.")
      else:
        mode_adjust = st.radio(
            "Pilih Skala Kenaikan Harga",
            ["Satu Toko Spesifik", f"Massal Semua Toko ({pilih_varian_adj})"],
            key="radio_skala",
        )

        if mode_adjust == "Satu Toko Spesifik":
          opsi_toko_adj = {
              f"{t['nama_toko']} (Harga Lama: Rp {t.get('harga_jual', 0):,.0f})"
              : t
              for t in toko_filtered_adj
          }
          pilih_toko_adj = st.selectbox(
              "Pilih Toko", list(opsi_toko_adj.keys()), key="sel_toko_spesifik"
          )
          obj_toko = opsi_toko_adj[pilih_toko_adj]

          harga_lama = obj_toko.get("harga_jual", 0)
          nominal_kenaikan = st.number_input(
              "Nominal Kenaikan Harga (Rp)",
              min_value=0.0,
              step=500.0,
              value=1000.0,
              format="%.2f",
              key="nom_spesifik",
          )

          harga_baru = harga_lama + nominal_kenaikan
          st.info(
              f"💡 **Harga Lama:** Rp {harga_lama:,.0f} ➡️ **Harga Baru:** Rp"
              f" {harga_baru:,.0f}"
          )

          if st.button("🚀 Terapkan Kenaikan Harga", use_container_width=True, key="btn_spesifik"):
            try:
              supabase.table("tabel_toko").update(
                  {"harga_jual": harga_baru}
              ).eq("id", obj_toko["id"]).execute()
              st.success(
                  f"✅ Harga jual {obj_toko['nama_toko']} [{pilih_varian_adj}]"
                  f" berhasil dinaikkan menjadi Rp {harga_baru:,.0f}!"
              )
              st.rerun()
            except Exception as e:
              st.error(f"❌ Gagal memperbarui harga: {e}")

        else:
          nominal_kenaikan_massal = st.number_input(
              f"Nominal Kenaikan untuk Semua Toko Varian {pilih_varian_adj} (Rp)",
              min_value=0.0,
              step=500.0,
              value=1000.0,
              format="%.2f",
              key="kenaikan_massal_drop",
          )
          st.warning(
              f"⚠️ Kenaikan harga Rp {nominal_kenaikan_massal:,.0f} akan"
              f" diterapkan ke **{len(toko_filtered_adj)} toko** untuk varian"
              f" **{pilih_varian_adj}**."
          )

          if st.button("🚀 Terapkan Kenaikan Massal", use_container_width=True, key="btn_massal_drop"):
            try:
              for t in toko_filtered_adj:
                h_baru = t.get("harga_jual", 0) + nominal_kenaikan_massal
                supabase.table("tabel_toko").update({"harga_jual": h_baru}).eq(
                    "id", t["id"]
                ).execute()
              st.success(
                  f"✅ Kenaikan harga berhasil diterapkan ke semua toko untuk"
                  f" varian {pilih_varian_adj}!"
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
