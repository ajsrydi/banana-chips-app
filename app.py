import datetime
import io
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import Client, create_client

# Konfigurasi halaman agar optimal di layar HP & sidebar otomatis tertutup saat awal buka
st.set_page_config(
    page_title="Wanna Be With U - Laporan",
    page_icon="🍌",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# CSS & SCRIPT UNTUK MENCEGAH KEYBOARD HP MUNCUL PADA DROPDOWN
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Menyembunyikan kursor ketik agar terlihat seperti tombol pilihan murni */
    input {
        caret-color: transparent !important;
    }
    </style>
    <script>
    function lockSelectInputs() {
        const selectInputs = document.querySelectorAll('div[data-baseweb="select"] input');
        selectInputs.forEach(input => {
            input.setAttribute('readonly', 'true');
            input.setAttribute('inputmode', 'none');
        });
    }
    document.addEventListener("click", lockSelectInputs);
    const observer = new MutationObserver(lockSelectInputs);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """,
    unsafe_allow_html=True,
)


# Fungsi untuk memuat file CSS eksternal
def load_css(file_name):
  try:
    with open(file_name) as f:
      st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
  except FileNotFoundError:
    pass


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

# -----------------------------------------------------------------------------
# SIDEBAR: JUDUL & NAVIGASI MENU
# -----------------------------------------------------------------------------
st.sidebar.title("🍌 Wanna Be With U")
st.sidebar.markdown("---")
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
# MENU 1: HOME (RINGKASAN KEUANGAN & STOK + TOP TOKO)
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
      if item.get("produk", "Matcha") == "Matcha"
  )
  stok_matcha = total_prod_matcha - total_kirim_matcha

  if stok_coklat < 20 or stok_matcha < 20:
    st.warning(
        f"⚠️ **Peringatan Stok Menipis!** Stok Coklat: **{stok_coklat} pcs** |"
        f" Stok Matcha: **{stok_matcha} pcs**. Segera jadwalkan produksi!"
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

  # ANALISIS PERFORMA & TOP TOKO (BAR CHART)
  st.markdown("🏆 **Analisis Performa & Top Toko (Berdasarkan Omset)**")
  if penjualan:
    df_top = pd.DataFrame(penjualan)
    df_toko_sum = (
        df_top.groupby("toko")["total_penjualan"].sum().reset_index()
    )
    df_toko_sum = df_toko_sum.sort_values(
        by="total_penjualan", ascending=False
    ).head(5)

    fig_toko = px.bar(
        df_toko_sum,
        x="toko",
        y="total_penjualan",
        text_auto=",.0f",
        labels={
            "toko": "Nama Toko / Reseller",
            "total_penjualan": "Total Omset (Rp)",
        },
        color="total_penjualan",
        color_continuous_scale="blues",
    )
    fig_toko.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="",
        yaxis_title="Omset (Rp)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_toko, use_container_width=True)
  else:
    st.info("Belum ada data penjualan untuk analisis performa toko.")

  st.markdown("---")
  st.markdown("#### 📊 Grafik Kinerja Keuangan Bulanan")

  df_p = pd.DataFrame(penjualan) if penjualan else pd.DataFrame()
  df_e = pd.DataFrame(pengeluaran) if pengeluaran else pd.DataFrame()

  if not df_p.empty or not df_e.empty:
    if not df_p.empty:
      df_p["bulan"] = (
          pd.to_datetime(df_p["tanggal"]).dt.to_period("M").astype(str)
      )
      df_p_bulan = df_p.groupby("bulan")["total_penjualan"].sum().reset_index()
    else:
      df_p_bulan = pd.DataFrame(columns=["bulan", "total_penjualan"])

    if not df_e.empty:
      df_e["bulan"] = (
          pd.to_datetime(df_e["tanggal"]).dt.to_period("M").astype(str)
      )
      df_exp_bulan = df_e.groupby("bulan")["pengeluaran"].sum().reset_index()
    else:
      df_exp_bulan = pd.DataFrame(columns=["bulan", "pengeluaran"])

    df_chart_bulanan = pd.merge(
        df_p_bulan, df_exp_bulan, on="bulan", how="outer"
    ).fillna(0)
    df_chart_bulanan = df_chart_bulanan.sort_values("bulan")
    df_chart_bulanan["Profit Bersih"] = (
        df_chart_bulanan["total_penjualan"] - df_chart_bulanan["pengeluaran"]
    )

    df_chart_melted = df_chart_bulanan.rename(
        columns={
            "bulan": "Bulan",
            "total_penjualan": "Pemasukan",
            "pengeluaran": "Pengeluaran",
            "Profit Bersih": "Profit Bersih",
        }
    ).melt(
        id_vars=["Bulan"],
        value_vars=["Pemasukan", "Pengeluaran", "Profit Bersih"],
        var_name="Kategori",
        value_name="Jumlah (Rp)",
    )

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
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
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
      if item.get("produk", "Matcha") == "Matcha"
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
          f"ID {p['id']} | {p.get('tanggal')} | [{p.get('produk', 'Coklat')}]"
          f" {p.get('jumlah_produksi')} pcs": p["id"]
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
      item for item in penjualan_all if "Belum" in str(item.get("status", ""))
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
            f" **{pilihan_produk_jual}**."
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
            "Status Pembayaran",
            ["Belum Lunas (Kontrabon)", "Lunas"],
            key="tambah_status",
        )

        st.info(
            f"💡 **Harga Bersih per Pcs:** Rp {harga_bersih_pcs:,.0f}"
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
      st.info("Belum ada data penjualan.")
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
      if daftar_bulan:
        pilih_bulan = st.selectbox(
            "📅 Pilih Bulan Transaksi", daftar_bulan, key="filter_bulan_edit"
        )
        penjualan_filtered_bulan = [
            item
            for item in penjualan_list
            if str(item["tanggal"]).startswith(pilih_bulan)
        ]
        if penjualan_filtered_bulan:
          opsi_penjualan = {
              f"ID {item['id']} | {item['tanggal']} | {item.get('toko')}"
              f" [{item.get('produk', 'Coklat')}] - Status:"
              f" {item.get('status', 'Belum Lunas (Kontrabon)')}": item
              for item in penjualan_filtered_bulan
          }
          pilih_data = st.selectbox(
              "Pilih Data Penjualan",
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
          current_status = data_terpilih.get(
              "status", "Belum Lunas (Kontrabon)"
          )

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
          new_total = new_dikirim * h_bersih_pcs
          st.markdown(f"💰 **Total Penjualan:** Rp {new_total:,.0f}")

          col_update, col_delete = st.columns(2)
          if col_update.button(
              "🔄 Update / Lunasi Data", key=f"btn_up_{current_id}"
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
              st.success("✅ Data berhasil diperbarui!")
              st.rerun()
            except Exception as e:
              st.error(f"❌ Gagal: {e}")

          if col_delete.button("🗑️ Hapus Data", key=f"btn_del_{current_id}"):
            try:
              supabase.table("tabel_penjualan").delete().eq(
                  "id", current_id
              ).execute()
              st.success("🗑️ Data berhasil dihapus!")
              st.rerun()
            except Exception as e:
              st.error(f"❌ Gagal: {e}")

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
          "Total Biaya Pengeluaran (Rp)", min_value=0.0, step=1000.0
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
          st.error(f"❌ Gagal: {e}")

  with tab2:
    pengeluaran_list = fetch_data("tabel_pengeluaran")
    if pengeluaran_list:
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
      if daftar_bulan_keluar:
        pilih_bulan_keluar = st.selectbox(
            "📅 Pilih Bulan Pengeluaran", daftar_bulan_keluar
        )
        pengeluaran_filtered_bulan = [
            item
            for item in pengeluaran_list
            if str(item["tanggal"]).startswith(pilih_bulan_keluar)
        ]
        if pengeluaran_filtered_bulan:
          opsi_keluar_edit = {
              f"ID {item['id']} | {item['tanggal']} | {item['nama_barang']} (Rp {item.get('pengeluaran', 0):,.0f})": item
              for item in pengeluaran_filtered_bulan
          }
          pilih_data_keluar = st.selectbox(
              "Pilih Data Pengeluaran", list(opsi_keluar_edit.keys())
          )
          data_terpilih_keluar = opsi_keluar_edit[pilih_data_keluar]

          curr_id_k = data_terpilih_keluar["id"]
          new_tgl_k = st.date_input(
              "Tanggal",
              value=datetime.datetime.strptime(
                  data_terpilih_keluar["tanggal"], "%Y-%m-%d"
              ).date(),
              key=f"tgl_k_{curr_id_k}",
          )
          new_barang_k = st.selectbox(
              "Barang",
              LIST_BARANG_PENGELUARAN,
              index=(
                  LIST_BARANG_PENGELUARAN.index(
                      data_terpilih_keluar.get(
                          "nama_barang", LIST_BARANG_PENGELUARAN[0]
                      )
                  )
                  if data_terpilih_keluar.get("nama_barang")
                  in LIST_BARANG_PENGELUARAN
                  else 0
              ),
              key=f"bar_k_{curr_id_k}",
          )
          new_biaya_k = st.number_input(
              "Biaya (Rp)",
              min_value=0.0,
              step=1000.0,
              value=float(data_terpilih_keluar.get("pengeluaran", 0.0)),
              key=f"biaya_k_{curr_id_k}",
          )
          new_qty_k = st.number_input(
              "Qty",
              min_value=0.0,
              step=0.5,
              value=float(data_terpilih_keluar.get("qty", 0.0)),
              key=f"qty_k_{curr_id_k}",
          )

          col_up_k, col_del_k = st.columns(2)
          if col_up_k.button("🔄 Update", key=f"up_k_{curr_id_k}"):
            try:
              supabase.table("tabel_pengeluaran").update({
                  "tanggal": str(new_tgl_k),
                  "nama_barang": new_barang_k,
                  "pengeluaran": new_biaya_k,
                  "qty": new_qty_k,
              }).eq("id", curr_id_k).execute()
              st.success("✅ Berhasil diperbarui!")
              st.rerun()
            except Exception as e:
              st.error(f"❌ Gagal: {e}")

          if col_del_k.button("🗑️ Hapus", key=f"del_k_{curr_id_k}"):
            try:
              supabase.table("tabel_pengeluaran").delete().eq(
                  "id", curr_id_k
              ).execute()
              st.success("🗑️ Berhasil dihapus!")
              st.rerun()
            except Exception as e:
              st.error(f"❌ Gagal: {e}")

  with tab3:
    st.markdown("#### 💸 Keseluruhan Data Pengeluaran")
    pengeluaran_list = fetch_data("tabel_pengeluaran")
    if pengeluaran_list:
      st.dataframe(pengeluaran_list, use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 5: REKAP LAPORAN & STOK + FILTER RENTANG TANGGAL BEBAS
# -----------------------------------------------------------------------------
elif menu == "📊 Rekap Laporan & Stok":
  st.markdown("### 📊 Rekap Laporan & Keuangan")

  penjualan = fetch_data("tabel_penjualan")
  produksi = fetch_data("tabel_produksi")
  pengeluaran = fetch_data("tabel_pengeluaran")

  # FITUR BARU: FILTER RENTANG TANGGAL BEBAS (CUSTOM DATE RANGE)
  st.markdown("📅 **Filter Rentang Tanggal Laporan**")
  col_d1, col_d2 = st.columns(2)
  min_default_date = datetime.date.today() - datetime.timedelta(days=90)
  start_date = col_d1.date_input("Dari Tanggal", min_default_date)
  end_date = col_d2.date_input("Sampai Tanggal", datetime.date.today())

  # Filter data berdasarkan rentang tanggal
  if penjualan:
    df_p_filtered = pd.DataFrame(penjualan)
    df_p_filtered["tanggal_dt"] = pd.to_datetime(
        df_p_filtered["tanggal"]
    ).dt.date
    df_p_filtered = df_p_filtered[
        (df_p_filtered["tanggal_dt"] >= start_date)
        & (df_p_filtered["tanggal_dt"] <= end_date)
    ]
  else:
    df_p_filtered = pd.DataFrame()

  if pengeluaran:
    df_e_filtered = pd.DataFrame(pengeluaran)
    df_e_filtered["tanggal_dt"] = pd.to_datetime(
        df_e_filtered["tanggal"]
    ).dt.date
    df_e_filtered = df_e_filtered[
        (df_e_filtered["tanggal_dt"] >= start_date)
        & (df_e_filtered["tanggal_dt"] <= end_date)
    ]
  else:
    df_e_filtered = pd.DataFrame()

  tab_stok, tab_keuangan = st.tabs(
      ["📦 Rekap Toko (Rentang Tanggal)", "💰 Ringkasan Keuangan Filter"]
  )

  with tab_stok:
    st.markdown(
        f"#### 📦 Rekap Penjualan per Toko ({start_date} s.d. {end_date})"
    )
    if not df_p_filtered.empty:
      df_toko_range = (
          df_p_filtered.groupby(["toko", "produk"])["dikirim"]
          .sum()
          .reset_index()
      )
      df_pivot_toko = df_toko_range.pivot_table(
          index="toko", columns="produk", values="dikirim", fill_value=0
      ).reset_index()
      st.dataframe(df_pivot_toko, use_container_width=True)
    else:
      st.info("Tidak ada data penjualan pada rentang tanggal tersebut.")

  with tab_keuangan:
    st.markdown(
        f"#### 💰 Ringkasan Keuangan ({start_date} s.d. {end_date})"
    )
    omset_range = (
        df_p_filtered["total_penjualan"].sum()
        if not df_p_filtered.empty
        else 0
    )
    biaya_range = (
        df_e_filtered["pengeluaran"].sum() if not df_e_filtered.empty else 0
    )
    profit_range = omset_range - biaya_range

    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Total Omset", f"Rp {omset_range:,.0f}")
    rc2.metric("Total Pengeluaran", f"Rp {biaya_range:,.0f}")
    rc3.metric("Profit Bersih", f"Rp {profit_range:,.0f}")

# -----------------------------------------------------------------------------
# MENU 6: PANTAU HARGA BAHAN
# -----------------------------------------------------------------------------
elif menu == "📈 Pantau Harga Bahan":
  st.markdown("### 📈 Perkembangan Harga Satuan")
  pengeluaran_list = fetch_data("tabel_pengeluaran")
  if not pengeluaran_list:
    st.info("Belum ada data pengeluaran.")
  else:
    df_bahan = pd.DataFrame(pengeluaran_list)
    df_bahan["qty"] = pd.to_numeric(df_bahan["qty"], errors="coerce").fillna(0)
    df_bahan["pengeluaran"] = pd.to_numeric(
        df_bahan["pengeluaran"], errors="coerce"
    ).fillna(0)
    df_bahan["harga_satuan"] = df_bahan.apply(
        lambda row: (
            row["pengeluaran"] / row["qty"]
            if row["qty"] > 0
            else row["pengeluaran"]
        ),
        axis=1,
    )
    df_pivot = df_bahan.pivot_table(
        index="tanggal",
        columns="nama_barang",
        values="harga_satuan",
        aggfunc="mean",
    ).reset_index()
    df_pivot = df_pivot.sort_values("tanggal", ascending=False)
    st.dataframe(df_pivot, use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 7: DOWNLOAD REKAP EXCEL
# -----------------------------------------------------------------------------
elif menu == "📥 Download Rekap Excel":
  st.markdown("### 📥 Download Rekap Excel")
  if st.button("📥 Unduh File Excel Sekarang", use_container_width=True):
    penjualan = fetch_data("tabel_penjualan")
    produksi = fetch_data("tabel_produksi")
    pengeluaran = fetch_data("tabel_pengeluaran")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      pd.DataFrame(penjualan).to_excel(
          writer, sheet_name="Stok dan Penjualan", index=False
      )
      pd.DataFrame(pengeluaran).to_excel(
          writer, sheet_name="Keuangan", index=False
      )
      pd.DataFrame(produksi).to_excel(
          writer, sheet_name="Harga Bahan", index=False
      )
    processed_data = output.getvalue()

    st.download_button(
        label="📥 Klik di Sini untuk Unduh File Excel",
        data=processed_data,
        file_name=f"Rekap_WannaBeWithU_{datetime.date.today()}.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )
    st.success("✅ File Excel siap diunduh!")

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
      nama_toko = st.text_input("Nama Toko / Reseller")
      pilih_produk_toko = st.selectbox("Varian Produk", LIST_PRODUK)
      harga_jual = st.number_input("Harga Jual per Pcs (Rp)", min_value=0.0)
      potongan_persen = st.number_input(
          "Potongan / Komisi Toko (%)", min_value=0.0, max_value=100.0
      )
      submit_toko = st.form_submit_button("💾 Simpan / Update Toko")

      if submit_toko:
        if nama_toko.strip() == "":
          st.warning("⚠️ Nama toko kosong!")
        else:
          try:
            supabase.table("tabel_toko").upsert(
                {
                    "nama_toko": nama_toko.strip(),
                    "produk": pilih_produk_toko,
                    "harga_jual": harga_jual,
                    "potongan_persen": potongan_persen,
                },
                on_conflict="nama_toko,produk",
            ).execute()
            st.success("✅ Berhasil disimpan!")
            st.rerun()
          except Exception as e:
            st.error(f"❌ Gagal: {e}")

  with tab2:
    st.markdown("#### 📈 Penyesuaian Kenaikan Harga")
    if list_toko:
      pilih_varian_adj = st.selectbox("Varian Produk", LIST_PRODUK)
      toko_filtered_adj = [
          t for t in list_toko if t.get("produk") == pilih_varian_adj
      ]
      if toko_filtered_adj:
        nominal_kenaikan = st.number_input(
            "Nominal Kenaikan Harga Massal (Rp)", min_value=0.0, step=500.0
        )
        if st.button("🚀 Terapkan Kenaikan Massal", use_container_width=True):
          try:
            for t in toko_filtered_adj:
              h_baru = t.get("harga_jual", 0) + nominal_kenaikan
              supabase.table("tabel_toko").update({"harga_jual": h_baru}).eq(
                  "id", t["id"]
              ).execute()
            st.success("✅ Kenaikan harga massal berhasil diterapkan!")
            st.rerun()
          except Exception as e:
            st.error(f"❌ Gagal: {e}")

  with tab3:
    st.markdown("#### 📋 Daftar Toko Terdaftar")
    if list_toko:
      df_toko = pd.DataFrame(list_toko)
      st.dataframe(df_toko, use_container_width=True)
