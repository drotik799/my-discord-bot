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
SETTINGS_FILE = "bot_settings.json"
WARNS_FILE = "warns_data.json"

# Данные о вайпе
raid_data = {
    "time": "20:00",
    "weekday": "Суббота",
    "server": "Rustoria #1",
    "channel_id": None,
    "reminder_hours": 1,
    "map_url": "https://rustmaps.com/"
}

monitored_servers = []
bot_settings = {"autoroles_enabled": True}
warns_data = {}  # { "user_id": [ {"reason": "...", "moderator": "...", "date": "..."} ] }
ANNOUNCEMENT_CHANNEL_ID = None

# ----------------------------------------------------
# ЗАГРУЗКА/СОХРАНЕНИЕ
# ----------------------------------------------------

def load_data():
    global raid_data, monitored_servers, bot_settings, warns_data, ANNOUNCEMENT_CHANNEL_ID
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                raid_data.update(saved)
                ANNOUNCEMENT_CHANNEL_ID = raid_data.get("channel_id")
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
    
    if os.path.exists(SERVERS_FILE):
        try:
            with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
                monitored_servers = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки серверов: {e}")

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                bot_settings.update(saved)
        except Exception as e:
            print(f"❌ Ошибка загрузки настроек: {e}")

    if os.path.exists(WARNS_FILE):
        try:
            with open(WARNS_FILE, 'r', encoding='utf-8') as f:
                warns_data = json.load(f)
            print(f"✅ Загружено {len(warns_data)} записей о варнах")
        except Exception as e:
            print(f"❌ Ошибка загрузки варнов: {e}")

def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(raid_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

def save_servers():
    try:
        with open(SERVERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(monitored_servers, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Ошибка сохранения серверов: {e}")

def save_settings():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(bot_settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Ошибка сохранения настроек: {e}")

def save_warns():
    try:
        with open(WARNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(warns_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Ошибка сохранения варнов: {e}")

load_data()

# ----------------------------------------------------
# ПРОВЕРКА ВАЙПА
# ----------------------------------------------------

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
            days_ahead = weekdays[weekday] - now.weekday()
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
    if not bot_settings.get("autoroles_enabled", True):
        return

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

# ====================================================
# МОДАЛЬНОЕ ОКНО: ВЫДАЧА ВАРНА
# ====================================================

class WarnModal(discord.ui.Modal, title='⚠️ ВЫДАЧА ВАРНА'):
    reason = discord.ui.TextInput(
        label='Причина варна',
        placeholder='Опишите причину...',
        required=True,
        max_length=200,
        style=discord.TextStyle.paragraph
    )
    
    def __init__(self, target_member: discord.Member):
        super().__init__()
        self.target_member = target_member
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(self.target_member.id)
        if user_id not in warns_data:
            warns_data[user_id] = []
        
        warn_info = {
            "reason": self.reason.value,
            "moderator": interaction.user.display_name,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        warns_data[user_id].append(warn_info)
        save_warns()
        
        # Отправляем ЛС пользователю
        try:
            dm_embed = discord.Embed(
                title="⚠️ ВАМ ВЫДАН ВАРН",
                description=f"На сервере **{interaction.guild.name}**",
                color=0xff5500,
                timestamp=datetime.now()
            )
            dm_embed.add_field(name="🛡️ Модератор", value=interaction.user.display_name, inline=True)
            dm_embed.add_field(name="📝 Причина", value=self.reason.value, inline=False)
            dm_embed.add_field(name="⚠️ Всего варнов", value=f"**{len(warns_data[user_id])}**", inline=True)
            await self.target_member.send(embed=dm_embed)
        except:
            pass
        
        await interaction.followup.send(
            f"✅ Варн выдан игроку {self.target_member.mention}!\n"
            f"📝 Причина: **{self.reason.value}**\n"
            f"⚠️ Всего варнов: **{len(warns_data[user_id])}**",
            ephemeral=True
        )

# ====================================================
# ПРОФИЛЬ (С КНОПКАМИ)
# ====================================================

class ProfileView(discord.ui.View):
    def __init__(self, user, guild, author_id, is_admin=False):
        super().__init__(timeout=120)
        self.user = user
        self.guild = guild
        self.author_id = author_id
        self.message = None
        
        # Безопасно скрываем кнопку варна для не-админов
        if not is_admin:
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label == "⚠️ Выдать варн":
                    item.disabled = True
                    item.style = discord.ButtonStyle.secondary
                    break
    
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
            try:
                await self.message.edit(view=self)
                await asyncio.sleep(5)
                await self.message.delete()
            except:
                pass
    
    def get_embed(self):
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
            title="📊 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ",
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

    @discord.ui.button(label="🔄 Обновить", style=discord.ButtonStyle.primary)
    async def btn_refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="⚠️ Выдать варн", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def btn_warn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ У вас нет прав для выдачи варна!", ephemeral=True)
            return
            
        await interaction.response.send_modal(WarnModal(target_member=self.user))

    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.secondary, emoji="❌")
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔒 Профиль закрыт",
            description="Используй `/профиль` чтобы открыть снова.",
            color=0x808080
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(5)
        try:
            await interaction.message.delete()
        except:
            pass

@bot.tree.command(name="профиль", description="Показывает профиль пользователя")
@app_commands.describe(пользователь="Пользователь, чей профиль нужно показать")
async def profile(interaction: discord.Interaction, пользователь: discord.Member = None):
    if not interaction.guild:
        await interaction.response.send_message("❌ Эта команда работает только на сервере!", ephemeral=True)
        return

    if пользователь is None:
        пользователь = interaction.user

    if пользователь not in interaction.guild.members:
        await interaction.response.send_message("❌ Этот пользователь не найден на сервере!", ephemeral=True)
        return

    is_admin = interaction.user.guild_permissions.administrator
    
    view = ProfileView(пользователь, interaction.guild, interaction.user.id, is_admin=is_admin)
    embed = view.get_embed()
    
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

# ====================================================
# ОСТАЛЬНЫЕ КОМАНДЫ (ВАЙПЫ, АВТОРОЛИ)
# ====================================================

class VipeSetModal(discord.ui.Modal, title='⚙️ НАСТРОЙКА ВАЙПА'):
    server_input = discord.ui.TextInput(label='🎮 Название сервера', placeholder='Например: Rustoria #1', required=True, max_length=100)
    time_input = discord.ui.TextInput(label='🕐 Время вайпа (ЧЧ:ММ)', placeholder='Например: 20:00', required=True, max_length=5)
    weekday_input = discord.ui.TextInput(label='📅 День недели', placeholder='Суббота / Ежедневно', required=True, max_length=20)
    channel_input = discord.ui.TextInput(label='📢 Канал (упоминание #канал или ID)', placeholder='Например: #вайпы', required=True, max_length=100)
    reminder_input = discord.ui.TextInput(label='⏰ Напоминание за N часов (1-24)', placeholder='Например: 1', required=True, max_length=2)
    
    def __init__(self):
        super().__init__()
        self.server_input.default = raid_data.get("server", "Rustoria #1")
        self.time_input.default = raid_data.get("time", "20:00")
        self.weekday_input.default = raid_data.get("weekday", "Суббота")
        if raid_data.get("channel_id"):
            self.channel_input.default = f"<#{raid_data['channel_id']}>"
        self.reminder_input.default = str(raid_data.get("reminder_hours", 1))
    
    async def on_submit(self, interaction: discord.Interaction):
        global raid_data, ANNOUNCEMENT_CHANNEL_ID
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            time_str = self.time_input.value.strip()
            try:
                hour, minute = map(int, time_str.split(":"))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError
            except:
                await interaction.followup.send("❌ Неверный формат времени!", ephemeral=True)
                return
            
            weekday_str = self.weekday_input.value.strip().capitalize()
            valid = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье", "Ежедневно"]
            if weekday_str not in valid:
                await interaction.followup.send(f"❌ Неверный день! Доступные: {', '.join(valid)}", ephemeral=True)
                return
            
            try:
                reminder_hours = int(self.reminder_input.value.strip())
                if not (1 <= reminder_hours <= 24):
                    raise ValueError
            except:
                await interaction.followup.send("❌ Напоминание от 1 до 24!", ephemeral=True)
                return
            
            channel_value = self.channel_input.value.strip()
            channel_id = None
            
            if channel_value.startswith("<#") and channel_value.endswith(">"):
                try:
                    channel_id = int(channel_value[2:-1])
                except:
                    pass
            
            if not channel_id and channel_value.isdigit():
                channel_id = int(channel_value)
            
            if not channel_id:
                name_clean = channel_value.replace("#", "").strip()
                for ch in interaction.guild.text_channels:
                    if ch.name.lower() == name_clean.lower():
                        channel_id = ch.id
                        break
            
            if not channel_id:
                await interaction.followup.send("❌ Канал не найден!", ephemeral=True)
                return
            
            raid_data["server"] = self.server_input.value.strip()
            raid_data["time"] = time_str
            raid_data["weekday"] = weekday_str
            raid_data["channel_id"] = channel_id
            raid_data["reminder_hours"] = reminder_hours
            
            ANNOUNCEMENT_CHANNEL_ID = channel_id
            save_data()
            
            embed = discord.Embed(title="✅ НАСТРОЙКИ СОХРАНЕНЫ", color=0x00ff00, timestamp=datetime.now())
            embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
            embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}**", inline=True)
            embed.add_field(name="📅 День", value=f"**{raid_data['weekday']}**", inline=True)
            embed.add_field(name="📢 Канал", value=f"<#{channel_id}>", inline=True)
            embed.add_field(name="⏰ Напоминание", value=f"За **{reminder_hours}** час(а)", inline=True)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {str(e)}", ephemeral=True)


class ServerAddModal(discord.ui.Modal, title='➕ ДОБАВЛЕНИЕ СЕРВЕРА'):
    name = discord.ui.TextInput(label='🎮 Название сервера', placeholder='Например: Rustoria #1', required=True, max_length=100)
    day = discord.ui.TextInput(label='📅 День вайпа', placeholder='Например: Суббота', default='Суббота', required=True, max_length=20)
    time = discord.ui.TextInput(label='🕐 Время вайпа (ЧЧ:ММ)', placeholder='Например: 20:00', default='20:00', required=True, max_length=5)
    
    async def on_submit(self, interaction: discord.Interaction):
        global monitored_servers
        await interaction.response.defer(ephemeral=True)
        
        name = self.name.value.strip()
        day = self.day.value.strip().capitalize()
        time_str = self.time.value.strip()
        
        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except:
            await interaction.followup.send("❌ Неверный формат времени!", ephemeral=True)
            return
        
        valid = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье", "Ежедневно"]
        if day not in valid:
            await interaction.followup.send(f"❌ Неверный день! Доступные: {', '.join(valid)}", ephemeral=True)
            return
        
        for s in monitored_servers:
            if s["name"].lower() == name.lower():
                await interaction.followup.send(f"❌ Сервер **{name}** уже есть в списке!", ephemeral=True)
                return
        
        monitored_servers.append({"name": name, "wipe_day": day, "wipe_time": time_str, "channel_id": interaction.channel.id})
        save_servers()
        await interaction.followup.send(f"✅ Сервер **{name}** добавлен!\n📅 {day} в **{time_str}**", ephemeral=True)


class ServerDeleteModal(discord.ui.Modal, title='🗑️ УДАЛЕНИЕ СЕРВЕРА'):
    name = discord.ui.TextInput(label='🎮 Название сервера для удаления', placeholder='Введи название точно как в списке', required=True, max_length=100)
    
    async def on_submit(self, interaction: discord.Interaction):
        global monitored_servers
        await interaction.response.defer(ephemeral=True)
        
        name = self.name.value.strip()
        
        for i, server in enumerate(monitored_servers):
            if server["name"].lower() == name.lower():
                monitored_servers.pop(i)
                save_servers()
                await interaction.followup.send(f"✅ Сервер **{name}** удалён!", ephemeral=True)
                return
        
        if monitored_servers:
            servers_list = "\n".join([f"• {s['name']}" for s in monitored_servers])
            await interaction.followup.send(f"❌ Сервер **{name}** не найден!\n\n**Доступные сервера:**\n{servers_list}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Сервер **{name}** не найден!\nСписок пуст.", ephemeral=True)

class ServersManageView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=300)
        self.author_id = author_id
    
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
        await interaction.response.send_modal(ServerDeleteModal())
    
    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.secondary)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.message.delete()
        except:
            pass
        await interaction.response.send_message("✅ Закрыто", ephemeral=True)

@bot.tree.command(name="vipeset", description="Настройка основного вайпа")
@app_commands.default_permissions(administrator=True)
async def vipeset(interaction: discord.Interaction):
    await interaction.response.send_modal(VipeSetModal())

@bot.tree.command(name="vipeset_servers", description="Управление списком серверов")
@app_commands.default_permissions(administrator=True)
async def vipeset_servers(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    view = ServersManageView(author_id=interaction.user.id)
    embed = discord.Embed(title="⚙️ УПРАВЛЕНИЕ СЕРВЕРАМИ", description="➕ **Добавить сервер**\n🗑️ **Удалить сервер**", color=0x00ff00, timestamp=datetime.now())
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="vipelist", description="Показывает список всех серверов с вайпами")
async def vipelist(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if not monitored_servers:
        await interaction.followup.send("📋 Список серверов пуст!")
        return
    
    embed = discord.Embed(title="📋 СПИСОК СЕРВЕРОВ", description=f"Всего: **{len(monitored_servers)}**", color=0x00aaff, timestamp=datetime.now())
    now = datetime.now()
    
    for server in monitored_servers:
        next_wipe = get_next_wipe_for_server(server)
        if next_wipe:
            time_left = next_wipe - now
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            status = f"🟢 ИДЁТ!" if time_left.total_seconds() < 0 else f"⏳ {days}д {hours}ч" if days > 0 else f"🟡 {hours}ч {minutes}мин"
        else:
            status = "❌ Ошибка"
        
        embed.add_field(name=f"🎮 {server['name']}", value=f"📅 **{server.get('wipe_day')}**\n🕐 **{server.get('wipe_time')}**\n⏳ {status}", inline=False)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="вайп", description="Показывает расписание основного вайпа")
async def raid_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    
    embed = discord.Embed(title="⚔️ РАСПИСАНИЕ ВАЙПА ⚔️", color=0xff5500, timestamp=datetime.now())
    embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}**", inline=True)
    embed.add_field(name="📅 День", value=f"**{raid_data['weekday']}**", inline=True)
    embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
    embed.add_field(name="📢 Канал", value=f"<#{raid_data['channel_id']}>" if raid_data.get('channel_id') else "❌ Не установлен", inline=True)
    embed.add_field(name="⏰ Напоминание", value=f"За **{raid_data['reminder_hours']}** час(а)", inline=True)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="arole", description="Включить или выключить систему авторолей")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(status="Выберите действие")
@app_commands.choices(status=[
    app_commands.Choice(name="Включить", value="on"),
    app_commands.Choice(name="Выключить", value="off")
])
async def arole(interaction: discord.Interaction, status: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)
    
    if status.value == "on":
        bot_settings["autoroles_enabled"] = True
        save_settings()
        embed = discord.Embed(title="✅ АВТОРОЛИ ВКЛЮЧЕНЫ", color=0x00ff00, timestamp=datetime.now())
    else:
        bot_settings["autoroles_enabled"] = False
        save_settings()
        embed = discord.Embed(title="🛑 АВТОРОЛИ ВЫКЛЮЧЕНЫ", color=0xff0000, timestamp=datetime.now())
    
    embed.set_footer(text=f"Текущий статус: {status.name}")
    await interaction.followup.send(embed=embed, ephemeral=True)

# ----------------------------------------------------
# ПРИНУДИТЕЛЬНАЯ СИНХРОНИЗАЦИЯ
# ----------------------------------------------------

@bot.tree.command(name="sync", description="Принудительно обновить список команд в Discord")
async def sync_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        # Синхронизируем именно для этого сервера (работает быстрее)
        await bot.tree.sync(guild=interaction.guild)
        
        # Получаем список команд, которые видит Discord
        commands = await bot.tree.fetch_commands(guild=interaction.guild)
        names = ", ".join([f"/{c.name}" for c in commands])
        
        await interaction.followup.send(
            f"✅ Синхронизация завершена!\n"
            f"📋 Зарегистрировано команд: **{len(commands)}**\n"
            f"Список: {names}", 
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка синхронизации: {e}", ephemeral=True)

# ====================================================
# ЗАПУСК
# ====================================================

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
