import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# טעינת הטוקן הסודי
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# הגדרת הרשאות מלאות לבוט
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# כתובת ה-GIF שלך בגיטהאב שיופיע ברקע של ההודעות המעוצבות
BACKGROUND_GIF = "https://githubusercontent.com"

# ==========================================
# 🛡️ מערכת אימות (VERIFY) - כפתור ולוגיקה
# ==========================================

class VerifyButton(discord.ui.View):
    def __init__(self):
        # timeout=None משאיר את הכפתור פעיל גם אם הבוט קורס או עובר הפעלה מחדש
        super().__init__(timeout=None)

    @discord.ui.button(label="להתחלת אימות / Verify", style=discord.ButtonStyle.success, emoji="🛡️", custom_id="verify_btn_67")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # שם הרול שהבוט יעניק למשתמש
        role_name = "Verified" 
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        
        # אם הרול לא קיים בשרת, הבוט ייצר אותו אוטומטית
        if not role:
            role = await interaction.guild.create_role(name=role_name, colour=discord.Colour.green())

        if role in interaction.user.roles:
            await interaction.response.send_message("אתה כבר מאומת במערכת! 🧭", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"האימות בוצע בהצלחה! קיבלת את הרול **{role_name}** ✨", ephemeral=True)

# פקודת סלאש למנהלים להצבת הודעת האימות בחדר
@bot.tree.command(name="setup_verify", description="שולח את הודעת האימות המעוצבת")
@app_commands.checks.has_permissions(administrator=True)
async def setup_verify(interaction: discord.Interaction):
    # חדר האימות שביקשת
    channel = interaction.guild.get_channel(1514409408489328801)
    if not channel:
        return await interaction.response.send_message("שגיאה: חדר האימות לא נמצא בשרת זה.", ephemeral=True)

    embed = discord.Embed(
        title="🛡️ מערכת אימות הגנה - שרת 67",
        description=(
            "ברוכים הבאים לשרת! כדי לקבל גישה מלאה לשאר החדרים והערוצים בשרת, "
            "עליכם לעבור אימות בסיסי נגד בוטים וחשבונות פיקטיביים.\n\n"
            "**לחצו על הכפתור הירוק למטה כדי להתחיל!**"
        ),
        color=0x2f3136 # צבע אפור כהה יוקרתי של דיסקורד
    )
    embed.set_image(url=BACKGROUND_GIF)
    embed.set_footer(text="Developed by Aaharon The Gamer", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    await channel.send(embed=embed, view=VerifyButton())
    await interaction.response.send_message("מערכת האימות הוצבה בהצלחה!", ephemeral=True)


# ==========================================
# 👋 מערכת ברוכים הבאים (WELCOME)
# ==========================================

@bot.event
async def on_member_join(member: discord.Member):
    # חדר ברוכים הבאים שביקשת
    channel = member.guild.get_channel(1514409410661842944)
    if not channel:
        return

    embed = discord.Embed(
        title="👋 חבר חדש הצטרף למשפחה!",
        description=(
            f"ברוך הבא {member.mention} אל השרת הרשמי שלנו!\n\n"
            f"➔ אתה החבר ה-**{len(member.guild.members)}** בקהילה.\n"
            f"➔ אל תשכח לעבור בחדר <#1514409408489328801> כדי להתאמת!"
        ),
        color=0x7289da # צבע כחול דיסקורד קלאסי
    )
    embed.set_image(url=BACKGROUND_GIF)
    
    # הוספת תמונת הפרופיל של השחקן בצד ההודעה במעגל קטן
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
        
    embed.set_footer(text="Developed by Aaharon The Gamer", icon_url=member.guild.icon.url if member.guild.icon else None)

    await channel.send(content=f"היי {member.mention}, ברוך הבא! ✨", embed=embed)


# ==========================================
# ⚙️ הפעלת הבוט וסנכרון פקודות
# ==========================================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------")
    
    # שומר על הכפתור פעיל גם אחרי שהבוט נדלק מחדש
    bot.add_view(VerifyButton())
    
    # סנכרון פקודות הסלאש (לוקח כמה שניות)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s) successfully.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

# הרצת הבוט עם הטוקן מקובץ ה-.env
bot.run(TOKEN)
