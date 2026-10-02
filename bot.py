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
    "date": "Ежедневно",
    "server": "Rustoria #1",
    "channel_id": None,
    "voice_channel": "Афк-канал",
    "map_url": "https://rustmaps.com/",
    "map_image": "",
    "reminder_hours": 1,
    "message": "⚔️ ВНИМАНИЕ! Вайп в {time} на карте {map}! Сбор в {location}! Не опаздываем! 🏃‍♂️"
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

def get_next_wipe(server):
    try:
        now = datetime.now()
        wipe_day = server.get("wipe_day", "Суббота").lower()
        wipe_time = server.get("wipe_time", "20:00")
        hour, minute = map(int, wipe_time.split(":"))
        weekdays = {
            "понедельник": 0, "вторник": 1, "среда": 2, 
            "четверг": 3, "пятница": 4, "суббота": 5, "воскресенье": 6
        }
        if wipe_day in weekdays:
            target_weekday = weekdays[wipe_day]
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
    print(f'📋 Отслеживаемых серверов: {len(monitored_servers)}')
    
    if not scheduler.running:
        scheduler.start()
    
    schedule_raid()
    schedule_server_monitoring()
    schedule_events()
    
    # ========== СИНХРОНИЗАЦИЯ СЛЕШ-КОМАНД ==========
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
    # ================================================
    
    await bot.change_presence(activity=discord.Game(name="/help | Раст"))

# ----------------------------------------------------
# КОМАНДА: /sync
# ----------------------------------------------------

@bot.tree.command(name="sync", description="Синхронизирует слеш-команды (только для владельца)")
async def sync_commands(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        await bot.tree.sync(guild=interaction.guild)
        commands = await bot.tree.fetch_commands(guild=interaction.guild)
        
        embed = discord.Embed(
            title="✅ КОМАНДЫ СИНХРОНИЗИРОВАНЫ",
            description=f"Зарегистрировано **{len(commands)}** команд",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        cmd_list = ""
        for cmd in commands[:25]:
            cmd_list += f"`/{cmd.name}`\n"
        
        if len(commands) > 25:
            cmd_list += f"... и ещё {len(commands) - 25} команд"
        
        embed.add_field(name="📋 Список команд", value=cmd_list, inline=False)
        embed.set_footer(text="Команды должны появиться в течение нескольких минут")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка синхронизации: {e}", ephemeral=True)

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
    print(f"✅ Уведомление о событии '{event['name']}' отправлено в {channel.name}")

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
    print(f"✅ Напоминание о событии '{event['name']}' отправлено в {channel.name}")

# ----------------------------------------------------
# СИСТЕМА ЗАЯВОК (МОДАЛЬНЫЕ ОКНА)
# ----------------------------------------------------

class ApplicationModal(discord.ui.Modal, title='📝 ПОДАЧА ЗАЯВКИ'):
    name = discord.ui.TextInput(
        label='👤 Ваше имя',
        placeholder='Введите ваше игровое имя',
        required=True,
        max_length=50
    )
    age = discord.ui.TextInput(
        label='📅 Ваш возраст',
        placeholder='Введите ваш возраст (например: 22)',
        required=True,
        max_length=3
    )
    steam = discord.ui.TextInput(
        label='🔗 Ссылка на Steam профиль',
        placeholder='https://steamcommunity.com/id/your_profile',
        required=True,
        max_length=200
    )
    role = discord.ui.TextInput(
        label='🎯 Желаемая роль',
        placeholder='Строитель / Комбат / Фарм / Фермер / Электрик / Коллер',
        required=True,
        max_length=50
    )
    source = discord.ui.TextInput(
        label='📢 Откуда вы о нас узнали?',
        placeholder='Например: Реклама, друзья, YouTube, Twitch и т.д.',
        required=True,
        max_length=100
    )
    steam_tag = discord.ui.TextInput(
        label='🏷️ Готовы поставить приписку в стиме?',
        placeholder='Напишите "Да" или "Нет"',
        required=True,
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        global applications_data
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            for app in applications_data.get("applications", []):
                if app["user_id"] == str(interaction.user.id) and app["status"] == "pending":
                    await interaction.followup.send(
                        "❌ У вас уже есть активная заявка! Дождитесь её рассмотрения.",
                        ephemeral=True
                    )
                    return
            
            try:
                age_int = int(self.age.value)
                if age_int < 14:
                    await interaction.followup.send(
                        "❌ Извините, вам должно быть 14+ лет для подачи заявки!",
                        ephemeral=True
                    )
                    return
            except:
                await interaction.followup.send(
                    "❌ Пожалуйста, введите корректный возраст (число)!",
                    ephemeral=True
                )
                return
            
            if self.steam_tag.value.lower() not in ["да", "нет"]:
                await interaction.followup.send(
                    "❌ Пожалуйста, ответьте 'Да' или 'Нет' на вопрос о приписке!",
                    ephemeral=True
                )
                return
            
            application = {
                "id": len(applications_data.get("applications", [])) + 1,
                "user_id": str(interaction.user.id),
                "username": interaction.user.display_name,
                "name": self.name.value,
                "age": self.age.value,
                "steam": self.steam.value,
                "role": self.role.value,
                "source": self.source.value,
                "steam_tag": self.steam_tag.value,
                "status": "pending",
                "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "moderator": None,
                "closed_at": None
            }
            
            if "applications" not in applications_data:
                applications_data["applications"] = []
            applications_data["applications"].append(application)
            applications_data["total"] = len(applications_data["applications"])
            applications_data["pending"] = sum(1 for a in applications_data["applications"] if a["status"] == "pending")
            save_applications()
            
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name="ЗАЯВКИ")
            if not category:
                category = await guild.create_category("ЗАЯВКИ")
            
            channel_name = f"заявка-{interaction.user.name.lower()[:20]}"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            for role in guild.roles:
                if role.name in ["Admin", "Администратор", "Moderator", "Модератор", "главный"]:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            for role_id in allowed_roles:
                role = guild.get_role(int(role_id))
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
            
            embed = discord.Embed(
                title="📋 НОВАЯ ЗАЯВКА",
                description=f"**Заявка #{application['id']}**",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.add_field(name="👤 Имя", value=self.name.value, inline=True)
            embed.add_field(name="📅 Возраст", value=f"{self.age.value} лет", inline=True)
            embed.add_field(name="🔗 Steam", value=f"[Профиль]({self.steam.value})", inline=True)
            embed.add_field(name="🎯 Желаемая роль", value=self.role.value, inline=True)
            embed.add_field(name="📢 Откуда узнали", value=self.source.value, inline=True)
            embed.add_field(name="🏷️ Приписка в стиме", value=self.steam_tag.value, inline=True)
            embed.add_field(name="📊 Статус", value="⏳ Ожидает рассмотрения", inline=False)
            embed.set_footer(text=f"Создана: {application['created_at']}")
            
            view = ApplicationControlView(application_id=application["id"])
            await channel.send(f"{interaction.user.mention} Ваша заявка создана!", embed=embed, view=view)
            
            apps_channel = bot.get_channel(APPLICATIONS_CHANNEL_ID) if APPLICATIONS_CHANNEL_ID else None
            if apps_channel:
                await apps_channel.send(
                    f"📢 **Новая заявка!** {interaction.user.mention} подал заявку. Канал: {channel.mention}"
                )
            
            await interaction.followup.send(
                f"✅ Ваша заявка успешно создана! Канал: {channel.mention}\nОжидайте рассмотрения администрацией.",
                ephemeral=True
            )
            
            await update_applications_stats()
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Произошла ошибка: {str(e)}",
                ephemeral=True
            )

class ApplicationButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="📝 Подать заявку", style=discord.ButtonStyle.primary, emoji="📝", custom_id="create_application")
    async def create_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())

class ApplicationControlView(discord.ui.View):
    def __init__(self, application_id: int):
        super().__init__(timeout=None)
        self.application_id = application_id
    
    def get_application(self):
        for app in applications_data.get("applications", []):
            if app["id"] == self.application_id:
                return app
        return None
    
    async def update_application_status(self, interaction: discord.Interaction, status: str, status_text: str, color: int):
        app = self.get_application()
        if not app:
            await interaction.response.send_message("❌ Заявка не найдена!", ephemeral=True)
            return
        
        app["status"] = status
        app["moderator"] = interaction.user.display_name
        app["closed_at"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        save_applications()
        
        embed = discord.Embed(
            title="📋 НОВАЯ ЗАЯВКА",
            description=f"**Заявка #{app['id']}**",
            color=color,
            timestamp=datetime.now()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.add_field(name="👤 Имя", value=app["name"], inline=True)
        embed.add_field(name="📅 Возраст", value=f"{app['age']} лет", inline=True)
        embed.add_field(name="🔗 Steam", value=f"[Профиль]({app['steam']})", inline=True)
        embed.add_field(name="🎯 Желаемая роль", value=app["role"], inline=True)
        embed.add_field(name="📢 Откуда узнали", value=app["source"], inline=True)
        embed.add_field(name="🏷️ Приписка в стиме", value=app["steam_tag"], inline=True)
        embed.add_field(name="📊 Статус", value=status_text, inline=False)
        embed.add_field(name="🛡️ Модератор", value=app["moderator"], inline=True)
        embed.add_field(name="📅 Закрыта", value=app["closed_at"], inline=True)
        embed.set_footer(text=f"Создана: {app['created_at']}")
        
        await interaction.message.edit(embed=embed, view=None)
        
        try:
            user = await interaction.guild.fetch_member(int(app["user_id"]))
            if user:
                dm_embed = discord.Embed(
                    title=f"📢 Ваша заявка #{app['id']}",
                    description=f"Статус: **{status_text}**",
                    color=color
                )
                dm_embed.add_field(name="🛡️ Модератор", value=app["moderator"], inline=True)
                dm_embed.add_field(name="📅 Дата", value=app["closed_at"], inline=True)
                await user.send(embed=dm_embed)
        except:
            pass
        
        if status == "accepted":
            await self.give_role(interaction, app)
        
        await update_applications_stats()
        await interaction.response.send_message(f"✅ Заявка #{app['id']} {status_text.lower()}!", ephemeral=True)
    
    async def give_role(self, interaction: discord.Interaction, app):
        try:
            user = await interaction.guild.fetch_member(int(app["user_id"]))
            if not user:
                return
            role_name = app["role"]
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if not role:
                for r in interaction.guild.roles:
                    if r.name.lower() == role_name.lower():
                        role = r
                        break
            if role:
                await user.add_roles(role)
            else:
                role = await interaction.guild.create_role(name=role_name)
                await user.add_roles(role)
        except:
            pass
    
    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.success, emoji="✅", custom_id="accept_application")
    async def accept_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin_or_moderator(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ У вас нет прав для этого действия!", ephemeral=True)
            return
        await self.update_application_status(interaction, "accepted", "✅ Принята", 0x00ff00)
    
    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger, emoji="❌", custom_id="reject_application")
    async def reject_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin_or_moderator(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ У вас нет прав для этого действия!", ephemeral=True)
            return
        await self.update_application_status(interaction, "rejected", "❌ Отклонена", 0xff0000)
    
    @discord.ui.button(label="🗑️ Закрыть", style=discord.ButtonStyle.secondary, emoji="🗑️", custom_id="close_application")
    async def close_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin_or_moderator(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ У вас нет прав для этого действия!", ephemeral=True)
            return
        app = self.get_application()
        if app:
            app["status"] = "closed"
            app["moderator"] = interaction.user.display_name
            app["closed_at"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            save_applications()
            await update_applications_stats()
        await interaction.response.send_message("🗑️ Канал будет удалён через 5 секунд...")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

async def update_applications_stats():
    apps_channel = bot.get_channel(APPLICATIONS_CHANNEL_ID) if APPLICATIONS_CHANNEL_ID else None
    if not apps_channel:
        return
    async for message in apps_channel.history(limit=100):
        if message.author == bot.user and message.embeds:
            embed = message.embeds[0]
            if embed.title and "📊 СТАТИСТИКА ЗАЯВОК" in embed.title:
                embed = discord.Embed(
                    title="📊 СТАТИСТИКА ЗАЯВОК",
                    description="Статистика всех заявок в клан",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📋 Всего заявок", value=applications_data.get("total", 0), inline=True)
                embed.add_field(name="⏳ На рассмотрении", value=applications_data.get("pending", 0), inline=True)
                embed.add_field(name="✅ Принято", value=applications_data.get("accepted", 0), inline=True)
                embed.add_field(name="❌ Отклонено", value=applications_data.get("rejected", 0), inline=True)
                embed.set_footer(text="Нажми кнопку ниже, чтобы подать заявку")
                await message.edit(embed=embed)
                return
    embed = discord.Embed(
        title="📊 СТАТИСТИКА ЗАЯВОК",
        description="Статистика всех заявок в клан",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.add_field(name="📋 Всего заявок", value=applications_data.get("total", 0), inline=True)
    embed.add_field(name="⏳ На рассмотрении", value=applications_data.get("pending", 0), inline=True)
    embed.add_field(name="✅ Принято", value=applications_data.get("accepted", 0), inline=True)
    embed.add_field(name="❌ Отклонено", value=applications_data.get("rejected", 0), inline=True)
   