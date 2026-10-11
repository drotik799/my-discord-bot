import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import json
import os

# ----------------------------------------------------
# НАСТРОЙКА БОТА
# ----------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='/', intents=intents)

# ОТКЛЮЧАЕМ СТАНДАРТНУЮ КОМАНДУ HELP
bot.remove_command('help')

# Планировщик
scheduler = AsyncIOScheduler()

# Файлы для хранения данных
DATA_FILE = "raid_data.json"
ROLES_FILE = "allowed_roles.json"
SERVERS_FILE = "rust_servers.json"
EVENTS_FILE = "events_data.json"
WARNS_FILE = "warns_data.json"
APPLICATIONS_FILE = "applications_data.json"

# Данные о вайпе (основной)
raid_data = {
    "time": "20:00",
    "weekday": "Суббота",
    "server": "Rustoria #1",
    "channel_id": None,
    "reminder_hours": 1,
    "map_url": "https://rustmaps.com/"
}

# Список ролей с доступом к настройкам
allowed_roles = []

# Список серверов для мониторинга
monitored_servers = []

# Список событий
events = []

# Данные о варнах
warns_data = {}

# Данные о заявках
applications_data = {
    "total": 0,
    "pending": 0,
    "accepted": 0,
    "rejected": 0,
    "applications": []
}

# Список целевых ролей для /состав
TARGET_ROLES = ["ʙᴜɪʟᴅᴇʀ", "ᴄᴏʟʟᴇʀ", "ᴄᴏᴍʙᴀᴛ", "ᴇʟᴇᴄᴛʀɪᴄ", "ꜰᴀʀᴍ", "ꜰᴇʀᴍᴇʀ"]

# ID канала для оповещений
ANNOUNCEMENT_CHANNEL_ID = None
APPLICATIONS_CHANNEL_ID = None

# Дни недели для меню
WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье", "Ежедневно"]

# ----------------------------------------------------
# ЗАГРУЗКА/СОХРАНЕНИЕ ДАННЫХ
# ----------------------------------------------------

def load_data():
    global raid_data, allowed_roles, monitored_servers, events, warns_data, applications_data, ANNOUNCEMENT_CHANNEL_ID
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                raid_data.update(saved_data)
                ANNOUNCEMENT_CHANNEL_ID = raid_data.get("channel_id")
            print("✅ Данные вайпа загружены")
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
    
    if os.path.exists(ROLES_FILE):
        try:
            with open(ROLES_FILE, 'r', encoding='utf-8') as f:
                allowed_roles = json.load(f)
            print(f"✅ Загружено {len(allowed_roles)} разрешённых ролей")
        except Exception as e:
            print(f"❌ Ошибка загрузки ролей: {e}")
    
    if os.path.exists(SERVERS_FILE):
        try:
            with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
                monitored_servers = json.load(f)
            print(f"✅ Загружено {len(monitored_servers)} серверов для мониторинга")
        except Exception as e:
            print(f"❌ Ошибка загрузки серверов: {e}")
    
    if os.path.exists(EVENTS_FILE):
        try:
            with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                events = json.load(f)
            print(f"✅ Загружено {len(events)} событий")
        except Exception as e:
            print(f"❌ Ошибка загрузки событий: {e}")
    
    if os.path.exists(WARNS_FILE):
        try:
            with open(WARNS_FILE, 'r', encoding='utf-8') as f:
                warns_data = json.load(f)
            print(f"✅ Загружено {len(warns_data)} записей о варнах")
        except Exception as e:
            print(f"❌ Ошибка загрузки варнов: {e}")
    
    if os.path.exists(APPLICATIONS_FILE):
        try:
            with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
                applications_data = json.load(f)
            print(f"✅ Загружено {len(applications_data.get('applications', []))} заявок")
        except Exception as e:
            print(f"❌ Ошибка загрузки заявок: {e}")

def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(raid_data, f, ensure_ascii=False, indent=4)
        print("✅ Данные вайпа сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")

def save_roles():
    try:
        with open(ROLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(allowed_roles, f, ensure_ascii=False, indent=4)
        print("✅ Роли сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения ролей: {e}")

def save_servers():
    try:
        with open(SERVERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(monitored_servers, f, ensure_ascii=False, indent=4)
        print("✅ Список серверов сохранён")
    except Exception as e:
        print(f"❌ Ошибка сохранения серверов: {e}")

def save_events():
    try:
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=4)
        print("✅ События сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения событий: {e}")

def save_warns():
    try:
        with open(WARNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(warns_data, f, ensure_ascii=False, indent=4)
        print("✅ Варны сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения варнов: {e}")

def save_applications():
    try:
        with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(applications_data, f, ensure_ascii=False, indent=4)
        print("✅ Заявки сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения заявок: {e}")

load_data()

# ----------------------------------------------------
# ФУНКЦИЯ АВТОУДАЛЕНИЯ
# ----------------------------------------------------

async def auto_delete_message(message, delay=120):
    if message.channel.id == ANNOUNCEMENT_CHANNEL_ID:
        return
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# ----------------------------------------------------
# ПРОВЕРКА ДОСТУПА
# ----------------------------------------------------

def has_access(user, guild):
    if user.id == guild.owner_id:
        return True
    if not allowed_roles:
        return False
    for role in user.roles:
        if str(role.id) in allowed_roles:
            return True
    return False

def is_admin_or_moderator(user, guild):
    if user.id == guild.owner_id:
        return True
    admin_roles = ["Admin", "Администратор", "Moderator", "Модератор", "главный"]
    for role in user.roles:
        if role.name in admin_roles:
            return True
    return False

# ----------------------------------------------------
# АВТО-РОЛИ ДЛЯ НОВЫХ УЧАСТНИКОВ
# ----------------------------------------------------

@bot.event
async def on_member_join(member):
    guild = member.guild
    
    if member.bot:
        bot_role = discord.utils.get(guild.roles, name="ʙᴏᴛ")
        if bot_role:
            try:
                await member.add_roles(bot_role)
                print(f"✅ Выдана роль ʙᴏᴛ для {member.name} (бот)")
            except Exception as e:
                print(f"❌ Ошибка выдачи роли ʙᴏᴛ для {member.name}: {e}")
    else:
        newbie_role = discord.utils.get(guild.roles, name="ɴᴇᴡʙɪᴇ")
        if newbie_role:
            try:
                await member.add_roles(newbie_role)
                print(f"✅ Выдана роль ɴᴇᴡʙɪᴇ для {member.name}")
                try:
                    embed = discord.Embed(
                        title=f"👋 Добро пожаловать на сервер {guild.name}!",
                        description="Ты получил роль **ɴᴇᴡʙɪᴇ**!\n\n"
                                   "📋 **Что дальше?**\n"
                                   "• Заполни заявку в канале `#заявки`\n"
                                   "• Ознакомься с правилами\n"
                                   "• Приятного времяпрепровождения! 🎉",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    embed.set_footer(text=f"Сервер: {guild.name}")
                    await member.send(embed=embed)
                except:
                    pass
            except Exception as e:
                print(f"❌ Ошибка выдачи роли ɴᴇᴡʙɪᴇ для {member.name}: {e}")
        else:
            try:
                newbie_role = await guild.create_role(name="ɴᴇᴡʙɪᴇ", color=discord.Color.green())
                await member.add_roles(newbie_role)
                print(f"✅ Создана и выдана роль ɴᴇᴡʙɪᴇ для {member.name}")
            except Exception as e:
                print(f"❌ Ошибка создания роли ɴᴇᴡʙɪᴇ: {e}")

@bot.event
async def on_member_remove(member):
    print(f"👋 Участник покинул сервер: {member.name} (ID: {member.id})")

# ----------------------------------------------------
# ФУНКЦИЯ ДЛЯ ПРОВЕРКИ ВАЙПА
# ----------------------------------------------------

def get_next_wipe_time():
    """Возвращает дату и время следующего вайпа"""
    try:
        now = datetime.now()
        weekday = raid_data.get("weekday", "Суббота").lower()
        time_str = raid_data.get("time", "20:00")
        hour, minute = map(int, time_str.split(":"))
        
        weekdays = {
            "понедельник": 0, "вторник": 1, "среда": 2,
            "четверг": 3, "пятница": 4, "суббота": 5, "воскресенье": 6
        }
        
        if weekday == "ежедневно":
            next_wipe = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now > next_wipe:
                next_wipe += timedelta(days=1)
        elif weekday in weekdays:
            target_weekday = weekdays[weekday]
            today_weekday = now.weekday()
            days_ahead = target_weekday - today_weekday
            if days_ahead <= 0:
                days_ahead += 7
            next_wipe = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        else:
            next_wipe = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now > next_wipe:
                next_wipe += timedelta(days=1)
        
        return next_wipe
    except:
        return None

# ----------------------------------------------------
# СОБЫТИЕ: БОТ ГОТОВ
# ----------------------------------------------------

@bot.event
async def on_ready():
    global ANNOUNCEMENT_CHANNEL_ID, APPLICATIONS_CHANNEL_ID
    ANNOUNCEMENT_CHANNEL_ID = raid_data.get("channel_id")
    
    print(f'✅ Бот {bot.user} успешно запущен!')
    print(f'👉 Он на {len(bot.guilds)} серверах.')
    print(f'📢 Канал оповещений: {ANNOUNCEMENT_CHANNEL_ID}')
    
    if not scheduler.running:
        scheduler.start()
    
    schedule_raid()
    schedule_server_monitoring()
    schedule_events()
    
    # СИНХРОНИЗАЦИЯ СЛЕШ-КОМАНД
    try:
        for guild in bot.guilds:
            try:
                await bot.tree.sync(guild=guild)
                print(f"✅ Команды синхронизированы для сервера: {guild.name}")
            except Exception as e:
                print(f"❌ Ошибка синхронизации для {guild.name}: {e}")
        
        await bot.tree.sync()
        print("✅ Глобальная синхронизация выполнена!")
        
        commands = await bot.tree.fetch_commands()
        print(f"📋 Зарегистрировано {len(commands)} слеш-команд:")
        for cmd in commands:
            print(f"   /{cmd.name}")
            
    except Exception as e:
        print(f"❌ Ошибка синхронизации команд: {e}")
    
    await bot.change_presence(activity=discord.Game(name="/vipeset | Раст"))

# ----------------------------------------------------
# РАСПИСАНИЕ ВАЙПА (НОВОЕ)
# ----------------------------------------------------

def schedule_raid():
    """Настраивает расписание вайпа и напоминаний"""
    for job in scheduler.get_jobs():
        if job.id in ["raid_announcement", "raid_reminder"]:
            scheduler.remove_job(job.id)
    
    try:
        hour, minute = map(int, raid_data["time"].split(":"))
        weekday = raid_data.get("weekday", "Суббота").lower()
        
        weekdays_map = {
            "понедельник": "mon", "вторник": "tue", "среда": "wed",
            "четверг": "thu", "пятница": "fri", "суббота": "sat", "воскресенье": "sun"
        }
        
        # Планируем оповещение в момент вайпа
        if weekday == "ежедневно":
            scheduler.add_job(
                func=send_raid_announcement,
                trigger=CronTrigger(hour=hour, minute=minute),
                id="raid_announcement",
                replace_existing=True
            )
        elif weekday in weekdays_map:
            scheduler.add_job(
                func=send_raid_announcement,
                trigger=CronTrigger(day_of_week=weekdays_map[weekday], hour=hour, minute=minute),
                id="raid_announcement",
                replace_existing=True
            )
        
        # Планируем напоминание
        reminder_hours = raid_data.get("reminder_hours", 1)
        reminder_hour = hour - reminder_hours
        reminder_day_offset = 0
        
        if reminder_hour < 0:
            reminder_hour = 24 + reminder_hour
            reminder_day_offset = -1
        
        if weekday == "ежедневно":
            scheduler.add_job(
                func=send_raid_reminder,
                trigger=CronTrigger(hour=reminder_hour, minute=minute),
                id="raid_reminder",
                replace_existing=True
            )
        elif weekday in weekdays_map:
            # Для напоминания используем тот же день недели (упрощённо)
            scheduler.add_job(
                func=send_raid_reminder,
                trigger=CronTrigger(day_of_week=weekdays_map[weekday], hour=reminder_hour, minute=minute),
                id="raid_reminder",
                replace_existing=True
            )
        
        print(f"⏰ Вайп запланирован на {raid_data['weekday']} в {raid_data['time']}")
        print(f"⏰ Напоминание за {reminder_hours} ч до вайпа")
    except Exception as e:
        print(f"❌ Ошибка при настройке расписания: {e}")

async def send_raid_reminder():
    """Отправляет напоминание о вайпе"""
    channel_id = raid_data.get("channel_id")
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    
    reminder_hours = raid_data.get("reminder_hours", 1)
    
    embed = discord.Embed(
        title="⏰ НАПОМИНАНИЕ О ВАЙПЕ!",
        description=f"**Через {reminder_hours} час(а)** начнётся вайп на сервере **{raid_data['server']}**!",
        color=0xffaa00,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}**", inline=True)
    embed.add_field(name="📅 День", value=f"**{raid_data['weekday']}**", inline=True)
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка на карту]({raid_data['map_url']})", inline=False)
    embed.set_footer(text="Подготовьтесь к вайпу! 🔥")
    
    await channel.send("@everyone", embed=embed)
    print(f"✅ Напоминание о вайпе отправлено в {channel.name}")

async def send_raid_announcement():
    """Отправляет сообщение о начале вайпа"""
    channel_id = raid_data.get("channel_id")
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    
    embed = discord.Embed(
        title="⚔️ СЕРВЕР УШЁЛ НА ВАЙП! ⚔️",
        description=f"**{raid_data['server']}** начал вайп! 🎉",
        color=0xff0000,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}**", inline=True)
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка на карту]({raid_data['map_url']})", inline=False)
    embed.set_footer(text="Всем удачи на новом вайпе! 🔥")
    
    await channel.send("@everyone", embed=embed)
    print(f"✅ Сообщение о вайпе отправлено в {channel.name}")

# ----------------------------------------------------
# КОМАНДА /vipeset — МЕНЮ НАСТРОЙКИ ВАЙПА
# ----------------------------------------------------

class VipeSetView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.message = None
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Это меню вызвано другим пользователем!",
                ephemeral=True
            )
            return False
        return True
    
    async def on_timeout(self):
        if self.message:
            embed = discord.Embed(
                title="⏰ Меню настроек закрыто",
                description="Время сессии истекло. Используй `/vipeset` снова.",
                color=0xff0000
            )
            try:
                await self.message.edit(embed=embed, view=None)
            except:
                pass
    
    def get_main_embed(self):
        embed = discord.Embed(
            title="⚙️ НАСТРОЙКА ВАЙПА",
            description="Настрой параметры вайпа с помощью кнопок ниже:",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="🕐 Время", value=f"**{raid_data.get('time', '20:00')}**", inline=True)
        embed.add_field(name="📅 День недели", value=f"**{raid_data.get('weekday', 'Суббота')}**", inline=True)
        embed.add_field(name="🎮 Сервер", value=f"**{raid_data.get('server', 'Rustoria #1')}**", inline=True)
        
        channel_text = f"<#{raid_data['channel_id']}>" if raid_data.get('channel_id') else "❌ Не установлен"
        embed.add_field(name="📢 Канал оповещений", value=channel_text, inline=True)
        embed.add_field(name="⏰ Напоминание", value=f"За **{raid_data.get('reminder_hours', 1)}** час(а)", inline=True)
        embed.add_field(name="🗺️ Карта", value=f"[Ссылка]({raid_data.get('map_url', 'https://rustmaps.com/')})", inline=True)
        
        embed.set_footer(text="Меню видно только тебе | Настройки сохраняются автоматически")
        return embed
    
    async def update_menu(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.get_main_embed(), view=self)
    
    @discord.ui.button(label="🕐 Время", style=discord.ButtonStyle.primary, row=0)
    async def set_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🕐 **Введите время вайпа** в формате ЧЧ:ММ (например, `20:00`):\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            time_str = msg.content.strip()
            hour, minute = map(int, time_str.split(":"))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                raid_data["time"] = time_str
                schedule_raid()
                save_data()
                await msg.delete()
                await interaction.edit_original_response(content=f"✅ Время установлено: **{time_str}**")
            else:
                await interaction.edit_original_response(content="❌ Неверный формат! Используй ЧЧ:ММ")
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
        except:
            await interaction.edit_original_response(content="❌ Неверный формат! Используй ЧЧ:ММ")
    
    @discord.ui.button(label="📅 День недели", style=discord.ButtonStyle.primary, row=0)
    async def set_weekday(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = WeekdaySelectView(author_id=interaction.user.id)
        await interaction.response.send_message(
            "📅 **Выбери день недели для вайпа:**",
            ephemeral=True,
            view=view
        )
    
    @discord.ui.button(label="🎮 Сервер", style=discord.ButtonStyle.primary, row=0)
    async def set_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🎮 **Введите название сервера** (например, `Rustoria #1`):\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            server = msg.content.strip()
            raid_data["server"] = server
            save_data()
            await msg.delete()
            await interaction.edit_original_response(content=f"✅ Сервер установлен: **{server}**")
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
    
    @discord.ui.button(label="📢 Канал", style=discord.ButtonStyle.primary, row=1)
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        global ANNOUNCEMENT_CHANNEL_ID
        await interaction.response.send_message(
            "📢 **Введи упоминание канала** (например, `#вайпы`) или его ID:\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            
            if msg.channel_mentions:
                channel_id = msg.channel_mentions[0].id
                channel_name = msg.channel_mentions[0].mention
            else:
                channel_id = int(msg.content.strip())
                channel = bot.get_channel(channel_id)
                channel_name = channel.mention if channel else "Неизвестный канал"
            
            raid_data["channel_id"] = channel_id
            ANNOUNCEMENT_CHANNEL_ID = channel_id
            save_data()
            await msg.delete()
            await interaction.edit_original_response(content=f"✅ Канал установлен: {channel_name}")
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
        except:
            await interaction.edit_original_response(content="❌ Неверный ID канала!")
    
    @discord.ui.button(label="⏰ Напоминание", style=discord.ButtonStyle.primary, row=1)
    async def set_reminder(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ReminderSelectView(author_id=interaction.user.id)
        await interaction.response.send_message(
            "⏰ **За сколько часов до вайпа напомнить?**",
            ephemeral=True,
            view=view
        )
    
    @discord.ui.button(label="🗺️ Карта", style=discord.ButtonStyle.primary, row=1)
    async def set_map(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🗺️ **Введите ссылку на карту** (например, `https://rustmaps.com/...`):\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            url = msg.content.strip()
            if url.startswith("http"):
                raid_data["map_url"] = url
                save_data()
                await msg.delete()
                await interaction.edit_original_response(content=f"✅ Ссылка на карту установлена!")
            else:
                await interaction.edit_original_response(content="❌ Ссылка должна начинаться с http:// или https://")
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
    
    @discord.ui.button(label="📋 Показать настройки", style=discord.ButtonStyle.success, row=2)
    async def show_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📋 ТЕКУЩИЕ НАСТРОЙКИ ВАЙПА",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="🕐 Время", value=f"**{raid_data.get('time', '20:00')}**", inline=True)
        embed.add_field(name="📅 День недели", value=f"**{raid_data.get('weekday', 'Суббота')}**", inline=True)
        embed.add_field(name="🎮 Сервер", value=f"**{raid_data.get('server', 'Rustoria #1')}**", inline=True)
        
        channel_text = f"<#{raid_data['channel_id']}>" if raid_data.get('channel_id') else "❌ Не установлен"
        embed.add_field(name="📢 Канал", value=channel_text, inline=True)
        embed.add_field(name="⏰ Напоминание", value=f"За **{raid_data.get('reminder_hours', 1)}** час(а)", inline=True)
        embed.add_field(name="🗺️ Карта", value=f"[Ссылка]({raid_data.get('map_url', 'https://rustmaps.com/')})", inline=True)
        
        # Показываем следующий вайп
        next_wipe = get_next_wipe_time()
        if next_wipe:
            time_left = next_wipe - datetime.now()
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            embed.add_field(
                name="⏳ До следующего вайпа",
                value=f"**{days}д {hours}ч {minutes}мин**",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.secondary, row=2)
    async def close_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔒 Меню настроек закрыто",
            description="Используй `/vipeset` чтобы открыть снова.",
            color=0x808080
        )
        await interaction.response.edit_message(embed=embed, view=None)


class WeekdaySelectView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id
        
        # Добавляем кнопки для каждого дня
        for i, day in enumerate(WEEKDAYS):
            row = i // 3  # 3 кнопки в ряд
            btn = discord.ui.Button(
                label=day,
                style=discord.ButtonStyle.primary,
                custom_id=f"weekday_{day}",
                row=row
            )
            btn.callback = self.make_callback(day)
            self.add_item(btn)
    
    def make_callback(self, day):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("❌ Не твоё меню!", ephemeral=True)
                return
            
            raid_data["weekday"] = day
            schedule_raid()
            save_data()
            
            await interaction.response.edit_message(
                content=f"✅ День недели установлен: **{day}**",
                view=None
            )
        return callback


class ReminderSelectView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id
        
        for hours in [1, 2, 3, 6, 12, 24]:
            btn = discord.ui.Button(
                label=f"{hours} час(а)",
                style=discord.ButtonStyle.primary,
                custom_id=f"reminder_{hours}"
            )
            btn.callback = self.make_callback(hours)
            self.add_item(btn)
    
    def make_callback(self, hours):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("❌ Не твоё меню!", ephemeral=True)
                return
            
            raid_data["reminder_hours"] = hours
            schedule_raid()
            save_data()
            
            await interaction.response.edit_message(
                content=f"✅ Напоминание установлено: за **{hours}** час(а) до вайпа",
                view=None
            )
        return callback


@bot.tree.command(name="vipeset", description="Настройка вайпа (только для администраторов)")
@app_commands.default_permissions(administrator=True)
async def vipeset(interaction: discord.Interaction):
    """Открывает меню настройки вайпа"""
    
    # Проверка доступа
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message(
            "❌ У вас нет прав для настройки вайпа!",
            ephemeral=True
        )
        return
    
    view = VipeSetView(author_id=interaction.user.id)
    embed = view.get_main_embed()
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    view.message = await interaction.original_response()

# ----------------------------------------------------
# МОНИТОРИНГ СЕРВЕРОВ (оставляем)
# ----------------------------------------------------

def schedule_server_monitoring():
    for job in scheduler.get_jobs():
        if job.id == "server_monitor":
            scheduler.remove_job(job.id)
    scheduler.add_job(
        func=check_all_servers,
        trigger=CronTrigger(minute=0),
        id="server_monitor",
        replace_existing=True
    )
    asyncio.create_task(check_all_servers())
    print("✅ Настроен мониторинг серверов (каждый час)")

async def check_all_servers():
    if not monitored_servers:
        return
    now = datetime.now()
    for server in monitored_servers:
        try:
            channel_id = server.get("channel_id")
            if not channel_id:
                continue
            channel = bot.get_channel(channel_id)
            if not channel:
                continue
            next_wipe = get_next_wipe_time()
            if not next_wipe:
                continue
            time_left = next_wipe - now
            if timedelta(0) < time_left <= timedelta(hours=1):
                notification_file = f"notified_{server['name'].replace(' ', '_')}.txt"
                today_str = now.strftime("%Y-%m-%d")
                already_notified = False
                if os.path.exists(notification_file):
                    with open(notification_file, 'r') as f:
                        if today_str in f.read():
                            already_notified = True
                if not already_notified:
                    hours = time_left.seconds // 3600
                    minutes = (time_left.seconds % 3600) // 60
                    embed = discord.Embed(
                        title="🔔 ВАЙП НА СЕРВЕРЕ!",
                        description=f"Сервер **{server['name']}** скоро вайпнется!",
                        color=0xff5500,
                        timestamp=datetime.now()
                    )
                    embed.add_field(name="⏰ До вайпа осталось", value=f"**{hours} ч {minutes} мин**", inline=True)
                    embed.add_field(name="📅 День вайпа", value=f"**{server.get('wipe_day', 'Не указан')}**", inline=True)
                    embed.add_field(name="🕐 Время вайпа", value=f"**{server.get('wipe_time', '20:00')}**", inline=True)
                    embed.set_footer(text="Готовьтесь к вайпу! 🔥")
                    await channel.send("@everyone", embed=embed)
                    with open(notification_file, 'w') as f:
                        f.write(today_str)
                    print(f"✅ Отправлено уведомление о вайпе на сервере {server['name']}")
        except Exception as e:
            print(f"❌ Ошибка при проверке сервера {server.get('name', 'Unknown')}: {e}")

# ----------------------------------------------------
# УПРАВЛЕНИЕ СОБЫТИЯМИ
# ----------------------------------------------------

def schedule_events():
    for job in scheduler.get_jobs():
        if job.id and job.id.startswith("event_"):
            scheduler.remove_job(job.id)
    
    for event in events:
        try:
            event_time = datetime.strptime(event["datetime"], "%Y-%m-%d %H:%M")
            if event_time <= datetime.now():
                continue
            scheduler.add_job(
                func=send_event_notification,
                trigger=CronTrigger(
                    year=event_time.year,
                    month=event_time.month,
                    day=event_time.day,
                    hour=event_time.hour,
                    minute=event_time.minute
                ),
                id=f"event_{event['id']}",
                args=[event],
                replace_existing=True
            )
            reminder_time = event_time - timedelta(hours=1)
            if reminder_time > datetime.now():
                scheduler.add_job(
                    func=send_event_reminder,
                    trigger=CronTrigger(
                        year=reminder_time.year,
                        month=reminder_time.month,
                        day=reminder_time.day,
                        hour=reminder_time.hour,
                        minute=reminder_time.minute
                    ),
                    id=f"event_reminder_{event['id']}",
                    args=[event],
                    replace_existing=True
                )
            print(f"✅ Событие '{event['name']}' запланировано на {event['datetime']}")
        except Exception as e:
            print(f"❌ Ошибка планирования события {event.get('name', 'Unknown')}: {e}")

async def send_event_notification(event):
    channel_id = event.get("channel_id")
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    embed = discord.Embed(
        title=f"📢 {event['name']}",
        description=event.get("description", "Событие началось!"),
        color=0xff5500,
        timestamp=datetime.now()
    )
    embed.add_field(name="📅 Дата", value=event["date"], inline=True)
    embed.add_field(name="🕐 Время", value=event["time"], inline=True)
    embed.add_field(name="🔊 Голосовой канал", value=f"**{event.get('voice_channel', 'Не указан')}**", inline=True)
    if event.get("map_url"):
        embed.add_field(name="🗺️ Карта", value=f"[Ссылка]({event['map_url']})", inline=False)
    embed.set_footer(text="Событие началось! Всех ждём! 🎉")
    await channel.send("@everyone", embed=embed)

async def send_event_reminder(event):
    channel_id = event.get("channel_id")
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    embed = discord.Embed(
        title=f"⏰ НАПОМИНАНИЕ: {event['name']}",
        description=f"**Через 1 час** начнётся событие!",
        color=0xffaa00,
        timestamp=datetime.now()
    )
    embed.add_field(name="📅 Дата", value=event["date"], inline=True)
    embed.add_field(name="🕐 Время", value=event["time"], inline=True)
    embed.add_field(name="🔊 Голосовой канал", value=f"**{event.get('voice_channel', 'Не указан')}**", inline=True)
    if event.get("map_url"):
        embed.add_field(name="🗺️ Карта", value=f"[Ссылка]({event['map_url']})", inline=False)
    embed.set_footer(text="Готовьтесь! Скоро начало! 🔥")
    await channel.send("@everyone", embed=embed)

# ----------------------------------------------------
# [ОСТАЛЬНЫЕ КОМАНДЫ: /help, /статистика, /варн, /состав, /событие и т.д.]
# Пока оставляем их без изменений, чтобы не сломать бота
# ----------------------------------------------------

# -------- /help --------
@bot.tree.command(name="help", description="Показывает список команд")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 КОМАНДЫ БОТА",
        color=0x00aaff,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="⚔️ ВАЙПЫ",
        value="`/vipeset` - Настройка вайпа",
        inline=False
    )
    
    embed.add_field(
        name="🎮 СЕРВЕРА",
        value="`/сервера` - Ближайшие вайпы\n"
              "`/сервер_добавить` - Добавить сервер\n"
              "`/сервер_удалить` - Удалить сервер",
        inline=False
    )
    
    embed.add_field(
        name="📋 ПРОЧЕЕ",
        value="`/статистика` - Статистика\n"
              "`/состав` - Отметить участников\n"
              "`/событие` - Создать событие",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------- /сервера (оставляем) --------
@bot.tree.command(name="сервера", description="Показывает отслеживаемые сервера")
async def servers_slash(interaction: discord.Interaction):
    if not monitored_servers:
        await interaction.response.send_message("📋 Нет отслеживаемых серверов.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎮 ОТСЛЕЖИВАЕМЫЕ СЕРВЕРА",
        color=0x00aaff,
        timestamp=datetime.now()
    )
    
    for server in monitored_servers:
        embed.add_field(
            name=f"🎮 {server['name']}",
            value=f"📅 Вайп: **{server.get('wipe_day', 'Не указан')}**\n"
                  f"🕐 Время: **{server.get('wipe_time', '20:00')}**",
            inline=True
        )
    
    await interaction.response.send_message(embed=embed)

# -------- /сервер_добавить --------
@bot.tree.command(name="сервер_добавить", description="Добавляет сервер для мониторинга")
@app_commands.default_permissions(administrator=True)
async def server_add_slash(interaction: discord.Interaction, название: str, день: str, время: str = "20:00"):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав!", ephemeral=True)
        return
    
    for server in monitored_servers:
        if server["name"].lower() == название.lower():
            await interaction.response.send_message(f"❌ Сервер **{название}** уже в списке!", ephemeral=True)
            return
    
    monitored_servers.append({
        "name": название,
        "wipe_day": день,
        "wipe_time": время,
        "channel_id": interaction.channel.id
    })
    save_servers()
    
    await interaction.response.send_message(f"✅ Сервер **{название}** добавлен!")

# -------- /сервер_удалить --------
@bot.tree.command(name="сервер_удалить", description="Удаляет сервер из мониторинга")
@app_commands.default_permissions(administrator=True)
async def server_remove_slash(interaction: discord.Interaction, название: str):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав!", ephemeral=True)
        return
    
    for i, server in enumerate(monitored_servers):
        if server["name"].lower() == название.lower():
            monitored_servers.pop(i)
            save_servers()
            await interaction.response.send_message(f"✅ Сервер **{название}** удалён!")
            return
    
    await interaction.response.send_message(f"❌ Сервер **{название}** не найден!", ephemeral=True)

# ----------------------------------------------------
# ЗАПУСК БОТА
# ----------------------------------------------------

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: Переменная окружения BOT_TOKEN не задана!")
    exit(1)

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Ошибка: Неверный токен.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
