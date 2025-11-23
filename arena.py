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
    .dusunuyor { font-size: 20px; font-weight: bold; color: #e74c3c; text-align: center; animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .skor-kutu { background-color: #2c3e50; padding: 10px; border-radius: 10px; text-align: center; border: 2px solid #34495e; color: white; }
    .kazandi-box { background-color: #27ae60; color: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); margin-bottom: 20px;}
    .kaybetti-box { background-color: #c0392b; color: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); margin-bottom: 20px;}
    .vs-text { font-size: 40px; font-weight: bold; color: #f39c12; text-align: center; font-family: 'Impact', sans-serif; }
    .savas-sozu { font-style: italic; font-size: 18px; margin-top: 10px; color: #ecf0f1; }
</style>
""", unsafe_allow_html=True)

# --- AVATARLAR VE SINIFLAR ---
AVATARLAR = {
    "Okçu": "🏹",
    "Savaşçı": "⚔️",
    "Büyücü": "🔮"
}

SINIF_ACIKLAMALARI = {
    "Okçu": "🎯 **Keskin Göz:** Berabere biten turlarda, maç başına 1 kez beraberliği bozar ve turu kazanır.",
    "Savaşçı": "🛡️ **Çelik İrade:** Her zorluk seviyesi için 1 kez kupa kaybetme cezası almazsın.",
    "Büyücü": "✨ **Mana Koruması:** Kaybetsen bile Galibiyet Serin (Win Streak) hemen bozulmaz."
}

# --- YARATICI SAVAŞ SÖZLERİ ---
SOZLER = {
    "kazandi": [
        "🔥 Arenada sesler yükseliyor, zafer senin!",
        "⚡ Efsanevi bir vuruş! Rakip neye uğradığını şaşırdı.",
        "🏆 Bu hamle tarih kitaplarına geçecek!",
        "💪 Gücünü hafife almışlardı, bedelini ödediler."
    ],
    "kaybetti": [
        "💀 Dikkatsiz bir an... Rakip affetmedi.",
        "🍂 Bugün şans senden yana değil, ama savaş bitmedi.",
        "🛡️ Savunman kırıldı! Daha güçlü dönmelisin.",
        "🌑 Karanlık üzerine çöktü, bir sonraki tur senin olsun."
    ],
    "berabere": [
        "⚔️ Kılıçlar çarpıştı, kıvılcımlar saçıldı! Kimse geri adım atmıyor.",
        "⚖️ Mükemmel bir denge! İki taraf da pes etmiyor.",
        "💨 Toz duman dağıldı ama kazanan yok. Savaş sürüyor!",
        "🤝 Denk güçlerin çarpışması! Nefesler tutuldu."
    ]
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

def rastgele_soz(durum):
    return random.choice(SOZLER.get(durum, [""]))

# --- PUANLAMA (AI MODU İÇİN) ---
def mac_sonu_hesapla_ai(isim, avatar_rol, zorluk, hedef, sonuc):
    veriler = json_oku(SKOR_DOSYASI)
    if isim not in veriler: veriler[isim] = {}
    
    defaults = {"avatar_rol": avatar_rol, "toplam_kupa": 0, "win_kolay": 0, "win_orta": 0, "win_zor": 0, "streaks": {}, "warrior_shields": {"Kolay": True, "Orta": True, "Zor": True}}
    for k, v in defaults.items():
        if k not in veriler[isim]: veriler[isim][k] = v
    veriler[isim]["avatar_rol"] = avatar_rol
    
    streak_key = f"{zorluk}_{hedef}"
    streak = veriler[isim]["streaks"].get(streak_key, 0)
    puan = 0
    ekstra = ""

    if sonuc == "kazandi":
        key_map = {"Kolay": "win_kolay", "Orta": "win_orta", "Zor": "win_zor"}
        veriler[isim][key_map[zorluk]] += 1
        base = {"Kolay": 1, "Orta": 5, "Zor": 10}
        carpan = {3: 1, 5: 2, 7: 3}
        puan = base[zorluk] * carpan[hedef]
        streak += 1
        veriler[isim]["streaks"][streak_key] = streak
        if streak > 3:
            puan += 1
            ekstra = f"(🔥 {streak}. Seri Bonusu: +1 Kupa)"
            
    elif sonuc == "kaybetti":
        streak = 0
        ceza_map = {"Kolay": {3: -6, 5: -3, 7: -1}, "Orta": {3: -3, 5: -2, 7: -1}, "Zor": {3: -1, 5: -1, 7: -1}}
        puan = ceza_map.get(zorluk, {}).get(hedef, -1)
        
        # Savaşçı Yeteneği
        if avatar_rol == "Savaşçı":
            shields = veriler[isim].get("warrior_shields", {"Kolay": True, "Orta": True, "Zor": True})
            if shields.get(zorluk, True):
                puan = 0; shields[zorluk] = False; veriler[isim]["warrior_shields"] = shields; ekstra += "🛡️ Savaşçı Kalkanı Cezayı Engelledi!"
        
        veriler[isim]["streaks"][streak_key] = streak

    veriler[isim]["toplam_kupa"] += puan
    json_yaz(SKOR_DOSYASI, veriler)
    return puan, ekstra, streak

# --- PUANLAMA (PVP MODU İÇİN) ---
def mac_sonu_hesapla_pvp(isim, avatar_rol, hedef_set, sonuc):
    # PvP'de zorluk olmadığı için sadece Set Türüne göre kupa veririz.
    # Bo3 -> +1, Bo5 -> +2, Bo7 -> +3
    veriler = json_oku(SKOR_DOSYASI)
    if isim not in veriler: veriler[isim] = {}
    if "toplam_kupa" not in veriler[isim]: veriler[isim]["toplam_kupa"] = 0
    if "avatar_rol" not in veriler[isim]: veriler[isim]["avatar_rol"] = avatar_rol
    
    # PvP için ayrı bir win sayacı tutabiliriz ama şimdilik toplam kupaya ekleyelim
    puan = 0
    if sonuc == "kazandi":
        if hedef_set == 3: puan = 1
        elif hedef_set == 5: puan = 2
        elif hedef_set == 7: puan = 3
    # Kaybedince PvP'de kupa düşmüyor (Arkadaş arası olduğu için), istenirse eklenebilir.
    
    veriler[isim]["toplam_kupa"] += puan
    json_yaz(SKOR_DOSYASI, veriler)
    return puan

# --- STATE ---
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'avatar_sec'
if 'isim' not in st.session_state: st.session_state.isim = ""
if 'avatar_rol' not in st.session_state: st.session_state.avatar_rol = None
if 'avatar_ikon' not in st.session_state: st.session_state.avatar_ikon = None

# AI
if 'oyuncu_skor' not in st.session_state: st.session_state.oyuncu_skor = 0
if 'pc_skor' not in st.session_state: st.session_state.pc_skor = 0
if 'ai_mesaj' not in st.session_state: st.session_state.ai_mesaj = ""
if 'ai_soz' not in st.session_state: st.session_state.ai_soz = ""
if 'ai_oyun_bitti' not in st.session_state: st.session_state.ai_oyun_bitti = False
if 'okcu_beraberlik_kullandi' not in st.session_state: st.session_state.okcu_beraberlik_kullandi = False
if 'p_hamle_ai' not in st.session_state: st.session_state.p_hamle_ai = None
if 'pc_hamle_ai' not in st.session_state: st.session_state.pc_hamle_ai = None

# PVP
if 'oda_kodu' not in st.session_state: st.session_state.oda_kodu = None

# --- SAYFALAR ---

def avatar_secim_sayfasi():
    st.title("🛡️ Sınıfını Seç")
    isim_giris = st.text_input("Savaşçı Adı:", value=st.session_state.isim, max_chars=15)
    st.write("---")
    cols = st.columns(3)
    for i, (rol, ikon) in enumerate(AVATARLAR.items()):
        with cols[i % 3]:
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
    if st.button("⬅️ Karakter Değiştir", use_container_width=True):
        st.session_state.sayfa = 'avatar_sec'
        st.rerun()

# --- AI MODU ---
def ai_giris():
    st.markdown("<h2 style='text-align:center'>🤖 Yapay Zeka Modu</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: zorluk = st.radio("Zorluk:", ["Kolay", "Orta", "Zor"], horizontal=True)
    with c2: hedef = st.radio("Set:", [3, 5, 7], format_func=lambda x: f"Bo{x}", horizontal=True)
    
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚔️ BAŞLA", use_container_width=True):
            st.session_state.ai_zorluk = zorluk; st.session_state.ai_hedef = hedef
            st.session_state.oyuncu_skor = 0; st.session_state.pc_skor = 0
            st.session_state.p_hamle_ai = None; st.session_state.pc_hamle_ai = None
            st.session_state.ai_mesaj = "Hamleni Bekliyorum..."; st.session_state.ai_soz = ""
            st.session_state.ai_oyun_bitti = False; st.session_state.okcu_beraberlik_kullandi = False
            st.session_state.sayfa = 'ai_oyun'; st.rerun()
    with c2:
        if st.button("🏆 Liderlik Tablosu", use_container_width=True):
            st.session_state.sayfa = 'liderlik_ai'; st.rerun()
    if st.button("Geri"): st.session_state.sayfa = 'ana_menu'; st.rerun()

def ai_oyun():
    c1, c2, c3 = st.columns([3, 1, 3])
    with c1: st.markdown(f"<div class='skor-kutu'><h3>{st.session_state.avatar_ikon}</h3><h1>{st.session_state.oyuncu_skor}</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='skor-kutu'><h3>🤖 {st.session_state.ai_zorluk}</h3><h1>{st.session_state.pc_skor}</h1></div>", unsafe_allow_html=True)
    st.progress(min(st.session_state.oyuncu_skor / st.session_state.ai_hedef, 1.0))
    
    if st.session_state.ai_oyun_bitti:
        # Sonuç Kutusu
        if st.session_state.oyuncu_skor >= st.session_state.ai_hedef:
            renk = "kazandi-box"; baslik = "🏆 ZAFER SENİN!"; 
        else:
            renk = "kaybetti-box"; baslik = "💀 MAĞLUBİYET..."; 

        st.markdown(f"<div class='{renk}'><h1>{baslik}</h1><p class='savas-sozu'>{st.session_state.ai_soz}</p></div>", unsafe_allow_html=True)
        st.markdown(st.session_state.ai_sonuc_html, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 AYNI AYARLARLA TEKRAR", use_container_width=True):
                st.session_state.oyuncu_skor = 0; st.session_state.pc_skor = 0
                st.session_state.p_hamle_ai = None; st.session_state.pc_hamle_ai = None
                st.session_state.ai_mesaj = "Yeni maç başladı!"; st.session_state.ai_soz = ""
                st.session_state.ai_oyun_bitti = False; st.session_state.okcu_beraberlik_kullandi = False
                st.rerun()
        with c2:
            if st.button("🏠 ANA MENÜ", use_container_width=True): st.session_state.sayfa = 'ana_menu'; st.rerun()
        return

    bilgi = st.empty()
    if st.session_state.p_hamle_ai:
        ic1, ic2 = st.columns(2)
        with ic1: st.caption("Sen"); resim_goster(st.session_state.p_hamle_ai)
        with ic2: st.caption("Rakip"); resim_goster(st.session_state.pc_hamle_ai)
    if st.session_state.ai_mesaj: 
        bilgi.info(st.session_state.ai_mesaj)
        if st.session_state.ai_soz: st.markdown(f"<p style='text-align:center; font-style:italic;'>{st.session_state.ai_soz}</p>", unsafe_allow_html=True)

    st.write("---")
    col1, col2, col3 = st.columns(3)
    with col1: 
        if st.button("🗿 TAŞ", use_container_width=True): ai_hamle_yap("Taş", bilgi)
    with col2: 
        if st.button("📜 KAĞIT", use_container_width=True): ai_hamle_yap("Kağıt", bilgi)
    with col3: 
        if st.button("✂️ MAKAS", use_container_width=True): ai_hamle_yap("Makas", bilgi)
    st.write("")
    if st.button("🏳️ Çık"): st.session_state.sayfa='ana_menu'; st.rerun()

def ai_hamle_yap(p_hamle, bilgi_placeholder):
    st.session_state.p_hamle_ai = p_hamle
    bilgi_placeholder.markdown('<p class="dusunuyor">Yapay Zeka Hamle Yapıyor...</p>', unsafe_allow_html=True)
    time.sleep(1)
    
    secenekler = ["Taş", "Kağıt", "Makas"]
    kazanan = {"Taş": "Kağıt", "Kağıt": "Makas", "Makas": "Taş"}
    kaybeden = {"Taş": "Makas", "Kağıt": "Taş", "Makas": "Kağıt"}
    
    sans = random.randint(1, 100)
    pc_hamle = random.choice(secenekler)
    z = st.session_state.ai_zorluk
    if z == "Kolay" and sans <= 40: pc_hamle = kaybeden[p_hamle]
    elif z == "Zor" and sans <= 40: pc_hamle = kazanan[p_hamle]
    st.session_state.pc_hamle_ai = pc_hamle
    
    durum = ""
    if p_hamle == pc_hamle:
        if st.session_state.avatar_rol == "Okçu" and not st.session_state.okcu_beraberlik_kullandi:
            st.session_state.oyuncu_skor+=1; st.session_state.okcu_beraberlik_kullandi=True; 
            durum="kazandi"; st.session_state.ai_mesaj="🏹 OKÇU YETENEĞİ! Kazandın!"
        else:
            durum="berabere"; st.session_state.ai_mesaj="🤝 BERABERE!"
    elif (p_hamle=="Taş" and pc_hamle=="Makas") or (p_hamle=="Kağıt" and pc_hamle=="Taş") or (p_hamle=="Makas" and pc_hamle=="Kağıt"):
        st.session_state.oyuncu_skor+=1; durum="kazandi"; st.session_state.ai_mesaj="✅ KAZANDIN!"
    else:
        st.session_state.pc_skor+=1; durum="kaybetti"; st.session_state.ai_mesaj="❌ KAYBETTİN!"
    
    st.session_state.ai_soz = rastgele_soz(durum)
    
    # Bitiş Kontrol
    h = st.session_state.ai_hedef
    if st.session_state.oyuncu_skor >= h:
        p, e, s = mac_sonu_hesapla_ai(st.session_state.isim, st.session_state.avatar_rol, z, h, "kazandi")
        st.session_state.ai_sonuc_html = f"<h3>+{p} Kupa Kazandın</h3><p>{e}</p>"
        st.session_state.ai_oyun_bitti = True
    elif st.session_state.pc_skor >= h:
        p, e, s = mac_sonu_hesapla_ai(st.session_state.isim, st.session_state.avatar_rol, z, h, "kaybetti")
        st.session_state.ai_sonuc_html = f"<h3>{p} Kupa Kaybettin</h3>"
        st.session_state.ai_oyun_bitti = True
    st.rerun()

# --- PVP MODU ---
def pvp_oda_olustur(kod, oyuncu_adi, avatar_ikon, hedef_skor):
    maclar = json_oku(MAC_DOSYASI)
    maclar[kod] = {
        "p1": oyuncu_adi, "p1_avatar": avatar_ikon, "p1_hamle": None, "p1_puan": 0,
        "p2": None, "p2_avatar": None, "p2_hamle": None, "p2_puan": 0,
        "durum": "bekliyor", "son_mesaj": "Rakip bekleniyor...",
        "hedef": hedef_skor # Bo3 ise 2, Bo5 ise 3, Bo7 ise 4 olmalı (İlk ulaşan kazanır)
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

def pvp_yeniden_baslat(kod):
    maclar = json_oku(MAC_DOSYASI)
    if kod in maclar:
        # Puanları ve hamleleri sıfırla, oyuncuları tut
        maclar[kod]["p1_puan"] = 0; maclar[kod]["p2_puan"] = 0
        maclar[kod]["p1_hamle"] = None; maclar[kod]["p2_hamle"] = None
        maclar[kod]["son_p1_goster"] = None; maclar[kod]["son_p2_goster"] = None
        maclar[kod]["son_mesaj"] = "Yeni Maç Başladı!"
        maclar[kod]["durum"] = "oynaniyor"
        json_yaz(MAC_DOSYASI, maclar)

def pvp_kontrol_et(kod):
    maclar = json_oku(MAC_DOSYASI)
    if kod not in maclar: return None
    oda = maclar[kod]
    
    if oda["p1_hamle"] and oda["p2_hamle"]:
        p1h, p2h = oda["p1_hamle"], oda["p2_hamle"]
        durum = ""
        if (p1h=="Taş" and p2h=="Makas") or (p1h=="Kağıt" and p2h=="Taş") or (p1h=="Makas" and p2h=="Kağıt"):
            oda["p1_puan"]+=1; oda["son_mesaj"]=f"{oda['p1']} kazandı! ({p1h} > {p2h})"; durum="kazandi"
        elif p1h==p2h: oda["son_mesaj"]=f"Berabere! ({p1h})"; durum="berabere"
        else: oda["p2_puan"]+=1; oda["son_mesaj"]=f"{oda['p2']} kazandı! ({p2h} > {p1h})"; durum="kaybetti" # p1 açısından
        
        # Savaş Sözü Ekle (Son mesaja ek olarak)
        soz = rastgele_soz(durum if durum != "kaybetti" else "kazandi") # Rastgele pozitif bir söz koyalım heyecan olsun
        oda["son_mesaj"] += f" {soz}"

        oda["son_p1_goster"] = p1h; oda["son_p2_goster"] = p2h
        oda["p1_hamle"]=None; oda["p2_hamle"]=None
        json_yaz(MAC_DOSYASI, maclar)
    return oda

def pvp_giris():
    st.markdown("<h2 style='text-align:center'>👥 Online Savaş</h2>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Oda Kur", "Katıl"])
    with tab1:
        # Hedef Seçimi (Bo3, Bo5, Bo7)
        hedef_secim = st.radio("Set Sayısı:", [3, 5, 7], format_func=lambda x: f"Bo{x}", horizontal=True)
        st.caption(f"Bo{hedef_secim}: {hedef_secim//2 + 1} olan kazanır.")
        
        if st.button("Yeni Oda Oluştur (+Kod Al)"):
            kod = str(random.randint(1000, 9999))
            hedef_skor = (hedef_secim // 2) + 1 # 3->2, 5->3, 7->4
            pvp_oda_olustur(kod, st.session_state.isim, st.session_state.avatar_ikon, hedef_skor)
            st.session_state.oda_kodu = kod; st.session_state.oyuncu_no = "p1"; st.session_state.pvp_hedef_set = hedef_secim
            st.session_state.sayfa = 'pvp_lobi'; st.rerun()
    with tab2:
        gk = st.text_input("Oda Kodu:"); 
        if st.button("Katıl"):
            if pvp_odaya_katil(gk, st.session_state.isim, st.session_state.avatar_ikon):
                st.session_state.oda_kodu = gk; st.session_state.oyuncu_no = "p2"
                # Hedef bilgisi odadan gelecek ama session'da tutmaya gerek yok, oda bilgisinde var
                st.session_state.sayfa = 'pvp_lobi'; st.rerun()
            else: st.error("Oda bulunamadı!")

    st.write("---")
    if st.button("🏆 Liderlik Tablosu"): st.session_state.sayfa = 'liderlik_pvp'; st.rerun()
    if st.button("Geri"): st.session_state.sayfa = 'ana_menu'; st.rerun()

def pvp_lobi():
    st.title(f"🔑 Oda Kodu: {st.session_state.oda_kodu}")
    oda = pvp_kontrol_et(st.session_state.oda_kodu)
    
    if oda['durum'] == "bekliyor": time.sleep(2); st.rerun()
    
    c1, c2 = st.columns(2)
    with c1: st.success(f"P1: {oda['p1']}")
    with c2: 
        if oda['p2']: st.success(f"P2: {oda['p2']}")
        else: st.warning("Rakip Bekleniyor...")
        
    if oda['durum']=="oynaniyor": st.session_state.sayfa='pvp_oyun'; st.rerun()
    if st.button("Çık"): st.session_state.sayfa='ana_menu'; st.rerun()

def pvp_oyun():
    kod=st.session_state.oda_kodu; ben=st.session_state.oyuncu_no; oda=pvp_kontrol_et(kod)
    rakip = "p2" if ben == "p1" else "p1"
    
    # Oto Yenileme
    if oda[f"{ben}_hamle"] and not oda[f"{rakip}_hamle"]: time.sleep(2); st.rerun()

    # Skorlar
    c1,c2,c3 = st.columns([3,1,3])
    with c1: st.markdown(f"<div class='skor-kutu'><h3>{oda['p1_avatar']} {oda['p1']}</h3><h1>{oda['p1_puan']}</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='skor-kutu'><h3>{oda['p2_avatar']} {oda['p2']}</h3><h1>{oda['p2_puan']}</h1></div>", unsafe_allow_html=True)
    
    st.progress(min(max(oda['p1_puan'], oda['p2_puan']) / oda['hedef'], 1.0))
    st.info(f"📢 {oda['son_mesaj']}")
    
    # Son Hamleler
    if "son_p1_goster" in oda and oda["son_p1_goster"]:
        ic1, ic2 = st.columns(2)
        with ic1: st.caption(f"{oda['p1']}"); resim_goster(oda['son_p1_goster'], 80)
        with ic2: st.caption(f"{oda['p2']}"); resim_goster(oda['son_p2_goster'], 80)

    # --- OYUN SONU KONTROLÜ ---
    kazanan_kim = None
    if oda['p1_puan'] >= oda['hedef']: kazanan_kim = "p1"
    elif oda['p2_puan'] >= oda['hedef']: kazanan_kim = "p2"

    if kazanan_kim:
        st.write("---")
        if kazanan_kim == ben:
            st.markdown(f"<div class='kazandi-box'><h1>🏆 KAZANDIN!</h1><p>{rastgele_soz('kazandi')}</p></div>", unsafe_allow_html=True)
            # Puanı sadece 1 kere eklemek lazım. Basitlik için burada ekliyoruz ama sayfa yenilendikçe eklenmemesi için kontrol gerek.
            # Streamlit yapısında veritabanı dışı kontrol zor, o yüzden sadece görsel gösteriyoruz.
            # Gerçek kaydı 'mac_sonu_hesapla_pvp' ile yapabiliriz ama sonsuz döngüden kaçınmak lazım.
            # Şimdilik sadece görsel mesaj ve rövanş.
        else:
            st.markdown(f"<div class='kaybetti-box'><h1>💀 KAYBETTİN...</h1><p>{rastgele_soz('kaybetti')}</p></div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 RÖVANŞ YAP"):
                # Puan Ver (Sadece kazanan basınca değil, maç bitince verilmeli aslında ama basitlik için geçiyoruz)
                # Kupa Hesabı: Bo3=1, Bo5=2, Bo7=3. Hedef skor 2 ise Bo3'tür.
                hedef = oda['hedef']
                set_turu = 3 if hedef == 2 else (5 if hedef == 3 else 7)
                if kazanan_kim == ben:
                    puan = mac_sonu_hesapla_pvp(st.session_state.isim, st.session_state.avatar_rol, set_turu, "kazandi")
                    st.success(f"+{puan} Kupa Eklendi!")
                
                pvp_yeniden_baslat(kod)
                st.rerun()
        with c2:
            if st.button("🏠 Ana Menü"): st.session_state.sayfa='ana_menu'; st.rerun()
        return

    st.write("---")
    if oda[f"{ben}_hamle"]: 
        st.warning("Hamle yapıldı, rakip bekleniyor...")
    else:
        st.write("Hamleni Seç:")
        b1,b2,b3=st.columns(3)
        if b1.button("🗿 TAŞ"): pvp_hamle_yap(kod,ben,"Taş"); st.rerun()
        if b2.button("📜 KAĞIT"): pvp_hamle_yap(kod,ben,"Kağıt"); st.rerun()
        if b3.button("✂️ MAKAS"): pvp_hamle_yap(kod,ben,"Makas"); st.rerun()
    
    st.write("---")
    if st.button("Çık"): st.session_state.sayfa='ana_menu'; st.rerun()

# --- LİDERLİK TABLOSU ---
def liderlik_sayfasi(geri_don_sayfa):
    st.title("🏆 ŞAMPİYONLAR LİGİ")
    veriler = json_oku(SKOR_DOSYASI)
    if not veriler: st.warning("Veri yok")
    else:
        l = []
        for isim, d in veriler.items():
            # Emojiyi bulmak için rolü kullan
            rol = d.get("avatar_rol", "Bilinmiyor")
            ikon = AVATARLAR.get(rol, "👤")
            
            l.append({
                "Rank": 0,
                "Avatar": ikon, # Artık emoji gözükecek
                "Oyuncu": isim,
                "🏆 Kupa": d.get("toplam_kupa", 0)
            })
        df = pd.DataFrame(l)
        if not df.empty:
            df = df.sort_values(by="🏆 Kupa", ascending=False)
            df["Rank"] = range(1, len(df) + 1)
            cols = ["Rank", "Avatar", "Oyuncu", "🏆 Kupa"]
            st.table(df[cols])
        else: st.warning("Veri yok")
        
    if st.button("🏠 Geri Dön"): st.session_state.sayfa = geri_don_sayfa; st.rerun()

# --- YÖNLENDİRME ---
if st.session_state.sayfa == 'avatar_sec': avatar_secim_sayfasi()
elif st.session_state.sayfa == 'ana_menu': ana_menu()
elif st.session_state.sayfa == 'ai_giris': ai_giris()
elif st.session_state.sayfa == 'ai_oyun': ai_oyun()
elif st.session_state.sayfa == 'pvp_giris': pvp_giris()
elif st.session_state.sayfa == 'pvp_lobi': pvp_lobi()
elif st.session_state.sayfa == 'pvp_oyun': pvp_oyun()
elif st.session_state.sayfa == 'liderlik_ai': liderlik_sayfasi('ai_giris')
elif st.session_state.sayfa == 'liderlik_pvp': liderlik_sayfasi('pvp_giris')
