import json, os, re, smtplib, urllib.request
from email.mime.text import MIMEText

URL = "https://trouverunlogement.lescrous.fr/tools/48/search?bounds=6.134292_48.7092349_6.2126188_48.666906&locationName=Nancy+%2854000%29"
BASE = "https://trouverunlogement.lescrous.fr"
STATE = "seen.json"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")

# tous les liens de logements de la page
current = sorted(set(re.findall(r'/tools/48/accommodations/\d+', html)))
print(f"{len(current)} logements trouvés")

seen = json.load(open(STATE)) if os.path.exists(STATE) else None
json.dump(current, open(STATE, "w"), indent=1)

if seen is None:
    print("Premier lancement : liste enregistrée, pas de notif.")
    raise SystemExit

new = [u for u in current if u not in seen]
if not new:
    print("Rien de nouveau.")
    raise SystemExit

links = "\n".join(BASE + u for u in new)
msg_text = f"{len(new)} nouveau(x) logement(s) Crous à Nancy :\n\n{links}\n\nRecherche : {URL}"
print(msg_text)

# Notif téléphone via ntfy (si configuré)
topic = os.environ.get("NTFY_TOPIC")
if topic:
    r = urllib.request.Request(f"https://ntfy.sh/{topic}", data=msg_text.encode(),
        headers={"Title": "Nouveau logement Crous !", "Click": BASE + new[0]})
    urllib.request.urlopen(r, timeout=30)

# Mail via Gmail (si configuré)
user, pwd = os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_APP_PASSWORD")
if user and pwd:
    m = MIMEText(msg_text)
    m["Subject"] = "🏠 Nouveau logement Crous à Nancy"
    m["From"] = m["To"] = user
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.send_message(m)
