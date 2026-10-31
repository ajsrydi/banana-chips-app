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
        "🏭 Manajemen Stok Bahan",
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


LIST_PRODUK = ["Coklat", "Matcha"]

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
# FUNGSI BANTUAN: UPDATE OTOMATIS STOK BAHAN
# -----------------------------------------------------------------------------
def update_stok_db(nama_bahan, tambah_masuk=0.0, tambah_keluar=0.0, satuan="pcs", min_warn=5.0):
  try:
    bahan_lower = nama_bahan.strip().lower()
    resp = supabase.table("tabel_stok_bahan").select("*").eq("nama_bahan", bahan_lower).execute()
    data_existing = resp.data

    if data_existing:
      item = data_existing[0]
      curr_masuk = float(item.get("stok_masuk", 0)) + float(tambah_masuk)
      curr_keluar = float(item.get("stok_keluar", 0)) + float(tambah_keluar)
      supabase.table("tabel_stok_bahan").update({
          "stok_masuk": curr_masuk,
          "stok_keluar": curr_keluar,
          "satuan": satuan,
          "min_warning": min_warn
      }).eq("id", item["id"]).execute()
    else:
      supabase.table("tabel_stok_bahan").insert({
          "nama_bahan": bahan_lower,
          "stok_masuk": float(tambah_masuk),
          "stok_keluar": float(tambah_keluar),
          "satuan": satuan,
          "min_warning": min_warn
      }).execute()
  except Exception as e:
    print(f"Gagal update stok otomatis: {e}")

# -----------------------------------------------------------------------------
# MENU 1: HOME
# -----------------------------------------------------------------------------
if menu == "🏠 Home":
  st.markdown("### 📈 Ringkasan Keuangan & Stok")

  penjualan = fetch_data("tabel_penjualan")
  pengeluaran = fetch_data("tabel_pengeluaran")
  produksi = fetch_data("tabel_produksi")

  total_omset = sum(item.get("total_penjualan", 0) for item in penjualan)
  parse_piutang = sum(item.get("total_penjualan", 0) for item in penjualan if "Belum" in str(item.get("status", "")))
  total_biaya = sum(item.get("pengeluaran", 0) for item in pengeluaran)

  bulan_ini = str(datetime.date.today())[:7]
  biaya_bulan_ini = sum(item.get("pengeluaran", 0) for item in pengeluaran if str(item.get("tanggal", "")).startswith(bulan_ini))
  total_profit = total_omset - total_biaya

  total_prod_coklat = sum(item.get("jumlah_produksi", 0) for item in produksi if item.get("produk", "Coklat") == "Coklat")
  total_kirim_coklat = sum(item.get("dikirim", 0) for item in penjualan if item.get("produk", "Coklat") == "Coklat")
  stok_coklat = total_prod_coklat - total_kirim_coklat

  total_prod_matcha = sum(item.get("jumlah_produksi", 0) for item in produksi if item.get("produk") == "Matcha")
  total_kirim_matcha = sum(item.get("dikirim", 0) for item in penjualan if item.get("produk") == "Matcha")
  stok_matcha = total_prod_matcha - total_kirim_matcha

  if stok_coklat < 20 or stok_matcha < 20:
    st.warning(f"⚠️ **Peringatan Stok Menipis!** Stok Coklat: **{stok_coklat} pcs** | Stok Matcha: **{stok_matcha} pcs**. Segera jadwalkan produksi!")

  col1, col2, col3 = st.columns(3)
  col1.metric("Total Omset", f"Rp {total_omset:,.0f}")
  col2.metric("Total Piutang", f"Rp {parse_piutang:,.0f}")
  col3.metric("Estimasi Profit", f"Rp {total_profit:,.0f}")

  col4, col5, col6 = st.columns(3)
  col4.metric("Pengeluaran Bulan Ini", f"Rp {biaya_bulan_ini:,.0f}")
  col5.metric("Stok Gudang Coklat", f"{stok_coklat:,} pcs")
  col6.metric("Stok Gudang Matcha", f"{stok_matcha:,} pcs")

  st.markdown("---")
  st.markdown("🏆 **Analisis Performa & Top Toko (Berdasarkan Omset)**")
  if penjualan:
    df_top = pd.DataFrame(penjualan)
    df_toko_sum = df_top.groupby("toko")["total_penjualan"].sum().reset_index().sort_values(by="total_penjualan", ascending=False).head(5)
    fig_toko = px.bar(df_toko_sum, x="toko", y="total_penjualan", text_auto=",.0f", color="total_penjualan", color_continuous_scale="blues")
    fig_toko.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title="", yaxis_title="Omset (Rp)", coloraxis_showscale=False)
    st.plotly_chart(fig_toko, use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 2: PRODUKSI & STOK (OTOMATIS KURANGI BAHAN BAKU BERDASARKAN RESEP)
# -----------------------------------------------------------------------------
elif menu == "📦 Produksi & Stok":
  st.markdown("### 📦 Kelola Produksi & Stok Gudang")

  produksi_list = fetch_data("tabel_produksi")
  penjualan_list = fetch_data("tabel_penjualan")

  total_prod_coklat = sum(item.get("jumlah_produksi", 0) for item in produksi_list if item.get("produk", "Coklat") == "Coklat")
  total_kirim_coklat = sum(item.get("dikirim", 0) for item in penjualan_list if item.get("produk", "Coklat") == "Coklat")
  stok_coklat = total_prod_coklat - total_kirim_coklat

  total_prod_matcha = sum(item.get("jumlah_produksi", 0) for item in produksi_list if item.get("produk") == "Matcha")
  total_kirim_matcha = sum(item.get("dikirim", 0) for item in penjualan_list if item.get("produk") == "Matcha")
  stok_matcha = total_prod_matcha - total_kirim_matcha

  c1, c2 = st.columns(2)
  c1.metric("Stok Coklat", f"{stok_coklat:,} pcs")
  c2.metric("Stok Matcha", f"{stok_matcha:,} pcs")
  st.markdown("---")

  tab1, tab2 = st.tabs(["➕ Tambah Produksi", "📋 Riwayat Produksi"])

  with tab1:
    with st.form("form_produksi", clear_on_submit=True):
      tanggal_prod = st.date_input("Tanggal Produksi", datetime.date.today())
      pilih_produk = st.selectbox("Varian Produk", LIST_PRODUK)
      jumlah_prod = st.number_input("Jumlah Produksi (Pcs)", min_value=1, step=1, value=11)
      submit_prod = st.form_submit_button("💾 Simpan Data Produksi")

      if submit_prod:
        try:
          # Simpan ke tabel produksi
          supabase.table("tabel_produksi").insert({
              "tanggal": str(tanggal_prod),
              "produk": pilih_produk,
              "jumlah_produksi": jumlah_prod,
          }).execute()

          # LOGIKA OTOMATIS PEMOTONGAN STOK BERDASARKAN RESEP (Hanya aktif untuk varian Coklat)
          if pilih_produk == "Coklat":
            # Berdasarkan resep per 11 pcs: keripik pisang 0.75 Kg, kemasan coklat 11 pcs, coklat 0.25 Kg, minyak 0.10 L
            faktor_pengali = jumlah_prod / 11.0
            
            pakai_keripik = 0.75 * faktor_pengali
            pakai_kemasan = 11 * faktor_pengali
            pakai_coklat = 0.25 * faktor_pengali
            pakai_minyak = 0.10 * faktor_pengali

            update_stok_db("keripik pisang", tambah_keluar=pakai_keripik, satuan="Kg")
            update_stok_db("kemasan coklat", tambah_keluar=pakai_kemasan, satuan="pcs")
            update_stok_db("coklat", tambah_keluar=pakai_coklat, satuan="Kg")
            update_stok_db("minyak", tambah_keluar=pakai_minyak, satuan="L")

          elif pilih_produk == "Matcha":
            st.info("Resep matcha masih dalam tahap pengembangan (development).")

          st.success("✅ Data produksi disimpan & stok bahan baku otomatis terpotong!")
          st.rerun()
        except Exception as e:
          st.error(f"❌ Gagal: {e}")

  with tab2:
    if produksi_list:
      st.dataframe(pd.DataFrame(produksi_list), use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 3: KELOLA PENJUALAN
# -----------------------------------------------------------------------------
elif menu == "🛒 Kelola Penjualan":
  st.markdown("#### 🚨 Kontrabon Aktif (Belum Lunas)")
  penjualan_all = fetch_data("tabel_penjualan")
  piutang_all = [item for item in penjualan_all if "Belum" in str(item.get("status", ""))]
  if piutang_all:
    for item in piutang_all:
      st.warning(f"📅 `{item.get('tanggal')}` | 🏪 **{item.get('toko')}** [{item.get('produk', 'Coklat')}] ➡️ **{item.get('dikirim'):,} pcs** (Rp {item.get('total_penjualan', 0):,.0f})")
  else:
    st.success("🎉 Semua toko sudah lunas!")

  st.markdown("---")
  st.markdown("### 📝 Kelola Catatan Penjualan")
  tab1, tab2, tab3 = st.tabs(["➕ Tambah Baru", "✏️ Edit / Lunas", "📦 Data Penjualan"])
  data_toko = fetch_data("tabel_toko")

  with tab1:
    if data_toko:
      with st.form("form_jual", clear_on_submit=True):
        tanggal = st.date_input("Tanggal", datetime.date.today())
        pilihan_produk_jual = st.selectbox("Varian Produk", LIST_PRODUK)
        toko_filtered = [t for t in data_toko if t.get("produk", "Coklat") == pilihan_produk_jual]
        
        if toko_filtered:
          opsi_toko = {t["nama_toko"]: t for t in toko_filtered}
          pilihan_toko_nama = st.selectbox("Pilih Toko", list(opsi_toko.keys()))
          toko_terpilih = opsi_toko[pilihan_toko_nama]
          
          harga_jual = toko_terpilih.get("harga_jual", 0)
          potongan = toko_terpilih.get("potongan_persen", 0)
          harga_bersih_pcs = harga_jual - (harga_jual * potongan / 100)
          
          dikirim = st.number_input("Jumlah Dikirim / Laku", min_value=0, step=1)
          status_bayar = st.selectbox("Status", ["Belum Lunas (Kontrabon)", "Lunas"])
          total_otomatis = dikirim * harga_bersih_pcs
          st.markdown(f"💰 **Total Penjualan:** Rp {total_otomatis:,.0f}")

          if st.form_submit_button("💾 Simpan Penjualan", use_container_width=True):
            try:
              supabase.table("tabel_penjualan").insert({
                  "tanggal": str(tanggal),
                  "toko": pilihan_toko_nama,
                  "produk": pilihan_produk_jual,
                  "dikirim": dikirim,
                  "status": status_bayar,
                  "total_penjualan": total_otomatis,
              }).execute()
              st.success("✅ Penjualan berhasil disimpan!")
              st.rerun()
            except Exception as e:
              st.error(f"❌ Gagal: {e}")

  with tab3:
    if penjualan_all:
      st.dataframe(pd.DataFrame(penjualan_all), use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 4: KELOLA PENGELUARAN (OTOMATIS TAMBAH STOK BAHAN MASUK)
# -----------------------------------------------------------------------------
elif menu == "💸 Kelola Pengeluaran":
  st.markdown("### 📝 Kelola Catatan Pengeluaran")
  tab1, tab2, tab3 = st.tabs(["➕ Tambah Baru", "✏️ Edit & Hapus", "💸 Data Pengeluaran"])

  with tab1:
    with st.form("form_pengeluaran", clear_on_submit=True):
      tanggal = st.date_input("Tanggal Pengeluaran", datetime.date.today())
      nama_barang = st.selectbox("Nama Barang / Bahan", LIST_BARANG_PENGELUARAN)
      pengeluaran = st.number_input("Total Biaya Pengeluaran (Rp)", min_value=0.0, step=1000.0)
      qty = st.number_input("Banyak Barang (Qty)", min_value=0.0, step=0.5)
      submit_pengeluaran = st.form_submit_button("💾 Simpan Pengeluaran")

      if submit_pengeluaran:
        try:
          # Simpan ke tabel pengeluaran
          supabase.table("tabel_pengeluaran").insert({
              "tanggal": str(tanggal),
              "nama_barang": nama_barang,
              "qty": qty,
              "pengeluaran": pengeluaran,
          }).execute()

          # LOGIKA OTOMATIS TAMBAH STOK MASUK JIKA YANG DIBELI ADALAH BAHAN BAKU STOK
          satuan_default = "Kg" if "kg" in nama_barang or nama_barang in ["keripik pisang", "coklat", "matcha"] else ("L" if nama_barang == "minyak" else "pcs")
          update_stok_db(nama_barang, tambah_masuk=qty, satuan=satuan_default)

          st.success("✅ Pengeluaran disimpan & stok bahan baku gudang otomatis bertambah!")
          st.rerun()
        except Exception as e:
          st.error(f"❌ Gagal: {e}")

  with tab3:
    pengeluaran_list = fetch_data("tabel_pengeluaran")
    if pengeluaran_list:
      st.dataframe(pd.DataFrame(pengeluaran_list), use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 5: REKAP LAPORAN & STOK
# -----------------------------------------------------------------------------
elif menu == "📊 Rekap Laporan & Stok":
  st.markdown("### 📊 Rekap Laporan & Keuangan")
  penjualan = fetch_data("tabel_penjualan")
  pengeluaran = fetch_data("tabel_pengeluaran")

  st.markdown("📅 **Filter Rentang Tanggal Laporan**")
  col_d1, col_d2 = st.columns(2)
  start_date = col_d1.date_input("Dari Tanggal", datetime.date.today() - datetime.timedelta(days=90))
  end_date = col_d2.date_input("Sampai Tanggal", datetime.date.today())

  df_p_filtered = pd.DataFrame(penjualan) if penjualan else pd.DataFrame()
  if not df_p_filtered.empty:
    df_p_filtered["tanggal_dt"] = pd.to_datetime(df_p_filtered["tanggal"]).dt.date
    df_p_filtered = df_p_filtered[(df_p_filtered["tanggal_dt"] >= start_date) & (df_p_filtered["tanggal_dt"] <= end_date)]

  df_e_filtered = pd.DataFrame(pengeluaran) if pengeluaran else pd.DataFrame()
  if not df_e_filtered.empty:
    df_e_filtered["tanggal_dt"] = pd.to_datetime(df_e_filtered["tanggal"]).dt.date
    df_e_filtered = df_e_filtered[(df_e_filtered["tanggal_dt"] >= start_date) & (df_e_filtered["tanggal_dt"] <= end_date)]

  tab_stok, tab_keuangan = st.tabs(["📦 Rekap Toko (Rentang Tanggal)", "💰 Ringkasan Keuangan Filter"])
  with tab_stok:
    if not df_p_filtered.empty:
      df_toko_range = df_p_filtered.groupby(["toko", "produk"])["dikirim"].sum().reset_index()
      st.dataframe(df_toko_range.pivot_table(index="toko", columns="produk", values="dikirim", fill_value=0).reset_index(), use_container_width=True)
    else:
      st.info("Tidak ada data penjualan pada rentang tanggal tersebut.")

  with tab_keuangan:
    omset_range = df_p_filtered["total_penjualan"].sum() if not df_p_filtered.empty else 0
    biaya_range = df_e_filtered["pengeluaran"].sum() if not df_e_filtered.empty else 0
    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Total Omset", f"Rp {omset_range:,.0f}")
    rc2.metric("Total Pengeluaran", f"Rp {biaya_range:,.0f}")
    rc3.metric("Profit Bersih", f"Rp {omset_range - biaya_range:,.0f}")

# -----------------------------------------------------------------------------
# MENU 6: MANAJEMEN STOK BAHAN (AUTO UPDATE DARI PENGELUARAN & PRODUKSI)
# -----------------------------------------------------------------------------
elif menu == "🏭 Manajemen Stok Bahan":
  st.markdown("### 🏭 Manajemen Stok Bahan Baku Mentah")
  st.markdown("Stok di bawah ini otomatis terakumulasi dari belanja (Pengeluaran) dan terpotong dari Resep (Produksi).")

  list_bahan_db = fetch_data("tabel_stok_bahan")
  if not list_bahan_db:
    st.info("Belum ada data stok bahan baku. Silakan catat belanja bahan di menu Kelola Pengeluaran.")
  else:
    df_bahan_stok = pd.DataFrame(list_bahan_db)
    df_bahan_stok["sisa_stok"] = df_bahan_stok["stok_masuk"] - df_bahan_stok["stok_keluar"]

    stok_menipis = df_bahan_stok[df_bahan_stok["sisa_stok"] <= df_bahan_stok["min_warning"]]
    if not stok_menipis.empty:
      for _, row in stok_menipis.iterrows():
        st.warning(f"⚠️ **Peringatan!** Bahan **{row['nama_bahan']}** tersisa **{row['sisa_stok']} {row['satuan']}**. Segera lakukan restock!")

    st.dataframe(df_bahan_stok, use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 7: PANTAU HARGA BAHAN
# -----------------------------------------------------------------------------
elif menu == "📈 Pantau Harga Bahan":
  st.markdown("### 📈 Perkembangan Harga Satuan")
  pengeluaran_list = fetch_data("tabel_pengeluaran")
  if pengeluaran_list:
    df_bahan = pd.DataFrame(pengeluaran_list)
    df_bahan["qty"] = pd.to_numeric(df_bahan["qty"], errors="coerce").fillna(0)
    df_bahan["pengeluaran"] = pd.to_numeric(df_bahan["pengeluaran"], errors="coerce").fillna(0)
    df_bahan["harga_satuan"] = df_bahan.apply(lambda row: row["pengeluaran"] / row["qty"] if row["qty"] > 0 else row["pengeluaran"], axis=1)
    df_pivot = df_bahan.pivot_table(index="tanggal", columns="nama_barang", values="harga_satuan", aggfunc="mean").reset_index()
    st.dataframe(df_pivot.sort_values("tanggal", ascending=False), use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 8: DOWNLOAD REKAP EXCEL
# -----------------------------------------------------------------------------
elif menu == "📥 Download Rekap Excel":
  st.markdown("### 📥 Download Rekap Excel")
  if st.button("📥 Unduh File Excel Sekarang", use_container_width=True):
    penjualan = fetch_data("tabel_penjualan")
    produksi = fetch_data("tabel_produksi")
    pengeluaran = fetch_data("tabel_pengeluaran")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      pd.DataFrame(penjualan).to_excel(writer, sheet_name="Penjualan", index=False)
      pd.DataFrame(pengeluaran).to_excel(writer, sheet_name="Pengeluaran", index=False)
      pd.DataFrame(produksi).to_excel(writer, sheet_name="Produksi", index=False)
    
    st.download_button(
        label="📥 Klik di Sini untuk Unduh File Excel",
        data=output.getvalue(),
        file_name=f"Rekap_WannaBeWithU_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.success("✅ File Excel siap diunduh!")

# -----------------------------------------------------------------------------
# MENU 9: KELOLA MASTER TOKO
# ------------------------------------------------net-----------------------------
elif menu == "🏪 Kelola Master Toko":
  st.markdown("### 🏪 Master Data Toko & Harga")
  tab1, tab2, tab3 = st.tabs(["➕ Tambah / Edit Toko", "📈 Adjust Kenaikan Harga", "📋 Daftar Toko"])
  list_toko = fetch_data("tabel_toko")

  with tab1:
    with st.form("form_toko", clear_on_submit=True):
      nama_toko = st.text_input("Nama Toko / Reseller")
      pilih_produk_toko = st.selectbox("Varian Produk", LIST_PRODUK)
      harga_jual = st.number_input("Harga Jual per Pcs (Rp)", min_value=0.0)
      potongan_persen = st.number_input("Potongan / Komisi (%)", min_value=0.0, max_value=100.0)
      if st.form_submit_button("💾 Simpan Toko"):
        if nama_toko.strip():
          supabase.table("tabel_toko").upsert({
              "nama_toko": nama_toko.strip(),
              "produk": pilih_produk_toko,
              "harga_jual": harga_jual,
              "potongan_persen": potongan_persen,
          }, on_conflict="nama_toko,produk").execute()
          st.success("✅ Toko disimpan!")
          st.rerun()

  with tab3:
    if list_toko:
      st.dataframe(pd.DataFrame(list_toko), use_container_width=True)
