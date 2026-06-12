import json
import streamlit as st
from PIL import Image
from google import genai

# ==================================
# PAGE CONFIG
# ==================================
st.set_page_config(
    page_title="CekGizi AI Pro",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================
# CUSTOM CSS
# ==================================
st.markdown("""
<style>
/* Background Utama */
.stApp { background: linear-gradient(135deg, #f0fdf4, #ecfeff); }
/* Hero Section */
.hero { background: linear-gradient(90deg, #10b981, #22c55e); padding: 30px; border-radius: 25px; text-align: center; color: white; margin-bottom: 25px; box-shadow: 0px 4px 20px rgba(0,0,0,0.1); }
/* Cards */
.card { background: white; color: #111827 !important; padding: 20px; border-radius: 20px; box-shadow: 0px 4px 20px rgba(0,0,0,0.08); margin-bottom: 20px; }
/* Sisa Kalori Card */
.target-card { background: linear-gradient(135deg, #fef3c7, #fde68a); padding: 20px; border-radius: 20px; text-align: center; border: 2px dashed #f59e0b; margin-bottom: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.05); }
.target-card h2 { color: #b45309 !important; margin: 0; font-size: 28px; }
/* Metrics */
[data-testid="metric-container"] { background: white !important; border-radius: 20px; padding: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.08); border: 1px solid #e5e7eb; }
[data-testid="metric-container"] label { color: #374151 !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] { color: #111827 !important; font-weight: 700 !important; }
/* Button Primary */
.stButton > button { width: 100%; height: 55px; border-radius: 15px; border: none; background: #10b981; color: white; font-size: 18px; font-weight: bold; }
.stButton > button:hover { background: #059669; color: white; }
/* Semua teks Streamlit */
label, p, span, small, div, li { color: #111827 !important; }
</style>
""", unsafe_allow_html=True)

# ==================================
# INGATAN APLIKASI (SESSION STATE)
# ==================================
# Kita tambahkan riwayat_makanan untuk "Keranjang Memori" perut pengguna
if "hasil_gizi_v2" not in st.session_state:
    st.session_state.hasil_gizi_v2 = None
if "riwayat_makanan" not in st.session_state:
    st.session_state.riwayat_makanan = [] 

# ==================================
# SIDEBAR: PROFIL & TARGET KALORI
# ==================================
st.sidebar.markdown("## 👤 Profil Pengguna")
st.sidebar.info("Isi data ini untuk mengetahui target kalori harianmu secara akurat!")

gender = st.sidebar.selectbox("Jenis Kelamin", ["Pria", "Wanita"])
umur = st.sidebar.number_input("Umur (tahun)", min_value=10, max_value=100, value=20)
tinggi = st.sidebar.number_input("Tinggi Badan (cm)", min_value=100, max_value=250, value=165)
berat = st.sidebar.number_input("Berat Badan (kg)", min_value=30, max_value=200, value=60)
aktivitas = st.sidebar.selectbox(
    "Tingkat Aktivitas",
    ["Jarang Olahraga", "Olahraga Ringan (1-3x/minggu)", "Olahraga Sedang (3-5x/minggu)", "Olahraga Berat (Tiap hari)"]
)

# Rumus BMR (Mifflin-St Jeor)
if gender == "Pria":
    bmr = (10 * berat) + (6.25 * tinggi) - (5 * umur) + 5
else:
    bmr = (10 * berat) + (6.25 * tinggi) - (5 * umur) - 161

# Faktor Aktivitas (TDEE)
if aktivitas == "Jarang Olahraga":
    kalori_harian = bmr * 1.2
elif aktivitas == "Olahraga Ringan (1-3x/minggu)":
    kalori_harian = bmr * 1.375
elif aktivitas == "Olahraga Sedang (3-5x/minggu)":
    kalori_harian = bmr * 1.55
else:
    kalori_harian = bmr * 1.725

kalori_harian = int(kalori_harian)

st.sidebar.markdown(f"""
<div style="background-color: #10b981; padding: 15px; border-radius: 15px; text-align: center; color: white; margin-top: 20px;">
    <h3 style="color: white; margin: 0;">🎯 Target Harian</h3>
    <h2 style="color: white; margin: 0;">{kalori_harian} kcal</h2>
</div>
""", unsafe_allow_html=True)

# ==================================
# HEADER & PANDUAN UX
# ==================================
st.markdown("""
<div class="hero">
    <h1>🥗 CekGizi AI Pro</h1>
    <p style="font-size:18px;">Asisten Diet Cerdas & Deteksi Nutrisi Makanan</p>
</div>
""", unsafe_allow_html=True)

# Peringatan untuk pengguna HP agar membuka sidebar
st.info("💡 **Tips untuk pengguna HP:** Buka menu dengan menekan tanda panah 👈 di pojok kiri atas untuk mengatur Profil dan Target Kalorimu!")

# ==================================
# KALKULASI SISA KALORI (AKUMULASI)
# ==================================
total_dimakan = sum([item["kalori"] for item in st.session_state.riwayat_makanan])
sisa_kalori = kalori_harian - total_dimakan

st.markdown(
    f"""
    <div class="target-card">
        <h4 style="color: #b45309 !important; margin-bottom: 5px;">📉 Sisa Jatah Kalori Harianmu:</h4>
        <h2>{sisa_kalori} kcal</h2>
        <p style="color: #92400e !important; font-size: 14px; margin-top: 10px;">
            (Target {kalori_harian} kcal - Total Dimakan Hari Ini {total_dimakan} kcal)
        </p>
    </div>
    """, unsafe_allow_html=True
)

# ==================================
# API KEY & INISIALISASI
# ==================================
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("⚠️ GEMINI_API_KEY tidak ditemukan di Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# ==================================
# INPUT FOTO & PREVIEW
# ==================================
left_col, right_col = st.columns([1, 1])

with left_col:
    st.markdown("""
    <div class="card">
        <h3>📷 Unggah Foto Makanan</h3>
    </div>
    """, unsafe_allow_html=True)
    
    camera_image = st.camera_input("Ambil Foto")
    uploaded_file = st.file_uploader("Atau Unggah Foto", type=["jpg", "jpeg", "png"])

image_file = camera_image if camera_image else uploaded_file

with right_col:
    st.markdown("""
    <div class="card">
        <h3>🖼️ Preview Gambar</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if image_file:
        preview_image = Image.open(image_file)
        st.image(preview_image, use_container_width=True)
    else:
        st.info("Unggah foto makanan untuk melihat preview.")

# ==================================
# ANALISIS LOGIC
# ==================================
st.markdown("<br>", unsafe_allow_html=True)

analyze = st.button("🔍 Analisis Nutrisi")

if analyze:
    if image_file:
        with st.spinner("🤖 AI sedang menganalisis makanan..."):
            proses_image = Image.open(image_file)
            proses_image.thumbnail((800, 800))
            
            prompt = """
            Anda adalah ahli gizi profesional.
            Lihat gambar makanan yang diberikan.
            Balas HANYA dalam format JSON berikut. Pastikan nilai kalori, protein, karbohidrat, dan lemak HANYA berupa angka (integer) tanpa huruf atau satuan:
            {
            "nama_makanan":"(nama makanan)",
            "kalori_kcal":0,
            "protein_g":0,
            "karbohidrat_g":0,
            "lemak_g":0,
            "tips":"(tips singkat)"
            }
            Jangan gunakan markdown. Jangan gunakan penjelasan tambahan.
            """
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, proses_image]
                )
                
                result_text = response.text
                result_text = result_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(result_text)
                
                # 1. Simpan hasil foto terbaru untuk ditampilkan
                st.session_state.hasil_gizi_v2 = data
                
                # 2. Ambil angka kalori dan masukkan ke dalam Keranjang Memori
                try:
                    kalori_baru = int(data.get('kalori_kcal', 0))
                except:
                    kalori_baru = 0
                
                st.session_state.riwayat_makanan.append({
                    "nama": data.get('nama_makanan', 'Tidak diketahui'),
                    "kalori": kalori_baru
                })
                
                st.success("Analisis berhasil dan otomatis ditambahkan ke Riwayat Harian!")
                st.rerun() # Refresh seketika agar banner Sisa Kalori langsung ter-update
                
            except Exception as e:
                error_text = str(e)
                if "429" in error_text:
                    st.markdown('<div style="background-color: #fff3cd; color: #000000; padding: 15px; border-radius: 10px; font-weight: bold; border: 1px solid #ffe69c;">⚠️ Kuota sedang beristirahat. Silakan tunggu 1 menit lalu coba lagi.</div>', unsafe_allow_html=True)
                elif "503" in error_text:
                    st.markdown('<div style="background-color: #fff3cd; color: #000000; padding: 15px; border-radius: 10px; font-weight: bold; border: 1px solid #ffe69c;">⏳ Server AI sedang penuh antrean. Silakan tunggu beberapa detik dan klik Analisis lagi!</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="background-color: #f8d7da; color: #000000; padding: 15px; border-radius: 10px; font-weight: bold; border: 1px solid #f5c6cb;">❌ Gagal menganalisis gambar: {e}</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Silakan unggah atau ambil foto makanan terlebih dahulu!")

# ==================================
# TAMPILAN HASIL CURRENT FOOD
# ==================================
if st.session_state.hasil_gizi_v2:
    data = st.session_state.hasil_gizi_v2
    
    st.markdown(
        f"""
        <div class="card">
            <h2>🍽️ Hasil Deteksi: {data.get('nama_makanan', 'Tidak diketahui')}</h2>
        </div>
        """, unsafe_allow_html=True
    )
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔥 Kalori", f"{data.get('kalori_kcal', 0)} kcal")
    with col2:
        st.metric("💪 Protein", f"{data.get('protein_g', 0)} g")
    with col3:
        st.metric("🍚 Karbo", f"{data.get('karbohidrat_g', 0)} g")
    with col4:
        st.metric("🥑 Lemak", f"{data.get('lemak_g', 0)} g")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="card">
            <h3>💡 Tips Kesehatan</h3>
            <p>{data.get('tips', '-')}</p>
        </div>
        """, unsafe_allow_html=True
    )

# ==================================
# RIWAYAT & TOMBOL RESET (UX)
# ==================================
if len(st.session_state.riwayat_makanan) > 0:
    st.markdown("---")
    st.markdown("### 📋 Riwayat Makananmu Hari Ini")
    for i, item in enumerate(st.session_state.riwayat_makanan):
        st.markdown(f"- **{item['nama']}**: {item['kalori']} kcal")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Membuat dua tombol aksi cepat
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Cek Makanan Baru (Bersihkan Layar)"):
            st.session_state.hasil_gizi_v2 = None # Hanya hapus foto & hasil saat ini
            st.rerun()
    with col_btn2:
        if st.button("🗑️ Hapus Semua Riwayat Hari Ini"):
            st.session_state.riwayat_makanan = [] # Hapus akumulasi memori
            st.session_state.hasil_gizi_v2 = None
            st.rerun()

# ==================================
# FOOTER
# ==================================
st.markdown("""
<br><br>
<center>
    <p style="color:gray;">CekGizi AI Pro • Powered by Gemini AI</p>
</center>
""", unsafe_allow_html=True)
