import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
import urllib.request
import json

# קריאה ישירה של הטוקן וה-CFX ID מהגדרות השרת של Railway
TOKEN = os.environ.get("DISCORD_TOKEN")
CFX_ID = os.environ.get("CFX_ID")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# מזהי רולים וחדרים המעודכנים של השרת שלך
GUILD_ID = 1499081999464267807  
VERIFY_ROLE_ID = 1514394547554226388
STATUS_CHANNEL_ID = 1520889866496249906
VERIFY_CHANNEL_ID = 1514409408489328801
WELCOME_CHANNEL_ID = 1514409410661842944

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
# 🛡️ מערכת אימות (VERIFY)
# ==========================================

class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="להתחלת אימות / Verify", style=discord.ButtonStyle.success, emoji="🛡️", custom_id="verify_btn_67")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
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

    # יצירת קובץ מצורף מתוך התיקייה של הפרויקט בגיטהאב
    if not os.path.exists("background.gif"):
        return await interaction.response.send_message("שגיאה: קובץ background.gif לא נמצא בתיקייה הראשית ב-GitHub.", ephemeral=True)
        
    gif_file = discord.File("background.gif", filename="background.gif")

    embed = discord.Embed(
        title="🛡️ מערכת אימות הגנה - שרת 67",
        description=(
            "ברוכים הבאים לשרת! כדי לקבל גישה מלאה לשאר החדרים והערוצים בשרת, "
            "עליכם לעבור אימות בסיסי נגד בוטים וחשבונות פיקטיביים.\n\n"
            "**לחצו על הכפתור הירוק למטה כדי להתחיל!**"
        ),
        color=0x2f3136
    )
    # טעינה בטוחה של ה-GIF מתוך הקובץ המצורף ישירות לשרתי דיסקורד
    embed.set_image(url="attachment://background.gif")
    embed.set_footer(text="Developed by Aaharon The Gamer", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    await channel.send(file=gif_file, embed=embed, view=VerifyButton())
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

    if not os.path.exists("background.gif"):
        return await interaction.response.send_message("שגיאה: קובץ background.gif לא נמצא.", ephemeral=True)
        
    gif_file = discord.File("background.gif", filename="background.gif")

    embed = discord.Embed(title="סטטוס שרת FiveM", color=0x2f3136)
    embed.add_field(name="שחקנים", value="🟢 בודק נתונים...", inline=True)
    embed.add_field(name="סטטוס", value="🟢 פעיל", inline=True)
    embed.add_field(name="חיבור מהיר", value="`cfx.re/join/xedygr`", inline=False)
    embed.set_image(url="attachment://background.gif")
    embed.set_footer(text="Developed by Aaharon The Gamer")

    msg = await channel.send(file=gif_file, embed=embed, view=StatusView())
    STATUS_MESSAGE_ID = msg.id
    await interaction.response.send_message("הודעת הסטטוס נוצרה! הבוט יעדכן אותה אוטומטית מעכשיו.", ephemeral=True)


# ==========================================
# 📊 משימה אוטומטית ברקע - פנייה ישירה ל-CFX Master List
# ==========================================

@tasks.loop(seconds=15)
async def track_live_players():
    if not CFX_ID:
        activity = discord.Activity(type=discord.ActivityType.watching, name="1/64 (0)")
        await bot.change_presence(activity=activity)
        return

    players_count = 0
    server_online = False

    try:
        # 🎯 מעבר לכתובת ה-API של ה-Master List שעוקפת את הגנות Cloudflare לבוטים
        url = f"https://fivem.net{CFX_ID}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            players_count = data['Data']['clients']
            server_online = True
    except Exception:
        server_online = False

    # 1. עדכון הסטטוס לפרופיל הבוט (Watching) בדיוק בפורמט שרצית
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
                
                # בגלל שהקובץ כבר הועלה להודעה, המלבן יישאר מעודכן בתוך ה-Embed
                embed.set_image(url="attachment://background.gif")
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
    if os.path.exists("background.gif"):
        embed.set_image(url="attachment://background.gif")
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text="Developed by Aaharon The Gamer", icon_url=member.guild.icon.url if member.guild.icon else None)

    if os.path.exists("background.gif"):
        gif_file = discord.File("background.gif", filename="background.gif")
        await channel.send(file=gif_file, embed=embed)
    else:
        await channel.send(embed=embed)


# ==========================================
# ⚙️ הפעלת הבוט וסנכרון פקודות
# ==========================================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------")
    
    bot.add_view(VerifyButton())
    bot.add_view(StatusView())
    
    if not track_live_players.is_running():
        track_live_players.start()
    
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild_obj)
        await bot.tree.sync(guild=guild_obj)
        print(f"🎯 Synced slash commands successfully.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    if TOKEN:
        bot.run(TOKEN)
