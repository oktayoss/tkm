import streamlit as st
import random
import json
import os
import time
import pandas as pd # Tabloyu güzelleştirmek için

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Taş Kağıt Makas Arena", page_icon="🎮", layout="centered")

# --- CSS STİLLERİ (Kırmızı Yazı ve Tablo İçin) ---
st.markdown("""
<style>
    .dusunuyor {
        font-size: 24px;
        font-weight: bold;
        color: #FF0000; /* Kırmızı */
        text-align: center;
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
</style>
""", unsafe_allow_html=True)

# --- DOSYA VE VERİ İŞLEMLERİ ---
DOSYA_ADI = "skorlar.json"

def skor_yukle():
    if not os.path.exists(DOSYA_ADI):
        return {}
    try:
        with open(DOSYA_ADI, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def skor_kaydet(isim, zorluk):
    veriler = skor_yukle()
    if isim not in veriler:
        veriler[isim] = {"Kolay": 0, "Orta": 0, "Zor": 0}
    
    if zorluk in veriler[isim]:
        veriler[isim][zorluk] += 1
    else:
        veriler[isim][zorluk] = 1
    
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)

# --- RESİM GÖSTERME FONKSİYONU ---
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
if 'isim' not in st.session_state: st.session_state.isim = "Misafir"
if 'sonuc_mesaji' not in st.session_state: st.session_state.sonuc_mesaji = ""
if 'pc_secimi' not in st.session_state: st.session_state.pc_secimi = None
if 'oyuncu_secimi' not in st.session_state: st.session_state.oyuncu_secimi = None

# --- SAYFALAR ---

def giris_sayfasi():
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🗿 📜 ✂️ ARENA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Mobilden ve Bilgisayardan Oyna!</h3>", unsafe_allow_html=True)
    st.write("---")
    
    isim = st.text_input("Savaşçı İsmi:", max_chars=15, placeholder="Adını yaz...")
    zorluk = st.radio("Zorluk Seviyesi:", ["Kolay", "Orta", "Zor"], horizontal=True)
    hedef = st.radio("Kaçta Biter?", [3, 5, 7], horizontal=True)
    
    st.write("")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("OYUNA BAŞLA 🚀", use_container_width=True):
            if not isim: isim = "Misafir"
            st.session_state.isim = isim
            st.session_state.zorluk = zorluk
            st.session_state.hedef = hedef
            st.session_state.oyuncu_skor = 0
            st.session_state.pc_skor = 0
            st.session_state.sonuc_mesaji = "Hamleni Bekliyorum..."
            st.session_state.pc_secimi = None
            st.session_state.oyuncu_secimi = None
            st.session_state.sayfa = 'oyun'
            st.rerun()

    with col2:
        if st.button("🏆 LİDERLİK TABLOSU", use_container_width=True):
            st.session_state.sayfa = 'liderlik'
            st.rerun()

def liderlik_sayfasi():
    st.title("🏆 ŞAMPİYONLAR LİGİ")
    st.info("Puanlama: Kolay(1), Orta(5), Zor(10) Kupa Puanı kazandırır.")
    
    veriler = skor_yukle()
    
    if not veriler:
        st.warning("Henüz kayıt yok.")
    else:
        # Veriyi tablo formatına çeviriyoruz
        tablo_verisi = []
        for isim, detaylar in veriler.items():
            kolay = detaylar.get("Kolay", 0)
            orta = detaylar.get("Orta", 0)
            zor = detaylar.get("Zor", 0)
            # Kupa Hesabı
            toplam_kupa = (kolay * 1) + (orta * 5) + (zor * 10)
            
            tablo_verisi.append({
                "OYUNCU": isim,
                "KOLAY (1)": kolay,
                "ORTA (5)": orta,
                "ZOR (10)": zor,
                "🏆 TOPLAM KUPA": toplam_kupa
            })
        
        # Pandas ile tablo oluştur ve Kupa sayısına göre sırala (En yüksek en üstte)
        df = pd.DataFrame(tablo_verisi)
        df = df.sort_values(by="🏆 TOPLAM KUPA", ascending=False)
        
        # Tabloyu ekrana bas (Index numaralarını gizleyerek)
        st.table(df)

    st.write("---")
    if st.button("⬅️ Geri Dön"):
        st.session_state.sayfa = 'giris'
        st.rerun()

def oyun_sayfasi():
    # SKOR TABLOSU
    col_p1, col_vs, col_p2 = st.columns([4, 2, 4])
    with col_p1:
        st.markdown(f"<h3 style='text-align: center; color: #2196F3;'>{st.session_state.isim}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{st.session_state.oyuncu_skor}</h1>", unsafe_allow_html=True)
    with col_vs:
        st.markdown("<h3 style='text-align: center; padding-top: 20px;'>VS</h3>", unsafe_allow_html=True)
    with col_p2:
        st.markdown(f"<h3 style='text-align: center; color: #F44336;'>Yapay Zeka ({st.session_state.zorluk})</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{st.session_state.pc_skor}</h1>", unsafe_allow_html=True)
    
    st.progress(st.session_state.oyuncu_skor / st.session_state.hedef)
    
    # ORTA ALAN (Animasyon ve Sonuç Mesajı İçin Yer Tutucu)
    bilgi_kutusu = st.empty()
    
    # RESİMLERİN GÖSTERİMİ (Sol: Oyuncu, Sağ: PC)
    if st.session_state.oyuncu_secimi and st.session_state.pc_secimi:
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.markdown("<p style='text-align: center;'>Senin Seçimin</p>", unsafe_allow_html=True)
            resim_goster(st.session_state.oyuncu_secimi)
        with col_img2:
            st.markdown("<p style='text-align: center;'>Yapay Zeka</p>", unsafe_allow_html=True)
            resim_goster(st.session_state.pc_secimi)
            
    # Sonuç mesajını yazdır (Animasyon bitince burası güncel kalacak)
    if st.session_state.sonuc_mesaji:
        bilgi_kutusu.info(st.session_state.sonuc_mesaji)

    st.write("---")
    st.markdown("<h4 style='text-align: center;'>Hamleni Seç:</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # BUTONLAR (Tıklayınca hamle_yap fonksiyonu çalışır)
    with col1:
        if st.button("🗿 TAŞ", use_container_width=True): hamle_islemleri("Taş", bilgi_kutusu)
    with col2:
        if st.button("📜 KAĞIT", use_container_width=True): hamle_islemleri("Kağıt", bilgi_kutusu)
    with col3:
        if st.button("✂️ MAKAS", use_container_width=True): hamle_islemleri("Makas", bilgi_kutusu)
    
    # ANA MENÜ
    st.write("")
    st.write("")
    if st.button("🏠 Pes Et / Ana Menü", use_container_width=True):
        st.session_state.sayfa = 'giris'
        st.rerun()

def hamle_islemleri(oyuncu_hamlesi, bilgi_kutusu_placeholder):
    # 1. Oyuncu hamlesini kaydet
    st.session_state.oyuncu_secimi = oyuncu_hamlesi
    st.session_state.pc_secimi = None # PC henüz seçmedi, gizle
    st.session_state.sonuc_mesaji = "" # Eski mesajı sil
    
    # 2. DÜŞÜNME ANİMASYONU (Kırmızı ve Hareketli)
    bilgi_kutusu_placeholder.markdown('<p class="dusunuyor">Yapay Zeka Düşünüyor...</p>', unsafe_allow_html=True)
    time.sleep(1.5) # 1.5 saniye bekle
    
    # 3. Yapay Zeka Mantığı
    secenekler = ["Taş", "Kağıt", "Makas"]
    kazanan_hamle = {"Taş": "Kağıt", "Kağıt": "Makas", "Makas": "Taş"}
    kaybeden_hamle = {"Taş": "Makas", "Kağıt": "Taş", "Makas": "Kağıt"}
    
    sans = random.randint(1, 100)
    zorluk = st.session_state.zorluk
    pc_hamlesi = random.choice(secenekler)
    
    if zorluk == "Kolay" and sans <= 40:
        pc_hamlesi = kaybeden_hamle[oyuncu_hamlesi]
    elif zorluk == "Zor" and sans <= 40:
        pc_hamlesi = kazanan_hamle[oyuncu_hamlesi]
        
    st.session_state.pc_secimi = pc_hamlesi
    
    # 4. Sonuç Kontrolü
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
        
    # 5. Oyun Bitti mi?
    if st.session_state.oyuncu_skor >= st.session_state.hedef:
        st.success(f"TEBRİKLER {st.session_state.isim.upper()}! ŞAMPİYON SENSİN! 🏆")
        skor_kaydet(st.session_state.isim, st.session_state.zorluk)
        time.sleep(3)
        st.session_state.sayfa = 'giris'
    elif st.session_state.pc_skor >= st.session_state.hedef:
        st.error("MAALESEF KAYBETTİN... 💀")
        time.sleep(3)
        st.session_state.sayfa = 'giris'
    
    st.rerun()

# --- UYGULAMAYI BAŞLAT ---
if st.session_state.sayfa == 'giris':
    giris_sayfasi()
elif st.session_state.sayfa == 'liderlik':
    liderlik_sayfasi()
elif st.session_state.sayfa == 'oyun':
    oyun_sayfasi()