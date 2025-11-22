import streamlit as st
import random
import json
import os
import time
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Taş Kağıt Makas RPG", page_icon="⚔️", layout="centered")

# --- CSS STİLLERİ ---
st.markdown("""
<style>
    .dusunuyor { font-size: 24px; font-weight: bold; color: #FF0000; text-align: center; animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .kazandi-box { background-color: #2ecc71; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    .kaybetti-box { background-color: #e74c3c; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    .streak-box { background-color: #f1c40f; color: black; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-top: 5px; }
    .avatar-btn { font-size: 40px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# --- AVATAR LİSTESİ ---
AVATARLAR = {
    "Okçu (Kadın)": "🧝‍♀️",
    "Okçu (Erkek)": "🧝‍♂️",
    "Savaşçı (Kadın)": "⚔️👩",
    "Savaşçı (Erkek)": "⚔️👨",
    "Büyücü (Kadın)": "🧙‍♀️",
    "Büyücü (Erkek)": "🧙‍♂️"
}

# --- DOSYA İŞLEMLERİ ---
DOSYA_ADI = "skorlar.json"

def skor_yukle():
    if not os.path.exists(DOSYA_ADI): return {}
    try:
        with open(DOSYA_ADI, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def skor_kaydet(veriler):
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)

def mac_sonu_islemleri(isim, avatar, zorluk, hedef, sonuc):
    veriler = skor_yukle()
    
    # Kullanıcı yoksa oluştur
    if isim not in veriler:
        veriler[isim] = {
            "avatar": avatar, "toplam_kupa": 0,
            "win_kolay": 0, "win_orta": 0, "win_zor": 0,
            "streaks": {} # Örn: "Kolay_3": 2
        }
    
    # Avatarı güncelle (değiştirdiyse)
    veriler[isim]["avatar"] = avatar
    
    # Streak Anahtarı (Örn: "Kolay_3")
    streak_key = f"{zorluk}_{hedef}"
    mevcut_streak = veriler[isim]["streaks"].get(streak_key, 0)
    
    puan_degisimi = 0
    ekstra_bilgi = ""

    if sonuc == "kazandi":
        # 1. Kazanma Sayısını Artır
        key_map = {"Kolay": "win_kolay", "Orta": "win_orta", "Zor": "win_zor"}
        veriler[isim][key_map[zorluk]] += 1
        
        # 2. Temel Puan Hesapla (Bo3=x1, Bo5=x2, Bo7=x3)
        base_puan = {"Kolay": 1, "Orta": 5, "Zor": 10}
        carpan = {3: 1, 5: 2, 7: 3}
        kazanc = base_puan[zorluk] * carpan[hedef]
        
        # 3. Streak Kontrolü
        mevcut_streak += 1
        veriler[isim]["streaks"][streak_key] = mevcut_streak
        
        # 4.maç ve sonrası (yani 3 win üstü) ekstra puan
        if mevcut_streak > 3:
            kazanc += 1
            ekstra_bilgi = f"(🔥 {mevcut_streak}. Seri Bonusu: +1 Kupa)"
        
        puan_degisimi = kazanc

    elif sonuc == "kaybetti":
        # 1. Streak Sıfırla (Sadece bu moddaki)
        veriler[isim]["streaks"][streak_key] = 0
        
        # 2. Ceza Hesapla (İstediğin özel kurallar)
        ceza = 0
        if zorluk == "Kolay":
            if hedef == 3: ceza = -6
            elif hedef == 5: ceza = -3
            elif hedef == 7: ceza = -1
        elif zorluk == "Orta":
            if hedef == 3: ceza = -3
            elif hedef == 5: ceza = -2
            elif hedef == 7: ceza = -1
        elif zorluk == "Zor":
            ceza = -1 # Her aşamada -1
            
        puan_degisimi = ceza

    # Toplam Puanı İşle
    veriler[isim]["toplam_kupa"] += puan_degisimi
    skor_kaydet(veriler)
    
    return puan_degisimi, ekstra_bilgi, mevcut_streak

# --- RESİM FONKSİYONU ---
def resim_goster(hamle, genislik=150):
    # Resim yoksa emoji, varsa resmi gösterir
    dosya = f"{hamle.lower()}.png"
    if os.path.exists(dosya): st.image(dosya, width=genislik)
    else:
        emo = {"Taş": "🪨", "Kağıt": "📜", "Makas": "✂️"}
        st.markdown(f"<div style='font-size:60px; text-align:center;'>{emo[hamle]}</div>", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'avatar_sec'
if 'isim' not in st.session_state: st.session_state.isim = ""
if 'avatar' not in st.session_state: st.session_state.avatar = None
if 'oyuncu_skor' not in st.session_state: st.session_state.oyuncu_skor = 0
if 'pc_skor' not in st.session_state: st.session_state.pc_skor = 0
if 'oyun_bitti' not in st.session_state: st.session_state.oyun_bitti = False
if 'sonuc_html' not in st.session_state: st.session_state.sonuc_html = ""
if 'oyuncu_secimi' not in st.session_state: st.session_state.oyuncu_secimi = None
if 'pc_secimi' not in st.session_state: st.session_state.pc_secimi = None
if 'mesaj' not in st.session_state: st.session_state.mesaj = ""

# --- SAYFALAR ---

def avatar_secim_sayfasi():
    st.title("Karakterini Seç")
    st.write("Arenaya girmeden önce sınıfını belirle!")
    
    isim_giris = st.text_input("Kahraman İsmi:", value=st.session_state.isim, max_chars=15)
    
    st.write("---")
    cols = st.columns(3)
    avatarlar_list = list(AVATARLAR.items())
    
    for i, (rol, ikon) in enumerate(avatarlar_list):
        with cols[i % 3]:
            if st.button(f"{ikon}\n{rol}", use_container_width=True):
                if not isim_giris:
                    st.error("Lütfen önce bir isim gir!")
                else:
                    st.session_state.isim = isim_giris
                    st.session_state.avatar = ikon
                    st.session_state.sayfa = 'giris'
                    st.rerun()

def giris_sayfasi():
    st.markdown(f"<h1 style='text-align: center;'>⚔️ ARENA MENÜSÜ</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Hoşgeldin {st.session_state.avatar} {st.session_state.isim}</h3>", unsafe_allow_html=True)
    
    # Ayarlar
    c1, c2 = st.columns(2)
    with c1:
        zorluk = st.radio("Zorluk:", ["Kolay", "Orta", "Zor"], horizontal=True)
    with c2:
        hedef = st.radio("Set Türü:", [3, 5, 7], format_func=lambda x: f"Bo{x}", horizontal=True)
    
    # Win Streak Bilgisi Göster
    st.write("---")
    if st.checkbox("🔥 Aktif Galibiyet Serilerini (Win Streak) Göster"):
        veriler = skor_yukle()
        if st.session_state.isim in veriler:
            streaks = veriler[st.session_state.isim]["streaks"]
            if streaks:
                st.write("Mevcut Serilerin:")
                s_cols = st.columns(3)
                for i, (k, v) in enumerate(streaks.items()):
                    if v > 0:
                        mod, set_sayi = k.split('_')
                        s_cols[i%3].info(f"{mod} Bo{set_sayi}: {v} Seri 🔥")
            else:
                st.caption("Henüz aktif bir serin yok.")
    
    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("SAVAŞA BAŞLA ⚔️", use_container_width=True):
            st.session_state.zorluk = zorluk
            st.session_state.hedef = hedef
            st.session_state.oyuncu_skor = 0
            st.session_state.pc_skor = 0
            st.session_state.oyuncu_secimi = None
            st.session_state.pc_secimi = None
            st.session_state.mesaj = "Hamleni Bekliyorum..."
            st.session_state.oyun_bitti = False
            st.session_state.sayfa = 'oyun'
            st.rerun()
            
    with b2:
        if st.button("🏆 LİDERLİK TABLOSU", use_container_width=True):
            st.session_state.sayfa = 'liderlik'
            st.rerun()
            
    if st.button("⬅️ Karakter Değiştir"):
        st.session_state.sayfa = 'avatar_sec'
        st.rerun()

def liderlik_sayfasi():
    st.title("🏆 LİDERLİK TABLOSU")
    veriler = skor_yukle()
    
    if not veriler:
        st.warning("Henüz veri yok.")
    else:
        liste = []
        for isim, d in veriler.items():
            liste.append({
                "AVATAR": d.get("avatar", "👤"),
                "OYUNCU": isim,
                "KOLAY W": d.get("win_kolay", 0),
                "ORTA W": d.get("win_orta", 0),
                "ZOR W": d.get("win_zor", 0),
                "🏆 KUPA": d.get("toplam_kupa", 0)
            })
            
        df = pd.DataFrame(liste)
        # Kupaya göre sırala
        df = df.sort_values(by="🏆 KUPA", ascending=False)
        # Sıra numarası ekle (1., 2. ...)
        df.insert(0, "#", range(1, 1 + len(df)))
        
        st.table(df)
        
    if st.button("🏠 Ana Menü"):
        st.session_state.sayfa = 'giris'
        st.rerun()

def oyun_sayfasi():
    # Başlıklar
    c1, c2, c3 = st.columns([3,2,3])
    with c1:
        st.markdown(f"<h3 style='text-align:center; color:#2980b9'>{st.session_state.avatar} {st.session_state.isim}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center'>{st.session_state.oyuncu_skor}</h1>", unsafe_allow_html=True)
    with c2:
        st.markdown("<h3 style='text-align:center; margin-top:20px'>VS</h3>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<h3 style='text-align:center; color:#c0392b'>Yapay Zeka ({st.session_state.zorluk})</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center'>{st.session_state.pc_skor}</h1>", unsafe_allow_html=True)

    # İlerleme Çubuğu
    st.progress(min(st.session_state.oyuncu_skor / st.session_state.hedef, 1.0))

    # --- OYUN BİTTİ EKRANI ---
    if st.session_state.oyun_bitti:
        st.markdown(st.session_state.sonuc_html, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 AYNI AYARLARLA DEVAM", use_container_width=True):
                st.session_state.oyuncu_skor = 0
                st.session_state.pc_skor = 0
                st.session_state.oyuncu_secimi = None
                st.session_state.pc_secimi = None
                st.session_state.mesaj = "Yeni maç başladı!"
                st.session_state.oyun_bitti = False
                st.rerun()
        with col2:
            if st.button("🏠 ANA MENÜ", use_container_width=True):
                st.session_state.sayfa = 'giris'
                st.rerun()
        return

    # --- OYUN ALANI ---
    bilgi = st.empty()
    
    # Seçimleri Göster
    if st.session_state.oyuncu_secimi and st.session_state.pc_secimi:
        ic1, ic2 = st.columns(2)
        with ic1:
            st.caption("Senin Hamlen")
            resim_goster(st.session_state.oyuncu_secimi)
        with ic2:
            st.caption("Rakip Hamlesi")
            resim_goster(st.session_state.pc_secimi)
            
    if st.session_state.mesaj:
        bilgi.info(st.session_state.mesaj)

    st.write("---")
    
    # Hamle Butonları
    col1, col2, col3 = st.columns(3)
    with col1: 
        if st.button("🗿 TAŞ", use_container_width=True): hamle_yap("Taş", bilgi)
    with col2: 
        if st.button("📜 KAĞIT", use_container_width=True): hamle_yap("Kağıt", bilgi)
    with col3: 
        if st.button("✂️ MAKAS", use_container_width=True): hamle_yap("Makas", bilgi)

    st.write("")
    if st.button("🏳️ Pes Et / Çık", use_container_width=True):
        st.session_state.sayfa = 'giris'
        st.rerun()

def hamle_yap(oyuncu_hamle, bilgi_placeholder):
    st.session_state.oyuncu_secimi = oyuncu_hamle
    st.session_state.pc_secimi = None
    st.session_state.mesaj = ""
    
    # Animasyon
    bilgi_placeholder.markdown('<p class="dusunuyor">Yapay Zeka Düşünüyor...</p>', unsafe_allow_html=True)
    time.sleep(1.5)
    
    # Mantık
    secenekler = ["Taş", "Kağıt", "Makas"]
    kazanan = {"Taş": "Kağıt", "Kağıt": "Makas", "Makas": "Taş"}
    kaybeden = {"Taş": "Makas", "Kağıt": "Taş", "Makas": "Kağıt"}
    
    sans = random.randint(1, 100)
    pc_hamle = random.choice(secenekler)
    z = st.session_state.zorluk
    
    if z == "Kolay" and sans <= 40: pc_hamle = kaybeden[oyuncu_hamle]
    elif z == "Zor" and sans <= 40: pc_hamle = kazanan[oyuncu_hamle]
    
    st.session_state.pc_secimi = pc_hamle
    
    # Sonuç
    if oyuncu_hamle == pc_hamle:
        st.session_state.mesaj = "🤝 BERABERE!"
    elif (oyuncu_hamle=="Taş" and pc_hamle=="Makas") or \
         (oyuncu_hamle=="Kağıt" and pc_hamle=="Taş") or \
         (oyuncu_hamle=="Makas" and pc_hamle=="Kağıt"):
        st.session_state.oyuncu_skor += 1
        st.session_state.mesaj = "✅ KAZANDIN!"
    else:
        st.session_state.pc_skor += 1
        st.session_state.mesaj = "❌ KAYBETTİN..."
        
    # Maç Bitti mi?
    hedef = st.session_state.hedef
    isim = st.session_state.isim
    avatar = st.session_state.avatar
    zorluk = st.session_state.zorluk
    
    if st.session_state.oyuncu_skor >= hedef:
        degisim, ek_bilgi, streak = mac_sonu_islemleri(isim, avatar, zorluk, hedef, "kazandi")
        st.session_state.sonuc_html = f"""
        <div class='kazandi-box'>
            <h1>KAZANDIN ŞAMPİYON! 🏆</h1>
            <h3>+{degisim} Kupa</h3>
            <p>{ek_bilgi}</p>
            <div class='streak-box'>🔥 Bu modda galibiyet serin: {streak}</div>
        </div>
        """
        st.session_state.oyun_bitti = True
        
    elif st.session_state.pc_skor >= hedef:
        degisim, ek_bilgi, streak = mac_sonu_islemleri(isim, avatar, zorluk, hedef, "kaybetti")
        st.session_state.sonuc_html = f"""
        <div class='kaybetti-box'>
            <h1>KAYBETTİN EZİK! 😂</h1>
            <h3>{degisim} Kupa</h3>
            <p>Bu moddaki serin sıfırlandı.</p>
        </div>
        """
        st.session_state.oyun_bitti = True
    
    st.rerun()

# --- UYGULAMAYI YÖNLENDİR ---
if st.session_state.sayfa == 'avatar_sec':
    avatar_secim_sayfasi()
elif st.session_state.sayfa == 'giris':
    giris_sayfasi()
elif st.session_state.sayfa == 'liderlik':
    liderlik_sayfasi()
elif st.session_state.sayfa == 'oyun':
    oyun_sayfasi()
