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
    .kupa-gosterge { background-color: #f1c40f; color: black; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; margin-bottom: 10px; }
    .kalkan-aktif { color: #2ecc71; font-weight: bold; }
    .kalkan-kirik { color: #e74c3c; font-weight: bold; text-decoration: line-through; }
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
        "Arenada sesler yükseliyor, zafer senin!",
        "Efsanevi bir vuruş! Rakip neye uğradığını şaşırdı.",
        "Bu hamle tarih kitaplarına geçecek!",
        "Gücünü hafife almışlardı, bedelini ödediler."
    ],
    "kaybetti": [
        "Dikkatsiz bir an... Rakip affetmedi.",
        "Bugün şans senden yana değil, ama savaş bitmedi.",
        "Savunman kırıldı! Daha güçlü dönmelisin.",
        "Karanlık üzerine çöktü, bir sonraki tur senin olsun."
    ],
    "berabere": [
        "Kılıçlar çarpıştı, kıvılcımlar saçıldı! Kimse geri adım atmıyor.",
        "Mükemmel bir denge! İki taraf da pes etmiyor.",
        "Toz duman dağıldı ama kazanan yok. Savaş sürüyor!"
    ]
}

# --- DOSYA İSİMLERİ ---
# Not: Dosya ismini değiştirdik ki herkes sıfırdan başlasın (Log silme işlemi)
SKOR_DOSYASI = "skorlar_v2.json" 
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

def get_player_data(isim):
    veriler = json_oku(SKOR_DOSYASI)
    if isim not in veriler:
        return None
    return veriler[isim]

# --- PUANLAMA (AI MODU) ---
def mac_sonu_hesapla_ai(isim, avatar_rol, zorluk, hedef, sonuc):
    veriler = json_oku(SKOR_DOSYASI)
    if isim not in veriler: veriler[isim] = {}
    
    # AI verilerini başlat
    if "ai" not in veriler[isim]:
        veriler[isim]["ai"] = {"toplam_kupa": 0, "streaks": {}, "warrior_shields": {"Kolay": True, "Orta": True, "Zor": True}, "wins": {"Kolay":0, "Orta":0, "Zor":0}}
    
    # Genel avatar güncelle
    veriler[isim]["avatar_rol"] = avatar_rol
    
    player_ai = veriler[isim]["ai"]
    streak_key = f"{zorluk}_{hedef}"
    streak = player_ai["streaks"].get(streak_key, 0)
    puan = 0
    streak_mesaj = ""

    if sonuc == "kazandi":
        player_ai["wins"][zorluk] += 1
        base = {"Kolay": 1, "Orta": 5, "Zor": 10}
        carpan = {3: 1, 5: 2, 7: 3}
        puan = base[zorluk] * carpan[hedef]
        
        streak += 1
        streak_mesaj = f"🔥 Seri Devam Ediyor: {streak}"
        if streak > 3:
            puan += 1
            streak_mesaj += " (+1 Bonus Kupa)"
            
    elif sonuc == "kaybetti":
        old_streak = streak
        streak = 0
        ceza_map = {"Kolay": {3: -6, 5: -3, 7: -1}, "Orta": {3: -3, 5: -2, 7: -1}, "Zor": {3: -1, 5: -1, 7: -1}}
        puan = ceza_map.get(zorluk, {}).get(hedef, -1)
        
        # Savaşçı Yeteneği
        kalkan_korudu = False
        if avatar_rol == "Savaşçı":
            shields = player_ai.get("warrior_shields", {"Kolay": True, "Orta": True, "Zor": True})
            if shields.get(zorluk, True):
                puan = 0
                shields[zorluk] = False
                player_ai["warrior_shields"] = shields
                streak_mesaj = "🛡️ Kalkan Kırıldı ama Ceza Engellendi!"
                kalkan_korudu = True
        
        if not kalkan_korudu:
            if old_streak > 0: streak_mesaj = f"❄️ Seri Bozuldu (Eski Seri: {old_streak})"
            else: streak_mesaj = ""

    player_ai["streaks"][streak_key] = streak
    player_ai["toplam_kupa"] += puan
    veriler[isim]["ai"] = player_ai
    
    json_yaz(SKOR_DOSYASI, veriler)
    return puan, streak_mesaj

# --- PUANLAMA (PVP MODU) ---
def mac_sonu_hesapla_pvp(isim, avatar_rol, hedef_set, sonuc):
    veriler = json_oku(SKOR_DOSYASI)
    if isim not in veriler: veriler[isim] = {}
    
    # PvP verilerini başlat
    if "pvp" not in veriler[isim]:
        veriler[isim]["pvp"] = {"toplam_kupa": 0}
        
    veriler[isim]["avatar_rol"] = avatar_rol
    
    puan = 0
    if sonuc == "kazandi":
        if hedef_set == 3: puan = 1
        elif hedef_set == 5: puan = 2
        elif hedef_set == 7: puan = 3
    
    veriler[isim]["pvp"]["toplam_kupa"] += puan
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
            st.session_state.sayfa = 'ai_giris'; st.rerun()
    with col2:
        st.markdown("### 👥 Çok Oyunculu")
        if st.button("KARŞILIKLI SAVAŞ (ONLINE)", use_container_width=True):
            st.session_state.sayfa = 'pvp_giris'; st.rerun()
    st.write("---")
    if st.button("⬅️ Karakter Değiştir", use_container_width=True):
        st.session_state.sayfa = 'avatar_sec'; st.rerun()

# --- AI MODU ---
def ai_giris():
    st.markdown("<h2 style='text-align:center'>🤖 Yapay Zeka Modu</h2>", unsafe_allow_html=True)
    
    # Anlık Kupa Göstergesi (AI)
    data = get_player_data(st.session_state.isim)
    kupa = data.get("ai", {}).get("toplam_kupa", 0) if data else 0
    st.markdown(f"<div class='kupa-gosterge'>🏆 Mevcut AI Kupan: {kupa}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: zorluk = st.radio("Zorluk Seviyesi:", ["Kolay", "Orta", "Zor"], horizontal=True)
    with c2: hedef = st.radio("Maç Türü (Bo):", [3, 5, 7], format_func=lambda x: f"Bo{x}", horizontal=True)
    
    # Savaşçı Kalkan Bilgisi
    if st.session_state.avatar_rol == "Savaşçı" and data and "ai" in data:
        shields = data["ai"].get("warrior_shields", {"Kolay": True, "Orta": True, "Zor": True})
        st.write("🛡️ **Kalkan Durumu:**")
        cols = st.columns(3)
        for i, z in enumerate(["Kolay", "Orta", "Zor"]):
            durum = "✅" if shields.get(z, True) else "❌"
            stil = "kalkan-aktif" if shields.get(z, True) else "kalkan-kirik"
            cols[i].markdown(f"{z}: <span class='{stil}'>{durum}</span>", unsafe_allow_html=True)
    
    if st.checkbox("🔥 Win Streak (Seri) Durumunu Göster"):
        if data and "ai" in data:
            streaks = data["ai"].get("streaks", {})
            if streaks:
                cols = st.columns(3)
                for i, (k, v) in enumerate(streaks.items()):
                    if v > 0: cols[i%3].success(f"{k}: {v} Seri")
            else: st.warning("Aktif serin yok.")

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
        if st.button("🏆 AI Liderlik Tablosu", use_container_width=True):
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
            renk = "kazandi-box"; baslik = "✅ KAZANDIN!"
        else:
            renk = "kaybetti-box"; baslik = "❌ KAYBETTİN..."

        st.markdown(f"""
        <div class='{renk}'>
            <h1>{baslik}</h1>
            <p class='savas-sozu'>{st.session_state.ai_soz}</p>
        </div>
        """, unsafe_allow_html=True)
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

    st.write("---")
    col1, col2, col3 = st.columns(3)
    with col1: 
        if st.button("🗿 TAŞ", use_container_width=True): ai_hamle_yap("Taş", bilgi)
    with col2: 
        if st.button("📜 KAĞIT", use_container_width=True): ai_hamle_yap("Kağıt", bilgi)
    with col3: 
        if st.button("✂️ MAKAS", use_container_width=True): ai_hamle_yap("Makas", bilgi)
    st.write("")
    if st.button("🏳️ Pes Et"): st.session_state.sayfa='ana_menu'; st.rerun()

def ai_hamle_yap(p_hamle, bilgi_placeholder):
    st.session_state.p_hamle_ai = p_hamle
    bilgi_placeholder.markdown('<p class="dusunuyor">Yapay Zeka Hamle Yapıyor...</p>', unsafe_allow_html=True)
    time.sleep(0.8)
    
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
            durum="kazandi"; st.session_state.ai_mesaj="✅ KAZANDIN! (Okçu Beraberliği Bozdu)"
        else:
            durum="berabere"; st.session_state.ai_mesaj="🤝 BERABERE!"
    elif (p_hamle=="Taş" and pc_hamle=="Makas") or (p_hamle=="Kağıt" and pc_hamle=="Taş") or (p_hamle=="Makas" and pc_hamle=="Kağıt"):
        st.session_state.oyuncu_skor+=1; durum="kazandi"; st.session_state.ai_mesaj="✅ KAZANDIN!"
    else:
        st.session_state.pc_skor+=1; durum="kaybetti"; st.session_state.ai_mesaj="❌ KAYBETTİN!"
    
    st.session_state.ai_soz = rastgele_soz(durum)
    
    h = st.session_state.ai_hedef
    if st.session_state.oyuncu_skor >= h:
        p, streak_msg = mac_sonu_hesapla_ai(st.session_state.isim, st.session_state.avatar_rol, z, h, "kazandi")
        st.session_state.ai_sonuc_html = f"<h3>+{p} Kupa Kazandın</h3><p>{streak_msg}</p>"
        st.session_state.ai_oyun_bitti = True
    elif st.session_state.pc_skor >= h:
        p, streak_msg = mac_sonu_hesapla_ai(st.session_state.isim, st.session_state.avatar_rol, z, h, "kaybetti")
        st.session_state.ai_sonuc_html = f"<h3>{p} Kupa Kaybettin</h3><p>{streak_msg}</p>"
        st.session_state.ai_oyun_bitti = True
    st.rerun()

# --- PVP MODU ---
def pvp_giris():
    st.markdown("<h2 style='text-align:center'>👥 Online Savaş</h2>", unsafe_allow_html=True)
    
    # Anlık Kupa Göstergesi (PvP)
    data = get_player_data(st.session_state.isim)
    kupa = data.get("pvp", {}).get("toplam_kupa", 0) if data else 0
    st.markdown(f"<div class='kupa-gosterge'>🏆 Mevcut PvP Kupan: {kupa}</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Oda Kur", "Katıl"])
    with tab1:
        hedef_secim = st.radio("Set Sayısı:", [3, 5, 7], format_func=lambda x: f"Bo{x}", horizontal=True)
        st.caption(f"Bo{hedef_secim}: {hedef_secim//2 + 1} olan kazanır.")
        if st.button("Yeni Oda Oluştur"):
            kod = str(random.randint(1000, 9999))
            hedef_skor = (hedef_secim // 2) + 1
            # PVP oda oluşturma (Basit)
            maclar = json_oku(MAC_DOSYASI)
            maclar[kod] = {"p1": st.session_state.isim, "p1_avatar": st.session_state.avatar_ikon, "p1_hamle": None, "p1_puan": 0, "p2": None, "p2_avatar": None, "p2_hamle": None, "p2_puan": 0, "durum": "bekliyor", "son_mesaj": "Rakip bekleniyor...", "hedef": hedef_skor}
            json_yaz(MAC_DOSYASI, maclar)
            st.session_state.oda_kodu = kod; st.session_state.oyuncu_no = "p1"; st.session_state.pvp_hedef_set = hedef_secim
            st.session_state.sayfa = 'pvp_lobi'; st.rerun()
    with tab2:
        gk = st.text_input("Oda Kodu:"); 
        if st.button("Katıl"):
            maclar = json_oku(MAC_DOSYASI)
            if gk in maclar and maclar[gk]["p2"] is None:
                maclar[gk]["p2"] = st.session_state.isim; maclar[gk]["p2_avatar"] = st.session_state.avatar_ikon
                maclar[gk]["durum"] = "oynaniyor"; maclar[gk]["son_mesaj"] = "Oyun Başladı!"
                json_yaz(MAC_DOSYASI, maclar)
                st.session_state.oda_kodu = gk; st.session_state.oyuncu_no = "p2"
                st.session_state.sayfa = 'pvp_lobi'; st.rerun()
            else: st.error("Oda bulunamadı!")
    st.write("---")
    if st.button("🏆 PvP Liderlik Tablosu"): st.session_state.sayfa = 'liderlik_pvp'; st.rerun()
    if st.button("Geri"): st.session_state.sayfa = 'ana_menu'; st.rerun()

def pvp_lobi():
    st.title(f"🔑 Oda Kodu: {st.session_state.oda_kodu}")
    maclar = json_oku(MAC_DOSYASI)
    if st.session_state.oda_kodu not in maclar: st.error("Oda kapandı"); return
    oda = maclar[st.session_state.oda_kodu]
    if oda['durum'] == "bekliyor": time.sleep(2); st.rerun()
    
    c1, c2 = st.columns(2)
    with c1: st.success(f"P1: {oda['p1']}")
    with c2: 
        if oda['p2']: st.success(f"P2: {oda['p2']}")
        else: st.warning("Rakip Bekleniyor...")
    if oda['durum']=="oynaniyor": st.session_state.sayfa='pvp_oyun'; st.rerun()
    if st.button("Çık"): st.session_state.sayfa='ana_menu'; st.rerun()

def pvp_oyun():
    kod=st.session_state.oda_kodu; ben=st.session_state.oyuncu_no
    maclar = json_oku(MAC_DOSYASI); oda = maclar.get(kod)
    if not oda: st.session_state.sayfa='ana_menu'; st.rerun(); return
    
    rakip = "p2" if ben == "p1" else "p1"
    if oda[f"{ben}_hamle"] and not oda[f"{rakip}_hamle"]: time.sleep(2); st.rerun()

    c1,c2,c3 = st.columns([3,1,3])
    with c1: st.markdown(f"<div class='skor-kutu'><h3>{oda['p1_avatar']} {oda['p1']}</h3><h1>{oda['p1_puan']}</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='skor-kutu'><h3>{oda['p2_avatar']} {oda['p2']}</h3><h1>{oda['p2_puan']}</h1></div>", unsafe_allow_html=True)
    
    st.progress(min(max(oda['p1_puan'], oda['p2_puan']) / oda['hedef'], 1.0))
    st.info(f"📢 {oda['son_mesaj']}")
    
    if "son_p1_goster" in oda and oda["son_p1_goster"]:
        ic1, ic2 = st.columns(2)
        with ic1: st.caption(f"{oda['p1']}"); resim_goster(oda['son_p1_goster'], 80)
        with ic2: st.caption(f"{oda['p2']}"); resim_goster(oda['son_p2_goster'], 80)

    # Oyun Sonu
    kazanan_kim = None
    if oda['p1_puan'] >= oda['hedef']: kazanan_kim = "p1"
    elif oda['p2_puan'] >= oda['hedef']: kazanan_kim = "p2"

    if kazanan_kim:
        durum = "kazandi" if kazanan_kim == ben else "kaybetti"
        soz = rastgele_soz(durum)
        if durum == "kazandi":
            renk = "kazandi-box"; baslik = "✅ KAZANDIN!"
        else:
            renk = "kaybetti-box"; baslik = "❌ KAYBETTİN..."
        
        st.markdown(f"""
        <div class='{renk}'>
            <h1>{baslik}</h1>
            <p class='savas-sozu'>{soz}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 RÖVANŞ YAP"):
                # Puanı kaydet
                hedef = oda['hedef']; set_turu = 3 if hedef == 2 else (5 if hedef == 3 else 7)
                if kazanan_kim == ben:
                    p = mac_sonu_hesapla_pvp(st.session_state.isim, st.session_state.avatar_rol, set_turu, "kazandi")
                    st.success(f"+{p} Kupa!")
                
                maclar[kod]["p1_puan"]=0; maclar[kod]["p2_puan"]=0; maclar[kod]["p1_hamle"]=None; maclar[kod]["p2_hamle"]=None
                maclar[kod]["son_p1_goster"]=None; maclar[kod]["son_p2_goster"]=None; maclar[kod]["son_mesaj"]="Rövanş Başladı!"
                json_yaz(MAC_DOSYASI, maclar)
                st.rerun()
        with c2:
             if st.button("🏠 Ana Menü"): st.session_state.sayfa='ana_menu'; st.rerun()
        return

    st.write("---")
    # Hamle Kontrol
    maclar = json_oku(MAC_DOSYASI); oda = maclar.get(kod) # Güncel oda verisini tekrar al
    
    # Hamle İşleme
    if oda[f"{ben}_hamle"]: 
        st.warning("Hamle yapıldı, rakip bekleniyor...")
        if oda["p1_hamle"] and oda["p2_hamle"]:
            # Sonuç hesapla
            p1h, p2h = oda["p1_hamle"], oda["p2_hamle"]
            if (p1h=="Taş" and p2h=="Makas") or (p1h=="Kağıt" and p2h=="Taş") or (p1h=="Makas" and p2h=="Kağıt"):
                oda["p1_puan"]+=1; oda["son_mesaj"]=f"{oda['p1']} kazandı!"
            elif p1h==p2h: oda["son_mesaj"]="Berabere!"
            else: oda["p2_puan"]+=1; oda["son_mesaj"]=f"{oda['p2']} kazandı!"
            oda["son_p1_goster"]=p1h; oda["son_p2_goster"]=p2h; oda["p1_hamle"]=None; oda["p2_hamle"]=None
            json_yaz(MAC_DOSYASI, maclar)
            st.rerun()
        else:
            time.sleep(2); st.rerun()
    else:
        st.write("Hamleni Seç:")
        b1,b2,b3=st.columns(3)
        if b1.button("🗿 TAŞ"): 
            maclar[kod][f"{ben}_hamle"] = "Taş"; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        if b2.button("📜 KAĞIT"): 
            maclar[kod][f"{ben}_hamle"] = "Kağıt"; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        if b3.button("✂️ MAKAS"): 
            maclar[kod][f"{ben}_hamle"] = "Makas"; json_yaz(MAC_DOSYASI, maclar); st.rerun()
    st.write("---")
    if st.button("Çık"): st.session_state.sayfa='ana_menu'; st.rerun()

# --- LİDERLİK TABLOSU ---
def liderlik_sayfasi(mod):
    baslik = "🤖 YAPAY ZEKA" if mod == 'ai' else "👥 PVP"
    st.title(f"🏆 {baslik} LİDERLİK TABLOSU")
    
    veriler = json_oku(SKOR_DOSYASI)
    if not veriler: st.warning("Veri yok")
    else:
        l = []
        for isim, d in veriler.items():
            rol = d.get("avatar_rol", "Bilinmiyor")
            ikon = AVATARLAR.get(rol, "👤")
            
            # Mod'a göre veri çek
            if mod == 'ai' and "ai" in d:
                ai_data = d["ai"]
                l.append({
                    "Rank": 0, "Avatar": ikon, "Oyuncu": isim,
                    "🏆 Kupa": ai_data.get("toplam_kupa", 0),
                    "Kolay W": ai_data.get("wins", {}).get("Kolay", 0),
                    "Orta W": ai_data.get("wins", {}).get("Orta", 0),
                    "Zor W": ai_data.get("wins", {}).get("Zor", 0)
                })
            elif mod == 'pvp' and "pvp" in d:
                pvp_data = d["pvp"]
                l.append({
                    "Rank": 0, "Avatar": ikon, "Oyuncu": isim,
                    "🏆 Kupa": pvp_data.get("toplam_kupa", 0)
                })

        df = pd.DataFrame(l)
        if not df.empty:
            df = df.sort_values(by="🏆 Kupa", ascending=False)
            df["Rank"] = range(1, len(df) + 1)
            
            # İndexi Rank yapalım ki soldaki 0,1,2 kalksın
            df.set_index("Rank", inplace=True)
            
            st.table(df)
        else: st.warning("Bu modda henüz kayıt yok.")
        
    donus = 'ai_giris' if mod == 'ai' else 'pvp_giris'
    if st.button("🏠 Geri Dön"): st.session_state.sayfa = donus; st.rerun()

# --- YÖNLENDİRME ---
if st.session_state.sayfa == 'avatar_sec': avatar_secim_sayfasi()
elif st.session_state.sayfa == 'ana_menu': ana_menu()
elif st.session_state.sayfa == 'ai_giris': ai_giris()
elif st.session_state.sayfa == 'ai_oyun': ai_oyun()
elif st.session_state.sayfa == 'pvp_giris': pvp_giris()
elif st.session_state.sayfa == 'pvp_lobi': pvp_lobi()
elif st.session_state.sayfa == 'pvp_oyun': pvp_oyun()
elif st.session_state.sayfa == 'liderlik_ai': liderlik_sayfasi('ai')
elif st.session_state.sayfa == 'liderlik_pvp': liderlik_sayfasi('pvp')
