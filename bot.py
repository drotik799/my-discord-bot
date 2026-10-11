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

# Планировщик
scheduler = AsyncIOScheduler()

# Файлы для хранения данных
DATA_FILE = "raid_data.json"
SERVERS_FILE = "rust_servers.json"

# Данные о вайпе
raid_data = {
    "time": "20:00",
    "weekday": "Суббота",
    "server": "Rustoria #1",
    "channel_id": None,
    "reminder_hours": 1,
    "map_url": "https://rustmaps.com/"
}

# Список серверов для мониторинга
monitored_servers = []

# Дни недели для меню
WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье", "Ежедневно"]

# ID канала для оповещений
ANNOUNCEMENT_CHANNEL_ID = None

# ----------------------------------------------------
# ЗАГРУЗКА/СОХРАНЕНИЕ ДАННЫХ
# ----------------------------------------------------

def load_data():
    global raid_data, monitored_servers, ANNOUNCEMENT_CHANNEL_ID
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                raid_data.update(saved_data)
                ANNOUNCEMENT_CHANNEL_ID = raid_data.get("channel_id")
            print("✅ Данные вайпа загружены")
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
    
    if os.path.exists(SERVERS_FILE):
        try:
            with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
                monitored_servers = json.load(f)
            print(f"✅ Загружено {len(monitored_servers)} серверов")
        except Exception as e:
            print(f"❌ Ошибка загрузки серверов: {e}")

def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(raid_data, f, ensure_ascii=False, indent=4)
        print("✅ Данные вайпа сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")

def save_servers():
    try:
        with open(SERVERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(monitored_servers, f, ensure_ascii=False, indent=4)
        print("✅ Список серверов сохранён")
    except Exception as e:
        print(f"❌ Ошибка сохранения серверов: {e}")

load_data()

# ----------------------------------------------------
# ФУНКЦИИ ДЛЯ ПРОВЕРКИ ВАЙПА
# ----------------------------------------------------

def get_next_wipe_time():
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

def get_next_wipe_for_server(server):
    try:
        now = datetime.now()
        weekday = server.get("wipe_day", "Суббота").lower()
        time_str = server.get("wipe_time", "20:00")
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
    global ANNOUNCEMENT_CHANNEL_ID
    ANNOUNCEMENT_CHANNEL_ID = raid_data.get("channel_id")
    
    print(f'✅ Бот {bot.user} успешно запущен!')
    print(f'👉 Он на {len(bot.guilds)} серверах.')
    print(f'📢 Канал оповещений: {ANNOUNCEMENT_CHANNEL_ID}')
    
    if not scheduler.running:
        scheduler.start()
    
    schedule_raid()
    
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
# АВТО-РОЛИ
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
            try:
                bot_role = await guild.create_role(name="ʙᴏᴛ", color=discord.Color.blue())
                await member.add_roles(bot_role)
                print(f"✅ Создана и выдана роль ʙᴏᴛ для {member.name}")
            except Exception as e:
                print(f"❌ Ошибка создания роли ʙᴏᴛ: {e}")
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
# РАСПИСАНИЕ ВАЙПА
# ----------------------------------------------------

def schedule_raid():
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
        
        reminder_hours = raid_data.get("reminder_hours", 1)
        reminder_hour = hour - reminder_hours
        if reminder_hour < 0:
            reminder_hour = 24 + reminder_hour
        
        if weekday == "ежедневно":
            scheduler.add_job(
                func=send_raid_reminder,
                trigger=CronTrigger(hour=reminder_hour, minute=minute),
                id="raid_reminder",
                replace_existing=True
            )
        elif weekday in weekdays_map:
            scheduler.add_job(
                func=send_raid_reminder,
                trigger=CronTrigger(day_of_week=weekdays_map[weekday], hour=reminder_hour, minute=minute),
                id="raid_reminder",
                replace_existing=True
            )
        
        print(f"⏰ Вайп запланирован на {raid_data['weekday']} в {raid_data['time']}")
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
    
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}**", inline=True)
    embed.add_field(name="📅 День", value=f"**{raid_data['weekday']}**", inline=True)
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка на карту]({raid_data['map_url']})", inline=False)
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
    
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}**", inline=True)
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка на карту]({raid_data['map_url']})", inline=False)
    embed.set_footer(text="Всем удачи на новом вайпе! 🔥")
    
    await channel.send("@everyone", embed=embed)
    print(f"✅ Сообщение о вайпе отправлено в {channel.name}")

# ----------------------------------------------------
# МОДАЛЬНОЕ ОКНО: НАСТРОЙКА ВАЙПА (С КАНАЛОМ)
# ----------------------------------------------------

class VipeSetModal(discord.ui.Modal, title='⚙️ НАСТРОЙКА ВАЙПА'):
    """Модальное окно для настройки вайпа"""
    
    time_input = discord.ui.TextInput(
        label='🕐 Время вайпа',
        placeholder='Например: 20:00',
        default='20:00',
        required=True,
        max_length=5
    )
    
    weekday_input = discord.ui.TextInput(
        label='📅 День недели',
        placeholder='Например: Суббота / Ежедневно',
        default='Суббота',
        required=True,
        max_length=20
    )
    
    server_input = discord.ui.TextInput(
        label='🎮 Название сервера',
        placeholder='Например: Rustoria #1',
        default='Rustoria #1',
        required=True,
        max_length=100
    )
    
    channel_input = discord.ui.TextInput(
        label='📢 Канал для оповещений',
        placeholder='Введи #канал или ID канала',
        required=True,
        max_length=100
    )
    
    reminder_input = discord.ui.TextInput(
        label='⏰ Напоминание (за сколько часов)',
        placeholder='Например: 1',
        default='1',
        required=True,
        max_length=3
    )
    
    map_input = discord.ui.TextInput(
        label='🗺️ Ссылка на карту',
        placeholder='https://rustmaps.com/...',
        default='https://rustmaps.com/',
        required=False,
        max_length=200
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        global raid_data, ANNOUNCEMENT_CHANNEL_ID
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Проверяем время
            time_str = self.time_input.value.strip()
            try:
                hour, minute = map(int, time_str.split(":"))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError
            except:
                await interaction.followup.send(
                    "❌ Неверный формат времени! Используй ЧЧ:ММ (например, 20:00)",
                    ephemeral=True
                )
                return
            
            # Проверяем день недели
            weekday_str = self.weekday_input.value.strip().capitalize()
            valid_weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье", "Ежедневно"]
            if weekday_str not in valid_weekdays:
                await interaction.followup.send(
                    f"❌ Неверный день недели! Доступные: {', '.join(valid_weekdays)}",
                    ephemeral=True
                )
                return
            
            # Проверяем напоминание
            try:
                reminder_hours = int(self.reminder_input.value.strip())
                if not (1 <= reminder_hours <= 24):
                    raise ValueError
            except:
                await interaction.followup.send(
                    "❌ Напоминание должно быть числом от 1 до 24 часов!",
                    ephemeral=True
                )
                return
            
            # Проверяем ссылку
            map_url = self.map_input.value.strip() if self.map_input.value else "https://rustmaps.com/"
            if map_url and not map_url.startswith("http"):
                await interaction.followup.send(
                    "❌ Ссылка должна начинаться с http:// или https://",
                    ephemeral=True
                )
                return
            
            # Обрабатываем канал
            channel_value = self.channel_input.value.strip()
            channel_id = None
            channel_name = None
            
            # Пытаемся найти канал по упоминанию
            if channel_value.startswith("<#") and channel_value.endswith(">"):
                try:
                    channel_id = int(channel_value[2:-1])
                    channel = interaction.guild.get_channel(channel_id)
                    if channel:
                        channel_name = channel.mention
                    else:
                        channel_id = None
                except:
                    channel_id = None
            
            # Если не упоминание, пробуем как ID
            if not channel_id:
                # Ищем канал по имени
                channel_name_clean = channel_value.replace("#", "").strip()
                for ch in interaction.guild.text_channels:
                    if ch.name.lower() == channel_name_clean.lower():
                        channel_id = ch.id
                        channel_name = ch.mention
                        break
            
            if not channel_id:
                await interaction.followup.send(
                    "❌ Канал не найден! Упомяни канал через `#название` или введи его ID.\n"
                    "Пример: `#вайпы` или `123456789012345678`",
                    ephemeral=True
                )
                return
            
            # Сохраняем настройки
            raid_data["time"] = time_str
            raid_data["weekday"] = weekday_str
            raid_data["server"] = self.server_input.value.strip()
            raid_data["channel_id"] = channel_id
            raid_data["reminder_hours"] = reminder_hours
            raid_data["map_url"] = map_url
            
            ANNOUNCEMENT_CHANNEL_ID = channel_id
            
            save_data()
            schedule_raid()
            
            embed = discord.Embed(
                title="✅ НАСТРОЙКИ ВАЙПА СОХРАНЕНЫ",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(name="🕐 Время", value=f"**{time_str}**", inline=True)
            embed.add_field(name="📅 День", value=f"**{weekday_str}**", inline=True)
            embed.add_field(name="🎮 Сервер", value=f"**{self.server_input.value.strip()}**", inline=True)
            embed.add_field(name="📢 Канал", value=channel_name, inline=True)
            embed.add_field(name="⏰ Напоминание", value=f"За **{reminder_hours}** час(а)", inline=True)
            embed.add_field(name="🗺️ Карта", value=f"[Ссылка]({map_url})", inline=False)
            embed.set_footer(text="Используй /vipeset чтобы изменить настройки")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"✅ Настройки вайпа обновлены пользователем {interaction.user.name}")
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Ошибка: {str(e)}",
                ephemeral=True
            )

# ----------------------------------------------------
# МОДАЛЬНОЕ ОКНО: УДАЛЕНИЕ СЕРВЕРА
# ----------------------------------------------------

class ServerDeleteModal(discord.ui.Modal, title='🗑️ УДАЛЕНИЕ СЕРВЕРА'):
    server_name = discord.ui.TextInput(
        label='🎮 Название сервера',
        placeholder='Введите название сервера для удаления',
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        global monitored_servers
        
        await interaction.response.defer(ephemeral=True)
        
        server_name = self.server_name.value.strip()
        
        found = False
        for i, server in enumerate(monitored_servers):
            if server["name"].lower() == server_name.lower():
                monitored_servers.pop(i)
                save_servers()
                found = True
                break
        
        if found:
            embed = discord.Embed(
                title="✅ СЕРВЕР УДАЛЁН",
                description=f"Сервер **{server_name}** удалён из списка мониторинга.",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"✅ Сервер {server_name} удалён")
        else:
            embed = discord.Embed(
                title="❌ СЕРВЕР НЕ НАЙДЕН",
                description=f"Сервер **{server_name}** не найден в списке мониторинга.\n"
                           f"Используй `/vipelist` чтобы посмотреть все сервера.",
                color=0xff0000,
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

# ----------------------------------------------------
# МОДАЛЬНОЕ ОКНО: ДОБАВЛЕНИЕ СЕРВЕРА
# ----------------------------------------------------

class ServerAddModal(discord.ui.Modal, title='➕ ДОБАВЛЕНИЕ СЕРВЕРА'):
    server_name = discord.ui.TextInput(
        label='🎮 Название сервера',
        placeholder='Например: Rustoria #1',
        required=True,
        max_length=100
    )
    
    wipe_day = discord.ui.TextInput(
        label='📅 День вайпа',
        placeholder='Например: Суббота',
        default='Суббота',
        required=True,
        max_length=20
    )
    
    wipe_time = discord.ui.TextInput(
        label='🕐 Время вайпа',
        placeholder='Например: 20:00',
        default='20:00',
        required=True,
        max_length=5
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        global monitored_servers
        
        await interaction.response.defer(ephemeral=True)
        
        server_name = self.server_name.value.strip()
        wipe_day = self.wipe_day.value.strip().capitalize()
        wipe_time = self.wipe_time.value.strip()
        
        try:
            hour, minute = map(int, wipe_time.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except:
            await interaction.followup.send("❌ Неверный формат времени! Используй ЧЧ:ММ", ephemeral=True)
            return
        
        valid_weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье", "Ежедневно"]
        if wipe_day not in valid_weekdays:
            await interaction.followup.send(f"❌ Неверный день недели! Доступные: {', '.join(valid_weekdays)}", ephemeral=True)
            return
        
        for server in monitored_servers:
            if server["name"].lower() == server_name.lower():
                await interaction.followup.send(f"❌ Сервер **{server_name}** уже в списке!", ephemeral=True)
                return
        
        new_server = {
            "name": server_name,
            "wipe_day": wipe_day,
            "wipe_time": wipe_time,
            "channel_id": interaction.channel.id
        }
        monitored_servers.append(new_server)
        save_servers()
        
        embed = discord.Embed(
            title="✅ СЕРВЕР ДОБАВЛЕН",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="🎮 Сервер", value=f"**{server_name}**", inline=False)
        embed.add_field(name="📅 День вайпа", value=f"**{wipe_day}**", inline=True)
        embed.add_field(name="🕐 Время", value=f"**{wipe_time}**", inline=True)
        embed.set_footer(text="Используй /vipelist чтобы посмотреть все сервера")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"✅ Сервер {server_name} добавлен")

# ----------------------------------------------------
# КОМАНДА /vipeset (С ПОЛЕМ КАНАЛА)
# ----------------------------------------------------

@bot.tree.command(name="vipeset", description="Настройка вайпа (только для администраторов)")
@app_commands.default_permissions(administrator=True)
async def vipeset(interaction: discord.Interaction):
    """Открывает модальное окно настройки вайпа"""
    await interaction.response.send_modal(VipeSetModal())

# ----------------------------------------------------
# КОМАНДА /vipelist
# ----------------------------------------------------

@bot.tree.command(name="vipelist", description="Показывает список всех серверов с вайпами")
async def vipelist(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if not monitored_servers:
        embed = discord.Embed(
            title="📋 СПИСОК СЕРВЕРОВ",
            description="Список пуст.\nАдминистраторы могут добавить сервера командой `/vipeset_servers`.",
            color=0xffaa00,
            timestamp=datetime.now()
        )
        await interaction.followup.send(embed=embed)
        return
    
    embed = discord.Embed(
        title="📋 СПИСОК СЕРВЕРОВ С ВАЙПАМИ",
        description=f"Всего серверов: **{len(monitored_servers)}**",
        color=0x00aaff,
        timestamp=datetime.now()
    )
    
    now = datetime.now()
    
    for server in monitored_servers:
        next_wipe = get_next_wipe_for_server(server)
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
            value=f"📅 День: **{server.get('wipe_day', 'Не указан')}**\n"
                  f"🕐 Время: **{server.get('wipe_time', '20:00')}**\n"
                  f"⏳ До вайпа: **{status}**",
            inline=False
        )
    
    embed.set_footer(text="Используй /vipeset для настройки своего сервера")
    await interaction.followup.send(embed=embed)

# ----------------------------------------------------
# КОМАНДА /vipeset_servers (МЕНЮ УПРАВЛЕНИЯ СЕРВЕРАМИ)
# ----------------------------------------------------

class ServersManageView(discord.ui.View):
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
            try:
                await self.message.delete()
            except:
                pass
    
    @discord.ui.button(label="➕ Добавить сервер", style=discord.ButtonStyle.success, emoji="➕")
    async def add_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ServerAddModal())
    
    @discord.ui.button(label="🗑️ Удалить сервер", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.message.delete()
        except:
            pass
        await interaction.response.send_modal(ServerDeleteModal())
    
    @discord.ui.button(label="📋 Список серверов", style=discord.ButtonStyle.primary, emoji="📋")
    async def list_servers(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not monitored_servers:
            await interaction.response.send_message("📋 Список серверов пуст!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📋 СПИСОК СЕРВЕРОВ",
            description=f"Всего: **{len(monitored_servers)}**",
            color=0x00aaff,
            timestamp=datetime.now()
        )
        
        for i, server in enumerate(monitored_servers, 1):
            embed.add_field(
                name=f"{i}. 🎮 {server['name']}",
                value=f"📅 {server.get('wipe_day', 'Не указан')} | 🕐 {server.get('wipe_time', '20:00')}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.secondary, emoji="❌")
    async def close_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.message.delete()
        except:
            pass
        await interaction.response.send_message("✅ Меню закрыто", ephemeral=True)

@bot.tree.command(name="vipeset_servers", description="Управление списком серверов (только для администраторов)")
@app_commands.default_permissions(administrator=True)
async def vipeset_servers(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    view = ServersManageView(author_id=interaction.user.id)
    
    embed = discord.Embed(
        title="⚙️ УПРАВЛЕНИЕ СЕРВЕРАМИ",
        description="Выбери действие:\n\n"
                   "➕ **Добавить сервер** — добавить новый сервер\n"
                   "🗑️ **Удалить сервер** — удалить сервер из списка\n"
                   "📋 **Список серверов** — показать все сервера",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Меню видно только тебе")
    
    message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    view.message = message

# ----------------------------------------------------
# КОМАНДА /вайп (ПРОСМОТР РАСПИСАНИЯ)
# ----------------------------------------------------

@bot.tree.command(name="вайп", description="Показывает расписание вайпа")
async def raid_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    
    embed = discord.Embed(
        title="⚔️ РАСПИСАНИЕ ВАЙПА ⚔️",
        color=0xff5500,
        timestamp=datetime.now()
    )
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}**", inline=True)
    embed.add_field(name="📅 День", value=f"**{raid_data['weekday']}**", inline=True)
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка]({raid_data['map_url']})", inline=False)
    embed.add_field(name="⏰ Напоминание", value=f"За **{raid_data['reminder_hours']}** час(а)", inline=True)
    
    next_wipe = get_next_wipe_time()
    if next_wipe:
        time_left = next_wipe - datetime.now()
        days = time_left.days
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        embed.add_field(
            name="⏳ До вайпа осталось",
            value=f"**{days}д {hours}ч {minutes}мин**",
            inline=False
        )
    
    embed.set_footer(text="Используй /vipeset для настройки")
    await interaction.followup.send(embed=embed)

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
