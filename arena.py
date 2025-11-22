import streamlit as st
import random
import json
import os
import time
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Taş Kağıt Makas Arena", page_icon="🎮", layout="centered")

# --- CSS STİLLERİ ---
st.markdown("""
<style>
    .dusunuyor {
        font-size: 24px; font-weight: bold; color: #FF0000; text-align: center;
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker { 50% { opacity: 0; } }
    
    .kazandi-box {
        background-color: #2ecc71; color: white; padding: 20px; border-radius: 15px;
        text-align: center; font-size: 30px; font-weight: bold; border: 3px solid white;
        box-shadow: 0px 0px 15px #2ecc71; margin-bottom: 20px;
    }
    .kaybetti-box {
        background-color: #e74c3c; color: white; padding: 20px; border-radius: 15px;
        text-align: center; font-size: 30px; font-weight: bold; border: 3px solid white;
        box-shadow: 0px 0px 15px #e74c3c; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- DOSYA İŞLEMLERİ ---
DOSYA_ADI = "skorlar.json"

def skor_yukle():
    if not os.path.exists(DOSYA_ADI):
        return {}
    try:
        with open(DOSYA_ADI, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def skor_guncelle(isim, zorluk, hedef, sonuc):
    veriler = skor_yukle()
    if isim not in veriler:
        veriler[isim] = {"Puan": 0} # Artık tek bir toplam puan tutuyoruz
    
    # Puan Hesaplama Mantığı
    puan_degisimi = 0
    
    if sonuc == "kazandi":
        # Temel Puanlar
        base_puan = {"Kolay": 1, "Orta": 5, "Zor": 10}
        # Çarpanlar (Bo3=x1, Bo5=x2, Bo7=x3)
        carpan = {3: 1, 5: 2, 7: 3}
        
        puan_degisimi = base_puan.get(zorluk, 1) * carpan.get(hedef, 1)
        
    elif sonuc == "kaybetti":
        # Ceza Puanları
        ceza = {"Kolay": -3, "Orta": -2, "Zor": -1}
        puan_degisimi = ceza.get(zorluk, -1)

    # Puanı güncelle (Eksiye düşebilir)
    veriler[isim]["Puan"] = veriler[isim].get("Puan", 0) + puan_degisimi
    
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)
        
    return puan_degisimi

# --- RESİM GÖSTERME ---
def resim_goster(hamle_ismi, genislik=150):
    dosya_adi = f"{hamle_ismi.lower()}.png"
    if os.path.exists(dosya_adi):
        st.image(dosya_adi, width=genislik)
    else:
        emojiler = {"Taş": "🪨", "Kağıt": "📜", "Makas": "✂️"}
        st.markdown(f"<h1 style='text-align: center;'>{emojiler.get(hamle_ismi, '?')}</h1>", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'giris'
if 'oyuncu_skor' not in st.session_state: st.session_state.oyuncu_skor = 0
if 'pc_skor' not in st.session_state: st.session_state.pc_skor = 0
if 'isim' not in st.session_state: st.session_state.isim = ""
if 'sonuc_mesaji' not in st.session_state: st.session_state.sonuc_mesaji = ""
if 'pc_secimi' not in st.session_state: st.session_state.pc_secimi = None
if 'oyuncu_secimi' not in st.session_state: st.session_state.oyuncu_secimi = None
if 'oyun_bitti' not in st.session_state: st.session_state.oyun_bitti = False
if 'mac_sonucu_metni' not in st.session_state: st.session_state.mac_sonucu_metni = ""

# --- SAYFALAR ---

def giris_sayfasi():
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🗿 📜 ✂️ ARENA</h1>", unsafe_allow_html=True)
    st.write("---")
    
    # İsim hafızada kalsın diye value=st.session_state.isim yapıyoruz
    girilen_isim = st.text_input("Savaşçı İsmi:", value=st.session_state.isim, max_chars=15, placeholder="Adını yaz...")
    
    col_ayar1, col_ayar2 = st.columns(2)
    with col_ayar1:
        zorluk = st.radio("Zorluk Seviyesi:", ["Kolay", "Orta", "Zor"], horizontal=True)
    with col_ayar2:
        hedef = st.radio("Kaçta Biter? (Set)", [3, 5, 7], horizontal=True)
        st.caption(f"3'lü set: x1 Puan | 5'li set: x2 Puan | 7'li set: x3 Puan")
    
    st.write("")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("OYUNA BAŞLA 🚀", use_container_width=True):
            st.session_state.isim = girilen_isim if girilen_isim else "Misafir"
            st.session_state.zorluk = zorluk
            st.session_state.hedef = hedef
            # Oyun verilerini sıfırla
            st.session_state.oyuncu_skor = 0
            st.session_state.pc_skor = 0
            st.session_state.sonuc_mesaji = "Hamleni Bekliyorum..."
            st.session_state.pc_secimi = None
            st.session_state.oyuncu_secimi = None
            st.session_state.oyun_bitti = False
            st.session_state.sayfa = 'oyun'
            st.rerun()

    with col2:
        if st.button("🏆 LİDERLİK TABLOSU", use_container_width=True):
            st.session_state.sayfa = 'liderlik'
            st.rerun()

def liderlik_sayfasi():
    st.title("🏆 ŞAMPİYONLAR LİGİ")
    veriler = skor_yukle()
    
    if not veriler:
        st.warning("Henüz kayıt yok.")
    else:
        tablo_verisi = []
        for isim, detaylar in veriler.items():
            puan = detaylar.get("Puan", 0)
            tablo_verisi.append({"OYUNCU": isim, "🏆 TOPLAM KUPA": puan})
        
        df = pd.DataFrame(tablo_verisi)
        df = df.sort_values(by="🏆 TOPLAM KUPA", ascending=False)
        st.table(df)

    if st.button("⬅️ Geri Dön"):
        st.session_state.sayfa = 'giris'
        st.rerun()

def oyun_sayfasi():
    # --- BAŞLIK VE SKOR ---
    col_p1, col_vs, col_p2 = st.columns([4, 2, 4])
    with col_p1:
        st.markdown(f"<h3 style='text-align: center; color: #2196F3;'>{st.session_state.isim}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{st.session_state.oyuncu_skor}</h1>", unsafe_allow_html=True)
    with col_vs:
        st.markdown("<h3 style='text-align: center; padding-top: 20px;'>VS</h3>", unsafe_allow_html=True)
    with col_p2:
        st.markdown(f"<h3 style='text-align: center; color: #F44336;'>Yapay Zeka ({st.session_state.zorluk})</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{st.session_state.pc_skor}</h1>", unsafe_allow_html=True)
    
    st.progress(min(st.session_state.oyuncu_skor / st.session_state.hedef, 1.0))
    
    # --- OYUN BİTTİYSE FİNAL EKRANI ---
    if st.session_state.oyun_bitti:
        st.markdown(st.session_state.mac_sonucu_metni, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 AYNI AYARLARLA TEKRAR OYNA", use_container_width=True):
                st.session_state.oyuncu_skor = 0
                st.session_state.pc_skor = 0
                st.session_state.pc_secimi = None
                st.session_state.oyuncu_secimi = None
                st.session_state.sonuc_mesaji = "Yeni maç başladı!"
                st.session_state.oyun_bitti = False
                st.rerun()
        with c2:
            if st.button("🏠 ANA MENÜYE DÖN", use_container_width=True):
                st.session_state.sayfa = 'giris'
                st.rerun()
        return # Oyun bittiyse aşağıdaki butonları gösterme

    # --- OYUN DEVAM EDİYORSA ---
    bilgi_kutusu = st.empty()
    
    if st.session_state.oyuncu_secimi and st.session_state.pc_secimi:
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.markdown("<p style='text-align: center;'>Senin Seçimin</p>", unsafe_allow_html=True)
            resim_goster(st.session_state.oyuncu_secimi)
        with col_img2:
            st.markdown("<p style='text-align: center;'>Yapay Zeka</p>", unsafe_allow_html=True)
            resim_goster(st.session_state.pc_secimi)
            
    if st.session_state.sonuc_mesaji:
        bilgi_kutusu.info(st.session_state.sonuc_mesaji)

    st.write("---")
    st.markdown("<h4 style='text-align: center;'>Hamleni Seç:</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗿 TAŞ", use_container_width=True): hamle_islemleri("Taş", bilgi_kutusu)
    with col2:
        if st.button("📜 KAĞIT", use_container_width=True): hamle_islemleri("Kağıt", bilgi_kutusu)
    with col3:
        if st.button("✂️ MAKAS", use_container_width=True): hamle_islemleri("Makas", bilgi_kutusu)
    
    st.write("")
    if st.button("Pes Et / Ana Menü", use_container_width=True):
        st.session_state.sayfa = 'giris'
        st.rerun()

def hamle_islemleri(oyuncu_hamlesi, bilgi_kutusu_placeholder):
    st.session_state.oyuncu_secimi = oyuncu_hamlesi
    st.session_state.pc_secimi = None
    st.session_state.sonuc_mesaji = ""
    
    bilgi_kutusu_placeholder.markdown('<p class="dusunuyor">Yapay Zeka Düşünüyor...</p>', unsafe_allow_html=True)
    time.sleep(1.5)
    
    secenekler = ["Taş", "Kağıt", "Makas"]
    kazanan_hamle = {"Taş": "Kağıt", "Kağıt": "Makas", "Makas": "Taş"}
    kaybeden_hamle = {"Taş": "Makas", "Kağıt": "Taş", "Makas": "Kağıt"}
    
    sans = random.randint(1, 100)
    zorluk = st.session_state.zorluk
    pc_hamlesi = random.choice(secenekler)
    
    if zorluk == "Kolay" and sans <= 40: pc_hamlesi = kaybeden_hamle[oyuncu_hamlesi]
    elif zorluk == "Zor" and sans <= 40: pc_hamlesi = kazanan_hamle[oyuncu_hamlesi]
        
    st.session_state.pc_secimi = pc_hamlesi
    
    if oyuncu_hamlesi == pc_hamlesi:
        st.session_state.sonuc_mesaji = f"🤝 BERABERE! İkiniz de {pc_hamlesi} yaptınız."
    elif (oyuncu_hamlesi == "Taş" and pc_hamlesi == "Makas") or \
         (oyuncu_hamlesi == "Kağıt" and pc_hamlesi == "Taş") or \
         (oyuncu_hamlesi == "Makas" and pc_hamlesi == "Kağıt"):
        st.session_state.oyuncu_skor += 1
        st.session_state.sonuc_mesaji = "✅ KAZANDIN!"
    else:
        st.session_state.pc_skor += 1
        st.session_state.sonuc_mesaji = "❌ KAYBETTİN..."
        
    # --- OYUN BİTİŞ KONTROLÜ ---
    if st.session_state.oyuncu_skor >= st.session_state.hedef:
        puan = skor_guncelle(st.session_state.isim, st.session_state.zorluk, st.session_state.hedef, "kazandi")
        st.session_state.mac_sonucu_metni = f"""
        <div class='kazandi-box'>
            KAZANDIN ŞAMPİYON 🏆<br>
            <span style='font-size:20px'>+{puan} Kupa Kazandın!</span>
        </div>
        """
        st.session_state.oyun_bitti = True
        
    elif st.session_state.pc_skor >= st.session_state.hedef:
        puan = skor_guncelle(st.session_state.isim, st.session_state.zorluk, st.session_state.hedef, "kaybetti")
        st.session_state.mac_sonucu_metni = f"""
        <div class='kaybetti-box'>
            KAYBETTİN EZİK 😂<br>
            <span style='font-size:20px'>{puan} Kupa Kaybettin...</span>
        </div>
        """
        st.session_state.oyun_bitti = True
    
    st.rerun()

# --- BAŞLAT ---
if st.session_state.sayfa == 'giris':
    giris_sayfasi()
elif st.session_state.sayfa == 'liderlik':
    liderlik_sayfasi()
elif st.session_state.sayfa == 'oyun':
    oyun_sayfasi()
