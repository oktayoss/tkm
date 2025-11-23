import streamlit as st
import random
import json
import os
import time
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Taş Kağıt Makas Arena", page_icon="🗿", layout="centered")

# --- CSS STİLLERİ ---
st.markdown("""
<style>
    .dusunuyor { font-size: 24px; font-weight: bold; color: #e74c3c; text-align: center; animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .skor-kutu { background-color: #2c3e50; padding: 10px; border-radius: 10px; text-align: center; border: 2px solid #34495e; color: white; }
    .kazandi-box { background-color: #27ae60; color: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); }
    .kaybetti-box { background-color: #c0392b; color: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); }
    .ozellik-box { background-color: #8e44ad; color: white; padding: 10px; border-radius: 8px; text-align: center; margin-top: 5px; font-size: 14px; }
    .vs-text { font-size: 40px; font-weight: bold; color: #f39c12; text-align: center; font-family: 'Impact', sans-serif; }
    .sinif-aciklama { background-color: #16a085; padding: 10px; border-radius: 5px; font-size: 14px; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- AVATARLAR VE SINIFLAR ---
AVATARLAR = {
    "Okçu": "🏹",
    "Savaşçı": "⚔️",
    "Büyücü": "🔮"
}

SINIF_ACIKLAMALARI = {
    "Okçu": "🎯 **Keskin Göz:** Berabere biten turlarda, maç başına 1 kez beraberliği bozar ve turu kazanır. (İki taraf da Okçu ise etki etmez).",
    "Savaşçı": "🛡️ **Çelik İrade:** Her zorluk seviyesi (Kolay/Orta/Zor) için 1 kez kupa kaybetme cezası almazsın. Kalkanın her zorlukta birer kez seni korur.",
    "Büyücü": "✨ **Mana Koruması:** Kaybetsen bile Galibiyet Serin (Win Streak) hemen bozulmaz. Her seride 1 kez koruma hakkın vardır."
}

# --- DOSYA İSİMLERİ ---
SKOR_DOSYASI = "skorlar.json"
MAC_DOSYASI = "maclar.json"

# --- FONKSİYONLAR ---
def json_oku(dosya):
    if not os.path.exists(dosya): return {}
    try:
        with open(dosya, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def json_yaz(dosya, veri):
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

def resim_goster(hamle, genislik=130):
    dosya = f"{hamle.lower()}.png"
    if os.path.exists(dosya): st.image(dosya, width=genislik)
    else:
        emo = {"Taş": "🪨", "Kağıt": "📜", "Makas": "✂️"}
        st.markdown(f"<div style='font-size:50px; text-align:center;'>{emo.get(hamle, '❓')}</div>", unsafe_allow_html=True)

# --- PUANLAMA VE RPG MANTIĞI ---
def mac_sonu_hesapla(isim, avatar_rol, zorluk, hedef, sonuc):
    veriler = json_oku(SKOR_DOSYASI)
    if isim not in veriler: veriler[isim] = {}
    
    # Eksik verileri tamamla
    defaults = {
        "avatar_rol": avatar_rol, "toplam_kupa": 0, 
        "win_kolay": 0, "win_orta": 0, "win_zor": 0, 
        "streaks": {}, # "Kolay_3": 5
        "warrior_shields": {"Kolay": True, "Orta": True, "Zor": True}, # Savaşçı Kalkanları
        "mage_protection_used": {} # Hangi seride koruma kullanıldı?
    }
    for k, v in defaults.items():
        if k not in veriler[isim]: veriler[isim][k] = v
        
    veriler[isim]["avatar_rol"] = avatar_rol
    
    streak_key = f"{zorluk}_{hedef}"
    streak = veriler[isim]["streaks"].get(streak_key, 0)
    puan = 0
    ekstra = ""

    if sonuc == "kazandi":
        # İstatistik
        key_map = {"Kolay": "win_kolay", "Orta": "win_orta", "Zor": "win_zor"}
        veriler[isim][key_map[zorluk]] += 1
        
        # Puan
        base = {"Kolay": 1, "Orta": 5, "Zor": 10}
        carpan = {3: 1, 5: 2, 7: 3}
        puan = base[zorluk] * carpan[hedef]
        
        # Streak Artır
        streak += 1
        veriler[isim]["streaks"][streak_key] = streak
        
        # Bonus
        if streak > 3:
            puan += 1
            ekstra = f"(🔥 {streak}. Seri Bonusu: +1 Kupa)"
            
        # Büyücü korumasını yeni seri için resetlemeye gerek yok, seri bozulunca resetlenir.

    elif sonuc == "kaybetti":
        ozel_mesaj = ""
        
        # --- BÜYÜCÜ YETENEĞİ ---
        buyucu_korudu = False
        if avatar_rol == "Büyücü" and streak > 0:
            # Bu seri için koruma kullanıldı mı?
            # Basit mantık: Her seri için 1 hak. 
            # JSON'da 'mage_active' tutmak yerine şans faktörü gibi: "1 kereliğine" dediğin için
            # Eğer streak > 0 ise ve henüz sıfırlanmadıysa koru.
            # Kod karmaşasını önlemek için: Büyücü kaybedince streak hemen 0 olmaz, 1 azalır veya kalır.
            # İsteğin: "1 kereliğine winstreak bozulmayacak"
            
            # Koruma anahtarı
            protection_key = f"{streak_key}_protected"
            if not veriler[isim].get(protection_key, False):
                # Koru!
                buyucu_korudu = True
                veriler[isim][protection_key] = True # Bu seri için hakkını kullandı
                ekstra += "✨ Büyücü Kalkanı: Seri Bozulmadı!"
            else:
                # Hakkı bitmiş, seri bozulur
                streak = 0
                veriler[isim][protection_key] = False # Reset
        else:
            streak = 0 # Diğer sınıflar direkt sıfırlanır
        
        veriler[isim]["streaks"][streak_key] = streak

        # --- CEZA HESAPLAMA ---
        ceza_map = {
            "Kolay": {3: -6, 5: -3, 7: -1},
            "Orta": {3: -3, 5: -2, 7: -1},
            "Zor": {3: -1, 5: -1, 7: -1}
        }
        puan = ceza_map.get(zorluk, {}).get(hedef, -1)
        
        # --- SAVAŞÇI YETENEĞİ ---
        if avatar_rol == "Savaşçı":
            # Kalkan var mı?
            shields = veriler[isim].get("warrior_shields", {"Kolay": True, "Orta": True, "Zor": True})
            if shields.get(zorluk, True):
                # Kalkanı kullan
                puan = 0
                shields[zorluk] = False
                veriler[isim]["warrior_shields"] = shields
                ekstra += f"🛡️ Savaşçı Kalkanı: {zorluk} Modunda Cezayı Engelledi!"
            else:
                pass # Kalkan bitmiş, ceza ye

    veriler[isim]["toplam_kupa"] += puan
    json_yaz(SKOR_DOSYASI, veriler)
    return puan, ekstra, streak

# --- STATE ---
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'avatar_sec'
if 'isim' not in st.session_state: st.session_state.isim = ""
if 'avatar_rol' not in st.session_state: st.session_state.avatar_rol = None # Okçu, Büyücü vs.
if 'avatar_ikon' not in st.session_state: st.session_state.avatar_ikon = None

# AI Değişkenleri
if 'oyuncu_skor' not in st.session_state: st.session_state.oyuncu_skor = 0
if 'pc_skor' not in st.session_state: st.session_state.pc_skor = 0
if 'ai_oyun_bitti' not in st.session_state: st.session_state.ai_oyun_bitti = False
if 'ai_sonuc_html' not in st.session_state: st.session_state.ai_sonuc_html = ""
if 'p_hamle_ai' not in st.session_state: st.session_state.p_hamle_ai = None
if 'pc_hamle_ai' not in st.session_state: st.session_state.pc_hamle_ai = None
if 'ai_mesaj' not in st.session_state: st.session_state.ai_mesaj = ""
if 'okcu_beraberlik_kullandi' not in st.session_state: st.session_state.okcu_beraberlik_kullandi = False

# PVP Değişkenleri
if 'oda_kodu' not in st.session_state: st.session_state.oda_kodu = None

# --- SAYFALAR ---

def avatar_secim_sayfasi():
    st.title("🛡️ Sınıfını Seç")
    isim_giris = st.text_input("Savaşçı Adı:", value=st.session_state.isim, max_chars=15)
    st.write("---")
    
    cols = st.columns(3)
    for i, (rol, ikon) in enumerate(AVATARLAR.items()):
        with cols[i % 3]:
            # Kart Görünümü
            st.markdown(f"<div style='font-size:40px; text-align:center;'>{ikon}</div>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='text-align:center;'>{rol}</h4>", unsafe_allow_html=True)
            st.info(SINIF_ACIKLAMALARI[rol])
            
            if st.button(f"SEÇ: {rol}", key=f"btn_{rol}", use_container_width=True):
                if not isim_giris: st.error("İsim gir!")
                else:
                    st.session_state.isim = isim_giris
                    st.session_state.avatar_rol = rol
                    st.session_state.avatar_ikon = ikon
                    st.session_state.sayfa = 'ana_menu'
                    st.rerun()

def ana_menu():
    st.markdown(f"<h1 style='text-align: center;'>🗿 📜 ✂️ TAŞ-KAĞIT-MAKAS ARENA</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>{st.session_state.avatar_ikon} {st.session_state.isim} ({st.session_state.avatar_rol})</h3>", unsafe_allow_html=True)
    
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🤖 Tek Kişilik")
        if st.button("YAPAY ZEKA İLE OYNA", use_container_width=True):
            st.session_state.sayfa = 'ai_giris'
            st.rerun()
            
    with col2:
        st.markdown("### 👥 Çok Oyunculu")
        if st.button("KARŞILIKLI SAVAŞ (ONLINE)", use_container_width=True):
            st.session_state.sayfa = 'pvp_giris'
            st.rerun()

    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏆 LİDERLİK TABLOSU", use_container_width=True):
            st.session_state.sayfa = 'liderlik'
            st.rerun()
    with c2:
        if st.button("⬅️ Karakter Değiştir", use_container_width=True):
            st.session_state.sayfa = 'avatar_sec'
            st.rerun()

# --- AI BÖLÜMÜ ---
def ai_giris():
    st.markdown("<h2 style='text-align:center'>🤖 Yapay Zeka Ayarları</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        zorluk = st.radio("Zorluk Seviyesi:", ["Kolay", "Orta", "Zor"], horizontal=True)
    with col2:
        hedef = st.radio("Maç Türü (Bo):", [3, 5, 7], format_func=lambda x: f"Bo{x}", horizontal=True)
        st.caption("ℹ️ Bo3: 1x | Bo5: 2x | Bo7: 3x Puan")

    st.write("---")
    
    # Savaşçı Kalkan Bilgisi
    if st.session_state.avatar_rol == "Savaşçı":
        veriler = json_oku(SKOR_DOSYASI)
        if st.session_state.isim in veriler:
            shields = veriler[st.session_state.isim].get("warrior_shields", {})
            st.info(f"🛡️ Kalkan Durumu: Kolay:{shields.get('Kolay')} | Orta:{shields.get('Orta')} | Zor:{shields.get('Zor')}")

    if st.checkbox("🔥 Win Streak (Seri) Durumunu Göster"):
        veriler = json_oku(SKOR_DOSYASI)
        if st.session_state.isim in veriler:
            streaks = veriler[st.session_state.isim].get("streaks", {})
            if streaks:
                cols = st.columns(3)
                for i, (k, v) in enumerate(streaks.items()):
                    if v > 0: cols[i%3].success(f"{k}: {v} Seri")
            else: st.warning("Aktif serin yok.")

    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚔️ SAVAŞI BAŞLAT", use_container_width=True):
            st.session_state.ai_zorluk = zorluk
            st.session_state.ai_hedef = hedef
            st.session_state.oyuncu_skor = 0
            st.session_state.pc_skor = 0
            st.session_state.p_hamle_ai = None
            st.session_state.pc_hamle_ai = None
            st.session_state.ai_mesaj = "Hamleni Bekliyorum..."
            st.session_state.ai_oyun_bitti = False
            st.session_state.okcu_beraberlik_kullandi = False # Okçu reset
            st.session_state.sayfa = 'ai_oyun'
            st.rerun()
    with b2:
        if st.button("🏠 Ana Menü", use_container_width=True):
            st.session_state.sayfa = 'ana_menu'
            st.rerun()

def ai_oyun():
    # Skorlar
    c1, c2, c3 = st.columns([3, 1, 3])
    with c1:
        st.markdown(f"<div class='skor-kutu'><h3>{st.session_state.avatar_ikon} {st.session_state.isim}</h3><h1>{st.session_state.oyuncu_skor}</h1></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='skor-kutu'><h3>🤖 Yapay Zeka ({st.session_state.ai_zorluk})</h3><h1>{st.session_state.pc_skor}</h1></div>", unsafe_allow_html=True)

    st.progress(min(st.session_state.oyuncu_skor / st.session_state.ai_hedef, 1.0))

    # Bitiş Ekranı
    if st.session_state.ai_oyun_bitti:
        st.markdown(st.session_state.ai_sonuc_html, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 AYNI AYARLARLA TEKRAR", use_container_width=True):
                st.session_state.oyuncu_skor = 0
                st.session_state.pc_skor = 0
                st.session_state.p_hamle_ai = None
                st.session_state.pc_hamle_ai = None
                st.session_state.ai_mesaj = "Yeni maç başladı!"
                st.session_state.ai_oyun_bitti = False
                st.session_state.okcu_beraberlik_kullandi = False
                st.rerun()
        with col2:
            if st.button("🏠 ANA MENÜ", use_container_width=True):
                st.session_state.sayfa = 'ana_menu'
                st.rerun()
        return

    # Oyun Alanı
    bilgi = st.empty()
    
    if st.session_state.p_hamle_ai and st.session_state.pc_hamle_ai:
        ic1, ic2 = st.columns(2)
        with ic1:
            st.caption("Senin Hamlen")
            resim_goster(st.session_state.p_hamle_ai)
        with ic2:
            st.caption("Rakip Hamlesi")
            resim_goster(st.session_state.pc_hamle_ai)

    if st.session_state.ai_mesaj:
        bilgi.info(f"📢 {st.session_state.ai_mesaj}")

    st.write("---")
    
    col1, col2, col3 = st.columns(3)
    with col1: 
        if st.button("🗿 TAŞ", use_container_width=True): ai_hamle_yap("Taş", bilgi)
    with col2: 
        if st.button("📜 KAĞIT", use_container_width=True): ai_hamle_yap("Kağıt", bilgi)
    with col3: 
        if st.button("✂️ MAKAS", use_container_width=True): ai_hamle_yap("Makas", bilgi)

    st.write("")
    if st.button("🏳️ Pes Et / Ana Menü", use_container_width=True):
        st.session_state.sayfa = 'ana_menu'
        st.rerun()

def ai_hamle_yap(p_hamle, bilgi_placeholder):
    st.session_state.p_hamle_ai = p_hamle
    st.session_state.pc_hamle_ai = None
    st.session_state.ai_mesaj = ""
    
    bilgi_placeholder.markdown('<p class="dusunuyor">Yapay Zeka Strateji Kuruyor...</p>', unsafe_allow_html=True)
    time.sleep(1.2)
    
    secenekler = ["Taş", "Kağıt", "Makas"]
    kazanan = {"Taş": "Kağıt", "Kağıt": "Makas", "Makas": "Taş"}
    kaybeden = {"Taş": "Makas", "Kağıt": "Taş", "Makas": "Kağıt"}
    
    sans = random.randint(1, 100)
    pc_hamle = random.choice(secenekler)
    z = st.session_state.ai_zorluk
    
    if z == "Kolay" and sans <= 40: pc_hamle = kaybeden[p_hamle]
    elif z == "Zor" and sans <= 40: pc_hamle = kazanan[p_hamle]
    
    st.session_state.pc_hamle_ai = pc_hamle
    
    # --- SONUÇ MANTIĞI VE OKÇU YETENEĞİ ---
    tur_sonuc = ""
    
    if p_hamle == pc_hamle:
        # Okçu Yeteneği: İlk beraberlikte kazanır
        if st.session_state.avatar_rol == "Okçu" and not st.session_state.okcu_beraberlik_kullandi:
            st.session_state.oyuncu_skor += 1
            st.session_state.okcu_beraberlik_kullandi = True
            tur_sonuc = "kazandi"
            st.session_state.ai_mesaj = "🏹 OKÇU YETENEĞİ! Beraberliği bozdun ve kazandın!"
        else:
            tur_sonuc = "berabere"
            st.session_state.ai_mesaj = "🤝 BERABERE!"
            
    elif (p_hamle=="Taş" and pc_hamle=="Makas") or \
         (p_hamle=="Kağıt" and pc_hamle=="Taş") or \
         (p_hamle=="Makas" and pc_hamle=="Kağıt"):
        st.session_state.oyuncu_skor += 1
        tur_sonuc = "kazandi"
        st.session_state.ai_mesaj = "✅ KAZANDIN!"
    else:
        st.session_state.pc_skor += 1
        tur_sonuc = "kaybetti"
        st.session_state.ai_mesaj = "❌ KAYBETTİN!"
        
    # Maç Bitti mi?
    hedef = st.session_state.ai_hedef
    isim = st.session_state.isim
    avatar_rol = st.session_state.avatar_rol
    zorluk = st.session_state.ai_zorluk
    
    if st.session_state.oyuncu_skor >= hedef:
        degisim, ek_bilgi, streak = mac_sonu_hesapla(isim, avatar_rol, zorluk, hedef, "kazandi")
        st.session_state.ai_sonuc_html = f"""
        <div class='kazandi-box'>
            <h1>🏆 ZAFER SENİN!</h1>
            <h3>+{degisim} Kupa Kazandın</h3>
            <p>{ek_bilgi}</p>
            <p>Bu Moddaki Serin: {streak}</p>
        </div>
        """
        st.session_state.ai_oyun_bitti = True
        
    elif st.session_state.pc_skor >= hedef:
        degisim, ek_bilgi, streak = mac_sonu_hesapla(isim, avatar_rol, zorluk, hedef, "kaybetti")
        st.session_state.ai_sonuc_html = f"""
        <div class='kaybetti-box'>
            <h1>💀 MAĞLUBİYET...</h1>
            <h3>{degisim} Kupa</h3>
            <p>{ek_bilgi}</p>
        </div>
        """
        st.session_state.ai_oyun_bitti = True
    
    st.rerun()

# --- PVP (ONLINE) BÖLÜMÜ ---
def pvp_oda_olustur(kod, oyuncu_adi, avatar_ikon):
    maclar = json_oku(MAC_DOSYASI)
    maclar[kod] = {
        "p1": oyuncu_adi, "p1_avatar": avatar_ikon, "p1_hamle": None, "p1_puan": 0,
        "p2": None, "p2_avatar": None, "p2_hamle": None, "p2_puan": 0,
        "durum": "bekliyor", "son_mesaj": "Rakip bekleniyor..."
    }
    json_yaz(MAC_DOSYASI, maclar)

def pvp_odaya_katil(kod, oyuncu_adi, avatar_ikon):
    maclar = json_oku(MAC_DOSYASI)
    if kod in maclar and maclar[kod]["p2"] is None:
        maclar[kod]["p2"] = oyuncu_adi; maclar[kod]["p2_avatar"] = avatar_ikon
        maclar[kod]["durum"] = "oynaniyor"; maclar[kod]["son_mesaj"] = "Oyun Başladı!"
        json_yaz(MAC_DOSYASI, maclar)
        return True
    return False

def pvp_hamle_yap(kod, oyuncu_no, hamle):
    maclar = json_oku(MAC_DOSYASI)
    if kod in maclar:
        maclar[kod][f"{oyuncu_no}_hamle"] = hamle
        json_yaz(MAC_DOSYASI, maclar)

def pvp_kontrol_et(kod):
    maclar = json_oku(MAC_DOSYASI)
    if kod not in maclar: return None
    oda = maclar[kod]
    
    # İki taraf da hamle yaptıysa
    if oda["p1_hamle"] and oda["p2_hamle"]:
        p1h, p2h = oda["p1_hamle"], oda["p2_hamle"]
        
        # Sonuç
        if (p1h=="Taş" and p2h=="Makas") or (p1h=="Kağıt" and p2h=="Taş") or (p1h=="Makas" and p2h=="Kağıt"):
            oda["p1_puan"]+=1; oda["son_mesaj"]=f"{oda['p1']} kazandı! ({p1h} > {p2h})"
        elif p1h==p2h: oda["son_mesaj"]=f"Berabere! ({p1h})"
        else: 
            oda["p2_puan"]+=1; oda["son_mesaj"]=f"{oda['p2']} kazandı! ({p2h} > {p1h})"
        
        # Hamleleri sıfırla ama ekranda göstermek için "son_hamleler" diye kaydedelim
        oda["son_p1_goster"] = p1h
        oda["son_p2_goster"] = p2h
        oda["p1_hamle"]=None; oda["p2_hamle"]=None
        json_yaz(MAC_DOSYASI, maclar)
        
    return oda

def pvp_giris():
    st.markdown("<h2 style='text-align:center'>👥 Online Savaş</h2>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Oda Kur", "Katıl"])
    with tab1:
        if st.button("Yeni Oda Kod Al"):
            kod = str(random.randint(1000, 9999))
            pvp_oda_olustur(kod, st.session_state.isim, st.session_state.avatar_ikon)
            st.session_state.oda_kodu = kod; st.session_state.oyuncu_no = "p1"
            st.session_state.sayfa = 'pvp_lobi'; st.rerun()
    with tab2:
        gk = st.text_input("Oda Kodu:"); 
        if st.button("Katıl"):
            if pvp_odaya_katil(gk, st.session_state.isim, st.session_state.avatar_ikon):
                st.session_state.oda_kodu = gk; st.session_state.oyuncu_no = "p2"
                st.session_state.sayfa = 'pvp_lobi'; st.rerun()
    if st.button("Geri"): st.session_state.sayfa = 'ana_menu'; st.rerun()

def pvp_lobi():
    st.title(f"🔑 Oda Kodu: {st.session_state.oda_kodu}")
    
    # OTO YENİLEME (POLLING)
    oda = pvp_kontrol_et(st.session_state.oda_kodu)
    if oda['durum'] == "bekliyor":
        time.sleep(2) # 2 Saniye bekle
        st.rerun()    # Sayfayı yenile
    
    c1, c2 = st.columns(2)
    with c1: st.success(f"P1: {oda['p1']}")
    with c2: 
        if oda['p2']: st.success(f"P2: {oda['p2']}")
        else: st.warning("Rakip Bekleniyor...")
        
    if oda['durum']=="oynaniyor": st.session_state.sayfa='pvp_oyun'; st.rerun()
    if st.button("Çık"): st.session_state.sayfa='ana_menu'; st.rerun()

def pvp_oyun():
    kod=st.session_state.oda_kodu; ben=st.session_state.oyuncu_no; 
    oda=pvp_kontrol_et(kod)
    
    # OTO YENİLEME (Eğer rakip hamle yapmadıysa bekle ve yenile)
    rakip = "p2" if ben == "p1" else "p1"
    
    # Eğer ben hamle yaptım ama rakip yapmadıysa bekle
    if oda[f"{ben}_hamle"] and not oda[f"{rakip}_hamle"]:
        time.sleep(2)
        st.rerun()

    # Skorlar
    c1,c2,c3 = st.columns([3,1,3])
    with c1: st.markdown(f"<div class='skor-kutu'><h3>{oda['p1_avatar']} {oda['p1']}</h3><h1>{oda['p1_puan']}</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='skor-kutu'><h3>{oda['p2_avatar']} {oda['p2']}</h3><h1>{oda['p2_puan']}</h1></div>", unsafe_allow_html=True)
    
    st.info(f"Son Durum: {oda['son_mesaj']}")
    
    # Son Hamleleri Göster (Varsa)
    if "son_p1_goster" in oda:
        ic1, ic2 = st.columns(2)
        with ic1: 
            st.caption(f"{oda['p1']} Seçimi")
            resim_goster(oda['son_p1_goster'], 100)
        with ic2: 
            st.caption(f"{oda['p2']} Seçimi")
            resim_goster(oda['son_p2_goster'], 100)

    st.write("---")
    
    if oda[f"{ben}_hamle"]: 
        st.warning("Hamle yapıldı, rakip bekleniyor...")
        # Oto yenileme yukarıda yapılıyor
    else:
        st.write("Hamleni Seç:")
        b1,b2,b3=st.columns(3)
        if b1.button("🗿 TAŞ"): pvp_hamle_yap(kod,ben,"Taş"); st.rerun()
        if b2.button("📜 KAĞIT"): pvp_hamle_yap(kod,ben,"Kağıt"); st.rerun()
        if b3.button("✂️ MAKAS"): pvp_hamle_yap(kod,ben,"Makas"); st.rerun()
    
    st.write("---")
    if st.button("Çık"): st.session_state.sayfa='ana_menu'; st.rerun()

# --- LİDERLİK ---
def liderlik_sayfasi():
    st.title("🏆 ŞAMPİYONLAR LİGİ")
    veriler = json_oku(SKOR_DOSYASI)
    if not veriler: st.warning("Veri yok")
    else:
        l = []
        for i, d in veriler.items():
            l.append({
                "Rank": 0,
                "Avatar": d.get("avatar_rol", "Bilinmiyor"), # Rolü yazalım
                "Oyuncu": i,
                "🏆 Kupa": d.get("toplam_kupa", 0)
            })
        df = pd.DataFrame(l)
        if not df.empty:
            df = df.sort_values(by="🏆 Kupa", ascending=False)
            df["Rank"] = range(1, len(df) + 1)
            cols = ["Rank", "Avatar", "Oyuncu", "🏆 Kupa"]
            st.table(df[cols])
        else: st.warning("Veri yok")
        
    if st.button("🏠 Ana Menü"): st.session_state.sayfa = 'ana_menu'; st.rerun()

# --- YÖNLENDİRME ---
if st.session_state.sayfa == 'avatar_sec': avatar_secim_sayfasi()
elif st.session_state.sayfa == 'ana_menu': ana_menu()
elif st.session_state.sayfa == 'ai_giris': ai_giris()
elif st.session_state.sayfa == 'ai_oyun': ai_oyun()
elif st.session_state.sayfa == 'pvp_giris': pvp_giris()
elif st.session_state.sayfa == 'pvp_lobi': pvp_lobi()
elif st.session_state.sayfa == 'pvp_oyun': pvp_oyun()
elif st.session_state.sayfa == 'liderlik': liderlik_sayfasi()
