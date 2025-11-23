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
    .teklif-box { background-color: #3498db; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.02); } 100% { transform: scale(1); } }
    .kalkan-aktif { color: #2ecc71; font-weight: bold; }
    .kalkan-kirik { color: #e74c3c; font-weight: bold; text-decoration: line-through; }
</style>
""", unsafe_allow_html=True)

# --- AVATARLAR VE SINIFLAR ---
AVATARLAR = {
    "Okçu": "🏹",
    "Savaşçı": "⚔️",
    "Büyücü": "🔮",
    "Tank": "🛡️"
}

SINIF_ACIKLAMALARI = {
    "Okçu": "🎯 **Keskin Göz:** Berabere biten turlarda, maç başına 1 kez beraberliği bozar ve turu kazanır.",
    "Savaşçı": "⚔️ **Çelik İrade:** Her zorluk seviyesi için 1 kez kupa kaybetme cezası almazsın.",
    "Büyücü": "✨ **Mana Koruması:** Kaybetsen bile Galibiyet Serin (Win Streak) hemen bozulmaz.",
    "Tank": "🚜 **Yıkıcı Güç:** Maç içindeki İLK galibiyetinde rakibe ağır hasar vererek 1 yerine **2 Puan** kazanırsın."
}

# --- SÖZLER ---
SOZLER = {
    "kazandi": ["Arenada sesler yükseliyor!", "Efsanevi bir vuruş!", "Tarih yazıldı!", "Rakip neye uğradığını şaşırdı!"],
    "kaybetti": ["Dikkatsiz bir an...", "Şans senden yana değil.", "Savunman kırıldı!", "Karanlık üzerine çöktü."],
    "berabere": ["Kılıçlar çarpıştı!", "Mükemmel denge!", "Kazanan yok, savaş sürüyor!"]
}

# --- DOSYALAR ---
SKOR_DOSYASI = "skorlar_v2.json"
MAC_DOSYASI = "maclar.json"

# --- FONKSİYONLAR ---
def json_oku(dosya):
    if not os.path.exists(dosya): return {}
    try: with open(dosya, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def json_yaz(dosya, veri):
    with open(dosya, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)

def resim_goster(hamle, genislik=130):
    dosya = f"{hamle.lower()}.png"
    if os.path.exists(dosya): st.image(dosya, width=genislik)
    else:
        emo = {"Taş": "🪨", "Kağıt": "📜", "Makas": "✂️"}
        st.markdown(f"<div style='font-size:50px; text-align:center;'>{emo.get(hamle, '❓')}</div>", unsafe_allow_html=True)

def get_player_data(isim):
    veriler = json_oku(SKOR_DOSYASI)
    return veriler.get(isim)

# --- PUANLAMA (AI) ---
def mac_sonu_hesapla_ai(isim, avatar_rol, zorluk, hedef, sonuc):
    veriler = json_oku(SKOR_DOSYASI)
    if isim not in veriler: veriler[isim] = {}
    if "ai" not in veriler[isim]: veriler[isim]["ai"] = {"toplam_kupa": 0, "streaks": {}, "warrior_shields": {"Kolay": True, "Orta": True, "Zor": True}, "wins": {"Kolay":0, "Orta":0, "Zor":0}}
    veriler[isim]["avatar_rol"] = avatar_rol
    
    player_ai = veriler[isim]["ai"]
    streak_key = f"{zorluk}_{hedef}"
    streak = player_ai["streaks"].get(streak_key, 0)
    puan = 0; streak_mesaj = ""

    if sonuc == "kazandi":
        player_ai["wins"][zorluk] += 1
        base = {"Kolay": 1, "Orta": 5, "Zor": 10}
        carpan = {3: 1, 5: 2, 7: 3}
        puan = base[zorluk] * carpan[hedef]
        streak += 1
        streak_mesaj = f"🔥 Seri: {streak}"
        if streak > 3: puan += 1; streak_mesaj += " (+1 Bonus)"
        
        # Büyücü Korumasını Resetle (Gerekirse)
        veriler[isim][f"{streak_key}_protected"] = False

    elif sonuc == "kaybetti":
        # Büyücü Kontrolü
        buyucu_korudu = False
        if avatar_rol == "Büyücü" and streak > 0:
            prot_key = f"{streak_key}_protected"
            if not veriler[isim].get(prot_key, False):
                buyucu_korudu = True
                veriler[isim][prot_key] = True
                streak_mesaj = "✨ Büyücü Kalkanı Seriyi Korudu!"
        
        if not buyucu_korudu:
            if streak > 0: streak_mesaj = "❄️ Seri Bozuldu"
            streak = 0
        
        ceza_map = {"Kolay": {3: -6, 5: -3, 7: -1}, "Orta": {3: -3, 5: -2, 7: -1}, "Zor": {3: -1, 5: -1, 7: -1}}
        puan = ceza_map.get(zorluk, {}).get(hedef, -1)
        
        # Savaşçı Kontrolü
        if avatar_rol == "Savaşçı":
            shields = player_ai.get("warrior_shields", {"Kolay": True, "Orta": True, "Zor": True})
            if shields.get(zorluk, True):
                puan = 0; shields[zorluk] = False; player_ai["warrior_shields"] = shields; streak_mesaj = "🛡️ Kalkan Cezayı Engelledi!"

    player_ai["streaks"][streak_key] = streak
    player_ai["toplam_kupa"] += puan
    json_yaz(SKOR_DOSYASI, veriler)
    return puan, streak_mesaj

# --- PUANLAMA (PVP) ---
def mac_sonu_hesapla_pvp(isim, avatar_rol, hedef_set, sonuc):
    veriler = json_oku(SKOR_DOSYASI)
    if isim not in veriler: veriler[isim] = {}
    if "pvp" not in veriler[isim]: veriler[isim]["pvp"] = {"toplam_kupa": 0}
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

# AI Değişkenleri
if 'ai_state' not in st.session_state:
    st.session_state.ai_state = {
        'p_skor': 0, 'pc_skor': 0, 'mesaj': "", 'soz': "", 'bitti': False, 
        'okcu_hak': False, 'pc_okcu_hak': False, 'tank_hak': True, 'pc_tank_hak': True,
        'pc_rol': "Savaşçı", 'pc_ikon': "⚔️"
    }

# PVP Değişkenleri
if 'oda_kodu' not in st.session_state: st.session_state.oda_kodu = None

# --- SAYFALAR ---

def avatar_secim_sayfasi():
    st.title("🛡️ Sınıfını Seç")
    isim_giris = st.text_input("Savaşçı Adı:", value=st.session_state.isim, max_chars=15)
    st.write("---")
    cols = st.columns(2)
    for i, (rol, ikon) in enumerate(AVATARLAR.items()):
        with cols[i % 2]:
            st.markdown(f"<div style='font-size:40px; text-align:center;'>{ikon}</div>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='text-align:center;'>{rol}</h4>", unsafe_allow_html=True)
            st.info(SINIF_ACIKLAMALARI[rol])
            if st.button(f"SEÇ: {rol}", key=f"btn_{rol}", use_container_width=True):
                if not isim_giris: st.error("İsim gir!")
                else:
                    st.session_state.isim = isim_giris; st.session_state.avatar_rol = rol; st.session_state.avatar_ikon = ikon; st.session_state.sayfa = 'ana_menu'; st.rerun()

def ana_menu():
    st.markdown(f"<h1 style='text-align: center;'>🗿 📜 ✂️ TAŞ-KAĞIT-MAKAS ARENA</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>{st.session_state.avatar_ikon} {st.session_state.isim} ({st.session_state.avatar_rol})</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🤖 Tek Kişilik")
        if st.button("YAPAY ZEKA İLE OYNA", use_container_width=True): st.session_state.sayfa = 'ai_giris'; st.rerun()
    with c2:
        st.markdown("### 👥 Çok Oyunculu")
        if st.button("KARŞILIKLI SAVAŞ (ONLINE)", use_container_width=True): st.session_state.sayfa = 'pvp_giris'; st.rerun()
    st.write("---")
    if st.button("⬅️ Karakter Değiştir", use_container_width=True): st.session_state.sayfa = 'avatar_sec'; st.rerun()

# --- AI MODU ---
def ai_giris():
    st.markdown("<h2 style='text-align:center'>🤖 Yapay Zeka Modu</h2>", unsafe_allow_html=True)
    data = get_player_data(st.session_state.isim)
    kupa = data.get("ai", {}).get("toplam_kupa", 0) if data else 0
    st.markdown(f"<div class='kupa-gosterge'>🏆 Mevcut AI Kupan: {kupa}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: zorluk = st.radio("Zorluk:", ["Kolay", "Orta", "Zor"], horizontal=True)
    with c2: hedef = st.radio("Set:", [3, 5, 7], format_func=lambda x: f"Bo{x}", horizontal=True)
    
    if st.session_state.avatar_rol == "Savaşçı" and data and "ai" in data:
        shields = data["ai"].get("warrior_shields", {})
        st.caption(f"🛡️ Kalkanlar: K:{shields.get('Kolay')} | O:{shields.get('Orta')} | Z:{shields.get('Zor')}")

    if st.button("⚔️ BAŞLA", use_container_width=True):
        st.session_state.ai_zorluk = zorluk; st.session_state.ai_hedef = hedef
        # AI Rastgele Rol Seçimi
        pc_rol = random.choice(list(AVATARLAR.keys()))
        pc_ikon = AVATARLAR[pc_rol]
        
        st.session_state.ai_state = {
            'p_skor': 0, 'pc_skor': 0, 'mesaj': "Hamleni Bekliyorum...", 'soz': "", 'bitti': False, 
            'okcu_hak': False, 'pc_okcu_hak': False, 'tank_hak': True, 'pc_tank_hak': True,
            'pc_rol': pc_rol, 'pc_ikon': pc_ikon,
            'p_hamle': None, 'pc_hamle': None
        }
        st.session_state.sayfa = 'ai_oyun'; st.rerun()
        
    if st.button("🏆 AI Liderlik"): st.session_state.sayfa = 'liderlik_ai'; st.rerun()
    if st.button("Geri"): st.session_state.sayfa = 'ana_menu'; st.rerun()

def ai_oyun():
    s = st.session_state.ai_state
    
    c1, c2, c3 = st.columns([3, 1, 3])
    with c1: st.markdown(f"<div class='skor-kutu'><h3>{st.session_state.avatar_ikon}</h3><h1>{s['p_skor']}</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='skor-kutu'><h3>{s['pc_ikon']} {s['pc_rol']} (AI)</h3><h1>{s['pc_skor']}</h1></div>", unsafe_allow_html=True)
    st.progress(min(s['p_skor'] / st.session_state.ai_hedef, 1.0))
    
    if s['bitti']:
        baslik = "✅ KAZANDIN!" if s['p_skor'] >= st.session_state.ai_hedef else "❌ KAYBETTİN..."
        renk = "kazandi-box" if "KAZANDIN" in baslik else "kaybetti-box"
        st.markdown(f"<div class='{renk}'><h1>{baslik}</h1><p class='savas-sozu'>{s['soz']}</p></div>", unsafe_allow_html=True)
        st.markdown(s.get('sonuc_html', ''), unsafe_allow_html=True)
        
        if st.button("🏠 ANA MENÜ", use_container_width=True): st.session_state.sayfa = 'ana_menu'; st.rerun()
        return

    bilgi = st.empty()
    if s['p_hamle']:
        ic1, ic2 = st.columns(2)
        with ic1: st.caption("Sen"); resim_goster(s['p_hamle'])
        with ic2: st.caption("Rakip"); resim_goster(s['pc_hamle'])
    bilgi.info(s['mesaj'])

    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🗿 TAŞ"): ai_hamle_yap("Taş", bilgi)
    with c2: 
        if st.button("📜 KAĞIT"): ai_hamle_yap("Kağıt", bilgi)
    with c3: 
        if st.button("✂️ MAKAS"): ai_hamle_yap("Makas", bilgi)
    st.write("")
    if st.button("🏳️ Çık"): st.session_state.sayfa='ana_menu'; st.rerun()

def ai_hamle_yap(p_hamle, bilgi_placeholder):
    s = st.session_state.ai_state
    s['p_hamle'] = p_hamle
    bilgi_placeholder.markdown('<p class="dusunuyor">Yapay Zeka Hamle Yapıyor...</p>', unsafe_allow_html=True)
    time.sleep(0.8)
    
    kazanan = {"Taş": "Makas", "Kağıt": "Taş", "Makas": "Kağıt"}
    pc_hamle = random.choice(["Taş", "Kağıt", "Makas"])
    
    # AI Zorluk Mantığı
    z = st.session_state.ai_zorluk
    if z == "Kolay" and random.randint(1,100) <= 40: pc_hamle = {"Taş":"Makas", "Kağıt":"Taş", "Makas":"Kağıt"}[p_hamle] # Kaybet
    elif z == "Zor" and random.randint(1,100) <= 40: pc_hamle = {"Taş":"Kağıt", "Kağıt":"Makas", "Makas":"Taş"}[p_hamle] # Kazan
    
    s['pc_hamle'] = pc_hamle
    
    tur_sonuc = ""
    # Sonuç Hesapla
    if p_hamle == pc_hamle:
        # OKÇU YETENEĞİ
        if st.session_state.avatar_rol == "Okçu" and not s['okcu_hak']:
            s['p_skor']+=1; s['okcu_hak']=True; tur_sonuc="kazandi"; s['mesaj']="🏹 OKÇU YETENEĞİ: Beraberliği bozdun!"
        elif s['pc_rol'] == "Okçu" and not s['pc_okcu_hak']:
            s['pc_skor']+=1; s['pc_okcu_hak']=True; tur_sonuc="kaybetti"; s['mesaj']="🏹 RAKİP OKÇU: Beraberliği bozdu!"
        else:
            tur_sonuc="berabere"; s['mesaj']="🤝 BERABERE!"
    elif kazanan[p_hamle] == pc_hamle:
        # TANK YETENEĞİ (Oyuncu)
        puan = 1
        if st.session_state.avatar_rol == "Tank" and s['tank_hak']:
            puan = 2; s['tank_hak'] = False; s['mesaj'] = "🚜 TANK GÜCÜ: +2 Puan!"
        else: s['mesaj'] = "✅ KAZANDIN!"
        s['p_skor']+=puan; tur_sonuc="kazandi"
    else:
        # TANK YETENEĞİ (AI)
        puan = 1
        if s['pc_rol'] == "Tank" and s['pc_tank_hak']:
            puan = 2; s['pc_tank_hak'] = False; s['mesaj'] = "🚜 RAKİP TANK EZDİ: +2 Puan!"
        else: s['mesaj'] = "❌ KAYBETTİN!"
        s['pc_skor']+=puan; tur_sonuc="kaybetti"
    
    s['soz'] = random.choice(SOZLER.get(tur_sonuc, [""]))
    
    # Bitiş
    h = st.session_state.ai_hedef
    if s['p_skor'] >= h:
        p, m = mac_sonu_hesapla_ai(st.session_state.isim, st.session_state.avatar_rol, z, h, "kazandi")
        s['sonuc_html'] = f"<h3>+{p} Kupa</h3><p>{m}</p>"; s['bitti'] = True
    elif s['pc_skor'] >= h:
        p, m = mac_sonu_hesapla_ai(st.session_state.isim, st.session_state.avatar_rol, z, h, "kaybetti")
        s['sonuc_html'] = f"<h3>{p} Kupa</h3><p>{m}</p>"; s['bitti'] = True
    st.rerun()

# --- PVP MODU ---
def pvp_giris():
    st.markdown("<h2 style='text-align:center'>👥 Online Savaş</h2>", unsafe_allow_html=True)
    data = get_player_data(st.session_state.isim)
    kupa = data.get("pvp", {}).get("toplam_kupa", 0) if data else 0
    st.markdown(f"<div class='kupa-gosterge'>🏆 Mevcut PvP Kupan: {kupa}</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Oda Kur", "Katıl"])
    with tab1:
        hs = st.radio("Set Sayısı:", [3, 5, 7], format_func=lambda x: f"Bo{x}", horizontal=True)
        if st.button("Oda Oluştur"):
            kod = str(random.randint(1000, 9999))
            h_skor = (hs // 2) + 1
            maclar = json_oku(MAC_DOSYASI)
            maclar[kod] = {
                "p1": st.session_state.isim, "p1_avatar": st.session_state.avatar_ikon, "p1_rol": st.session_state.avatar_rol,
                "p2": None, "p2_avatar": None, "p2_rol": None,
                "p1_puan": 0, "p2_puan": 0, "hedef": h_skor, "set_turu": hs,
                "p1_hamle": None, "p2_hamle": None,
                "p1_durum": "oynuyor", "p2_durum": "bekliyor", # oynuyor, bekliyor, rovan_istiyor, cikti
                "son_mesaj": "Rakip Bekleniyor...", "p1_tank": True, "p2_tank": True
            }
            json_yaz(MAC_DOSYASI, maclar)
            st.session_state.oda_kodu = kod; st.session_state.oyuncu_no = "p1"
            st.session_state.sayfa = 'pvp_lobi'; st.rerun()
    with tab2:
        gk = st.text_input("Oda Kodu:"); 
        if st.button("Katıl"):
            maclar = json_oku(MAC_DOSYASI)
            if gk in maclar and maclar[gk]["p2"] is None:
                maclar[gk]["p2"] = st.session_state.isim; maclar[gk]["p2_avatar"] = st.session_state.avatar_ikon
                maclar[gk]["p2_rol"] = st.session_state.avatar_rol; maclar[gk]["p2_durum"] = "oynuyor"
                maclar[gk]["son_mesaj"] = "Oyun Başladı!"
                json_yaz(MAC_DOSYASI, maclar)
                st.session_state.oda_kodu = gk; st.session_state.oyuncu_no = "p2"
                st.session_state.sayfa = 'pvp_lobi'; st.rerun()
            else: st.error("Oda Yok/Dolu")
    
    st.write("---")
    if st.button("🏆 PvP Liderlik"): st.session_state.sayfa = 'liderlik_pvp'; st.rerun()
    if st.button("Geri"): st.session_state.sayfa = 'ana_menu'; st.rerun()

def pvp_lobi():
    st.title(f"🔑 Oda: {st.session_state.oda_kodu}")
    oda = json_oku(MAC_DOSYASI).get(st.session_state.oda_kodu)
    if not oda: st.error("Oda kapandı"); time.sleep(2); st.session_state.sayfa='ana_menu'; st.rerun(); return

    if oda['p2'] is None: time.sleep(2); st.rerun()
    
    c1, c2 = st.columns(2)
    with c1: st.success(f"P1: {oda['p1']} {oda['p1_avatar']}")
    with c2: st.success(f"P2: {oda['p2']} {oda['p2_avatar']}") if oda['p2'] else st.warning("Bekleniyor...")
    
    if oda['p2']: st.session_state.sayfa='pvp_oyun'; st.rerun()
    if st.button("Çık"): st.session_state.sayfa='ana_menu'; st.rerun()

def pvp_oyun():
    kod = st.session_state.oda_kodu; ben = st.session_state.oyuncu_no
    rakip = "p2" if ben == "p1" else "p1"
    maclar = json_oku(MAC_DOSYASI); oda = maclar.get(kod)
    
    if not oda: st.session_state.sayfa='ana_menu'; st.rerun(); return
    
    # Durum Kontrolü (Rakip çıktı mı?)
    if oda[f"{rakip}_durum"] == "cikti":
        st.error("Rakip masadan kalktı (Ana Menüye döndü)."); 
        if st.button("Ana Menüye Dön"): st.session_state.sayfa='ana_menu'; st.rerun()
        return

    # Oto Yenileme
    if (oda[f"{ben}_hamle"] and not oda[f"{rakip}_hamle"]) or \
       (oda[f"{rakip}_durum"] == "rovan_istiyor" and oda[f"{ben}_durum"] != "rovan_istiyor"):
        time.sleep(2); st.rerun()

    # Skorlar
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

    # --- OYUN BİTTİ Mİ? ---
    kazanan = None
    if oda['p1_puan'] >= oda['hedef']: kazanan = "p1"
    elif oda['p2_puan'] >= oda['hedef']: kazanan = "p2"

    if kazanan:
        durum = "kazandi" if kazanan == ben else "kaybetti"
        renk = "kazandi-box" if durum == "kazandi" else "kaybetti-box"
        baslik = "✅ KAZANDIN!" if durum == "kazandi" else "❌ KAYBETTİN..."
        
        st.markdown(f"<div class='{renk}'><h1>{baslik}</h1></div>", unsafe_allow_html=True)
        
        # Rövanş Mantığı
        st.write("---")
        if oda[f"{rakip}_durum"] == "rovan_istiyor":
            st.info(f"🔄 {oda[rakip]} Rövanş İstiyor!")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("KABUL ET (Rövanş)"):
                    # Puanı Kaydet (Sadece kazanan için)
                    if kazanan == ben:
                        p = mac_sonu_hesapla_pvp(st.session_state.isim, st.session_state.avatar_rol, oda['set_turu'], "kazandi")
                    # Odayı Sıfırla
                    maclar[kod]["p1_puan"]=0; maclar[kod]["p2_puan"]=0
                    maclar[kod]["p1_hamle"]=None; maclar[kod]["p2_hamle"]=None
                    maclar[kod]["p1_durum"]="oynuyor"; maclar[kod]["p2_durum"]="oynuyor"
                    maclar[kod]["p1_tank"]=True; maclar[kod]["p2_tank"]=True
                    maclar[kod]["son_mesaj"]="Rövanş Başladı!"; maclar[kod].pop("son_p1_goster", None)
                    json_yaz(MAC_DOSYASI, maclar)
                    st.rerun()
            with c2:
                if st.button("REDDET (Çık)"):
                    maclar[kod][f"{ben}_durum"] = "cikti"
                    json_yaz(MAC_DOSYASI, maclar)
                    st.session_state.sayfa='ana_menu'; st.rerun()
        elif oda[f"{ben}_durum"] == "rovan_istiyor":
            st.warning("Rakip Bekleniyor...")
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 RÖVANŞ TEKLİF ET"):
                    if kazanan == ben: # Puanı hemen kaydet (ilk basışta)
                         mac_sonu_hesapla_pvp(st.session_state.isim, st.session_state.avatar_rol, oda['set_turu'], "kazandi")
                    
                    maclar[kod][f"{ben}_durum"] = "rovan_istiyor"
                    json_yaz(MAC_DOSYASI, maclar)
                    st.rerun()
            with c2:
                if st.button("🏠 Ana Menü"):
                    maclar[kod][f"{ben}_durum"] = "cikti"
                    json_yaz(MAC_DOSYASI, maclar)
                    st.session_state.sayfa='ana_menu'; st.rerun()
        return

    # --- OYUN DEVAM EDİYOR ---
    if oda[f"{ben}_hamle"]: 
        st.warning("Hamle yapıldı, rakip bekleniyor...")
        if oda["p1_hamle"] and oda["p2_hamle"]: # İkisi de yapmış
            # Sonuç Hesapla
            p1h, p2h = oda["p1_hamle"], oda["p2_hamle"]
            kazanan = "berabere"
            if (p1h=="Taş" and p2h=="Makas") or (p1h=="Kağıt" and p2h=="Taş") or (p1h=="Makas" and p2h=="Kağıt"): kazanan="p1"
            elif p1h!=p2h: kazanan="p2"
            
            # Tank Bonusu Kontrol (PVP)
            puan = 1
            if kazanan == "p1":
                if oda["p1_rol"] == "Tank" and oda["p1_tank"]: puan=2; oda["p1_tank"]=False; oda["son_mesaj"]=f"{oda['p1']} TANK GÜCÜYLE EZDİ!"
                else: oda["son_mesaj"]=f"{oda['p1']} Kazandı!"
                oda["p1_puan"] += puan
            elif kazanan == "p2":
                if oda["p2_rol"] == "Tank" and oda["p2_tank"]: puan=2; oda["p2_tank"]=False; oda["son_mesaj"]=f"{oda['p2']} TANK GÜCÜYLE EZDİ!"
                else: oda["son_mesaj"]=f"{oda['p2']} Kazandı!"
                oda["p2_puan"] += puan
            else: oda["son_mesaj"] = "Berabere!"
            
            oda["son_p1_goster"]=p1h; oda["son_p2_goster"]=p2h
            oda["p1_hamle"]=None; oda["p2_hamle"]=None
            json_yaz(MAC_DOSYASI, maclar)
            st.rerun()
    else:
        st.write("Hamleni Seç:")
        b1,b2,b3=st.columns(3)
        if b1.button("🗿 TAŞ"): maclar[kod][f"{ben}_hamle"]="Taş"; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        if b2.button("📜 KAĞIT"): maclar[kod][f"{ben}_hamle"]="Kağıt"; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        if b3.button("✂️ MAKAS"): maclar[kod][f"{ben}_hamle"]="Makas"; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        
    st.write("---")
    if st.button("Çık"): 
        maclar[kod][f"{ben}_durum"]="cikti"; json_yaz(MAC_DOSYASI, maclar)
        st.session_state.sayfa='ana_menu'; st.rerun()

# --- LİDERLİK ---
def liderlik_sayfasi(mod):
    baslik = "🤖 YAPAY ZEKA" if mod == 'ai' else "👥 PVP"
    st.title(f"🏆 {baslik} LİDERLİK TABLOSU")
    veriler = json_oku(SKOR_DOSYASI)
    l = []
    for isim, d in veriler.items():
        rol = d.get("avatar_rol", "Bilinmiyor"); ikon = AVATARLAR.get(rol, "👤")
        if mod == 'ai' and "ai" in d:
            l.append({"Avatar": ikon, "Oyuncu": isim, "🏆 Kupa": d["ai"].get("toplam_kupa", 0)})
        elif mod == 'pvp' and "pvp" in d:
            l.append({"Avatar": ikon, "Oyuncu": isim, "🏆 Kupa": d["pvp"].get("toplam_kupa", 0)})
    
    if l:
        df = pd.DataFrame(l).sort_values(by="🏆 Kupa", ascending=False)
        df.insert(0, "Rank", range(1, len(df) + 1)); df.set_index("Rank", inplace=True)
        st.table(df)
    else: st.warning("Veri yok.")
    
    if st.button("🏠 Geri Dön"): st.session_state.sayfa = 'ai_giris' if mod=='ai' else 'pvp_giris'; st.rerun()

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
