import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
import urllib.request
import json

# קריאת משתני המערכת מ-Railway
TOKEN = os.environ.get("DISCORD_TOKEN")
CFX_ID = os.environ.get("CFX_ID")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# הלינק הישיר ל-GIF שלך בגיטהאב שיופיע ברקע של ההודעות
BACKGROUND_GIF = "https://githubusercontent.com"

# מזהי רולים וחדרים מתוך השרת שלך
VERIFY_ROLE_ID = 1514394547554226388
STATUS_CHANNEL_ID = 1520889866496249906
VERIFY_CHANNEL_ID = 1514409408489328801
WELCOME_CHANNEL_ID = 1514409410661842944

# מזהה ההודעה של הסטטוס למניעת הצפות של הצ'אט
STATUS_MESSAGE_ID = None

# ==========================================
# 🌐 שרת אינטרנט פנימי למניעת קריסה (Keep Alive)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7! Developed by Aaharon The Gamer"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==========================================
# 🛡️ מערכת אימות (VERIFY) - כפתור ולוגיקה
# ==========================================

class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="להתחלת אימות / Verify", style=discord.ButtonStyle.success, emoji="🛡️", custom_id="verify_btn_67")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # מציאת הרול לפי ה-ID המדויק שסיפקת
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role:
            return await interaction.response.send_message("שגיאה: רול האימות לא נמצא בשרת.", ephemeral=True)

        if role in interaction.user.roles:
            await interaction.response.send_message("אתה כבר מאומת במערכת! 🧭", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"האימות בוצע בהצלחה! קיבלת את הרול **{role.name}** ✨", ephemeral=True)

@bot.tree.command(name="setup_verify", description="שולח את הודעת האימות המעוצבת")
@app_commands.checks.has_permissions(administrator=True)
async def setup_verify(interaction: discord.Interaction):
    channel = interaction.guild.get_channel(VERIFY_CHANNEL_ID)
    if not channel:
        return await interaction.response.send_message("שגיאה: חדר האימות לא נמצא.", ephemeral=True)

    embed = discord.Embed(
        title="🛡️ מערכת אימות הגנה - שרת 67",
        description=(
            "ברוכים הבאים לשרת! כדי לקבל גישה מלאה לשאר החדרים והערוצים בשרת, "
            "עליכם לעבור אימות בסיסי נגד בוטים וחשבונות פיקטיביים.\n\n"
            "**לחצו על הכפתור הירוק למטה כדי להתחיל!**"
        ),
        color=0x2f3136
    )
    embed.set_image(url=BACKGROUND_GIF)
    embed.set_footer(text="Developed by Aaharon The Gamer", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    await channel.send(embed=embed, view=VerifyButton())
    await interaction.response.send_message("מערכת האימות הוצבה בהצלחה!", ephemeral=True)


# ==========================================
# 🎮 מערכת סטטוס שרת אוטומטית (SERVER STATUS)
# ==========================================

class StatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="צפה ברשימת שחקנים", style=discord.ButtonStyle.blurple, emoji="👥", custom_id="status_players_btn")
    async def view_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔍 טוען את רשימת השחקנים המחוברים...", ephemeral=True)

@bot.tree.command(name="setup_status", description="שולח את הודעת סטטוס השרת הראשונית")
@app_commands.checks.has_permissions(administrator=True)
async def setup_status(interaction: discord.Interaction):
    global STATUS_MESSAGE_ID
    channel = interaction.guild.get_channel(STATUS_CHANNEL_ID)
    if not channel:
        return await interaction.response.send_message("שגיאה: חדר הסטטוס לא נמצא.", ephemeral=True)

    embed = discord.Embed(title="סטטוס שרת FiveM", color=0x2f3136)
    embed.add_field(name="שחקנים", value="🟢 בודק נתונים...", inline=True)
    embed.add_field(name="סטטוס", value="🟢 פעיל", inline=True)
    embed.add_field(name="חיבור מהיר", value="`cfx.re/join/xedygr`", inline=False)
    embed.set_image(url=BACKGROUND_GIF)
    embed.set_footer(text="Developed by Aaharon The Gamer")

    msg = await channel.send(embed=embed, view=StatusView())
    STATUS_MESSAGE_ID = msg.id
    await interaction.response.send_message("הודעת הסטטוס נוצרה! הבוט יעדכן אותה אוטומטית מעכשיו.", ephemeral=True)


# ==========================================
# 📊 משימה אוטומטית ברקע - פנייה ישירה ל-CFX
# ==========================================

@tasks.loop(seconds=30)
async def track_live_players():
    if not CFX_ID:
        return

    players_count = 0
    server_online = False

    # פנייה לשרת הרישום הרשמי של FiveM לקבלת נתוני השחקנים בלייב
    try:
        url = f"https://cfx-services.net{CFX_ID}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=7) as response:
            data = json.loads(response.read().decode())
            players_count = data['Data']['clients']
            server_online = True
    except Exception:
        server_online = False

    # 1. עדכון הסטטוס של הבוט עצמו (Watching)
    status_text = f"1/64 ({players_count})" if server_online else "שרת אופליין 🔴"
    activity = discord.Activity(type=discord.ActivityType.watching, name=status_text)
    await bot.change_presence(activity=activity)

    # 2. עדכון אוטומטי של הודעת ה-Embed בחדר סטטוס-שרת
    if STATUS_MESSAGE_ID:
        try:
            channel = bot.get_channel(STATUS_CHANNEL_ID)
            if channel:
                msg = await channel.fetch_message(STATUS_MESSAGE_ID)
                embed = discord.Embed(title="סטטוס שרת FiveM", color=0x2f3136)
                
                players_val = f"🟢 {players_count}/64" if server_online else "🔴 אופליין"
                status_val = "🟢 פעיל" if server_online else "🔴 תחזוקה / כבוי"
                
                embed.add_field(name="שחקנים", value=players_val, inline=True)
                embed.add_field(name="סטטוס", value=status_val, inline=True)
                embed.add_field(name="חיבור מהיר", value="`cfx.re/join/xedygr`", inline=False)
                embed.set_image(url=BACKGROUND_GIF)
                embed.set_footer(text="Developed by Aaharon The Gamer")
                
                await msg.edit(embed=embed, view=StatusView())
        except Exception:
            pass


# ==========================================
# 👋 מערכת ברוכים הבאים (WELCOME)
# ==========================================

@bot.event
async def on_member_join(member: discord.Member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title="👋 חבר חדש הצטרף למשפחה!",
        description=(
            f"ברוך הבא {member.mention} אל השרת הרשמי שלנו!\n\n"
            f"➔ אתה החבר ה-**{len(member.guild.members)}** בקהילה.\n"
            f"➔ אל תשכח לעבור בחדר <#1514409408489328801> כדי להתאמת!"
        ),
        color=0x7289da
    )
    embed.set_image(url=BACKGROUND_GIF)
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text="Developed by Aaharon The Gamer", icon_url=member.guild.icon.url if member.guild.icon else None)

    await channel.send(content=f"היי {member.mention}, ברוך הבא! ✨", embed=embed)


# ==========================================
# ⚙️ הפעלת הבוט וסנכרון פקודות
# ==========================================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------")
    
    # שמירה על כפתורי הבוט פעילים גם אחרי קריסה או הפעלה מחדש
    bot.add_view(VerifyButton())
    bot.add_view(StatusView())
    
    # התחלת לולאת המעקב האוטומטית ברקע אחרי השרת
    if not track_live_players.is_running():
        track_live_players.start()
    
    try:
        await bot.tree.sync()
        print("Synced slash commands successfully.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

if __name__ == "__main__":
    # הרצת השרת המשני של פלאסק
    t = Thread(target=run_flask)
    t.start()
    
    # הרצת הבוט הראשי
    if TOKEN:
        bot.run(TOKEN)
