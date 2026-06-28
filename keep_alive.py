from flask import Flask
from threading import Thread

# יצירת שרת אינטרנט קטן
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7! Developed by Aaharon The Gamer"

def run():
    # הרצת השרת על פורט 8080 (סטנדרטי להוסטים)
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # הרצת השרת בנתיב נפרד (Thread) כדי שלא יתקע את הבוט של דיסקורד
    t = Thread(target=run)
    t.start()
