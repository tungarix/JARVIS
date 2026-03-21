import customtkinter as ctk
import ollama
import threading
import os
import subprocess
import webbrowser
import json
import re
import ctypes
import psutil
import platform
import socket
import schedule
import time
import keyboard
import pyautogui
from datetime import datetime
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BLUE = "#00BFFF"
BLUE2 = "#0099CC"
DARK_BLUE = "#003F6B"
BG = "#0A0D12"
BG2 = "#0D1420"
BG3 = "#111820"
WHITE = "#E8F4FD"
MUTED = "#4A7FA5"
USER_BALON = "#003F6B"
JARVIS_BALON = "#0D1A2A"

HAFIZA_DOSYASI = "hafiza.json"
SOHBET_KLASORU = "sohbetler"
GOREV_DOSYASI = "gorevler.json"
os.makedirs(SOHBET_KLASORU, exist_ok=True)

aktif_sohbet = {"id": None, "mesajlar": [], "baslik": "Yeni Sohbet"}

KOMUTLAR = [
    ("UYGULAMALAR", ["not defteri aç","hesap makinesi aç","chrome aç","görev yöneticisi aç","spotify aç"]),
    ("KLASÖRLER",   ["belgeler klasörünü aç","indirmeler klasörünü aç","resimler klasörünü aç"]),
    ("SİSTEM",      ["sistem bilgisi","pil durumu","disk alanı","açık uygulamaları listele","ağ durumu","internet hızı ölç"]),
    ("MOUSE/KLV",   ["mouse konumu","mouse ortala","ekran boyutu"]),
    ("DOSYA",       ["dosya oluştur [ad]","dosya sil [yol]","klasör oluştur [ad]"]),
    ("GÖREV",       ["görevleri listele","görev ekle [saat] [komut]","görevleri temizle"]),
    ("NOTLAR",      ["notları göster","notları temizle"]),
    ("WEB",         ["youtube aç","google'da ara","instagram aç","netflix aç"]),
    ("HAFIZA",      ["hafızayı göster","hafızayı temizle"]),
]

def hafiza_yukle():
    if os.path.exists(HAFIZA_DOSYASI):
        with open(HAFIZA_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"bilgiler": []}

def hafiza_kaydet(h):
    with open(HAFIZA_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)

def gorev_yukle():
    if os.path.exists(GOREV_DOSYASI):
        with open(GOREV_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def gorev_kaydet(g):
    with open(GOREV_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)

hafiza = hafiza_yukle()
gorevler = gorev_yukle()

def hafiza_ozeti():
    if not hafiza["bilgiler"]: return ""
    return "\n\nKullanıcı hakkında:\n" + "\n".join(f"- {b}" for b in hafiza["bilgiler"])

def sistem_promptu():
    saat = datetime.now().hour
    if saat < 12:
        selamlama = "Günaydın"
        vakit = "sabah"
    elif saat < 18:
        selamlama = "İyi günler"
        vakit = "öğleden sonra"
    else:
        selamlama = "İyi akşamlar"
        vakit = "akşam"

    isim = ""
    for b in hafiza["bilgiler"]:
        if "isim" in b.lower() or "adı" in b.lower() or "adım" in b.lower():
            parcalar = b.split()
            isim = parcalar[-1] if parcalar else ""
            break

    return f"""Sen JARVIS'sin — Just A Rather Very Intelligent System.
Iron Man'in JARVIS'i gibi zeki, sadık ve samimi bir asistansın.
Türkçe konuşuyorsun. Şu an {vakit} vakti.
{f"Kullanıcının adı {isim}." if isim else ""}

KİŞİLİK:
- Zeki ve özgüvenli konuş, ama kibirli olma
- Zaman zaman ince espri yap — aşırıya kaçma
- Kısa ve net cevaplar ver, gereksiz uzatma
- Eğer soruyu yanlış anladıysan veya emin değilsen, kibarca düzeltme iste
- "Üzgünüm", "Özür dilerim" gibi aşırı özür dolu ifadeler kullanma
- Cevapların doğal ve akıcı olsun, robot gibi konuşma

ÖRNEK ÜSLUP:
- "Tabii, hemen halledelim."
- "İlginç soru. Şöyle düşün..."
- "Bunu tam anlamadım — biraz daha açar mısın?"
- "Bu aslında oldukça basit..."

[HAFIZA] KURALLARI:
- SADECE kullanıcının kendi hakkındaki bilgilerini kaydet (isim, yaş, meslek, hobiler)
- Genel bilgileri ASLA kaydetme
- Kullanıcı açıkça söylemedikçe hafızaya EKLEME
- Format: [HAFIZA: bilgi]{hafiza_ozeti()}"""

messages = []

def sohbet_kaydet():
    if not aktif_sohbet["mesajlar"] or not aktif_sohbet["id"]: return
    with open(os.path.join(SOHBET_KLASORU, f"{aktif_sohbet['id']}.json"), "w", encoding="utf-8") as f:
        json.dump(aktif_sohbet, f, ensure_ascii=False, indent=2)

def sohbet_sil(sid):
    yol = os.path.join(SOHBET_KLASORU, f"{sid}.json")
    if os.path.exists(yol): os.remove(yol)

def sohbet_listesi():
    dosyalar = sorted([f for f in os.listdir(SOHBET_KLASORU) if f.endswith(".json")], reverse=True)
    sonuc = []
    for d in dosyalar[:30]:
        with open(os.path.join(SOHBET_KLASORU, d), "r", encoding="utf-8") as f:
            sonuc.append(json.load(f))
    return sonuc

def yeni_sohbet_baslat():
    aktif_sohbet["id"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    aktif_sohbet["mesajlar"] = []
    aktif_sohbet["baslik"] = "Yeni Sohbet"
    messages.clear()

def spotify_ac(arama=None):
    for yol in [os.path.join(os.getenv("APPDATA"), "Spotify", "Spotify.exe"),
                os.path.join(os.getenv("LOCALAPPDATA"), "Microsoft", "WindowsApps", "Spotify.exe")]:
        if os.path.exists(yol):
            subprocess.Popen([yol])
            if arama:
                time.sleep(3); webbrowser.open(f"spotify:search:{arama}")
            return
    webbrowser.open("https://open.spotify.com" + (f"/search/{arama}" if arama else ""))

def ag_durumu():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        net = psutil.net_io_counters()
        sent = net.bytes_sent // (1024*1024)
        recv = net.bytes_recv // (1024*1024)
        return f"Bilgisayar: {hostname}\nIP: {ip}\nGönderilen: {sent}MB\nAlınan: {recv}MB"
    except: return "Ağ bilgisi alınamadı."

def internet_hizi():
    try:
        webbrowser.open("https://www.speedtest.net")
        return "Speedtest.net açıldı — tarayıcıda hız testini başlat!"
    except:
        return "Tarayıcı açılamadı."

def gorev_zamanlayici():
    while True:
        schedule.run_pending()
        time.sleep(10)

threading.Thread(target=gorev_zamanlayici, daemon=True).start()

def bilgisayar_komutu(metin):
    m = metin.lower()

    if any(x in m for x in ["yardım","komutlar","ne yapabilirsin"]):
        return "Komut menüsü için ⌨ butonuna tıkla!"

    # UYGULAMALAR
    elif "not defteri" in m or "notepad" in m:
        subprocess.Popen("notepad.exe"); return "Not defteri açıldı!"
    elif "hesap makinesi" in m:
        subprocess.Popen("calc.exe"); return "Hesap makinesi açıldı!"
    elif "görev yönetici" in m:
        subprocess.Popen("taskmgr", shell=True); return "Görev yöneticisi açıldı!"
    elif "spotify" in m:
        arama = None
        for a in ["çal","oynat","ara"]:
            if a in m: arama = m.split(a)[-1].strip(); break
        spotify_ac(arama)
        return "Spotify açıldı!" + (f" '{arama}'..." if arama else "")
    elif "chrome" in m or "tarayıcı" in m:
        subprocess.Popen("chrome.exe", shell=True); return "Chrome açıldı!"
    elif "dosya yönetici" in m:
        subprocess.Popen("explorer.exe"); return "Dosya yöneticisi açıldı!"
    elif "ekran görüntüsü" in m:
        subprocess.Popen("snippingtool.exe"); return "Ekran alıntısı aracı açıldı!"

    # SİSTEM
    elif "kapatmayı iptal" in m:
        os.system("shutdown /a"); return "Kapatma iptal edildi!"
    elif "bilgisayarı kapat" in m or "bilgisayar kapat" in m:
        os.system("shutdown /s /t 10"); return "10 saniyede kapanacak!"
    elif "yeniden başlat" in m:
        os.system("shutdown /r /t 10"); return "Yeniden başlatılıyor!"
    elif "masaüstü" in m and "klasör" not in m:
        os.system("explorer shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}"); return "Masaüstü gösterildi!"

    # KLASÖRLER
    elif "klasör" in m and "aç" in m and "oluştur" not in m:
        if "belgeler" in m: subprocess.Popen(f"explorer {os.path.expanduser('~')}\\Documents"); return "Belgeler açıldı!"
        elif "masaüstü" in m: subprocess.Popen(f"explorer {os.path.expanduser('~')}\\Desktop"); return "Masaüstü açıldı!"
        elif "indirmeler" in m: subprocess.Popen(f"explorer {os.path.expanduser('~')}\\Downloads"); return "İndirmeler açıldı!"
        elif "resimler" in m: subprocess.Popen(f"explorer {os.path.expanduser('~')}\\Pictures"); return "Resimler açıldı!"
        else: subprocess.Popen("explorer.exe"); return "Dosya yöneticisi açıldı!"

    # SİSTEM BİLGİSİ
    elif "sistem bilgisi" in m:
        try: return f"Bilgisayar: {socket.gethostname()}\nIP: {socket.gethostbyname(socket.gethostname())}\nWindows: {platform.version()}\nİşlemci: {platform.processor()}"
        except: return "Sistem bilgisi alınamadı."
    elif "pil" in m or "batarya" in m:
        b = psutil.sensors_battery()
        if b: return f"Pil: %{b.percent:.0f} — {'Şarj oluyor' if b.power_plugged else 'Şarj olmuyor'}"
        return "Pil bilgisi alınamadı."
    elif "disk" in m and ("alan" in m or "doluluk" in m):
        sonuc = ""
        for disk in psutil.disk_partitions():
            try:
                k = psutil.disk_usage(disk.mountpoint)
                sonuc += f"{disk.mountpoint} → {k.total//(1024**3)}GB | Dolu: {k.used//(1024**3)}GB | Boş: {k.free//(1024**3)}GB\n"
            except: pass
        return sonuc.strip() if sonuc else "Disk bilgisi alınamadı."
    elif "açık uygulama" in m or "uygulamaları listele" in m:
        uyg = set()
        for proc in psutil.process_iter(['name']):
            try:
                n = proc.info['name']
                if n and n.endswith('.exe') and n not in ['svchost.exe','System','Registry','smss.exe','csrss.exe','wininit.exe','services.exe','lsass.exe','winlogon.exe','fontdrvhost.exe','dwm.exe']:
                    uyg.add(n.replace('.exe',''))
            except: pass
        return "Açık uygulamalar:\n" + "\n".join(f"• {a}" for a in sorted(list(uyg))[:20])
    elif "parlaklık artır" in m: os.system("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,80)"); return "Parlaklık artırıldı!"
    elif "parlaklık azalt" in m: os.system("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,40)"); return "Parlaklık azaltıldı!"
    elif "kapat" in m and any(x in m for x in ["chrome","firefox","notepad","spotify","discord"]):
        for u in ["chrome","firefox","notepad","spotify","discord"]:
            if u in m: os.system(f"taskkill /f /im {u}.exe"); return f"{u.capitalize()} kapatıldı!"
    elif "panodakini oku" in m or "panoyu oku" in m:
        try:
            r = tk.Tk(); r.withdraw(); ic = r.clipboard_get(); r.destroy()
            return f"Panodaki içerik:\n{ic}"
        except: return "Panoda metin bulunamadı."

    # AĞ
    elif "ağ durumu" in m or "internet durumu" in m:
        return ag_durumu()
    elif "internet hızı" in m or "hız testi" in m:
        return internet_hizi()

    # MOUSE / KLAVYe
    elif "mouse konumu" in m:
        x, y = pyautogui.position()
        return f"Mouse konumu: X={x}, Y={y}"
    elif "mouse ortala" in m or "mouse merkez" in m:
        sw, sh = pyautogui.size()
        pyautogui.moveTo(sw//2, sh//2, duration=0.5)
        return f"Mouse ekran ortasına taşındı ({sw//2}, {sh//2})"
    elif "ekran boyutu" in m:
        sw, sh = pyautogui.size()
        return f"Ekran boyutu: {sw}x{sh}"
    elif "mouse taşı" in m or "mouse git" in m:
        sayilar = re.findall(r'\d+', m)
        if len(sayilar) >= 2:
            pyautogui.moveTo(int(sayilar[0]), int(sayilar[1]), duration=0.5)
            return f"Mouse {sayilar[0]},{sayilar[1]} konumuna taşındı!"
        return "Koordinat belirt. Örnek: 'mouse taşı 500 300'"
    elif "tıkla" in m and ("sol" in m or "sağ" in m or "çift" in m):
        if "çift" in m: pyautogui.doubleClick(); return "Çift tıklandı!"
        elif "sağ" in m: pyautogui.rightClick(); return "Sağ tıklandı!"
        else: pyautogui.click(); return "Sol tıklandı!"
    elif "klavye yaz" in m or "yaz klavye" in m:
        yazi = metin.lower().replace("klavye yaz","").replace("yaz klavye","").strip()
        if yazi: pyautogui.write(yazi, interval=0.05); return f"Yazıldı: {yazi}"
        return "Ne yazayım? Örnek: 'klavye yaz merhaba'"
    elif "kopyala" in m and "hepsini" in m:
        pyautogui.hotkey('ctrl', 'a'); pyautogui.hotkey('ctrl', 'c')
        return "Tüm metin kopyalandı!"
    elif "yapıştır" in m:
        pyautogui.hotkey('ctrl', 'v'); return "Yapıştırıldı!"
    elif "geri al" in m:
        pyautogui.hotkey('ctrl', 'z'); return "Geri alındı!"

    # DOSYA İŞLEMLERİ
    elif "dosya oluştur" in m:
        ad = metin.replace("dosya oluştur","").replace("Dosya oluştur","").strip()
        if ad:
            yol = os.path.join(os.path.expanduser("~"), "Desktop", ad)
            with open(yol, "w", encoding="utf-8") as f: f.write("")
            return f"Dosya oluşturuldu: {yol}"
        return "Dosya adı belirt. Örnek: 'dosya oluştur notlar.txt'"
    elif "klasör oluştur" in m:
        ad = metin.replace("klasör oluştur","").replace("Klasör oluştur","").strip()
        if ad:
            yol = os.path.join(os.path.expanduser("~"), "Desktop", ad)
            os.makedirs(yol, exist_ok=True)
            return f"Klasör oluşturuldu: {yol}"
        return "Klasör adı belirt. Örnek: 'klasör oluştur projeler'"
    elif "dosya sil" in m:
        yol = metin.replace("dosya sil","").replace("Dosya sil","").strip()
        if yol and os.path.exists(yol):
            os.remove(yol); return f"Dosya silindi: {yol}"
        return f"Dosya bulunamadı: {yol}"
    elif "klasör sil" in m:
        yol = metin.replace("klasör sil","").replace("Klasör sil","").strip()
        if yol and os.path.exists(yol):
            import shutil; shutil.rmtree(yol); return f"Klasör silindi: {yol}"
        return f"Klasör bulunamadı: {yol}"

    # GÖREV ZAMANLAYICI
    elif "görev ekle" in m or "görev kur" in m:
        parcalar = metin.split()
        saatler = [p for p in parcalar if re.match(r'\d{2}:\d{2}', p)]
        if saatler:
            saat = saatler[0]
            komut = metin.split(saat)[-1].strip()
            gorev = {"saat": saat, "komut": komut, "id": datetime.now().strftime("%H%M%S")}
            gorevler.append(gorev)
            gorev_kaydet(gorevler)
            schedule.every().day.at(saat).do(lambda k=komut: bilgisayar_komutu(k))
            return f"Görev eklendi: {saat} → {komut}"
        return "Saat belirt. Örnek: 'görev ekle 09:00 spotify aç'"
    elif "görevleri listele" in m or "görevler" in m:
        if gorevler:
            return "Aktif görevler:\n" + "\n".join(f"• {g['saat']} → {g['komut']}" for g in gorevler)
        return "Henüz görev yok."
    elif "görevleri temizle" in m:
        gorevler.clear(); gorev_kaydet(gorevler); schedule.clear()
        return "Tüm görevler temizlendi!"

    # NOTLAR
    elif "notları temizle" in m:
        nf = os.path.join(os.path.expanduser("~"), "jarvis_notlar.txt")
        if os.path.exists(nf): os.remove(nf)
        return "Notlar silindi!"
    elif "notları göster" in m or "notlarım" in m:
        nf = os.path.join(os.path.expanduser("~"), "jarvis_notlar.txt")
        if os.path.exists(nf):
            with open(nf, "r", encoding="utf-8") as f: notlar = f.read().strip()
            return ("Notların:\n" + notlar) if notlar else "Henüz not yok."
        return "Henüz not yok."
    elif "not al" in m or "not ekle" in m:
        icerik = metin
        for x in ["not al","not ekle","Not al","Not ekle"]: icerik = icerik.replace(x,"")
        icerik = icerik.strip()
        if icerik:
            nf = os.path.join(os.path.expanduser("~"), "jarvis_notlar.txt")
            with open(nf, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}] {icerik}\n")
            return f"Not kaydedildi: {icerik}"
        return "Ne not alayım?"

    # ZAMANLAYICI
    elif "zamanlayıcı" in m or "alarm" in m:
        sayilar = re.findall(r'\d+', m)
        if sayilar:
            sure = int(sayilar[0]); birim = "saniye" if "saniye" in m else "dakika"
            toplam = sure if birim == "saniye" else sure * 60
            def zaman():
                time.sleep(toplam)
                ctypes.windll.user32.MessageBoxW(0, f"⏰ {sure} {birim} doldu!", "JARVIS", 0x40)
            threading.Thread(target=zaman, daemon=True).start()
            return f"⏰ {sure} {birim} zamanlayıcı kuruldu!"
        return "Kaç dakika?"

    # WEB
    elif "son indirilen" in m:
        ind = os.path.join(os.path.expanduser("~"), "Downloads")
        dosyalar = [os.path.join(ind, f) for f in os.listdir(ind) if os.path.isfile(os.path.join(ind, f))]
        if dosyalar: son = max(dosyalar, key=os.path.getmtime); os.startfile(son); return f"Açıldı: {os.path.basename(son)}"
        return "İndirmeler klasörü boş."
    elif "hava durumu" in m:
        sehir = m.replace("hava durumu","").strip()
        webbrowser.open(f"https://www.google.com/search?q={sehir}+hava+durumu")
        return f"{sehir.capitalize()} hava durumu!" if sehir else "Hava durumu açıldı!"
    elif "youtube" in m:
        arama = m.replace("youtube","").replace("aç","").replace("ara","").strip()
        if arama: webbrowser.open(f"https://www.youtube.com/results?search_query={arama}"); return f"YouTube: '{arama}'"
        webbrowser.open("https://www.youtube.com"); return "YouTube açıldı!"
    elif "google" in m and "ara" in m:
        arama = m.replace("google","").replace("ara","").replace("'da","").replace("'de","").strip()
        if arama: webbrowser.open(f"https://www.google.com/search?q={arama}"); return f"Google: '{arama}'"
        webbrowser.open("https://www.google.com"); return "Google açıldı!"
    elif "aç" in m and any(s in m for s in ["twitter","instagram","facebook","reddit","github","linkedin","twitch","netflix","discord"]):
        siteler = {"twitter":"https://twitter.com","instagram":"https://instagram.com","facebook":"https://facebook.com","reddit":"https://reddit.com","github":"https://github.com","linkedin":"https://linkedin.com","twitch":"https://twitch.tv","netflix":"https://netflix.com","discord":"https://discord.com/app"}
        for site, url in siteler.items():
            if site in m: webbrowser.open(url); return f"{site.capitalize()} açıldı!"

    # HAFIZA
    elif "hafızayı göster" in m or "ne biliyorsun" in m:
        if hafiza["bilgiler"]: return "Hakkında bildiklerim:\n" + "\n".join(f"• {b}" for b in hafiza["bilgiler"])
        return "Henüz hafıza yok."
    elif "hafızayı temizle" in m:
        hafiza["bilgiler"] = []; hafiza_kaydet(hafiza); return "Hafıza temizlendi!"

    return None

# ── ANA PENCERE ──────────────────────────────────────────────
app = ctk.CTk()
app.title("JARVIS")
app.geometry("1200x750")
app.configure(fg_color=BG)
app.resizable(True, True)
app.withdraw()

# ── SPLASH ───────────────────────────────────────────────────
splash = ctk.CTkToplevel(app)
splash.overrideredirect(True)
sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
splash.geometry(f"500x300+{(sw-500)//2}+{(sh-300)//2}")
splash.configure(fg_color=BG)
splash.lift(); splash.attributes("-topmost", True)

ctk.CTkLabel(splash, text="⬡", font=ctk.CTkFont("Consolas", 60), text_color=BLUE).pack(pady=(30,0))
stitle = ctk.CTkLabel(splash, text="", font=ctk.CTkFont("Consolas", 36, "bold"), text_color=BLUE)
stitle.pack()
ctk.CTkLabel(splash, text="Just A Rather Very Intelligent System", font=ctk.CTkFont("Consolas", 11), text_color=MUTED).pack(pady=(4,0))
sstatus = ctk.CTkLabel(splash, text="Başlatılıyor...", font=ctk.CTkFont("Consolas", 11), text_color=MUTED)
sstatus.pack(pady=(16,0))
sbar = ctk.CTkProgressBar(splash, width=300, height=4, fg_color=BG2, progress_color=BLUE)
sbar.pack(pady=(8,0)); sbar.set(0)

ai = [0]
def anim():
    t = "JARVIS"
    if ai[0] <= len(t): stitle.configure(text=t[:ai[0]]); ai[0] += 1; splash.after(80, anim)
anim()

def sg(v,t): sbar.set(v); sstatus.configure(text=t); splash.update()
def sb(): splash.destroy(); app.deiconify(); build_ui()

splash.after(400,  lambda: sg(0.25,"Modüller yükleniyor..."))
splash.after(900,  lambda: sg(0.50,"Ollama hazırlanıyor..."))
splash.after(1400, lambda: sg(0.75,"Görevler yükleniyor..."))
splash.after(1900, lambda: sg(1.00,"Hazır!"))
splash.after(2300, sb)

def build_ui():
    header = ctk.CTkFrame(app, fg_color=BG2, corner_radius=0, height=56)
    header.pack(fill="x")
    header.pack_propagate(False)
    ctk.CTkLabel(header, text="⬡  JARVIS", font=ctk.CTkFont("Consolas", 20, "bold"), text_color=BLUE).pack(side="left", padx=20)
    clock_lbl = ctk.CTkLabel(header, text="", font=ctk.CTkFont("Consolas", 11), text_color=MUTED)
    clock_lbl.pack(side="right", padx=16)
    komut_btn = ctk.CTkButton(header, text="⌨ Komutlar", width=110, height=32,
        font=ctk.CTkFont("Consolas", 11), fg_color=BG3, hover_color=DARK_BLUE,
        text_color=BLUE, corner_radius=6)
    komut_btn.pack(side="right", padx=(0,8))

    main = ctk.CTkFrame(app, fg_color="transparent")
    main.pack(fill="both", expand=True)

    sol = ctk.CTkFrame(main, fg_color=BG2, width=240, corner_radius=0)
    sol.pack(side="left", fill="y")
    sol.pack_propagate(False)

    yeni_btn = ctk.CTkButton(sol, text="＋  Yeni Sohbet", height=38,
        font=ctk.CTkFont("Consolas", 12, "bold"),
        fg_color=DARK_BLUE, hover_color="#005A9E", text_color=BLUE, corner_radius=8)
    yeni_btn.pack(fill="x", padx=10, pady=(14,6))

    ctk.CTkLabel(sol, text="SOHBETLER", font=ctk.CTkFont("Consolas", 9, "bold"), text_color=MUTED).pack(anchor="w", padx=14, pady=(6,2))

    gecmis_scroll = ctk.CTkScrollableFrame(sol, fg_color="transparent")
    gecmis_scroll.pack(fill="both", expand=True, padx=6)

    cpu_lbl = ctk.CTkLabel(sol, text="CPU:  --%", font=ctk.CTkFont("Consolas", 10), text_color="#7ABFDF")
    cpu_lbl.pack(anchor="w", padx=14)
    cpu_bar = ctk.CTkProgressBar(sol, width=210, height=3, fg_color=BG3, progress_color=BLUE)
    cpu_bar.pack(padx=14, pady=(1,4)); cpu_bar.set(0)
    ram_lbl = ctk.CTkLabel(sol, text="RAM: --%", font=ctk.CTkFont("Consolas", 10), text_color="#7ABFDF")
    ram_lbl.pack(anchor="w", padx=14)
    ram_bar = ctk.CTkProgressBar(sol, width=210, height=3, fg_color=BG3, progress_color=BLUE2)
    ram_bar.pack(padx=14, pady=(1,12)); ram_bar.set(0)

    def sistem_guncelle():
        try:
            cpu = psutil.cpu_percent(interval=None); ram = psutil.virtual_memory().percent
            cpu_lbl.configure(text=f"CPU:  {cpu:.0f}%"); ram_lbl.configure(text=f"RAM: {ram:.0f}%")
            cpu_bar.set(cpu/100); ram_bar.set(ram/100)
        except: pass
        app.after(2000, sistem_guncelle)

    sag = ctk.CTkFrame(main, fg_color="transparent")
    sag.pack(side="left", fill="both", expand=True)

    sohbet_baslik = ctk.CTkLabel(sag, text="Yeni Sohbet", font=ctk.CTkFont("Consolas", 12), text_color=MUTED)
    sohbet_baslik.pack(anchor="w", padx=20, pady=(8,0))

    chat_scroll = ctk.CTkScrollableFrame(sag, fg_color=BG, scrollbar_button_color=BG2)
    chat_scroll.pack(padx=0, pady=(4,0), fill="both", expand=True)

    typing_lbl = ctk.CTkLabel(sag, text="", font=ctk.CTkFont("Consolas", 11), text_color=MUTED)
    typing_lbl.pack(anchor="w", padx=20)

    bottom_frame = ctk.CTkFrame(sag, fg_color="transparent")
    bottom_frame.pack(fill="x", padx=20, pady=(4,16))

    input_frame = ctk.CTkFrame(bottom_frame, fg_color=BG2, corner_radius=24, height=52)
    input_frame.pack(fill="x")
    input_frame.pack_propagate(False)

    entry = ctk.CTkEntry(input_frame, placeholder_text="JARVIS'e bir şey sor veya komut ver...",
        font=ctk.CTkFont("Consolas", 13), fg_color="transparent", border_width=0,
        text_color=WHITE, placeholder_text_color="#2A5A7A", height=44)
    entry.pack(side="left", fill="x", expand=True, padx=(20,8), pady=4)

    send_btn = ctk.CTkButton(input_frame, text="↑", width=36, height=36,
        font=ctk.CTkFont(size=18, weight="bold"),
        fg_color=DARK_BLUE, hover_color="#005A9E", text_color=BLUE, corner_radius=18)
    send_btn.pack(side="right", padx=(0,8), pady=8)

    # KOMUT POPUP
    popup_acik = [False]
    komut_popup = tk.Toplevel(app)
    komut_popup.withdraw()
    komut_popup.overrideredirect(True)
    komut_popup.configure(bg="#0D1420")
    komut_popup.attributes("-topmost", True)

    popup_inner = ctk.CTkScrollableFrame(komut_popup, fg_color=BG2, width=270, height=390)
    popup_inner.pack(fill="both", expand=True, padx=4, pady=4)

    def komut_popup_doldur():
        for w in popup_inner.winfo_children(): w.destroy()
        for baslik, komutlar in KOMUTLAR:
            ctk.CTkLabel(popup_inner, text=baslik, font=ctk.CTkFont("Consolas", 9, "bold"), text_color=MUTED).pack(anchor="w", pady=(8,2), padx=4)
            for k in komutlar:
                ctk.CTkButton(popup_inner, text=k, font=ctk.CTkFont("Consolas", 11),
                    fg_color=BG3, hover_color=DARK_BLUE, text_color="#7ABFDF",
                    anchor="w", height=28, corner_radius=6,
                    command=lambda x=k: [komut_gonder(x), kapat_popup()]).pack(fill="x", pady=1)

    def kapat_popup():
        komut_popup.withdraw(); popup_acik[0] = False

    def toggle_popup():
        if popup_acik[0]:
            kapat_popup()
        else:
            app.update_idletasks()
            bx = komut_btn.winfo_rootx()
            by = komut_btn.winfo_rooty() + komut_btn.winfo_height() + 6
            px = max(10, bx - 170)
            komut_popup.geometry(f"290x410+{px}+{by}")
            komut_popup.deiconify(); komut_popup.lift()
            popup_acik[0] = True

    komut_btn.configure(command=toggle_popup)

    def add_message(sender, text):
        is_user = sender == "Sen"
        outer = ctk.CTkFrame(chat_scroll, fg_color="transparent")
        outer.pack(fill="x", padx=12, pady=4)
        if is_user:
            ctk.CTkFrame(outer, fg_color="transparent").pack(side="left", fill="x", expand=True)
            bubble = ctk.CTkFrame(outer, fg_color=USER_BALON, corner_radius=16)
            bubble.pack(side="right", padx=(80,0))
            ctk.CTkLabel(bubble, text=text, font=ctk.CTkFont("Consolas", 13),
                text_color=WHITE, wraplength=420, justify="left").pack(padx=14, pady=10)
        else:
            ico = ctk.CTkLabel(outer, text="⬡", font=ctk.CTkFont("Consolas", 14, "bold"), text_color=BLUE)
            ico.pack(side="left", anchor="n", padx=(0,8), pady=10)
            bubble = ctk.CTkFrame(outer, fg_color=JARVIS_BALON, corner_radius=16)
            bubble.pack(side="left", padx=(0,80))
            ctk.CTkLabel(bubble, text=text, font=ctk.CTkFont("Consolas", 13),
                text_color="#A8D8F0", wraplength=500, justify="left").pack(padx=14, pady=10)
        app.after(50, lambda: chat_scroll._parent_canvas.yview_moveto(1.0))

    def gecmis_paneli_guncelle():
        for w in gecmis_scroll.winfo_children(): w.destroy()
        sohbetler = sohbet_listesi()
        if not sohbetler:
            ctk.CTkLabel(gecmis_scroll, text="Henüz sohbet yok", font=ctk.CTkFont("Consolas", 10), text_color=MUTED).pack(anchor="w", padx=4, pady=8)
            return
        for s in sohbetler:
            satir = ctk.CTkFrame(gecmis_scroll, fg_color="transparent")
            satir.pack(fill="x", pady=1)
            baslik = s.get("baslik","Sohbet")[:22]
            rid = s.get("id","")
            tarih = f"{rid[6:8]}.{rid[4:6]}.{rid[:4]}" if len(rid) >= 8 else ""
            ctk.CTkButton(satir, text=f"{baslik}\n{tarih}",
                font=ctk.CTkFont("Consolas", 10),
                fg_color=BG3, hover_color="#0D2A3A", text_color="#7ABFDF",
                anchor="w", height=44, corner_radius=8,
                command=lambda sv=s: sohbet_yukle_ui(sv)).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(satir, text="✕", width=28, height=44,
                font=ctk.CTkFont(size=11), fg_color="transparent",
                hover_color="#2A0A0A", text_color="#FF4444", corner_radius=8,
                command=lambda sid=s["id"]: sil_sohbet(sid)).pack(side="right")

    def sil_sohbet(sid):
        sohbet_sil(sid)
        if aktif_sohbet["id"] == sid: yeni_sohbet()
        gecmis_paneli_guncelle()

    def sohbet_yukle_ui(s):
        messages.clear()
        aktif_sohbet["id"] = s["id"]
        aktif_sohbet["mesajlar"] = s["mesajlar"]
        aktif_sohbet["baslik"] = s.get("baslik","Sohbet")
        sohbet_baslik.configure(text=aktif_sohbet["baslik"])
        for w in chat_scroll.winfo_children(): w.destroy()
        for msg in s["mesajlar"]:
            add_message(msg["sender"], msg["text"])
            messages.append({"role": "user" if msg["sender"]=="Sen" else "assistant", "content": msg["text"]})

    def yeni_sohbet():
        sohbet_kaydet()
        yeni_sohbet_baslat()
        for w in chat_scroll.winfo_children(): w.destroy()
        sohbet_baslik.configure(text="Yeni Sohbet")
        saat = datetime.now().hour
        if saat < 12:
            selamlama = "Günaydın"
        elif saat < 18:
            selamlama = "İyi günler"
        else:
            selamlama = "İyi akşamlar"

        isim = ""
        for b in hafiza["bilgiler"]:
            if "isim" in b.lower() or "adı" in b.lower() or "adım" in b.lower():
                isim = " " + b.split()[-1]
                break

        add_message("JARVIS", f"{selamlama}{isim}! Sistemler aktif ve hazır. Nasıl yardımcı olabilirim?")
        gecmis_paneli_guncelle()
        entry.focus()

    def komut_gonder(k):
        entry.delete(0,"end"); entry.insert(0, k); send_message()

    def send_message():
        user_input = entry.get().strip()
        if not user_input: return
        entry.delete(0,"end")
        if not aktif_sohbet["id"]: yeni_sohbet_baslat()

        add_message("Sen", user_input)
        aktif_sohbet["mesajlar"].append({"sender":"Sen","text":user_input})
        if len(aktif_sohbet["mesajlar"]) == 1:
            aktif_sohbet["baslik"] = user_input[:40]
            sohbet_baslik.configure(text=aktif_sohbet["baslik"])

        komut = bilgisayar_komutu(user_input)
        if komut:
            add_message("JARVIS", komut)
            aktif_sohbet["mesajlar"].append({"sender":"JARVIS","text":komut})
            sohbet_kaydet(); gecmis_paneli_guncelle(); return

        send_btn.configure(state="disabled")
        messages.append({"role":"user","content":user_input})

        def get_resp():
            typing_lbl.configure(text="  ● JARVIS yazıyor...")
            resp = ollama.chat(
                model="qwen2.5:3b",
                messages=[{"role":"system","content":sistem_promptu()}]+messages,
                options={"num_ctx":2048,"num_predict":256,"temperature":0.7}
            )
            reply = resp["message"]["content"]
            eslesme = re.findall(r'\[HAFIZA[:\]]\s*(.+?)[\].]', reply)
            if eslesme:
                for mm in eslesme:
                    mm = mm.strip()
                    if mm and mm not in hafiza["bilgiler"]: hafiza["bilgiler"].append(mm)
                hafiza_kaydet(hafiza)
            reply = re.sub(r'\[HAFIZA[^\]]*\][^\n]*', '', reply).strip()
            reply = re.sub(r'\[HAFIZA\].*', '', reply, flags=re.DOTALL).strip()
            messages.append({"role":"assistant","content":reply})
            aktif_sohbet["mesajlar"].append({"sender":"JARVIS","text":reply})
            sohbet_kaydet(); gecmis_paneli_guncelle()
            typing_lbl.configure(text="")
            add_message("JARVIS", reply)
            send_btn.configure(state="normal")
            entry.focus()

        threading.Thread(target=get_resp, daemon=True).start()

    send_btn.configure(command=send_message)
    entry.bind("<Return>", lambda e: send_message())
    yeni_btn.configure(command=yeni_sohbet)

    def update_clock():
        clock_lbl.configure(text=datetime.now().strftime("%H:%M:%S  |  %d.%m.%Y"))
        app.after(1000, update_clock)

    yeni_sohbet_baslat()
    saat = datetime.now().hour
    if saat < 12:
        selamlama = "Günaydın"
    elif saat < 18:
        selamlama = "İyi günler"
    else:
        selamlama = "İyi akşamlar"
    isim = ""
    for b in hafiza["bilgiler"]:
        if "isim" in b.lower() or "adı" in b.lower() or "adım" in b.lower():
            isim = " " + b.split()[-1]
            break
    add_message("JARVIS", f"{selamlama}{isim}! Sistemler aktif ve hazır. Nasıl yardımcı olabilirim?")
    gecmis_paneli_guncelle()
    komut_popup_doldur()
    update_clock()
    sistem_guncelle()
    entry.focus()

app.mainloop()