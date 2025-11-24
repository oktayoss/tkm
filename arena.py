import streamlit as st
import random
import json
import os
import time
import uuid
import pandas as pd
import extra_streamlit_components as stx

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Taş Kağıt Makas Arena", page_icon="🗿", layout="centered")

# --- ÇEREZ YÖNETİCİSİ (En Başta) ---
cookie_manager = stx.CookieManager(key="cookie_manager_v23")

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
    
    /* POP-UP VE BUTON DÜZELTMESİ */
    .modal-overlay { 
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
        background: rgba(0,0,0,0.9); z-index: 99990; 
        display: flex; justify-content: center; align-items: center;
        flex-direction: column;
    }
    .modal-content { 
        background-color: #2d3436; color: #dfe6e9; padding: 30px; 
        border-radius: 15px; width: 90%; max-width: 500px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #636e72; 
        text-align: left; margin-bottom: 20px;
    }
    .modal-header { font-size: 24px; font-weight: bold; color: #00cec9; margin-bottom: 20px; border-bottom: 2px solid #0984e3; padding-bottom: 10px; }
    .patch-item { font-size: 16px; margin-bottom: 10px; }
    
    /* KAPAT BUTONUNU EN ÜSTE ZORLA */
    div.stButton > button:first-child {
        z-index: 999999 !important; 
        position: relative;
    }
</style>
""", unsafe_allow_html=True)

# --- SABİTLER ---
AVATARLAR = {"Okçu": "🏹", "Savaşçı": "⚔️", "Büyücü": "🔮", "Tank": "🛡️", "Şifacı": "🩹"}
SINIF_ACIKLAMALARI = {
    "Okçu": "🎯 **Keskin Göz:** Berabere biten turlarda, maç başına 1 kez beraberliği bozar ve turu kazanır.",
    "Savaşçı": "⚔️ **Çelik İrade:** Her zorluk seviyesi için 1 kez kupa kaybetme cezası almazsın.",
    "Büyücü": "✨ **Mana Koruması:** Kaybetsen bile Galibiyet Serin (Win Streak) hemen bozulmaz.",
    "Tank": "🚜 **Yıkıcı Güç:** Maç içindeki İLK galibiyetinde rakibe 1 yerine **2 Puan** hasar verirsin.",
    "Şifacı": "💖 **Kutsal Kalkan:** Maç içinde İLK kez kaybettiğinde rakip puan kazanamaz (Hasarı yutar)."
}
SOZLER = {
    "kazandi": ["Arenada sesler yükseliyor!", "Efsanevi bir vuruş!", "Tarih yazıldı!", "Rakip neye uğradığını şaşırdı!"],
    "kaybetti": ["Dikkatsiz bir an...", "Şans senden yana değil.", "Savunman kırıldı!", "Karanlık üzerine çöktü."],
    "berabere": ["Kılıçlar çarpıştı!", "Mükemmel denge!", "Kazanan yok, savaş sürüyor!"]
}
SKOR_DOSYASI = "skorlar_v2.json"
MAC_DOSYASI = "maclar.json"
USERS_DOSYASI = "users.json"

# --- FONKSİYONLAR ---
def json_oku(dosya):
    if not os.path.exists(dosya): return {}
    try:
        with open(dosya, "r", encoding="utf-8") as f: return json.load(f)
    except:
        time.sleep(0.1)
        try: with open(dosya, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}

def json_yaz(dosya, veri):
    try: with open(dosya, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)
    except: pass

def resim_goster(hamle, genislik=130):
    dosya = f"{hamle.lower()}.png"
    if os.path.exists(dosya): st.image(dosya, width=genislik)
    else:
        emo = {"Taş": "🪨", "Kağıt": "📜", "Makas": "✂️"}
        st.markdown(f"<div style='font-size:50px; text-align:center;'>{emo.get(hamle, '❓')}</div>", unsafe_allow_html=True)

def get_player_data(isim):
    veriler = json_oku(SKOR_DOSYASI)
    return veriler.get(isim)

def rastgele_soz(durum): return random.choice(SOZLER.get(durum, [""]))

# --- ÜYELİK SİSTEMİ ---
def kullanici_kayit(kadi, sifre):
    users = json_oku(USERS_DOSYASI)
    if kadi in users: return False, "Bu kullanıcı adı dolu."
    token = str(uuid.uuid4())
    users[kadi] = {"sifre": sifre, "token": token}
    json_yaz(USERS_DOSYASI, users)
    return True, "Kayıt başarılı!"

def kullanici_giris(kadi, sifre):
    users = json_oku(USERS_DOSYASI)
    if kadi not in users: return False, None
    user_data = users[kadi]
    if isinstance(user_data, dict):
        if user_data.get("sifre") == sifre: return True, user_data.get("token")
    elif isinstance(user_data, str): 
        if user_data == sifre:
            token = str(uuid.uuid4())
            users[kadi] = {"sifre": sifre, "token": token}
            json_yaz(USERS_DOSYASI, users)
            return True, token
    return False, None

def token_ile_giris(token):
    users = json_oku(USERS_DOSYASI)
    for kadi, data in users.items():
        if isinstance(data, dict) and data.get("token") == token: return kadi
    return None

# --- PUANLAMA (AI) ---
def mac_sonu_hesapla_ai(isim, avatar_rol, zorluk, hedef, sonuc):
    veriler = json_oku(SKOR_DOSYASI)
    if isim not in veriler: veriler[isim] = {}
    if "ai" not in veriler[isim]: 
        veriler[isim]["ai"] = {"toplam_kupa": 0, "streaks": {}, "warrior_shields": {"Kolay":True,"Orta":True,"Zor":True}, "wins": {"Kolay":0,"Orta":0,"Zor":0}}
    
    if "streaks" not in veriler[isim]["ai"]: veriler[isim]["ai"]["streaks"] = {}
    if "wins" not in veriler[isim]["ai"]: veriler[isim]["ai"]["wins"] = {"Kolay":0,"Orta":0,"Zor":0}
    if "warrior_shields" not in veriler[isim]["ai"]: veriler[isim]["ai"]["warrior_shields"] = {"Kolay":True,"Orta":True,"Zor":True}

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
        veriler[isim][f"{streak_key}_protected"] = False

    elif sonuc == "kaybetti":
        buyucu_korudu = False
        if avatar_rol == "Büyücü" and streak > 0:
            prot_key = f"{streak_key}_protected"
            if not veriler[isim].get(prot_key, False):
                buyucu_korudu = True; veriler[isim][prot_key] = True; streak_mesaj = "✨ Büyücü Kalkanı Seriyi Korudu!"
        
        if not buyucu_korudu:
            if streak > 0: streak_mesaj = "❄️ Seri Bozuldu"
            streak = 0
        
        ceza_map = {"Kolay": {3: -6, 5: -3, 7: -1}, "Orta": {3: -3, 5: -2, 7: -1}, "Zor": {3: -1, 5: -1, 7: -1}}
        puan = ceza_map.get(zorluk, {}).get(hedef, -1)
        
        if avatar_rol == "Savaşçı":
            shields = player_ai.get("warrior_shields", {"Kolay":True,"Orta":True,"Zor":True})
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
        if hedef_set == 3: puan = 3
        elif hedef_set == 5: puan = 5
        elif hedef_set == 7: puan = 7
    elif sonuc == "kaybetti":
        if hedef_set == 3: puan = -3
        elif hedef_set == 5: puan = -2
        elif hedef_set == 7: puan = -1
    
    veriler[isim]["pvp"]["toplam_kupa"] += puan
    json_yaz(SKOR_DOSYASI, veriler)
    return puan

# --- OTO-LOGIN (SAĞLAMLAŞTIRILMIŞ) ---
# Çerezi okumak bazen zaman alır, o yüzden sayfa başında bekletiyoruz.
time.sleep(0.1)
cookie_token = cookie_manager.get(cookie="tkm_auth_token_v23")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'isim' not in st.session_state: st.session_state.isim = ""

# Eğer çerez varsa ve henüz giriş yapılmadıysa dene
if cookie_token and not st.session_state.logged_in:
    user_from_cookie = token_ile_giris(cookie_token)
    if user_from_cookie:
        st.session_state.logged_in = True
        st.session_state.isim = user_from_cookie
        # Verileri yükle
        v = json_oku(SKOR_DOSYASI)
        if user_from_cookie in v:
            st.session_state.avatar_rol = v[user_from_cookie].get("avatar_rol")
            st.session_state.avatar_ikon = AVATARLAR.get(st.session_state.avatar_rol, "👤")
            st.session_state.sayfa = 'ana_menu'
        else:
            st.session_state.sayfa = 'avatar_sec'
        st.rerun()

# Değişkenler
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'login'
if 'avatar_rol' not in st.session_state: st.session_state.avatar_rol = None
if 'avatar_ikon' not in st.session_state: st.session_state.avatar_ikon = None
if 'ai_state' not in st.session_state: st.session_state.ai_state = {'p_skor': 0, 'pc_skor': 0}
if 'oda_kodu' not in st.session_state: st.session_state.oda_kodu = None
if 'show_patch_notes' not in st.session_state: st.session_state.show_patch_notes = False

# ==========================
# SAYFALAR
# ==========================

def login_sayfasi():
    st.markdown("<h1 style='text-align: center;'>🔐 TAŞ KAĞIT MAKAS ARENA</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    with tab1:
        l_user = st.text_input("Kullanıcı Adı", key="l_user")
        l_pass = st.text_input("Şifre", type="password", key="l_pass")
        beni_hatirla = st.checkbox("Beni Hatırla (Çerez)")
        if st.button("GİRİŞ YAP", use_container_width=True):
            basari, token = kullanici_giris(l_user, l_pass)
            if basari:
                st.session_state.logged_in = True
                st.session_state.isim = l_user
                st.session_state.show_patch_notes = True
                
                if beni_hatirla:
                    cookie_manager.set("tkm_auth_token_v23", token, expires_at=None)
                
                veriler = json_oku(SKOR_DOSYASI)
                if l_user in veriler and "avatar_rol" in veriler[l_user]:
                    rol = veriler[l_user]["avatar_rol"]
                    st.session_state.avatar_rol = rol
                    st.session_state.avatar_ikon = AVATARLAR.get(rol, "👤")
                    st.session_state.sayfa = 'ana_menu'
                else: st.session_state.sayfa = 'avatar_sec'
                st.rerun()
            else: st.error("Hatalı bilgi!")
    with tab2:
        r_user = st.text_input("Kullanıcı Adı Belirle", key="r_user")
        r_pass = st.text_input("Şifre Belirle", type="password", key="r_pass")
        if st.button("KAYIT OL", use_container_width=True):
            if r_user and r_pass:
                basari, msj = kullanici_kayit(r_user, r_pass)
                if basari: st.success(msj)
                else: st.error(msj)
            else: st.warning("Boş bırakma.")

def avatar_secim_sayfasi():
    st.title(f"🛡️ Hoşgeldin {st.session_state.isim}!")
    st.info("Sınıfını seç!")
    cols = st.columns(2)
    for i, (rol, ikon) in enumerate(AVATARLAR.items()):
        with cols[i % 2]:
            st.markdown(f"<div style='font-size:40px; text-align:center;'>{ikon}</div>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='text-align:center;'>{rol}</h4>", unsafe_allow_html=True)
            st.info(SINIF_ACIKLAMALARI[rol])
            if st.button(f"SEÇ: {rol}", key=f"btn_{rol}", use_container_width=True):
                veriler = json_oku(SKOR_DOSYASI)
                if st.session_state.isim not in veriler:
                    veriler[st.session_state.isim] = {"avatar_rol": rol, "degisim_hakki": 1, "ai": {"toplam_kupa":0}, "pvp": {"toplam_kupa":0}}
                else:
                    veriler[st.session_state.isim]["avatar_rol"] = rol
                    veriler[st.session_state.isim]["degisim_hakki"] = 0
                json_yaz(SKOR_DOSYASI, veriler)
                st.session_state.avatar_rol = rol; st.session_state.avatar_ikon = ikon
                st.session_state.sayfa = 'ana_menu'; st.rerun()

def ana_menu():
    # --- GÜNCELLEME NOTLARI (POP-UP) ---
    # st.session_state.show_patch_notes True ise, ekranı kaplayan overlay göster
    if st.session_state.show_patch_notes:
        st.markdown("""
        <div class="modal-overlay"><div class="modal-content">
            <div class="modal-header">📢 GÜNCELLEME NOTLARI v23</div>
            <div class="modal-body">
                <div class="patch-item">✅ <b>Hata Düzeltildi:</b> 'Kapat' tuşu artık çalışıyor ve en üstte gözüküyor.</div>
                <div class="patch-item">🍪 <b>Beni Hatırla:</b> Sayfa yenilense (F5) bile hesabın açık kalır.</div>
                <div class="patch-item">🩹 <b>Yeni Sınıf:</b> Şifacı eklendi!</div>
                <div class="patch-item">🔄 <b>Karakter Değişimi:</b> 1 hak verildi.</div>
            </div>
        </div></div>
        """, unsafe_allow_html=True)
        
        # Butonu ortaya koyuyoruz, CSS ile z-index'i en yüksek yapıldı
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("❌ KAPAT VE OYUNA GİR", type="primary"):
                st.session_state.show_patch_notes = False
                st.rerun()
        
        # Eğer pop-up açıksa, alt tarafı göstermemek için return
        return

    st.markdown(f"<h1 style='text-align: center;'>🗿 📜 ✂️ TAŞ-KAĞIT-MAKAS ARENA</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>{st.session_state.avatar_ikon} {st.session_state.isim} ({st.session_state.avatar_rol})</h3>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🤖 Tek Kişilik")
        if st.button("YAPAY ZEKA İLE OYNA", use_container_width=True): st.session_state.sayfa = 'ai_giris'; st.rerun()
    with c2:
        st.markdown("### 👥 Çok Oyunculu")
        if st.button("KARŞILIKLI SAVAŞ (ONLINE)", use_container_width=True): st.session_state.sayfa = 'pvp_giris'; st.rerun()
    
    veriler = json_oku(SKOR_DOSYASI)
    hak = veriler.get(st.session_state.isim, {}).get("degisim_hakki", 1)
    st.write("---")
    if hak > 0:
        if st.button("⬅️ Karakter Değiştir (1 Hakkın Var)", use_container_width=True): st.session_state.sayfa = 'avatar_sec'; st.rerun()
    
    if st.button("🔒 Çıkış Yap", use_container_width=True):
        st.session_state.logged_in = False; st.session_state.isim = ""; 
        cookie_manager.delete("tkm_auth_token_v23")
        st.session_state.sayfa = 'login'; st.rerun()

# --- AI MODU ---
def ai_giris():
    st.markdown("<h2 style='text-align:center'>🤖 Yapay Zeka Modu</h2>", unsafe_allow_html=True)
    data = get_player_data(st.session_state.isim)
    kupa = data.get("ai", {}).get("toplam_kupa", 0) if data else 0
    st.markdown(f"<div class='kupa-gosterge'>🏆 Mevcut AI Kupan: {kupa}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: zorluk = st.radio("Zorluk:", ["Kolay", "Orta", "Zor"], horizontal=True)
    with c2: 
        hedef = st.radio("Set:", [3, 5, 7], format_func=lambda x: f"Bo{x}", horizontal=True)
        st.caption("ℹ️ Bo3: 1x | Bo5: 2x | Bo7: 3x Puan")
    
    if st.session_state.avatar_rol == "Savaşçı" and data and "ai" in data:
        shields = data["ai"].get("warrior_shields", {})
        cols = st.columns(3)
        for i, z in enumerate(["Kolay", "Orta", "Zor"]):
            durum = "✅" if shields.get(z, True) else "❌"
            stil = "kalkan-aktif" if shields.get(z, True) else "kalkan-kirik"
            cols[i].markdown(f"🛡️ {z}: <span class='{stil}'>{durum}</span>", unsafe_allow_html=True)

    if st.checkbox("🔥 Win Streak Göster"):
        if data and "ai" in data:
            streaks = data["ai"].get("streaks", {})
            if streaks:
                for k, v in streaks.items():
                    if v > 0: st.info(f"{k}: {v} Seri")
            else: st.caption("Aktif seri yok.")

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚔️ BAŞLA", use_container_width=True):
            st.session_state.ai_zorluk = zorluk; st.session_state.ai_hedef = hedef
            pc_rol = random.choice(list(AVATARLAR.keys()))
            st.session_state.ai_state = {'p_skor': 0, 'pc_skor': 0, 'mesaj': "Başla!", 'soz': "", 'bitti': False, 'okcu_hak': False, 'pc_okcu_hak': False, 'tank_hak': True, 'pc_tank_hak': True, 'sifaci_hak': True, 'pc_sifaci_hak': True, 'pc_rol': pc_rol, 'pc_ikon': AVATARLAR[pc_rol], 'p_hamle': None, 'pc_hamle': None}
            st.session_state.sayfa = 'ai_oyun'; st.rerun()
    with c2:
        if st.button("🏆 AI Liderlik", use_container_width=True): st.session_state.sayfa = 'liderlik_ai'; st.rerun()
    if st.button("Geri"): st.session_state.sayfa = 'ana_menu'; st.rerun()

def ai_oyun():
    s = st.session_state.ai_state
    c1, c2, c3 = st.columns([3, 1, 3])
    with c1: st.markdown(f"<div class='skor-kutu'><h3>{st.session_state.avatar_ikon} {st.session_state.isim}</h3><h1>{s['p_skor']}</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='skor-kutu'><h3>{s['pc_ikon']} (AI)</h3><h1>{s['pc_skor']}</h1></div>", unsafe_allow_html=True)
    st.progress(min(s['p_skor'] / st.session_state.ai_hedef, 1.0))
    
    if s['bitti']:
        baslik = "✅ KAZANDIN!" if s['p_skor'] >= st.session_state.ai_hedef else "❌ KAYBETTİN..."
        renk = "kazandi-box" if "KAZANDIN" in baslik else "kaybetti-box"
        st.markdown(f"<div class='{renk}'><h1>{baslik}</h1><p class='savas-sozu'>{s['soz']}</p></div>", unsafe_allow_html=True)
        st.markdown(s.get('sonuc_html', ''), unsafe_allow_html=True)
        if st.button("🔄 TEKRAR", use_container_width=True): st.session_state.ai_state['bitti']=False; st.session_state.ai_state['p_skor']=0; st.session_state.ai_state['pc_skor']=0; st.rerun()
        if st.button("🏠 MENÜ", use_container_width=True): st.session_state.sayfa = 'ana_menu'; st.rerun()
        return

    bilgi = st.empty()
    if s['p_hamle']:
        ic1, ic2 = st.columns(2)
        with ic1: st.caption("Sen"); resim_goster(s['p_hamle'])
        with ic2: st.caption("Rakip"); resim_goster(s['pc_hamle'])
    bilgi.info(s['mesaj'])

    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🗿 TAŞ"): ai_hamle_yap("Taş", bilgi)
    with c2: 
        if st.button("📜 KAĞIT"): ai_hamle_yap("Kağıt", bilgi)
    with c3: 
        if st.button("✂️ MAKAS"): ai_hamle_yap("Makas", bilgi)

def ai_hamle_yap(p_hamle, bilgi_placeholder):
    s = st.session_state.ai_state; s['p_hamle'] = p_hamle
    bilgi_placeholder.markdown('<p class="dusunuyor">...</p>', unsafe_allow_html=True); time.sleep(0.5)
    
    kazanan = {"Taş": "Makas", "Kağıt": "Taş", "Makas": "Kağıt"}
    z = st.session_state.ai_zorluk
    pc_hamle = random.choice(["Taş", "Kağıt", "Makas"])
    if z == "Kolay" and random.randint(1,100) <= 40: pc_hamle = {"Taş":"Makas", "Kağıt":"Taş", "Makas":"Kağıt"}[p_hamle]
    elif z == "Zor" and random.randint(1,100) <= 40: pc_hamle = {"Taş":"Kağıt", "Kağıt":"Makas", "Makas":"Taş"}[p_hamle]
    s['pc_hamle'] = pc_hamle
    
    tur_sonuc = ""
    my_rol = st.session_state.avatar_rol; pc_rol = s['pc_rol']
    
    if p_hamle == pc_hamle:
        if my_rol == "Okçu" and not s['okcu_hak']: s['p_skor']+=1; s['okcu_hak']=True; tur_sonuc="kazandi"; s['mesaj']="🏹 OKÇU!"
        elif pc_rol == "Okçu" and not s['pc_okcu_hak']: s['pc_skor']+=1; s['pc_okcu_hak']=True; tur_sonuc="kaybetti"; s['mesaj']="🏹 AI OKÇU!"
        else: tur_sonuc="berabere"; s['mesaj']="🤝 BERABERE"
    elif kazanan[p_hamle] == pc_hamle:
        if pc_rol == "Şifacı" and s['pc_sifaci_hak']: s['pc_sifaci_hak']=False; s['mesaj']="🩹 AI ŞİFACI HASARI ENGELLEDİ!"; tur_sonuc="kazandi" # Puan yok
        else:
            puan = 2 if (my_rol == "Tank" and s['tank_hak']) else 1
            if puan == 2: s['tank_hak'] = False; s['mesaj'] = "🚜 TANK +2!"
            else: s['mesaj'] = "✅ KAZANDIN!"
            s['p_skor']+=puan; tur_sonuc="kazandi"
    else:
        if my_rol == "Şifacı" and s['sifaci_hak']: s['sifaci_hak']=False; s['mesaj']="🩹 ŞİFACI KALKANI!"; tur_sonuc="kaybetti" # Puan yok
        else:
            puan = 2 if (pc_rol == "Tank" and s['pc_tank_hak']) else 1
            if puan == 2: s['pc_tank_hak'] = False; s['mesaj'] = "🚜 AI TANK +2!"
            else: s['mesaj'] = "❌ KAYBETTİN!"
            s['pc_skor']+=puan; tur_sonuc="kaybetti"
    
    s['soz'] = rastgele_soz(tur_sonuc)
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
            maclar = json_oku(MAC_DOSYASI)
            maclar[kod] = {
                "p1": st.session_state.isim, "p1_avatar": st.session_state.avatar_ikon, "p1_rol": st.session_state.avatar_rol,
                "p2": None, "p2_avatar": None, "p2_rol": None,
                "p1_puan": 0, "p2_puan": 0, "hedef": (hs // 2) + 1, "set_turu": hs,
                "p1_hamle": None, "p2_hamle": None,
                "p1_durum": "oynuyor", "p2_durum": "bekliyor", "son_mesaj": "...",
                "p1_tank": True, "p2_tank": True, "p1_sifaci": True, "p2_sifaci": True, "p1_okcu": True, "p2_okcu": True
            }
            json_yaz(MAC_DOSYASI, maclar)
            st.session_state.oda_kodu = kod; st.session_state.oyuncu_no = "p1"; st.session_state.pvp_hedef_set = hs
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
            else: st.error("Hata")
    if st.button("Geri"): st.session_state.sayfa = 'ana_menu'; st.rerun()

def pvp_lobi():
    st.title(f"🔑 Oda: {st.session_state.oda_kodu}")
    oda = json_oku(MAC_DOSYASI).get(st.session_state.oda_kodu)
    if not oda: st.error("Kapalı"); time.sleep(1); st.session_state.sayfa='pvp_giris'; st.rerun(); return
    if oda.get('p2') is None: time.sleep(2); st.rerun()
    st.success("Rakip Bulundu!"); time.sleep(1)
    if oda.get('p2'): st.session_state.sayfa='pvp_oyun'; st.rerun()

def pvp_oyun():
    kod=st.session_state.oda_kodu; ben=st.session_state.oyuncu_no; rakip = "p2" if ben == "p1" else "p1"
    maclar = json_oku(MAC_DOSYASI); oda = maclar.get(kod)
    if not oda: st.session_state.sayfa='pvp_giris'; st.rerun(); return
    
    if oda[f"{rakip}_durum"] == "cikti": st.error("Rakip gitti."); time.sleep(2); st.session_state.sayfa='ana_menu'; st.rerun(); return
    if (oda[f"{ben}_hamle"] and not oda[f"{rakip}_hamle"]): time.sleep(2); st.rerun()

    c1,c2,c3 = st.columns([3,1,3])
    with c1: st.markdown(f"<div class='skor-kutu'><h3>{oda.get('p1_avatar')}</h3><h1>{oda.get('p1_puan')}</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='skor-kutu'><h3>{oda.get('p2_avatar')}</h3><h1>{oda.get('p2_puan')}</h1></div>", unsafe_allow_html=True)
    st.info(f"📢 {oda.get('son_mesaj')}")
    
    if oda.get("son_p1_goster"):
        ic1, ic2 = st.columns(2)
        with ic1: st.caption(f"{oda.get('p1')}"); resim_goster(oda['son_p1_goster'], 80)
        with ic2: st.caption(f"{oda.get('p2')}"); resim_goster(oda['son_p2_goster'], 80)

    if oda.get('p1_puan') >= oda.get('hedef') or oda.get('p2_puan') >= oda.get('hedef'):
        kazanan = "p1" if oda.get('p1_puan') >= oda.get('hedef') else "p2"
        if kazanan == ben and not oda.get(f"{ben}_odul_alindi"):
            mac_sonu_hesapla_pvp(st.session_state.isim, st.session_state.avatar_rol, oda['set_turu'], "kazandi")
            maclar[kod][f"{ben}_odul_alindi"] = True; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        elif kazanan != ben and not oda.get(f"{ben}_odul_alindi"):
            mac_sonu_hesapla_pvp(st.session_state.isim, st.session_state.avatar_rol, oda['set_turu'], "kaybetti")
            maclar[kod][f"{ben}_odul_alindi"] = True; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        
        baslik = "✅ KAZANDIN!" if kazanan == ben else "❌ KAYBETTİN..."
        st.markdown(f"<h1>{baslik}</h1>", unsafe_allow_html=True)
        if st.button("Çık"): maclar[kod][f"{ben}_durum"]="cikti"; json_yaz(MAC_DOSYASI, maclar); st.session_state.sayfa='ana_menu'; st.rerun()
        return

    st.write("---")
    if oda.get(f"{ben}_hamle"): st.warning("Rakip Bekleniyor...")
    else:
        c1,c2,c3=st.columns(3)
        if c1.button("🗿 TAŞ"): maclar[kod][f"{ben}_hamle"]="Taş"; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        if c2.button("📜 KAĞIT"): maclar[kod][f"{ben}_hamle"]="Kağıt"; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        if c3.button("✂️ MAKAS"): maclar[kod][f"{ben}_hamle"]="Makas"; json_yaz(MAC_DOSYASI, maclar); st.rerun()
        
    if oda.get("p1_hamle") and oda.get("p2_hamle"):
        p1h, p2h = oda["p1_hamle"], oda["p2_hamle"]
        kazanan = "berabere"; 
        if (p1h=="Taş" and p2h=="Makas") or (p1h=="Kağıt" and p2h=="Taş") or (p1h=="Makas" and p2h=="Kağıt"): kazanan="p1"
        elif p1h!=p2h: kazanan="p2"
        
        # PVP Yetenek Mantığı
        p1_rol = oda["p1_rol"]; p2_rol = oda["p2_rol"]
        
        if kazanan == "berabere":
            if p1_rol == "Okçu" and oda["p1_okcu"]: oda["p1_puan"]+=1; oda["p1_okcu"]=False; oda["son_mesaj"]=f"{oda['p1']} OKÇU YETENEĞİ!"
            elif p2_rol == "Okçu" and oda["p2_okcu"]: oda["p2_puan"]+=1; oda["p2_okcu"]=False; oda["son_mesaj"]=f"{oda['p2']} OKÇU YETENEĞİ!"
            else: oda["son_mesaj"] = "Berabere!"
        elif kazanan == "p1":
            if p2_rol == "Şifacı" and oda["p2_sifaci"]: oda["p2_sifaci"]=False; oda["son_mesaj"]=f"🩹 {oda['p2']} HASARI ENGELLEDİ!"
            else:
                p = 2 if (p1_rol == "Tank" and oda["p1_tank"]) else 1
                if p==2: oda["p1_tank"]=False; oda["son_mesaj"]=f"🚜 {oda['p1']} TANK EZDİ!"
                else: oda["son_mesaj"]=f"{oda['p1']} Kazandı!"
                oda["p1_puan"] += p
        elif kazanan == "p2":
            if p1_rol == "Şifacı" and oda["p1_sifaci"]: oda["p1_sifaci"]=False; oda["son_mesaj"]=f"🩹 {oda['p1']} HASARI ENGELLEDİ!"
            else:
                p = 2 if (p2_rol == "Tank" and oda["p2_tank"]) else 1
                if p==2: oda["p2_tank"]=False; oda["son_mesaj"]=f"🚜 {oda['p2']} TANK EZDİ!"
                else: oda["son_mesaj"]=f"{oda['p2']} Kazandı!"
                oda["p2_puan"] += p
                
        oda["son_p1_goster"]=p1h; oda["son_p2_goster"]=p2h; oda["p1_hamle"]=None; oda["p2_hamle"]=None
        json_yaz(MAC_DOSYASI, maclar); st.rerun()

# --- LİDERLİK ---
def liderlik_sayfasi(mod):
    baslik = "🤖 YAPAY ZEKA" if mod == 'ai' else "👥 PVP"
    st.title(f"🏆 {baslik} LİDERLİK TABLOSU")
    veriler = json_oku(SKOR_DOSYASI)
    l = []
    for isim, d in veriler.items():
        rol = d.get("avatar_rol", "Bilinmiyor"); ikon = AVATARLAR.get(rol, "👤")
        if mod == 'ai' and "ai" in d:
            ai_d = d["ai"]
            l.append({
                "Avatar": ikon, "Oyuncu": isim, "🏆 Kupa": ai_d.get("toplam_kupa", 0),
                "Kolay W": ai_d.get("wins", {}).get("Kolay", 0),
                "Orta W": ai_d.get("wins", {}).get("Orta", 0),
                "Zor W": ai_d.get("wins", {}).get("Zor", 0)
            })
        elif mod == 'pvp' and "pvp" in d:
            l.append({"Avatar": ikon, "Oyuncu": isim, "🏆 Kupa": d["pvp"].get("toplam_kupa", 0)})
    
    if l:
        df = pd.DataFrame(l).sort_values(by="🏆 Kupa", ascending=False)
        df.index = range(1, len(df) + 1)
        st.table(df)
    else: st.warning("Veri yok.")
    
    if st.button("🏠 Geri Dön"): st.session_state.sayfa = 'ai_giris' if mod=='ai' else 'pvp_giris'; st.rerun()

# --- YÖNLENDİRME ---
if not st.session_state.logged_in:
    login_sayfasi()
elif st.session_state.sayfa == 'avatar_sec': avatar_secim_sayfasi()
elif st.session_state.sayfa == 'ana_menu': ana_menu()
elif st.session_state.sayfa == 'ai_giris': ai_giris()
elif st.session_state.sayfa == 'ai_oyun': ai_oyun()
elif st.session_state.sayfa == 'pvp_giris': pvp_giris()
elif st.session_state.sayfa == 'pvp_lobi': pvp_lobi()
elif st.session_state.sayfa == 'pvp_oyun': pvp_oyun()
elif st.session_state.sayfa == 'liderlik_ai': liderlik_sayfasi('ai')
elif st.session_state.sayfa == 'liderlik_pvp': liderlik_sayfasi('pvp')
