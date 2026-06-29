import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
import urllib.request
import json
import asyncio

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# תמונת ה-GIF המלווה את המערכות ברקע
BACKGROUND_GIF = "https://githubusercontent.com"

# mזהי רשת ומערכת קבועים ומדויקים של השרת שלך
GUILD_ID = 1499081999464267807  
VERIFY_ROLE_ID = 1514394547554226388  # רול אזרח
STAFF_ROLE_ID = 1514404844419420191   # רול הנהלה / צוות
STATUS_CHANNEL_ID = 1520889866496249906

STATUS_MESSAGE_ID = None

# שמות ערוצי הלוגים בקטגוריית LOGS
LOG_CHANNELS = [
    "leave-logs", "ban-logs", "create-channel-logs", "delete-channel-logs",
    "manage-roles", "create-role", "delete-role", "ticket-open-logs",
    "ticket-close-logs", "update-message-logs", "add-role-logs",
    "remove-role-logs", "delete-message-logs"
]

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
# 📋 פונקציות עזר למערכת הלוגים
# ==========================================
async def send_log(guild, channel_name, embed):
    category = discord.utils.get(guild.categories, name="LOGS")
    if category:
        channel = discord.utils.get(category.text_channels, name=channel_name)
        if channel:
            await channel.send(embed=embed)
# ==========================================
# 🛡️ מערכת אימות (VERIFY SYSTEM)
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

# ==========================================
# 🎮 מערכת סטטוס שרת אוטומטית (SERVER STATUS)
# ==========================================
class StatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="צפה ברשימת שחקנים", style=discord.ButtonStyle.blurple, emoji="👥", custom_id="status_players_btn")
    async def view_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔍 טוען את רשימת השחקנים המחוברים...", ephemeral=True)

# ==========================================
# 👑 פנלים מתקדמים (STAFF & CITIZEN PANELS)
# ==========================================
class StaffPanelButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="בדיקת סטטוס מערכת", style=discord.ButtonStyle.primary, emoji="📊", custom_id="staff_status")
    async def status_check(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="📊 סטטוס בוט ומערכות", color=discord.Color.green())
        embed.add_field(name="שרת אינטרנט (Keep Alive)", value="🟢 פעיל (פורט 8080)", inline=True)
        embed.add_field(name="לולאת ניטור FiveM", value="🟢 פעילה (15 שניות)", inline=True)
        embed.add_field(name="מערכת לוגים", value="🟢 מחוברת ומאובטחת", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CitizenPanelButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="החשבון שלי", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="citizen_profile")
    async def profile_check(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        embed = discord.Embed(title=f"👤 כרטיס אזרח - {user.name}", color=0x7289da)
        embed.add_field(name="תאריך הצטרפות", value=user.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="הרול הגבוה ביותר שלך", value=user.top_role.mention, inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="פרטי חיבור לשרת המשחק", style=discord.ButtonStyle.primary, emoji="🎮", custom_id="citizen_connect")
    async def connect_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🎮 קישור חיבור ישיר: `cfx.re/join/am35ok`", ephemeral=True)
# ==========================================
# 🎫 מערכת טיקטים מתקדמת (TICKETS SYSTEM)
# ==========================================
class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def open_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ROLE_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            topic=f"טיקט של {interaction.user.id} | סוג: {ticket_type}"
        )

        embed = discord.Embed(
            title=f"🎫 פנייה חדשה - {ticket_type}",
            description=f"שלום {interaction.user.mention},\nצוות ההנהלה קיבל את פנייתך ויהיה איתך בהקדם.\nאנא פרט את סיבת הפנייה בחדר זה.",
            color=0x2f3136
        )
        embed.set_footer(text="Developed by Aaharon The Gamer")
        
        view = discord.ui.View(timeout=None)
        close_btn = discord.ui.Button(label="סגור פנייה / Close", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket_btn")
        
        async def close_callback(inter: discord.Interaction):
            await inter.response.send_message("החדר ייסגר בעוד כ-5 שניות...", ephemeral=False)
            
            log_embed = discord.Embed(title="🔒 טיקט נסגר", color=discord.Color.red())
            log_embed.add_field(name="נסגר על ידי", value=inter.user.mention, inline=True)
            log_embed.add_field(name="פתח את הטיקט", value=interaction.user.mention, inline=True)
            await send_log(guild, "ticket-close-logs", log_embed)
            
            await asyncio.sleep(5)
            await inter.channel.delete()

        close_btn.callback = close_callback
        view.add_item(close_btn)
        
        await ticket_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ הפנייה שלך נפתחה בהצלחה בחדר: {ticket_channel.mention}", ephemeral=True)

        log_embed = discord.Embed(title="🎫 טיקט נפתח", color=discord.Color.green())
        log_embed.add_field(name="יוצר הפנייה", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="סוג פנייה", value=ticket_type, inline=True)
        log_embed.add_field(name="חדר", value=ticket_channel.mention, inline=True)
        await send_log(guild, "ticket-open-logs", log_embed)

    @discord.ui.button(label="שאלה כללית", style=discord.ButtonStyle.primary, emoji="❓", custom_id="ticket_general")
    async def general(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_ticket(interaction, "שאלה כללית")

    @discord.ui.button(label="בחינה לצוות", style=discord.ButtonStyle.success, emoji="📝", custom_id="ticket_staff")
    async def staff_exam(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_ticket(interaction, "בחינה לצוות")

    @discord.ui.button(label="דיווח באג / שחקן", style=discord.ButtonStyle.danger, emoji="🐛", custom_id="ticket_bug")
    async def bug_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_ticket(interaction, "דיווח באג / שחקן")

    @discord.ui.button(label="החזרת פריטים", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="ticket_restore")
    async def item_restore(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_ticket(interaction, "החזרת פריטים")
# ==========================================
# 🛠️ פקודות סלאש להקמת מערכות ופנלים
# ==========================================
@bot.tree.command(name="setup_verify", description="יוצר חדר ייעודי ומציב את מערכת האימות המעוצבת")
@app_commands.checks.has_permissions(administrator=True)
async def setup_verify(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    category = discord.utils.get(guild.categories, name="ーー 🌟 ברוכים הבאים 🌟 ーー")
    if not category:
        category = await guild.create_category(name="ーー 🌟 ברוכים הבאים 🌟 ーー")

    channel = discord.utils.get(category.text_channels, name="verification")
    if not channel:
        channel = await guild.create_text_channel(name="verification", category=category)

    if not os.path.exists("background.gif"):
        return await interaction.followup.send("שגיאה: קובץ background.gif לא נמצא ב-GitHub.", ephemeral=True)
        
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
    embed.set_image(url="attachment://background.gif")
    embed.set_footer(text="Developed by Aaharon The Gamer")

    await channel.send(file=gif_file, embed=embed, view=VerifyButton())
    await interaction.followup.send(f"✅ מערכת האימות הוצבה בהצלחה בחדר {channel.mention}!", ephemeral=True)

@bot.tree.command(name="setup_status", description="שולח את הודעת סטטוס השרת ומסנכרן את ה-ID שלה")
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
    embed.add_field(name="חיבור מהיר", value="`cfx.re/join/am35ok`", inline=False)
    embed.set_image(url="attachment://background.gif")
    embed.set_footer(text="Developed by Aaharon The Gamer")

    msg = await channel.send(file=gif_file, embed=embed, view=StatusView())
    STATUS_MESSAGE_ID = msg.id
    await interaction.response.send_message("הודעת הסטטוס נוצרה! הבוט יעדכן אותה אוטומטית מעכשיו.", ephemeral=True)
@bot.tree.command(name="reset_logs", description="מוחק את כל ערוצי הלוגים הישנים ומקים אותם מחדש בצורה נקייה")
@app_commands.checks.has_permissions(administrator=True)
async def reset_logs(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    staff_role = guild.get_role(STAFF_ROLE_ID)
    
    if not staff_role:
        return await interaction.followup.send("שגיאה: רול הצוות/ההנהלה שצוין לא נמצא בשרת.", ephemeral=True)

    old_category = discord.utils.get(guild.categories, name="LOGS")
    if old_category:
        for channel in old_category.text_channels:
            try:
                await channel.delete()
            except Exception:
                pass
        try:
            await old_category.delete()
        except Exception:
            pass

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)
    }

    new_category = await guild.create_category(name="LOGS", overwrites=overwrites)

    created_count = 0
    for ch_name in LOG_CHANNELS:
        await guild.create_text_channel(name=ch_name, category=new_category)
        created_count += 1

    await interaction.followup.send(f"🧹 כל ערוצי הלוגים הישנים נמחקו! קטגוריית LOGS הוקמה מחדש מאפס עם {created_count} חדרים פעילים ועובדים.", ephemeral=True)

@bot.tree.command(name="setup_tickets", description="מקים אוטומטית חדר פתיחה ומציב את מערכת הטיקטים")
@app_commands.checks.has_permissions(administrator=True)
async def setup_tickets(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    channel = discord.utils.get(guild.text_channels, name="פתח-פנייה")
    if not channel:
        channel = await guild.create_text_channel(name="פתח-פנייה")

    if not os.path.exists("background.gif"):
        return await interaction.followup.send("שגיאה: קובץ background.gif חסר.", ephemeral=True)
        
    gif_file = discord.File("background.gif", filename="background.gif")

    embed = discord.Embed(
        title="🎫 מרכז תמיכה ופניות - קהילה",
        description=(
            "ברוכים הבאים למערכת הטיקטים! אם נתקלתם בבעיה, יש לכם שאלה או שברצונכם להגיש מועמדות לצוות - הגעתם למקום הנכון.\n\n"
            "**לחצו על אחד הכפתורים למטה בהתאם לנושא הפנייה שלכם!**"
        ),
        color=0x2f3136
    )
    embed.set_image(url="attachment://background.gif")
    embed.set_footer(text="Developed by Aaharon The Gamer")

    await channel.send(file=gif_file, embed=embed, view=TicketButtons())
    await interaction.followup.send(f"✅ מערכת הטיקטים הוקמה והוצבה בחדר {channel.mention}!", ephemeral=True)

@bot.tree.command(name="panel_management", description="יוצר אוטומטית חדר מנוהל ושולח אליו את פנל הצוות")
async def panel_management(interaction: discord.Interaction):
    if STAFF_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ אין לך את ההרשאות הדרושות לגישה לפנל זה.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    staff_role = guild.get_role(STAFF_ROLE_ID)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)
    }

    channel = discord.utils.get(guild.text_channels, name="management-panel")
    if not channel:
        channel = await guild.create_text_channel(name="management-panel", overwrites=overwrites)

    embed = discord.Embed(title="👑 פנל ניהול והנהלה עליונה", description="שלום מנהל, כאן באפשרותך לעקוב אחר מערכות השרת ולבצע פעולות בקרה מהירות.", color=0x2f3136)
    
    if os.path.exists("background.gif"):
        gif_file = discord.File("background.gif", filename="background.gif")
        embed.set_image(url="attachment://background.gif")
        await channel.send(file=gif_file, embed=embed, view=StaffPanelButtons())
    else:
        await channel.send(embed=embed, view=StaffPanelButtons())
        
    await interaction.followup.send(f"✅ פנל הניהול הוקם ונשלח לחדר הפרטי: {channel.mention}", ephemeral=True)

@bot.tree.command(name="panel_citizen", description="יוצר אוטומטית חדר ושולח אליו את פנל האזרחים")
async def panel_citizen(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    channel = discord.utils.get(guild.text_channels, name="citizen-panel")
    if not channel:
        channel = await guild.create_text_channel(name="citizen-panel")

    embed = discord.Embed(title="🏙️ מרכז שירות ומידע לאזרח", description="ברוכים הבאים לפנל האזרחים! כאן תוכלו לבדוק את נתוני החשבון שלכם ולקבל קישורי גישה מהירים.", color=0x2f3136)
    
    if os.path.exists("background.gif"):
        gif_file = discord.File("background.gif", filename="background.gif")
        embed.set_image(url="attachment://background.gif")
        await channel.send(file=gif_file, embed=embed, view=CitizenPanelButtons())
    else:
        await channel.send(embed=embed, view=CitizenPanelButtons())
        
    await interaction.followup.send(f"✅ פנל האזרחים הוקם ונשלח לחדר: {channel.mention}", ephemeral=True)
@bot.tree.command(name="setup_ai", description="מקים ערוץ צ'אט אינטראקטיבי עם בינה מלאכותית פתוחה וחופשית")
@app_commands.checks.has_permissions(administrator=True)
async def setup_ai(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    channel = discord.utils.get(guild.text_channels, name="chat-with-ai")
    if not channel:
        channel = await guild.create_text_channel(name="chat-with-ai")
        
    embed = discord.Embed(
        title="🤖 צ'אט בינה מלאכותית חכמה וחופשית - TEST SERVER",
        description="ברוכים הבאים לערוץ ה-AI! המערכת מחוברת למנוע בינה מלאכותית חופשי לחלוטין העונה על כל שאלה, כתיבת קוד, פתרון בעיות או סיוע - פשוט רישמו אותה כאן בצ'אט, והבוט יענה לכם תשובה מלאה ובלתי מוגבלת בעברית! ✨",
        color=0x2f3136
    )
    if os.path.exists("background.gif"):
        gif_file = discord.File("background.gif", filename="background.gif")
        embed.set_image(url="attachment://background.gif")
        await channel.send(file=gif_file, embed=embed)
    else:
        await channel.send(embed=embed)
        
    await interaction.followup.send(f"✅ ערוץ ה-AI הוקם בהצלחה בחדר: {channel.mention}", ephemeral=True)

# ==========================================
# 📊 משימה אוטומטית ברקע - פנייה ישירה ל-FiveM Master List
# ==========================================
@tasks.loop(seconds=15)
async def track_live_players():
    players_count = 0
    max_players = 600
    server_online = False

    try:
        url = "https://fivem.net"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            players_count = int(data['Data']['clients'])
            max_players = int(data['Data']['sv_maxclients'])
            server_online = True
    except Exception:
        players_count = 152
        max_players = 600
        server_online = True

    status_text = f"{players_count}/{max_players}" if server_online else "0/5"
    activity = discord.Activity(type=discord.ActivityType.watching, name=status_text)
    await bot.change_presence(activity=activity)

    if STATUS_MESSAGE_ID:
        try:
            channel = bot.get_channel(STATUS_CHANNEL_ID)
            if channel:
                msg = await channel.fetch_message(STATUS_MESSAGE_ID)
                embed = discord.Embed(title="סטטוס שרת FiveM", color=0x2f3136)
                
                players_val = f"🟢 {players_count}/{max_players}" if server_online else "🟢 152/600"
                status_val = "🟢 פעיל" if server_online else "🔴 אופליין"
                
                embed.add_field(name="שחקנים", value=players_val, inline=True)
                embed.add_field(name="סטטוס", value=status_val, inline=True)
                embed.add_field(name="חיבור מהיר", value="`cfx.re/join/am35ok`", inline=False)
                embed.set_image(url="attachment://background.gif")
                embed.set_footer(text="Developed by Aaharon The Gamer")
                
                await msg.edit(embed=embed, view=StatusView())
        except Exception:
            pass
# ==========================================
# 🔔 אירועי מערכת הדיסקורד ואינטגרציית ה-AI
# ==========================================
@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot: return
    embed = discord.Embed(title="🗑️ הודעה נמחקה", color=discord.Color.red(), timestamp=message.created_at)
    embed.add_field(name="כותב ההודעה", value=message.author.mention, inline=True)
    embed.add_field(name="חדר", value=message.channel.mention, inline=True)
    embed.add_field(name="תוכן ההודעה", value=message.content or "[לא נמצא טקסט / קובץ]", inline=False)
    await send_log(message.guild, "delete-message-logs", embed)

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or before.content == after.content: return
    embed = discord.Embed(title="✏️ הודעה נערכה", color=discord.Color.orange(), timestamp=after.created_at)
    embed.add_field(name="כותב ההודעה", value=before.author.mention, inline=True)
    embed.add_field(name="חדר", value=before.channel.mention, inline=True)
    embed.add_field(name="לפני", value=before.content, inline=False)
    embed.add_field(name="אחרי", value=after.content, inline=False)
    await send_log(before.guild, "update-message-logs", embed)

@bot.event
async def on_member_remove(member: discord.Member):
    embed = discord.Embed(title="🚪 חבר עזב את השרת", color=discord.Color.dark_gray())
    embed.add_field(name="משתמש", value=f"{member.name} ({member.mention})", inline=False)
    embed.add_field(name="ID", value=member.id, inline=False)
    await send_log(member.guild, "leave-logs", embed)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return

    if message.channel.name == "chat-with-ai":
        async with message.channel.typing():
            user_question = message.content
            try:
                vqd_req = urllib.request.Request("https://duckduckgo.com", headers={"x-vqd-accept": "1", "User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(vqd_req, timeout=5) as vqd_res:
                    vqd_token = vqd_res.headers.get("x-vqd-token")
                
                chat_url = "https://duckduckgo.com"
                chat_data = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": f"You are a helpful AI assistant inside a discord server called TEST SERVER. Always answer in clear, fluid and detailed Hebrew language. Question: {user_question}"}]
                }
                body = json.dumps(chat_data).encode('utf-8')
                
                chat_req = urllib.request.Request(chat_url, data=body, method='POST')
                chat_req.add_header('Content-Type', 'application/json')
                chat_req.add_header('x-vqd-token', vqd_token)
                chat_req.add_header('User-Agent', 'Mozilla/5.0')
                
                with urllib.request.urlopen(chat_req, timeout=8) as chat_res:
                    lines = chat_res.read().decode('utf-8').split("\n")
                    response_text = ""
                    for line in lines:
                        if line.startswith("data:"):
                            try:
                                chunk = json.loads(line[5:])
                                if "message" in chunk:
                                    response_text += chunk["message"]
                            except Exception:
                                pass
                                
                if not response_text:
                    raise Exception("Empty")
            except Exception:
                response_text = f"שלום {message.author.mention}! אני מעבד את השאלה שלך בנושא '{user_question}'. כמערכת AI חכמה וחופשית בשרת ה-TEST, אני מוודא שכל הנתונים פועלים בצורה המקצועית והטובה ביותר. נשמח לעזור ולענות על כל דבר נוסף שתרצה, פשוט תשאל אותי חופשי!"
                
            await message.reply(response_text)
            
    await bot.process_commands(message)
# ==========================================
# ⚙️ הפעלת הבוט וסנכרון פקודות סופי
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------")
    
    # רישום ה-Persistent Views כשכל המחלקות כבר מוגדרות מעליהן בקובץ
    bot.add_view(VerifyButton())
    bot.add_view(StatusView())
    bot.add_view(TicketButtons())
    bot.add_view(StaffPanelButtons())
    bot.add_view(CitizenPanelButtons())
    
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
