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
    embed.set_footer(text="Нажми кнопку ниже, чтобы подать заявку")
    view = ApplicationButton()
    await apps_channel.send(embed=embed, view=view)

# ----------------------------------------------------
# РАСПИСАНИЕ МОНИТОРИНГА СЕРВЕРОВ
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
            next_wipe = get_next_wipe(server)
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
# РАСПИСАНИЕ ВАЙПА
# ----------------------------------------------------

def schedule_raid():
    for job in scheduler.get_jobs():
        if job.id in ["raid_announcement", "raid_reminder"]:
            scheduler.remove_job(job.id)
    try:
        hour, minute = map(int, raid_data["time"].split(":"))
        scheduler.add_job(
            func=send_raid_announcement,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="raid_announcement",
            replace_existing=True
        )
        reminder_hours = raid_data.get("reminder_hours", 1)
        reminder_hour = hour - reminder_hours
        if reminder_hour < 0:
            reminder_hour = 24 + reminder_hour
        scheduler.add_job(
            func=send_raid_reminder,
            trigger=CronTrigger(hour=reminder_hour, minute=minute),
            id="raid_reminder",
            replace_existing=True
        )
        print(f"⏰ Вайп запланирован на {raid_data['time']}")
        print(f"⏰ Напоминание за {reminder_hours} ч до вайпа")
    except Exception as e:
        print(f"❌ Ошибка при настройке расписания: {e}")

async def send_raid_reminder():
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
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}** по МСК", inline=True)
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка на карту]({raid_data['map_url']})", inline=True)
    embed.add_field(name="🔊 Голосовой канал", value=f"**{raid_data['voice_channel']}**", inline=True)
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=False)
    if raid_data.get("map_image"):
        embed.set_image(url=raid_data["map_image"])
    embed.set_footer(text="Подготовьтесь к вайпу! 🔥")
    await channel.send("@everyone", embed=embed)
    print(f"✅ Напоминание о вайпе отправлено в {channel.name}")

async def send_raid_announcement():
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
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}** по МСК", inline=True)
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка на карту]({raid_data['map_url']})", inline=True)
    embed.add_field(name="🔊 Голосовой канал", value=f"**{raid_data['voice_channel']}**", inline=True)
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=False)
    if raid_data.get("map_image"):
        embed.set_image(url=raid_data["map_image"])
    embed.set_footer(text="Всем удачи на новом вайпе! 🔥")
    await channel.send("@everyone", embed=embed)
    print(f"✅ Сообщение о вайпе отправлено в {channel.name}")

# ----------------------------------------------------
# СЛЕШ-КОМАНДЫ
# ----------------------------------------------------

# -------- /помощь --------
class HelpView(discord.ui.View):
    def __init__(self, author_id, has_admin_access):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.has_admin_access = has_admin_access
        self.current_page = 0
        self.message = None
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Это меню помощи вызвано другим пользователем!",
                ephemeral=True
            )
            return False
        return True
    
    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)
            await asyncio.sleep(5)
            try:
                await self.message.delete()
            except:
                pass
    
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        if self.current_page < 0:
            self.current_page = 0
        await self.update_help(interaction)
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_help(interaction)
    
    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.secondary, emoji="❌")
    async def close_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔒 Меню помощи закрыто",
            description="Используй `/help` чтобы открыть снова.",
            color=0x808080
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(5)
        try:
            await interaction.message.delete()
        except:
            pass
    
    async def update_help(self, interaction: discord.Interaction):
        embed = self.get_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    def get_embed(self):
        embed = discord.Embed(
            title="📚 ПОМОЩЬ ПО КОМАНДАМ",
            color=0x00aaff,
            timestamp=datetime.now()
        )
        if self.current_page == 0:
            embed.description = "**Страница 1/3 — Основные команды**"
            embed.add_field(
                name="👥 ОСНОВНЫЕ КОМАНДЫ (ДЛЯ ВСЕХ)",
                value="`/вайп` - Показать расписание вайпа\n"
                      "`/состав` - Отметить всех участников с ролью\n"
                      "`/состав_онлайн` - Отметить только онлайн участников\n"
                      "`/сервера` - Показать все отслеживаемые сервера\n"
                      "`/события` - Показать список событий\n"
                      "`/статистика` - Показать статистику пользователя\n"
                      "`/help` - Показать это меню",
                inline=False
            )
            embed.set_footer(text="Страница 1/3 | Используй стрелки для навигации")
        elif self.current_page == 1:
            embed.description = "**Страница 2/3 — Команды настройки**"
            player_commands = (
                "**Для всех:**\n"
                "`/вайп` - Расписание вайпа\n"
                "`/состав` - Отметить участников\n"
                "`/состав_онлайн` - Отметить онлайн\n"
                "`/сервера` - Сервера и вайпы\n"
                "`/события` - Список событий\n"
                "`/статистика` - Статистика пользователя\n"
                "`/help` - Это меню"
            )
            embed.add_field(name="👥 ОБЩИЕ КОМАНДЫ", value=player_commands, inline=False)
            if self.has_admin_access:
                admin_commands = (
                    "**Для администраторов:**\n"
                    "`/vexset` - Открыть меню настроек\n"
                    "`/событие` - Создать новое событие\n"
                    "`/событие_удалить` - Удалить событие\n"
                    "`/варн` - Выдать варн игроку\n"
                    "`/варны` - Показать варны игрока\n"
                    "`/снять_варн` - Снять варн\n"
                    "`/заявки_канал` - Установить канал для заявок\n"
                    "`/заявки_список` - Список всех заявок\n"
                    "`/заявка_удалить` - Удалить заявку\n"
                    "`/вайп_канал` - Установить канал для оповещений\n"
                    "`/вайп_настройка` - Настроить время, карту, место, канал и другое\n"
                    "`/вайп_сообщение` - Изменить текст оповещения\n"
                    "`/вайп_тест` - Отправить тестовое оповещение\n"
                    "`/сервер_добавить` - Добавить сервер для мониторинга\n"
                    "`/сервер_удалить` - Удалить сервер\n"
                    "`/сервер_список` - Список серверов\n"
                    "`/сервер_канал` - Изменить канал для сервера\n"
                    "`/проверить_роли` - Проверить наличие ролей авто-выдачи\n"
                    "`/выдать_роль_новичка` - Выдать роль ɴᴇᴡʙɪᴇ вручную\n"
                    "`/убрать_роль_новичка` - Убрать роль ɴᴇᴡʙɪᴇ\n"
                    "`/sync` - Синхронизировать слеш-команды"
                )
                embed.add_field(name="⚙️ АДМИН-КОМАНДЫ", value=admin_commands, inline=False)
            else:
                embed.add_field(
                    name="🔒 АДМИН-КОМАНДЫ",
                    value="У вас нет прав для использования команд настройки.\n"
                          "Обратитесь к администратору сервера.",
                    inline=False
                )
            embed.set_footer(text="Страница 2/3 | Используй стрелки для навигации")
        else:
            embed.description = "**Страница 3/3 — Настройка ролей для /состав**"
            embed.add_field(
                name="🎯 ДОСТУПНЫЕ РОЛИ ДЛЯ /СОСТАВ",
                value="Бот ищет следующие роли на сервере:\n"
                      "• `ʙᴜɪʟᴅᴇʀ` - Строители\n"
                      "• `ᴄᴏʟʟᴇʀ` - Сборщики\n"
                      "• `ᴄᴏᴍʙᴀᴛ` - Бойцы\n"
                      "• `ᴇʟᴇᴄᴛʀɪᴄ` - Электрики\n"
                      "• `ꜰᴀʀᴍ` - Фермеры\n"
                      "• `ꜰᴇʀᴍᴇʀ` - Животноводы\n\n"
                      "**Для отметки участников:**\n"
                      "1. Создай роли с этими названиями\n"
                      "2. Выдай их участникам\n"
                      "3. Используй `/состав` для выбора роли",
                inline=False
            )
            embed.set_footer(text="Страница 3/3 | Используй стрелки для навигации")
        return embed

@bot.tree.command(name="help", description="Показывает меню помощи")
async def help_slash(interaction: discord.Interaction):
    has_admin = has_access(interaction.user, interaction.guild)
    view = HelpView(author_id=interaction.user.id, has_admin_access=has_admin)
    embed = view.get_embed()
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

# -------- /вайп --------
@bot.tree.command(name="вайп", description="Показывает расписание вайпа")
async def raid_slash(interaction: discord.Interaction):
    if not raid_data.get("channel_id"):
        await interaction.response.send_message("❌ Вайп ещё не настроен! Администратор должен использовать `/вайп_настройка`", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="⚔️ РАСПИСАНИЕ ВАЙПА ⚔️",
        color=0xff5500,
        timestamp=datetime.now()
    )
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}** по МСК", inline=True)
    embed.add_field(name="📅 Дата", value=f"**{raid_data.get('date', 'Ежедневно')}**", inline=True)
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка на карту]({raid_data['map_url']})", inline=True)
    embed.add_field(name="🔊 Голосовой канал", value=f"**{raid_data['voice_channel']}**", inline=True)
    embed.add_field(
        name="⏰ Напоминание",
        value=f"За **{raid_data.get('reminder_hours', 1)}** час(а) до вайпа",
        inline=True
    )
    if raid_data.get("map_image"):
        embed.set_image(url=raid_data["map_image"])
    try:
        now = datetime.now()
        raid_hour, raid_minute = map(int, raid_data["time"].split(":"))
        raid_time_today = now.replace(hour=raid_hour, minute=raid_minute, second=0, microsecond=0)
        if now > raid_time_today:
            raid_time_today += timedelta(days=1)
        time_left = raid_time_today - now
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        seconds = time_left.seconds % 60
        embed.add_field(
            name="⏳ До вайпа осталось",
            value=f"**{hours} ч {minutes} мин {seconds} сек**",
            inline=False
        )
    except:
        pass
    embed.set_footer(text="Используй /вайп для актуальной информации")
    await interaction.response.send_message(embed=embed)

# -------- /вайп_канал --------
@bot.tree.command(name="вайп_канал", description="Устанавливает текущий канал для оповещений о вайпе")
@app_commands.default_permissions(administrator=True)
async def raid_channel_slash(interaction: discord.Interaction):
    global ANNOUNCEMENT_CHANNEL_ID
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    raid_data["channel_id"] = interaction.channel.id
    ANNOUNCEMENT_CHANNEL_ID = interaction.channel.id
    save_data()
    await interaction.response.send_message(f"✅ Канал для оповещений установлен: {interaction.channel.mention}")

# -------- /вайп_настройка --------
@bot.tree.command(name="вайп_настройка", description="Настройка времени, карты, места и канала оповещений")
@app_commands.default_permissions(administrator=True)
async def raid_setup_slash(
    interaction: discord.Interaction,
    время: str = None,
    карта: str = None,
    место: str = None,
    канал: discord.TextChannel = None,
    голосовой_канал: str = None,
    ссылка_карта: str = None,
    напоминание_за: int = None
):
    global ANNOUNCEMENT_CHANNEL_ID
    
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    
    if not время and not карта and not место and not канал and not голосовой_канал and not ссылка_карта and not напоминание_за:
        embed = discord.Embed(
            title="⚙️ ТЕКУЩИЕ НАСТРОЙКИ ВАЙПА",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}** по МСК", inline=True)
        embed.add_field(name="🗺️ Карта", value=f"**{raid_data.get('map', 'Остров')}**", inline=True)
        embed.add_field(name="📍 Место", value=f"**{raid_data.get('location', 'Аэродром')}**", inline=True)
        embed.add_field(
            name="📢 Канал оповещений",
            value=f"<#{raid_data['channel_id']}>" if raid_data.get('channel_id') else "❌ Не установлен",
            inline=True
        )
        embed.add_field(
            name="🔊 Голосовой канал",
            value=f"**{raid_data.get('voice_channel', 'Не установлен')}**",
            inline=True
        )
        embed.add_field(
            name="🗺️ Ссылка на карту",
            value=f"[Клик для перехода]({raid_data.get('map_url', 'Не установлена')})",
            inline=True
        )
        embed.add_field(
            name="⏰ Напоминание",
            value=f"За **{raid_data.get('reminder_hours', 1)}** час(а) до вайпа",
            inline=True
        )
        embed.set_footer(text="Используй параметры для изменения настроек")
        await interaction.response.send_message(embed=embed)
        return
    
    changes = []
    
    if время:
        try:
            hour, minute = map(int, время.split(":"))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                raid_data["time"] = время
                schedule_raid()
                changes.append(f"🕐 Время: **{время}**")
            else:
                await interaction.response.send_message("❌ Неверный формат времени! Используй ЧЧ:ММ (например, 20:00)", ephemeral=True)
                return
        except:
            await interaction.response.send_message("❌ Неверный формат времени! Используй ЧЧ:ММ (например, 20:00)", ephemeral=True)
            return
    
    if карта:
        raid_data["map"] = карта
        changes.append(f"🗺️ Карта: **{карта}**")
    
    if место:
        raid_data["location"] = место
        changes.append(f"📍 Место: **{место}**")
    
    if канал:
        raid_data["channel_id"] = канал.id
        ANNOUNCEMENT_CHANNEL_ID = канал.id
        changes.append(f"📢 Канал: {канал.mention}")
    
    if голосовой_канал:
        raid_data["voice_channel"] = голосовой_канал
        changes.append(f"🔊 Голосовой канал: **{голосовой_канал}**")
    
    if ссылка_карта:
        if ссылка_карта.startswith("http"):
            raid_data["map_url"] = ссылка_карта
            changes.append(f"🗺️ Ссылка на карту: [Клик для перехода]({ссылка_карта})")
        else:
            await interaction.response.send_message("❌ Неверный формат ссылки! Ссылка должна начинаться с http:// или https://", ephemeral=True)
            return
    
    if напоминание_за:
        if 1 <= напоминание_за <= 24:
            raid_data["reminder_hours"] = напоминание_за
            schedule_raid()
            changes.append(f"⏰ Напоминание: за **{напоминание_за}** час(а) до вайпа")
        else:
            await interaction.response.send_message("❌ Напоминание должно быть от 1 до 24 часов!", ephemeral=True)
            return
    
    save_data()
    
    if changes:
        embed = discord.Embed(
            title="✅ НАСТРОЙКИ ОБНОВЛЕНЫ",
            description="\n".join(changes),
            color=0x00ff00,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Ничего не изменено!", ephemeral=True)

# -------- /вайп_сообщение --------
@bot.tree.command(name="вайп_сообщение", description="Изменяет текст оповещения о вайпе")
@app_commands.default_permissions(administrator=True)
async def raid_message_slash(interaction: discord.Interaction, текст: str):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    raid_data["message"] = текст
    save_data()
    await interaction.response.send_message("✅ Текст сообщения обновлён!")

# -------- /вайп_тест --------
@bot.tree.command(name="вайп_тест", description="Отправляет тестовое оповещение о вайпе")
@app_commands.default_permissions(administrator=True)
async def raid_test_slash(interaction: discord.Interaction):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    await interaction.response.send_message("✅ Тестовое сообщение отправляется...")
    await send_raid_announcement()

# -------- /vexset --------
@bot.tree.command(name="vexset", description="Открывает меню настройки вайпа")
@app_commands.default_permissions(administrator=True)
async def vexset_slash(interaction: discord.Interaction):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для настройки бота!", ephemeral=True)
        return
    embed = discord.Embed(
        title="⚙️ НАСТРОЙКА ВАЙПА",
        description="Используйте команды для настройки:",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}** по МСК", inline=True)
    embed.add_field(name="📅 Дата", value=f"**{raid_data.get('date', 'Ежедневно')}**", inline=True)
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
    embed.add_field(
        name="📢 Канал оповещений",
        value=f"<#{raid_data['channel_id']}>" if raid_data.get('channel_id') else "❌ Не установлен",
        inline=False
    )
    embed.add_field(
        name="🔊 Голосовой канал",
        value=f"**{raid_data.get('voice_channel', 'Не установлен')}**",
        inline=True
    )
    embed.add_field(
        name="🗺️ Карта",
        value=f"[Ссылка]({raid_data.get('map_url', 'Не установлена')})",
        inline=True
    )
    embed.add_field(
        name="⏰ Напоминание",
        value=f"За **{raid_data.get('reminder_hours', 1)}** час(а) до вайпа",
        inline=True
    )
    embed.set_footer(text="Используй /вайп_настройка для изменения параметров")
    await interaction.response.send_message(embed=embed)

# -------- /статистика --------
class StatsView(discord.ui.View):
    def __init__(self, user, guild, author_id):
        super().__init__(timeout=120)
        self.user = user
        self.guild = guild
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
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)
            await asyncio.sleep(5)
            try:
                await self.message.delete()
            except:
                pass
    
    @discord.ui.button(label="🔄 Обновить", style=discord.ButtonStyle.primary)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.get_stats_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.secondary, emoji="❌")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔒 Статистика закрыта",
            description="Используй `/статистика` чтобы открыть снова.",
            color=0x808080
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(5)
        try:
            await interaction.message.delete()
        except:
            pass
    
    def get_stats_embed(self):
        user_id = str(self.user.id)
        warns = warns_data.get(user_id, [])
        warn_count = len(warns)
        
        joined_at = self.user.joined_at
        joined_str = joined_at.strftime("%d.%m.%Y в %H:%M") if joined_at else "Неизвестно"
        
        roles = [role.mention for role in self.user.roles if role.name != "@everyone"]
        roles_str = " ".join(roles) if roles else "Нет ролей"
        
        status_map = {
            discord.Status.online: "🟢 Онлайн",
            discord.Status.idle: "🟡 Не активен",
            discord.Status.dnd: "🔴 Не беспокоить",
            discord.Status.offline: "⚫ Оффлайн"
        }
        status = status_map.get(self.user.status, "⚪ Неизвестно")
        
        voice_time = "Не в голосовом канале"
        if self.user.voice and self.user.voice.channel:
            voice_time = f"В канале: {self.user.voice.channel.name}"
        
        embed = discord.Embed(
            title=f"📊 СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ",
            color=self.user.color if self.user.color.value != 0 else 0x00ff00,
            timestamp=datetime.now()
        )
        
        embed.set_author(name=self.user.display_name, icon_url=self.user.avatar.url if self.user.avatar else None)
        embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else None)
        
        embed.add_field(name="🆔 Никнейм", value=f"{self.user.mention}", inline=False)
        embed.add_field(name="🆔 ID", value=f"`{self.user.id}`", inline=True)
        embed.add_field(name="📅 На сервере с", value=joined_str, inline=True)
        embed.add_field(name="📊 Статус", value=status, inline=True)
        embed.add_field(name="👥 Роли", value=roles_str if len(roles_str) < 1024 else roles_str[:1020] + "...", inline=False)
        embed.add_field(name="🔊 Голосовой канал", value=voice_time, inline=True)
        embed.add_field(name="⚠️ Варны", value=f"**{warn_count}**", inline=True)
        
        if warn_count > 0:
            warns_list = ""
            for i, warn in enumerate(warns[:5], 1):
                warns_list += f"**{i}.** {warn['reason']} (от {warn['moderator']}, {warn['date']})\n"
            if len(warns) > 5:
                warns_list += f"... и ещё {len(warns) - 5} варнов"
            embed.add_field(name="📋 Последние варны", value=warns_list, inline=False)
        
        embed.set_footer(text=f"Запросил: {self.author_id}")
        
        return embed

@bot.tree.command(name="статистика", description="Показывает статистику пользователя")
async def stats_slash(interaction: discord.Interaction, пользователь: discord.Member = None):
    if not interaction.guild:
        await interaction.response.send_message("❌ Эта команда работает только на сервере!", ephemeral=True)
        return
    
    if пользователь is None:
        пользователь = interaction.user
    
    if пользователь not in interaction.guild.members:
        await interaction.response.send_message("❌ Этот пользователь не найден на сервере!", ephemeral=True)
        return
    
    view = StatsView(пользователь, interaction.guild, interaction.user.id)
    embed = view.get_stats_embed()
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

# -------- /варн --------
@bot.tree.command(name="варн", description="Выдаёт варн игроку")
@app_commands.default_permissions(moderate_members=True)
async def warn_slash(interaction: discord.Interaction, игрок: discord.Member, причина: str = "Нарушение правил"):
    if not interaction.guild:
        await interaction.response.send_message("❌ Эта команда работает только на сервере!", ephemeral=True)
        return
    
    if игрок.id == interaction.user.id:
        await interaction.response.send_message("❌ Вы не можете выдать варн самому себе!", ephemeral=True)
        return
    
    if interaction.user.top_role <= игрок.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Вы не можете выдать варн участнику с более высокой или равной ролью!", ephemeral=True)
        return
    
    user_id = str(игрок.id)
    if user_id not in warns_data:
        warns_data[user_id] = []
    
    warn_info = {
        "reason": причина,
        "moderator": interaction.user.display_name,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    warns_data[user_id].append(warn_info)
    save_warns()
    
    embed = discord.Embed(
        title="⚠️ ВЫДАН ВАРН",
        color=0xff5500,
        timestamp=datetime.now()
    )
    embed.add_field(name="👤 Игрок", value=игрок.mention, inline=True)
    embed.add_field(name="🛡️ Модератор", value=interaction.user.mention, inline=True)
    embed.add_field(name="📝 Причина", value=причина, inline=False)
    embed.add_field(name="⚠️ Всего варнов", value=f"**{len(warns_data[user_id])}**", inline=True)
    
    await interaction.response.send_message(embed=embed)
    
    try:
        dm_embed = discord.Embed(
            title="⚠️ ВАМ ВЫДАН ВАРН",
            description=f"На сервере **{interaction.guild.name}**",
            color=0xff5500
        )
        dm_embed.add_field(name="🛡️ Модератор", value=interaction.user.display_name, inline=True)
        dm_embed.add_field(name="📝 Причина", value=причина, inline=False)
        dm_embed.add_field(name="⚠️ Всего варнов", value=f"**{len(warns_data[user_id])}**", inline=True)
        await игрок.send(embed=dm_embed)
    except:
        pass

# -------- /варны --------
@bot.tree.command(name="варны", description="Показывает все варны игрока")
@app_commands.default_permissions(moderate_members=True)
async def warns_slash(interaction: discord.Interaction, игрок: discord.Member):
    if not interaction.guild:
        await interaction.response.send_message("❌ Эта команда работает только на сервере!", ephemeral=True)
        return
    
    user_id = str(игрок.id)
    warns = warns_data.get(user_id, [])
    
    if not warns:
        await interaction.response.send_message(f"✅ У {игрок.mention} нет варнов!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"⚠️ ВАРНЫ ИГРОКА",
        description=f"Всего варнов: **{len(warns)}**",
        color=0xff5500,
        timestamp=datetime.now()
    )
    embed.set_author(name=игрок.display_name, icon_url=игрок.avatar.url if игрок.avatar else None)
    
    warns_list = ""
    for i, warn in enumerate(warns, 1):
        warns_list += f"**{i}.** {warn['reason']}\n   🛡️ {warn['moderator']} | {warn['date']}\n"
    
    if len(warns_list) > 1024:
        warns_list = warns_list[:1020] + "..."
    
    embed.add_field(name="📋 Список варнов", value=warns_list, inline=False)
    
    await interaction.response.send_message(embed=embed)

# -------- /снять_варн --------
@bot.tree.command(name="снять_варн", description="Снимает варн с игрока")
@app_commands.default_permissions(moderate_members=True)
async def unwarn_slash(interaction: discord.Interaction, игрок: discord.Member, номер: int = None):
    if not interaction.guild:
        await interaction.response.send_message("❌ Эта команда работает только на сервере!", ephemeral=True)
        return
    
    user_id = str(игрок.id)
    warns = warns_data.get(user_id, [])
    
    if not warns:
        await interaction.response.send_message(f"✅ У {игрок.mention} нет варнов!", ephemeral=True)
        return
    
    if номер is None:
        removed = warns.pop()
        save_warns()
        await interaction.response.send_message(f"✅ Снят последний варн у {игрок.mention} (причина: {removed['reason']})")
        return
    
    if 1 <= номер <= len(warns):
        removed = warns.pop(номер - 1)
        save_warns()
        await interaction.response.send_message(f"✅ Снят варн #{номер} у {игрок.mention} (причина: {removed['reason']})")
    else:
        await interaction.response.send_message(f"❌ Варн с номером {номер} не найден! Всего варнов: {len(warns)}", ephemeral=True)

# -------- /сервер_добавить --------
@bot.tree.command(name="сервер_добавить", description="Добавляет сервер для мониторинга вайпов")
@app_commands.default_permissions(administrator=True)
async def server_add_slash(
    interaction: discord.Interaction,
    название: str,
    день: str,
    время: str = "20:00"
):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    
    for server in monitored_servers:
        if server["name"].lower() == название.lower():
            await interaction.response.send_message(f"❌ Сервер **{название}** уже в списке!", ephemeral=True)
            return
    
    new_server = {
        "name": название,
        "wipe_day": день,
        "wipe_time": время,
        "channel_id": interaction.channel.id
    }
    monitored_servers.append(new_server)
    save_servers()
    
    await interaction.response.send_message(
        f"✅ Сервер **{название}** добавлен в мониторинг!\n"
        f"📅 День вайпа: **{день}**\n"
        f"🕐 Время: **{время}**\n"
        f"📢 Оповещения будут в этот канал"
    )

# -------- /сервер_удалить --------
@bot.tree.command(name="сервер_удалить", description="Удаляет сервер из мониторинга")
@app_commands.default_permissions(administrator=True)
async def server_remove_slash(interaction: discord.Interaction, название: str):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    
    for i, server in enumerate(monitored_servers):
        if server["name"].lower() == название.lower():
            monitored_servers.pop(i)
            save_servers()
            await interaction.response.send_message(f"✅ Сервер **{название}** удалён из мониторинга!")
            return
    
    await interaction.response.send_message(f"❌ Сервер **{название}** не найден в списке!", ephemeral=True)

# -------- /сервер_список --------
@bot.tree.command(name="сервер_список", description="Показывает список всех отслеживаемых серверов")
@app_commands.default_permissions(administrator=True)
async def server_list_slash(interaction: discord.Interaction):
    if not monitored_servers:
        await interaction.response.send_message("📋 Список серверов пуст. Добавьте сервер командой `/сервер_добавить`")
        return
    
    embed = discord.Embed(
        title="📋 ОТСЛЕЖИВАЕМЫЕ СЕРВЕРА",
        description=f"Всего: **{len(monitored_servers)}** серверов",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    
    for server in monitored_servers:
        next_wipe = get_next_wipe(server)
        time_left = ""
        if next_wipe:
            time_left_delta = next_wipe - datetime.now()
            days = time_left_delta.days
            hours = time_left_delta.seconds // 3600
            minutes = (time_left_delta.seconds % 3600) // 60
            time_left = f"**{days}д {hours}ч {minutes}мин**"
        else:
            time_left = "❌ Ошибка"
        
        embed.add_field(
            name=f"🎮 {server['name']}",
            value=f"📅 День: **{server.get('wipe_day', 'Не указан')}**\n"
                  f"🕐 Время: **{server.get('wipe_time', '20:00')}**\n"
                  f"⏳ До вайпа: {time_left}\n"
                  f"📢 Канал: <#{server.get('channel_id', 'Не установлен')}>",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

# -------- /сервер_канал --------
@bot.tree.command(name="сервер_канал", description="Меняет канал для оповещений о конкретном сервере")
@app_commands.default_permissions(administrator=True)
async def server_channel_slash(interaction: discord.Interaction, название: str):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    
    for server in monitored_servers:
        if server["name"].lower() == название.lower():
            server["channel_id"] = interaction.channel.id
            save_servers()
            await interaction.response.send_message(f"✅ Канал для сервера **{название}** обновлён: {interaction.channel.mention}")
            return
    
    await interaction.response.send_message(f"❌ Сервер **{название}** не найден в списке!", ephemeral=True)

# -------- /сервера --------
@bot.tree.command(name="сервера", description="Показывает все отслеживаемые сервера и время до вайпа")
async def servers_slash(interaction: discord.Interaction):
    if not monitored_servers:
        await interaction.response.send_message("📋 Нет отслеживаемых серверов.")
        return
    
    embed = discord.Embed(
        title="🎮 БЛИЖАЙШИЕ ВАЙПЫ",
        description="Информация о вайпах на отслеживаемых серверах:",
        color=0x00aaff,
        timestamp=datetime.now()
    )
    
    now = datetime.now()
    
    for server in monitored_servers:
        next_wipe = get_next_wipe(server)
        if next_wipe:
            time_left = next_wipe - now
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            
            if time_left.total_seconds() < 0:
                status = "🟢 ВАЙП ИДЁТ!"
            elif days == 0 and hours == 0:
                status = f"🟡 МЕНЕЕ ЧАСА!"
            elif days == 0:
                status = f"⏳ {hours}ч {minutes}мин"
            else:
                status = f"⏳ {days}д {hours}ч"
        else:
            status = "❌ Ошибка"
        
        embed.add_field(
            name=f"🎮 {server['name']}",
            value=f"📅 Вайп: **{server.get('wipe_day', 'Не указан')}**\n"
                  f"🕐 Время: **{server.get('wipe_time', '20:00')}**\n"
                  f"⏳ Осталось: **{status}**",
            inline=True
        )
    
    embed.set_footer(text="Бот оповестит за час до вайпа!")
    await interaction.response.send_message(embed=embed)

# -------- /заявки_канал --------
@bot.tree.command(name="заявки_канал", description="Устанавливает текущий канал для заявок")
@app_commands.default_permissions(administrator=True)
async def applications_channel_slash(interaction: discord.Interaction):
    global APPLICATIONS_CHANNEL_ID
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    
    APPLICATIONS_CHANNEL_ID = interaction.channel.id
    embed = discord.Embed(
        title="📋 ПОДАЧА ЗАЯВКИ В КЛАН",
        description="**Привет!** Чтобы подать заявку в наш клан, нажми на кнопку ниже и заполни анкету.\n\n"
                   "📝 **Заполни все поля внимательно!**\n"
                   "⏱️ Заявка будет рассмотрена в течение 24 часов\n"
                   "⚠️ Неправдивая информация может стать причиной отказа",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.add_field(name="📋 Что нужно указать:", 
                   value="• 👤 Ваше имя\n"
                         "• 📅 Ваш возраст (14+)\n"
                         "• 🔗 Ссылка на Steam профиль\n"
                         "• 🎯 Желаемая роль\n"
                         "• 📢 Откуда вы о нас узнали\n"
                         "• 🏷️ Готовы поставить приписку в стиме",
                   inline=False)
    embed.set_footer(text="Нажми кнопку ниже, чтобы подать заявку")
    view = ApplicationButton()
    await interaction.response.send_message(embed=embed, view=view)
    await update_applications_stats()

# -------- /заявки_список --------
@bot.tree.command(name="заявки_список", description="Показывает список всех заявок")
@app_commands.default_permissions(administrator=True)
async def applications_list_slash(interaction: discord.Interaction):
    if not is_admin_or_moderator(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    
    if not applications_data.get("applications"):
        await interaction.response.send_message("📋 Нет ни одной заявки!")
        return
    
    embed = discord.Embed(
        title="📋 СПИСОК ЗАЯВОК",
        description=f"Всего: **{len(applications_data['applications'])}** заявок",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    
    for app in applications_data["applications"][-10:]:
        status_emoji = {"pending": "⏳", "accepted": "✅", "rejected": "❌", "closed": "🗑️"}.get(app["status"], "❓")
        embed.add_field(
            name=f"#{app['id']} {app['username']}",
            value=f"Роль: {app['role']}\nСтатус: {status_emoji} {app['status'].capitalize()}\nСоздана: {app['created_at']}",
            inline=True
        )
    
    await interaction.response.send_message(embed=embed)

# -------- /заявка_удалить --------
@bot.tree.command(name="заявка_удалить", description="Удаляет заявку по номеру")
@app_commands.default_permissions(administrator=True)
async def application_delete_slash(interaction: discord.Interaction, номер: int):
    if not is_admin_or_moderator(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    
    for i, app in enumerate(applications_data.get("applications", [])):
        if app["id"] == номер:
            applications_data["applications"].pop(i)
            save_applications()
            await update_applications_stats()
            await interaction.response.send_message(f"✅ Заявка #{номер} удалена!")
            return
    
    await interaction.response.send_message(f"❌ Заявка #{номер} не найдена!", ephemeral=True)

# -------- /проверить_роли --------
@bot.tree.command(name="проверить_роли", description="Проверяет наличие ролей для авто-выдачи")
@app_commands.default_permissions(administrator=True)
async def check_roles_slash(interaction: discord.Interaction):
    guild = interaction.guild
    
    embed = discord.Embed(
        title="🔍 ПРОВЕРКА РОЛЕЙ",
        description="Проверка наличия ролей для авто-выдачи",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    
    newbie_role = discord.utils.get(guild.roles, name="ɴᴇᴡʙɪᴇ")
    if newbie_role:
        embed.add_field(
            name="✅ ɴᴇᴡʙɪᴇ",
            value=f"Роль найдена! ID: {newbie_role.id}\nУчастников: {len(newbie_role.members)}",
            inline=False
        )
    else:
        try:
            newbie_role = await guild.create_role(name="ɴᴇᴡʙɪᴇ", color=discord.Color.green())
            embed.add_field(
                name="✅ ɴᴇᴡʙɪᴇ",
                value=f"Роль создана! ID: {newbie_role.id}",
                inline=False
            )
        except Exception as e:
            embed.add_field(
                name="❌ ɴᴇᴡʙɪᴇ",
                value=f"Ошибка создания: {e}",
                inline=False
            )
    
    bot_role = discord.utils.get(guild.roles, name="ʙᴏᴛ")
    if bot_role:
        embed.add_field(
            name="✅ ʙᴏᴛ",
            value=f"Роль найдена! ID: {bot_role.id}\nУчастников: {len(bot_role.members)}",
            inline=False
        )
    else:
        try:
            bot_role = await guild.create_role(name="ʙᴏᴛ", color=discord.Color.blue())
            embed.add_field(
                name="✅ ʙᴏᴛ",
                value=f"Роль создана! ID: {bot_role.id}",
                inline=False
            )
        except Exception as e:
            embed.add_field(
                name="❌ ʙᴏᴛ",
                value=f"Ошибка создания: {e}",
                inline=False
            )
    
    total_members = len(guild.members)
    bots = len([m for m in guild.members if m.bot])
    humans = total_members - bots
    
    embed.add_field(
        name="📊 СТАТИСТИКА СЕРВЕРА",
        value=f"👥 Всего участников: **{total_members}**\n"
              f"🤖 Ботов: **{bots}**\n"
              f"👤 Игроков: **{humans}**",
        inline=False
    )
    
    embed.set_footer(text="Роли будут выдаваться автоматически новым участникам")
    await interaction.response.send_message(embed=embed)

# -------- /выдать_роль_новичка --------
@bot.tree.command(name="выдать_роль_новичка", description="Выдаёт роль ɴᴇᴡʙɪᴇ вручную")
@app_commands.default_permissions(administrator=True)
async def give_newbie_role_slash(interaction: discord.Interaction, участник: discord.Member):
    guild = interaction.guild
    newbie_role = discord.utils.get(guild.roles, name="ɴᴇᴡʙɪᴇ")
    
    if not newbie_role:
        try:
            newbie_role = await guild.create_role(name="ɴᴇᴡʙɪᴇ", color=discord.Color.green())
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка создания роли: {e}", ephemeral=True)
            return
    
    if newbie_role in участник.roles:
        await interaction.response.send_message(f"⚠️ У {участник.mention} уже есть роль {newbie_role.mention}!", ephemeral=True)
        return
    
    try:
        await участник.add_roles(newbie_role)
        await interaction.response.send_message(f"✅ Роль {newbie_role.mention} выдана {участник.mention}!")
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка выдачи роли: {e}", ephemeral=True)

# -------- /убрать_роль_новичка --------
@bot.tree.command(name="убрать_роль_новичка", description="Убирает роль ɴᴇᴡʙɪᴇ у участника")
@app_commands.default_permissions(administrator=True)
async def remove_newbie_role_slash(interaction: discord.Interaction, участник: discord.Member):
    guild = interaction.guild
    newbie_role = discord.utils.get(guild.roles, name="ɴᴇᴡʙɪᴇ")
    
    if not newbie_role:
        await interaction.response.send_message("❌ Роль ɴᴇᴡʙɪᴇ не найдена на сервере!", ephemeral=True)
        return
    
    if newbie_role not in участник.roles:
        await interaction.response.send_message(f"⚠️ У {участник.mention} нет роли {newbie_role.mention}!", ephemeral=True)
        return
    
    try:
        await участник.remove_roles(newbie_role)
        await interaction.response.send_message(f"✅ Роль {newbie_role.mention} убрана у {участник.mention}!")
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка удаления роли: {e}", ephemeral=True)

# -------- /состав и /состав_онлайн --------
class RoleSelectView(discord.ui.View):
    def __init__(self, guild, author_id, online_only=False):
        super().__init__(timeout=60)
        self.guild = guild
        self.author_id = author_id
        self.online_only = online_only
        self.message = None
        
        self.found_roles = []
        for role in guild.roles:
            if role.name in TARGET_ROLES:
                self.found_roles.append(role)
        
        if not self.found_roles:
            return
        
        for role in self.found_roles:
            if online_only:
                members = [m for m in guild.members if role in m.roles and m.status != discord.Status.offline]
            else:
                members = [m for m in guild.members if role in m.roles]
            count = len(members)
            btn = discord.ui.Button(
                label=f"{role.name} ({count})",
                style=discord.ButtonStyle.primary,
                custom_id=f"show_role_{role.id}_{'online' if online_only else 'all'}"
            )
            self.add_item(btn)
        
        all_members = []
        for role in self.found_roles:
            if online_only:
                all_members.extend([m for m in guild.members if role in m.roles and m.status != discord.Status.offline])
            else:
                all_members.extend([m for m in guild.members if role in m.roles])
        all_members = list(set(all_members))
        
        btn_all = discord.ui.Button(
            label=f"📋 Все роли ({len(all_members)})",
            style=discord.ButtonStyle.success,
            custom_id=f"show_all_roles_{'online' if online_only else 'all'}"
        )
        self.add_item(btn_all)
        
        btn_cancel = discord.ui.Button(
            label="❌ Отмена",
            style=discord.ButtonStyle.secondary,
            custom_id="cancel_roles"
        )
        self.add_item(btn_cancel)
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Это меню вызвано другим пользователем!",
                ephemeral=True
            )
            return False
        return True
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)
            await asyncio.sleep(5)
            try:
                await self.message.delete()
            except:
                pass

@bot.tree.command(name="состав", description="Отмечает участников с выбранной ролью")
async def team_slash(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Эта команда работает только на сервере!", ephemeral=True)
        return
    
    view = RoleSelectView(interaction.guild, interaction.user.id, online_only=False)
    if not view.found_roles:
        await interaction.response.send_message(
            "❌ Ни одна из указанных ролей не найдена на сервере!\n"
            "Нужны роли: ʙᴜɪʟᴅᴇʀ, ᴄᴏʟʟᴇʀ, ᴄᴏᴍʙᴀᴛ, ᴇʟᴇᴄᴛʀɪᴄ, ꜰᴀʀᴍ, ꜰᴇʀᴍᴇʀ",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="👥 ВЫБОР РОЛИ",
        description="Нажми на кнопку с нужной ролью, чтобы отметить участников:",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Кнопки активны 60 секунд")
    
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

@bot.tree.command(name="состав_онлайн", description="Отмечает только онлайн участников с выбранной ролью")
async def team_online_slash(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Эта команда работает только на сервере!", ephemeral=True)
        return
    
    view = RoleSelectView(interaction.guild, interaction.user.id, online_only=True)
    if not view.found_roles:
        await interaction.response.send_message(
            "❌ Ни одна из указанных ролей не найдена на сервере!\n"
            "Нужны роли: ʙᴜɪʟᴅᴇʀ, ᴄᴏʟʟᴇʀ, ᴄᴏᴍʙᴀᴛ, ᴇʟᴇᴄᴛʀɪᴄ, ꜰᴀʀᴍ, ꜰᴇʀᴍᴇʀ",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="🟢 ВЫБОР РОЛИ (ОНЛАЙН)",
        description="Нажми на кнопку с нужной ролью, чтобы отметить онлайн участников:",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Кнопки активны 60 секунд")
    
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

# -------- /событие --------
class EventCreationView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.message = None
        self.event_data = {}
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Это меню вызвано другим пользователем!",
                ephemeral=True
            )
            return False
        if not has_access(interaction.user, interaction.guild):
            await interaction.response.send_message(
                "❌ У вас нет прав для создания событий!",
                ephemeral=True
            )
            return False
        return True
    
    async def on_timeout(self):
        if self.message:
            embed = discord.Embed(
                title="⏰ Создание события отменено",
                description="Время сессии истекло.",
                color=0xff0000
            )
            await self.message.edit(embed=embed, view=None)
            await asyncio.sleep(5)
            try:
                await self.message.delete()
            except:
                pass
    
    @discord.ui.button(label="📝 Название", style=discord.ButtonStyle.primary)
    async def set_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📝 **Введите название события:**\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            self.event_data["name"] = msg.content.strip()
            await msg.delete()
            await interaction.edit_original_response(content=f"✅ Название: **{self.event_data['name']}**")
            await self.update_menu(interaction)
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
    
    @discord.ui.button(label="📅 Дата", style=discord.ButtonStyle.primary)
    async def set_date(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📅 **Введите дату события** (в формате ДД.ММ.ГГГГ, например `15.08.2026`):\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            date_str = msg.content.strip()
            datetime.strptime(date_str, "%d.%m.%Y")
            self.event_data["date"] = date_str
            await msg.delete()
            await interaction.edit_original_response(content=f"✅ Дата: **{self.event_data['date']}**")
            await self.update_menu(interaction)
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
        except:
            await interaction.edit_original_response(content="❌ Неверный формат! Используй ДД.ММ.ГГГГ")
    
    @discord.ui.button(label="🕐 Время", style=discord.ButtonStyle.primary)
    async def set_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🕐 **Введите время события** (в формате ЧЧ:ММ, например `20:00`):\n"
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
                self.event_data["time"] = time_str
                await msg.delete()
                await interaction.edit_original_response(content=f"✅ Время: **{self.event_data['time']}**")
                await self.update_menu(interaction)
            else:
                await interaction.edit_original_response(content="❌ Неверный формат!")
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
        except:
            await interaction.edit_original_response(content="❌ Неверный формат! Используй ЧЧ:ММ")
    
    @discord.ui.button(label="🔊 Голосовой", style=discord.ButtonStyle.primary)
    async def set_voice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🔊 **Введите название голосового канала** (например, `Сбор`):\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            self.event_data["voice_channel"] = msg.content.strip()
            await msg.delete()
            await interaction.edit_original_response(content=f"✅ Голосовой канал: **{self.event_data['voice_channel']}**")
            await self.update_menu(interaction)
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
    
    @discord.ui.button(label="📢 Канал", style=discord.ButtonStyle.primary)
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📢 **Укажите канал для оповещений:**\n"
            "Напиши `#канал` или ID канала.\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            if msg.channel_mentions:
                channel_id = msg.channel_mentions[0].id
            else:
                channel_id = int(msg.content.strip())
            self.event_data["channel_id"] = channel_id
            await msg.delete()
            await interaction.edit_original_response(content=f"✅ Канал установлен: <#{channel_id}>")
            await self.update_menu(interaction)
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
        except:
            await interaction.edit_original_response(content="❌ Неверный ID канала!")
    
    @discord.ui.button(label="🗺️ Карта", style=discord.ButtonStyle.primary)
    async def set_map(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🗺️ **Введите ссылку на карту** (если есть):\n"
            "Или напиши `Нет` чтобы пропустить.\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            url = msg.content.strip()
            if url.lower() == "нет":
                self.event_data["map_url"] = ""
            elif url.startswith("http"):
                self.event_data["map_url"] = url
            else:
                await interaction.edit_original_response(content="❌ Неверный формат!")
                return
            await msg.delete()
            await interaction.edit_original_response(content=f"✅ Ссылка на карту: {url if url.lower() != 'нет' else 'Пропущена'}")
            await self.update_menu(interaction)
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
    
    @discord.ui.button(label="📝 Описание", style=discord.ButtonStyle.primary)
    async def set_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📝 **Введите описание события** (необязательно):\n"
            "Или напиши `Нет` чтобы пропустить.\n"
            "Напиши ответ в этот чат в течение 60 секунд.",
            ephemeral=True
        )
        
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            text = msg.content.strip()
            if text.lower() == "нет":
                self.event_data["description"] = ""
            else:
                self.event_data["description"] = text
            await msg.delete()
            await interaction.edit_original_response(content=f"✅ Описание: {text if text.lower() != 'нет' else 'Пропущено'}")
            await self.update_menu(interaction)
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Время вышло!")
    
    @discord.ui.button(label="✅ Создать", style=discord.ButtonStyle.success)
    async def create_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        required = ["name", "date", "time", "voice_channel", "channel_id"]
        missing = [f for f in required if f not in self.event_data]
        
        if missing:
            await interaction.response.send_message(
                f"❌ Не все поля заполнены! Отсутствуют: {', '.join(missing)}",
                ephemeral=True
            )
            return
        
        event = {
            "id": len(events) + 1,
            "name": self.event_data["name"],
            "date": self.event_data["date"],
            "time": self.event_data["time"],
            "voice_channel": self.event_data["voice_channel"],
            "channel_id": self.event_data["channel_id"],
            "map_url": self.event_data.get("map_url", ""),
            "description": self.event_data.get("description", "")
        }
        
        try:
            day, month, year = event["date"].split(".")
            event["datetime"] = f"{year}-{month}-{day} {event['time']}"
        except:
            await interaction.response.send_message("❌ Ошибка в формате даты!", ephemeral=True)
            return
        
        events.append(event)
        save_events()
        schedule_events()
        
        embed = discord.Embed(
            title="✅ СОБЫТИЕ СОЗДАНО!",
            description=f"**{event['name']}**",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="📅 Дата", value=event["date"], inline=True)
        embed.add_field(name="🕐 Время", value=event["time"], inline=True)
        embed.add_field(name="🔊 Голосовой канал", value=f"**{event['voice_channel']}**", inline=True)
        embed.add_field(name="📢 Канал", value=f"<#{event['channel_id']}>", inline=False)
        if event.get("map_url"):
            embed.add_field(name="🗺️ Карта", value=f"[Ссылка]({event['map_url']})", inline=False)
        if event.get("description"):
            embed.add_field(name="📝 Описание", value=event["description"], inline=False)
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def update_menu(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📝 СОЗДАНИЕ СОБЫТИЯ",
            description="Заполни все поля с помощью кнопок ниже:",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        fields = [
            ("📝 Название", self.event_data.get("name", "Не указано")),
            ("📅 Дата", self.event_data.get("date", "Не указана")),
            ("🕐 Время", self.event_data.get("time", "Не указано")),
            ("🔊 Голосовой канал", self.event_data.get("voice_channel", "Не указан")),
            ("📢 Канал", f"<#{self.event_data['channel_id']}>" if self.event_data.get("channel_id") else "Не указан"),
            ("🗺️ Карта", "Установлена" if self.event_data.get("map_url") else "Не указана"),
            ("📝 Описание", self.event_data.get("description", "Не указано")[:50] + "..." if len(self.event_data.get("description", "")) > 50 else self.event_data.get("description", "Не указано"))
        ]
        
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        
        embed.set_footer(text="Нажми кнопку для заполнения поля | Нажми 'Создать' для завершения")
        
        await interaction.edit_original_response(embed=embed, view=self)

@bot.tree.command(name="событие", description="Создаёт новое событие")
@app_commands.default_permissions(administrator=True)
async def event_create_slash(interaction: discord.Interaction):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для создания событий!", ephemeral=True)
        return
    
    view = EventCreationView(author_id=interaction.user.id)
    embed = discord.Embed(
        title="📝 СОЗДАНИЕ СОБЫТИЯ",
        description="Заполни все поля с помощью кнопок ниже, затем нажми 'Создать':",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Меню активно 5 минут")
    
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

# -------- /события --------
@bot.tree.command(name="события", description="Показывает список всех событий")
async def events_slash(interaction: discord.Interaction):
    if not events:
        await interaction.response.send_message("📋 Нет запланированных событий.")
        return
    
    embed = discord.Embed(
        title="📋 ЗАПЛАНИРОВАННЫЕ СОБЫТИЯ",
        description=f"Всего: **{len(events)}** событий",
        color=0x00aaff,
        timestamp=datetime.now()
    )
    
    now = datetime.now()
    
    for event in events:
        try:
            event_time = datetime.strptime(event["datetime"], "%Y-%m-%d %H:%M")
            time_left = event_time - now
            
            if time_left.total_seconds() < 0:
                status = "✅ ПРОШЛО"
            elif time_left.total_seconds() < 3600:
                status = "🟡 СКОРО! МЕНЕЕ ЧАСА"
            else:
                days = time_left.days
                hours = time_left.seconds // 3600
                minutes = (time_left.seconds % 3600) // 60
                status = f"⏳ {days}д {hours}ч {minutes}мин"
            
            embed.add_field(
                name=f"📌 {event['name']}",
                value=f"📅 {event['date']} в {event['time']}\n"
                      f"🔊 {event.get('voice_channel', 'Не указан')}\n"
                      f"⏳ {status}",
                inline=True
            )
        except:
            continue
    
    await interaction.response.send_message(embed=embed)

# -------- /событие_удалить --------
@bot.tree.command(name="событие_удалить", description="Удаляет событие по номеру")
@app_commands.default_permissions(administrator=True)
async def event_delete_slash(interaction: discord.Interaction, номер: int):
    if not has_access(interaction.user, interaction.guild):
        await interaction.response.send_message("❌ У вас нет прав для этой команды!", ephemeral=True)
        return
    
    if not events:
        await interaction.response.send_message("❌ Нет событий для удаления!", ephemeral=True)
        return
    
    if 1 <= номер <= len(events):
        event_name = events[номер-1]["name"]
        events.pop(номер-1)
        save_events()
        schedule_events()
        await interaction.response.send_message(f"✅ Событие **{event_name}** удалено!")
    else:
        await interaction.response.send_message(f"❌ Событие с номером {номер} не найдено!", ephemeral=True)

# ----------------------------------------------------
# ОБРАБОТЧИК КНОПОК ДЛЯ /СОСТАВ
# ----------------------------------------------------

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data:
        return
    custom_id = interaction.data.get("custom_id")
    if not custom_id:
        return
    
    if custom_id.startswith("show_role_") or custom_id.startswith("show_all_roles_") or custom_id == "cancel_roles":
        if custom_id.startswith("show_role_"):
            parts = custom_id.split("_")
            role_id = int(parts[2])
            mode = parts[3] if len(parts) > 3 else "all"
            online_only = mode == "online"
            role = interaction.guild.get_role(role_id)
            if not role:
                await interaction.response.send_message("❌ Роль не найдена!", ephemeral=True)
                return
            if online_only:
                members = [m for m in interaction.guild.members if role in m.roles and m.status != discord.Status.offline]
            else:
                members = [m for m in interaction.guild.members if role in m.roles]
            if not members:
                await interaction.response.send_message(f"❌ Нет {'онлайн ' if online_only else ''}участников с ролью {role.mention}!", ephemeral=True)
                return
            embed = discord.Embed(
                title=f"{'🟢 ' if online_only else ''}{role.name}",
                description=f"Всего **{len(members)}** {'онлайн ' if online_only else ''}участников:",
                color=role.color if role.color.value != 0 else 0x00ff00,
                timestamp=datetime.now()
            )
            members_list = ""
            for member in members:
                status_emoji = ""
                if member.status == discord.Status.online:
                    status_emoji = "🟢"
                elif member.status == discord.Status.idle:
                    status_emoji = "🟡"
                elif member.status == discord.Status.dnd:
                    status_emoji = "🔴"
                elif member.status == discord.Status.offline:
                    status_emoji = "⚫"
                else:
                    status_emoji = "⚪"
                members_list += f"{status_emoji} {member.mention} - `{member.display_name}`\n"
            if len(members_list) > 1024:
                members_list = members_list[:1020] + "..."
            embed.add_field(name="📋 Участники", value=members_list, inline=False)
            if not online_only:
                online = sum(1 for m in members if m.status != discord.Status.offline)
                offline = len(members) - online
                embed.add_field(
                    name="📊 Статистика",
                    value=f"🟢 Онлайн: **{online}**\n⚫ Оффлайн: **{offline}**",
                    inline=True
                )
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            mentions = " ".join([member.mention for member in members])
            await interaction.response.send_message(f"{mentions}\n\n", embed=embed)
        elif custom_id.startswith("show_all_roles_"):
            mode = custom_id.replace("show_all_roles_", "")
            online_only = mode == "online"
            all_members = []
            for role_name in TARGET_ROLES:
                role = discord.utils.get(interaction.guild.roles, name=role_name)
                if role:
                    if online_only:
                        all_members.extend([m for m in interaction.guild.members if role in m.roles and m.status != discord.Status.offline])
                    else:
                        all_members.extend([m for m in interaction.guild.members if role in m.roles])
            all_members = list(set(all_members))
            if not all_members:
                await interaction.response.send_message(f"❌ Нет {'онлайн ' if online_only else ''}участников с указанными ролями!", ephemeral=True)
                return
            embed = discord.Embed(
                title=f"{'🟢 ' if online_only else ''}ВСЕ РОЛИ",
                description=f"Всего **{len(all_members)}** {'онлайн ' if online_only else ''}участников:",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            members_list = ""
            for member in all_members:
                status_emoji = ""
                if member.status == discord.Status.online:
                    status_emoji = "🟢"
                elif member.status == discord.Status.idle:
                    status_emoji = "🟡"
                elif member.status == discord.Status.dnd:
                    status_emoji = "🔴"
                elif member.status == discord.Status.offline:
                    status_emoji = "⚫"
                else:
                    status_emoji = "⚪"
                members_list += f"{status_emoji} {member.mention} - `{member.display_name}`\n"
            if len(members_list) > 1024:
                members_list = members_list[:1020] + "..."
            embed.add_field(name="📋 Участники", value=members_list, inline=False)
            if not online_only:
                online = sum(1 for m in all_members if m.status != discord.Status.offline)
                offline = len(all_members) - online
                embed.add_field(
                    name="📊 Статистика",
                    value=f"🟢 Онлайн: **{online}**\n⚫ Оффлайн: **{offline}**",
                    inline=True
                )
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            mentions = " ".join([member.mention for member in all_members])
            await interaction.response.send_message(f"{mentions}\n\n", embed=embed)
        elif custom_id == "cancel_roles":
            await interaction.response.send_message("❌ Отменено.", ephemeral=True)
        return

# ----------------------------------------------------
# ЗАПУСК БОТА
# ----------------------------------------------------

# Токен берётся из переменных окружения (Environment Variables)
# На хостинге (BotHost, Replit, Heroku и т.д.) ты задаёшь переменную BOT_TOKEN
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: Переменная окружения BOT_TOKEN не задана!")
    print("📝 Добавь переменную BOT_TOKEN на хостинге в разделе Environment Variables")
    exit(1)

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Ошибка: Неверный токен. Проверь переменную BOT_TOKEN")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
