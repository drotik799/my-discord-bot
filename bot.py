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

scheduler = AsyncIOScheduler()

DATA_FILE = "raid_data.json"
SERVERS_FILE = "rust_servers.json"

# Данные о вайпе
raid_data = {
    "time": "20:00",
    "weekday": "Суббота",
    "server": "Rustoria #1",
    "channel_id": None,
    "reminder_hours": 1,
    "reminder_count": 1,
    "map_url": "https://rustmaps.com/"
}

monitored_servers = []
ANNOUNCEMENT_CHANNEL_ID = None

# ----------------------------------------------------
# ЗАГРУЗКА/СОХРАНЕНИЕ
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
# ФУНКЦИИ ПРОВЕРКИ ВАЙПА
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

# ----------------------------------------------------
# СОБЫТИЕ: БОТ ГОТОВ
# ----------------------------------------------------

@bot.event
async def on_ready():
    global ANNOUNCEMENT_CHANNEL_ID
    ANNOUNCEMENT_CHANNEL_ID = raid_data.get("channel_id")
    
    print(f'✅ Бот {bot.user} запущен!')
    
    if not scheduler.running:
        scheduler.start()
    
    schedule_raid()
    
    try:
        await bot.tree.sync()
        print("✅ Команды синхронизированы!")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")
    
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
            except:
                pass
    else:
        newbie_role = discord.utils.get(guild.roles, name="ɴᴇᴡʙɪᴇ")
        if newbie_role:
            try:
                await member.add_roles(newbie_role)
            except:
                pass

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
        print(f"❌ Ошибка расписания: {e}")

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
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка]({raid_data['map_url']})", inline=False)
    embed.set_footer(text="Подготовьтесь к вайпу! 🔥")
    
    await channel.send("@everyone", embed=embed)

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
    embed.add_field(name="🗺️ Карта", value=f"[Ссылка]({raid_data['map_url']})", inline=False)
    embed.set_footer(text="Всем удачи!")
    
    await channel.send("@everyone", embed=embed)

# ====================================================
# МОДАЛЬНЫЕ ОКНА ДЛЯ КАЖДОГО ПОЛЯ
# ====================================================

class ServerNameModal(discord.ui.Modal, title='🎮 Название сервера'):
    value = discord.ui.TextInput(
        label='Название сервера',
        placeholder='Например: Rustoria #1',
        default='Rustoria #1',
        required=True,
        max_length=100
    )
    
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.value.default = raid_data.get("server", "Rustoria #1")
    
    async def on_submit(self, interaction: discord.Interaction):
        raid_data["server"] = self.value.value.strip()
        save_data()
        schedule_raid()
        await interaction.response.send_message(
            f"✅ Сервер: **{raid_data['server']}**",
            ephemeral=True
        )


class TimeModal(discord.ui.Modal, title='🕐 Время вайпа'):
    value = discord.ui.TextInput(
        label='Время (ЧЧ:ММ)',
        placeholder='Например: 20:00',
        default='20:00',
        required=True,
        max_length=5
    )
    
    def __init__(self):
        super().__init__()
        self.value.default = raid_data.get("time", "20:00")
    
    async def on_submit(self, interaction: discord.Interaction):
        time_str = self.value.value.strip()
        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except:
            await interaction.response.send_message(
                "❌ Неверный формат! Используй ЧЧ:ММ (например, 20:00)",
                ephemeral=True
            )
            return
        
        raid_data["time"] = time_str
        save_data()
        schedule_raid()
        await interaction.response.send_message(
            f"✅ Время: **{time_str}**",
            ephemeral=True
        )


class ChannelModal(discord.ui.Modal, title='📢 Канал для оповещений'):
    value = discord.ui.TextInput(
        label='Упоминание канала или ID',
        placeholder='Например: #вайпы или 123456789012345678',
        required=True,
        max_length=100
    )
    
    def __init__(self):
        super().__init__()
        if raid_data.get("channel_id"):
            self.value.default = f"<#{raid_data['channel_id']}>"
    
    async def on_submit(self, interaction: discord.Interaction):
        global ANNOUNCEMENT_CHANNEL_ID
        channel_value = self.value.value.strip()
        channel_id = None
        
        # Упоминание <#123>
        if channel_value.startswith("<#") and channel_value.endswith(">"):
            try:
                channel_id = int(channel_value[2:-1])
            except:
                channel_id = None
        
        # ID как число
        if not channel_id and channel_value.isdigit():
            channel_id = int(channel_value)
        
        # По имени канала
        if not channel_id:
            name_clean = channel_value.replace("#", "").strip()
            for ch in interaction.guild.text_channels:
                if ch.name.lower() == name_clean.lower():
                    channel_id = ch.id
                    break
        
        if not channel_id:
            await interaction.response.send_message(
                "❌ Канал не найден! Используй упоминание `#канал` или ID.",
                ephemeral=True
            )
            return
        
        raid_data["channel_id"] = channel_id
        ANNOUNCEMENT_CHANNEL_ID = channel_id
        save_data()
        
        await interaction.response.send_message(
            f"✅ Канал: <#{channel_id}>",
            ephemeral=True
        )


class WeekdayModal(discord.ui.Modal, title='📅 День недели'):
    value = discord.ui.TextInput(
        label='День недели',
        placeholder='Например: Суббота или Ежедневно',
        default='Суббота',
        required=True,
        max_length=20
    )
    
    def __init__(self):
        super().__init__()
        self.value.default = raid_data.get("weekday", "Суббота")
    
    async def on_submit(self, interaction: discord.Interaction):
        weekday_str = self.value.value.strip().capitalize()
        valid = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье", "Ежедневно"]
        
        if weekday_str not in valid:
            await interaction.response.send_message(
                f"❌ Неверный день! Доступные: {', '.join(valid)}",
                ephemeral=True
            )
            return
        
        raid_data["weekday"] = weekday_str
        save_data()
        schedule_raid()
        await interaction.response.send_message(
            f"✅ День: **{weekday_str}**",
            ephemeral=True
        )


class ReminderModal(discord.ui.Modal, title='⏰ Напоминание'):
    value = discord.ui.TextInput(
        label='За сколько часов напомнить (1-24)',
        placeholder='Например: 1',
        default='1',
        required=True,
        max_length=2
    )
    
    def __init__(self):
        super().__init__()
        self.value.default = str(raid_data.get("reminder_hours", 1))
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            hours = int(self.value.value.strip())
            if not (1 <= hours <= 24):
                raise ValueError
        except:
            await interaction.response.send_message(
                "❌ Введи число от 1 до 24!",
                ephemeral=True
            )
            return
        
        raid_data["reminder_hours"] = hours
        save_data()
        schedule_raid()
        await interaction.response.send_message(
            f"✅ Напоминание за **{hours}** час(а)",
            ephemeral=True
        )


class ReminderCountModal(discord.ui.Modal, title='🔔 Количество напоминаний'):
    value = discord.ui.TextInput(
        label='Сколько напоминаний отправить (1-5)',
        placeholder='Например: 1',
        default='1',
        required=True,
        max_length=1
    )
    
    def __init__(self):
        super().__init__()
        self.value.default = str(raid_data.get("reminder_count", 1))
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            count = int(self.value.value.strip())
            if not (1 <= count <= 5):
                raise ValueError
        except:
            await interaction.response.send_message(
                "❌ Введи число от 1 до 5!",
                ephemeral=True
            )
            return
        
        raid_data["reminder_count"] = count
        save_data()
        await interaction.response.send_message(
            f"✅ Количество напоминаний: **{count}**",
            ephemeral=True
        )


class DeleteServerModal(discord.ui.Modal, title='🗑️ Удаление сервера'):
    value = discord.ui.TextInput(
        label='Название сервера для удаления',
        placeholder='Введи название сервера',
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        global monitored_servers
        
        await interaction.response.defer(ephemeral=True)
        
        server_name = self.value.value.strip()
        
        for i, server in enumerate(monitored_servers):
            if server["name"].lower() == server_name.lower():
                monitored_servers.pop(i)
                save_servers()
                await interaction.followup.send(
                    f"✅ Сервер **{server_name}** удалён!",
                    ephemeral=True
                )
                return
        
        await interaction.followup.send(
            f"❌ Сервер **{server_name}** не найден!\n"
            f"Посмотри список: `/vipelist`",
            ephemeral=True
        )

# ====================================================
# МЕНЮ /vipeset
# ====================================================

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
            try:
                await self.message.delete()
            except:
                pass
    
    def get_embed(self):
        embed = discord.Embed(
            title="⚙️ НАСТРОЙКА ВАЙПА",
            description="Нажми на кнопку, чтобы изменить параметр",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        channel_text = f"<#{raid_data['channel_id']}>" if raid_data.get('channel_id') else "❌ Не установлен"
        
        embed.add_field(name="🎮 Сервер", value=f"**{raid_data.get('server', 'Не указан')}**", inline=True)
        embed.add_field(name="🕐 Время вайпа", value=f"**{raid_data.get('time', '20:00')}**", inline=True)
        embed.add_field(name="📢 Канал", value=channel_text, inline=True)
        
        embed.add_field(name="📅 День недели", value=f"**{raid_data.get('weekday', 'Суббота')}**", inline=True)
        embed.add_field(name="⏰ За сколько напомнить", value=f"**{raid_data.get('reminder_hours', 1)}** час(а)", inline=True)
        embed.add_field(name="🔔 Кол-во напоминаний", value=f"**{raid_data.get('reminder_count', 1)}**", inline=True)
        
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
        
        embed.set_footer(text="Меню видно только тебе")
        return embed
    
    async def refresh(self, interaction: discord.Interaction):
        try:
            await interaction.message.edit(embed=self.get_embed(), view=self)
        except:
            pass
    
    # Кнопки 1-го ряда
    @discord.ui.button(label="🎮 Сервер", style=discord.ButtonStyle.primary, row=0)
    async def btn_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ServerNameModal(self))
    
    @discord.ui.button(label="🕐 Время", style=discord.ButtonStyle.primary, row=0)
    async def btn_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TimeModal())
    
    @discord.ui.button(label="📢 Канал", style=discord.ButtonStyle.primary, row=0)
    async def btn_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChannelModal())
    
    # Кнопки 2-го ряда
    @discord.ui.button(label="📅 День недели", style=discord.ButtonStyle.primary, row=1)
    async def btn_weekday(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WeekdayModal())
    
    @discord.ui.button(label="⏰ Напоминание", style=discord.ButtonStyle.primary, row=1)
    async def btn_reminder(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReminderModal())
    
    @discord.ui.button(label="🔔 Кол-во напом.", style=discord.ButtonStyle.primary, row=1)
    async def btn_reminder_count(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReminderCountModal())
    
    # Кнопки 3-го ряда
    @discord.ui.button(label="🗑️ Удалить сервер", style=discord.ButtonStyle.danger, row=2, emoji="🗑️")
    async def btn_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DeleteServerModal())
    
    @discord.ui.button(label="🔄 Обновить", style=discord.ButtonStyle.success, row=2)
    async def btn_refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.secondary, row=2)
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.message.delete()
        except:
            pass
        await interaction.response.send_message("✅ Меню закрыто", ephemeral=True)

# ----------------------------------------------------
# КОМАНДА /vipeset
# ----------------------------------------------------

@bot.tree.command(name="vipeset", description="Настройка вайпа (только для администраторов)")
@app_commands.default_permissions(administrator=True)
async def vipeset(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    view = VipeSetView(author_id=interaction.user.id)
    embed = view.get_embed()
    
    message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    view.message = message

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
    
    for server in monitored_servers:
        embed.add_field(
            name=f"🎮 {server['name']}",
            value=f"📅 **{server.get('wipe_day', 'Не указан')}** в **{server.get('wipe_time', '20:00')}**",
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

# ----------------------------------------------------
# КОМАНДА /vipeset_servers
# ----------------------------------------------------

class ServersManageView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.message = None
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Не твоё меню!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="➕ Добавить сервер", style=discord.ButtonStyle.success)
    async def add_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ServerAddModal())
    
    @discord.ui.button(label="🗑️ Удалить сервер", style=discord.ButtonStyle.danger)
    async def delete_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DeleteServerModal())
    
    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.secondary)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.message.delete()
        except:
            pass
        await interaction.response.send_message("✅ Закрыто", ephemeral=True)


class ServerAddModal(discord.ui.Modal, title='➕ Добавление сервера'):
    name = discord.ui.TextInput(label='🎮 Название сервера', placeholder='Rustoria #1', required=True)
    day = discord.ui.TextInput(label='📅 День вайпа', placeholder='Суббота', default='Суббота', required=True)
    time = discord.ui.TextInput(label='🕐 Время вайпа', placeholder='20:00', default='20:00', required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        name = self.name.value.strip()
        day = self.day.value.strip().capitalize()
        time_str = self.time.value.strip()
        
        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except:
            await interaction.followup.send("❌ Неверное время!", ephemeral=True)
            return
        
        for s in monitored_servers:
            if s["name"].lower() == name.lower():
                await interaction.followup.send(f"❌ Сервер **{name}** уже есть!", ephemeral=True)
                return
        
        monitored_servers.append({
            "name": name,
            "wipe_day": day,
            "wipe_time": time_str,
            "channel_id": interaction.channel.id
        })
        save_servers()
        
        await interaction.followup.send(f"✅ Сервер **{name}** добавлен!", ephemeral=True)


@bot.tree.command(name="vipeset_servers", description="Управление списком серверов")
@app_commands.default_permissions(administrator=True)
async def vipeset_servers(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    view = ServersManageView(author_id=interaction.user.id)
    
    embed = discord.Embed(
        title="⚙️ УПРАВЛЕНИЕ СЕРВЕРАМИ",
        description="➕ **Добавить сервер**\n🗑️ **Удалить сервер**",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    
    message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    view.message = message

# ----------------------------------------------------
# КОМАНДА /вайп
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
    embed.add_field(name="🔔 Кол-во напом.", value=f"**{raid_data.get('reminder_count', 1)}**", inline=True)
    
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
    
    await interaction.followup.send(embed=embed)

# ----------------------------------------------------
# ЗАПУСК
# ----------------------------------------------------

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ BOT_TOKEN не задан!")
    exit(1)

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Неверный токен.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
