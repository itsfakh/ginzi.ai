import json
import streamlit as st
from PIL import Image
from google import genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ==================================
# PAGE CONFIG & CSS
# ==================================
st.set_page_config(page_title="CekGizi AI Pro", page_icon="🥗", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f0fdf4, #ecfeff); }
.hero { background: linear-gradient(90deg, #10b981, #22c55e); padding: 30px; border-radius: 25px; text-align: center; color: white; margin-bottom: 25px; box-shadow: 0px 4px 20px rgba(0,0,0,0.1); }
.card { background: white; color: #111827 !important; padding: 20px; border-radius: 20px; box-shadow: 0px 4px 20px rgba(0,0,0,0.08); margin-bottom: 20px; }
.target-card { background: linear-gradient(135deg, #fef3c7, #fde68a); padding: 20px; border-radius: 20px; text-align: center; border: 2px dashed #f59e0b; margin-bottom: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.05); }
.target-card h2 { color: #b45309 !important; margin: 0; font-size: 28px; }
[data-testid="metric-container"] { background: white !important; border-radius: 20px; padding: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.08); border: 1px solid #e5e7eb; }
[data-testid="metric-container"] label { color: #374151 !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] { color: #111827 !important; font-weight: 700 !important; }
.stButton > button { width: 100%; height: 55px; border-radius: 15px; border: none; background: #10b981; color: white; font-size: 18px; font-weight: bold; }
.stButton > button:hover { background: #059669; color: white; }
label, p, span, small, div, li { color: #111827 !important; }
</style>
""", unsafe_allow_html=True)

# ==================================
# API KEY & KONEKSI GOOGLE SHEETS
# ==================================
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("⚠️ GEMINI_API_KEY tidak ditemukan di Streamlit Secrets.")
    st.stop()

try:
    # Mengubah teks JSON di brankas menjadi kunci asli
    kunci_json = json.loads(st.secrets["GCP_CREDENTIALS"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(kunci_json, scopes=scopes)
    client_gs = gspread.authorize(creds)
    
    # PERHATIAN: Pastikan nama ini sama persis dengan nama file Google Sheets kamu
    sheet = client_gs.open("Database CekGizi").sheet1 
except Exception as e:
    st.error(f"⚠️ Gagal terhubung ke Google Sheets. Pastikan kuncinya benar dan email robot sudah di-share sebagai Editor. Error: {e}")
    st.stop()

# ==================================
# INGATAN APLIKASI (SESSION STATE)
# ==================================
if "hasil_gizi_v2" not in st.session_state:
    st.session_state.hasil_gizi_v2 = None
if "riwayat_makanan" not in st.session_state:
    st.session_state.riwayat_makanan = [] 

# ==================================
# SIDEBAR: PROFIL & TARGET KALORI
# ==================================
st.sidebar.markdown("## 👤 Profil Pengguna")
gender = st.sidebar.selectbox("Jenis Kelamin", ["Pria", "Wanita"])
umur = st.sidebar.number_input("Umur (tahun)", min_value=10, max_value=100, value=20)
tinggi = st.sidebar.number_input("Tinggi Badan (cm)", min_value=100, max_value=250, value=165)
berat = st.sidebar.number_input("Berat Badan (kg)", min_value=30, max_value=200, value=60)
aktivitas = st.sidebar.selectbox("Tingkat Aktivitas", ["Jarang Olahraga", "Olahraga Ringan", "Olahraga Sedang", "Olahraga Berat"])

if gender == "Pria":
    bmr = (10 * berat) + (6.25 * tinggi) - (5 * umur) + 5
else:
    bmr = (10 * berat) + (6.25 * tinggi) - (5 * umur) - 161

if aktivitas == "Jarang Olahraga": kalori_harian = bmr * 1.2
elif aktivitas == "Olahraga Ringan": kalori_harian = bmr * 1.375
elif aktivitas == "Olahraga Sedang": kalori_harian = bmr * 1.55
else: kalori_harian = bmr * 1.725
kalori_harian = int(kalori_harian)

st.sidebar.markdown(f"""
<div style="background-color: #10b981; padding: 15px; border-radius: 15px; text-align: center; color: white; margin-top: 20px;">
    <h3 style="color: white; margin: 0;">🎯 Target Harian</h3>
    <h2 style="color: white; margin: 0;">{kalori_harian} kcal</h2>
</div>
""", unsafe_allow_html=True)

# ==================================
# HEADER & SISA KALORI
# ==================================
st.markdown('<div class="hero"><h1>🥗 CekGizi AI Pro</h1><p style="font-size:18px;">Asisten Diet Cerdas dengan Database</p></div>', unsafe_allow_html=True)
st.info("💡 **Tips untuk pengguna HP:** Buka menu dengan menekan tanda panah 👈 di pojok kiri atas untuk mengatur profilmu!")

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
# INPUT FOTO & ANALISIS
# ==================================
left_col, right_col = st.columns([1, 1])
with left_col:
    st.markdown('<div class="card"><h3>📷 Unggah Foto Makanan</h3></div>', unsafe_allow_html=True)
    camera_image = st.camera_input("Ambil Foto")
    uploaded_file = st.file_uploader("Atau Unggah Foto", type=["jpg", "jpeg", "png"])
image_file = camera_image if camera_image else uploaded_file

with right_col:
    st.markdown('<div class="card"><h3>🖼️ Preview Gambar</h3></div>', unsafe_allow_html=True)
    if image_file:
        st.image(Image.open(image_file), use_container_width=True)
    else:
        st.info("Unggah foto makanan untuk melihat preview.")

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔍 Analisis Nutrisi"):
    if image_file:
        with st.spinner("🤖 AI sedang menganalisis makanan..."):
            proses_image = Image.open(image_file)
            proses_image.thumbnail((800, 800))
            prompt = """
            Anda adalah ahli gizi profesional. Lihat gambar makanan yang diberikan.
            Balas HANYA dalam format JSON berikut. Pastikan nilai HANYA berupa angka integer:
            {"nama_makanan":"(nama makanan)", "kalori_kcal":0, "protein_g":0, "karbohidrat_g":0, "lemak_g":0, "tips":"(tips)"}
            Jangan gunakan markdown atau teks tambahan.
            """
            
            try:
                response = client.models.generate_content(model="gemini-1.5-flash", contents=[prompt, proses_image])
                result_text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(result_text)
                
                try: kalori_baru = int(data.get('kalori_kcal', 0))
                except: kalori_baru = 0
                nama_makanan = data.get('nama_makanan', 'Tidak diketahui')
                
                # 1. Simpan ke Database Google Sheets
                waktu_sekarang = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                sisa_terkini = kalori_harian - (total_dimakan + kalori_baru)
                
                sheet.append_row([waktu_sekarang, nama_makanan, kalori_baru, sisa_terkini])
                
                # 2. Simpan ke Memori UI
                st.session_state.hasil_gizi_v2 = data
                st.session_state.riwayat_makanan.append({"nama": nama_makanan, "kalori": kalori_baru})
                
                st.success("✅ Analisis berhasil dan data otomatis tersimpan ke Google Sheets!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan saat memproses: {e}")
    else:
        st.warning("⚠️ Silakan unggah atau ambil foto makanan terlebih dahulu!")

# ==================================
# TAMPILAN HASIL & RIWAYAT
# ==================================
if st.session_state.hasil_gizi_v2:
    data = st.session_state.hasil_gizi_v2
    st.markdown(f'<div class="card"><h2>🍽️ Hasil: {data.get("nama_makanan", "-")}</h2></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("🔥 Kalori", f"{data.get('kalori_kcal', 0)} kcal")
    with col2: st.metric("💪 Protein", f"{data.get('protein_g', 0)} g")
    with col3: st.metric("🍚 Karbo", f"{data.get('karbohidrat_g', 0)} g")
    with col4: st.metric("🥑 Lemak", f"{data.get('lemak_g', 0)} g")

if len(st.session_state.riwayat_makanan) > 0:
    st.markdown("---")
    st.markdown("### 📋 Riwayat Makananmu Hari Ini")
    for item in st.session_state.riwayat_makanan:
        st.markdown(f"- **{item['nama']}**: {item['kalori']} kcal")
        
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Cek Makanan Baru (Bersihkan Layar)"):
            st.session_state.hasil_gizi_v2 = None
            st.rerun()
    with col_btn2:
        if st.button("🗑️ Hapus Semua Riwayat Layar"):
            st.session_state.riwayat_makanan = []
            st.session_state.hasil_gizi_v2 = None
            st.rerun()

st.markdown('<br><br><center><p style="color:gray;">CekGizi AI Pro • Terhubung dengan Database</p></center>', unsafe_allow_html=True)
