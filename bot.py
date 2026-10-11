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

# Данные о вайпе (основной)
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

ANNOUNCEMENT_CHANNEL_ID = None

# ----------------------------------------------------
# ЗАГРУЗКА/СОХРАНЕНИЕ
# ----------------------------------------------------

def load_data():
    global raid_data, monitored_servers, ANNOUNCEMENT_CHANNEL_ID
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                raid_data.update(saved)
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
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

def save_servers():
    try:
        with open(SERVERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(monitored_servers, f, ensure_ascii=False, indent=4)
        print("✅ Список серверов сохранён")
    except Exception as e:
        print(f"❌ Ошибка сохранения серверов: {e}")

load_data()

# ----------------------------------------------------
# ПРОВЕРКА ВАЙПА
# ----------------------------------------------------

def get_next_wipe_for_server(server):
    """Возвращает дату и время следующего вайпа для конкретного сервера"""
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
    guild = member.guild
    
    if member.bot:
        bot_role = discord.utils.get(guild.roles, name="ʙᴏᴛ")
        if bot_role:
            try:
                await member.add_roles(bot_role)
                print(f"✅ Роль ʙᴏᴛ выдана {member.name}")
            except:
                pass
    else:
        newbie_role = discord.utils.get(guild.roles, name="ɴᴇᴡʙɪᴇ")
        if newbie_role:
            try:
                await member.add_roles(newbie_role)
                print(f"✅ Роль ɴᴇᴡʙɪᴇ выдана {member.name}")
            except:
                pass

# ====================================================
# МОДАЛЬНЫЕ ОКНА
# ====================================================

class VipeSetModal(discord.ui.Modal, title='⚙️ НАСТРОЙКА ВАЙПА'):
    """Единое модальное окно для настройки ОСНОВНОГО вайпа"""
    
    server_input = discord.ui.TextInput(
        label='🎮 Название сервера',
        placeholder='Например: Rustoria #1',
        required=True,
        max_length=100
    )
    
    time_input = discord.ui.TextInput(
        label='🕐 Время вайпа (ЧЧ:ММ)',
        placeholder='Например: 20:00',
        required=True,
        max_length=5
    )
    
    weekday_input = discord.ui.TextInput(
        label='📅 День недели',
        placeholder='Суббота / Ежедневно',
        required=True,
        max_length=20
    )
    
    channel_input = discord.ui.TextInput(
        label='📢 Канал (упоминание #канал или ID)',
        placeholder='Например: #вайпы',
        required=True,
        max_length=100
    )
    
    reminder_input = discord.ui.TextInput(
        label='⏰ Напоминание за N часов (1-24)',
        placeholder='Например: 1',
        required=True,
        max_length=2
    )
    
    def __init__(self):
        super().__init__()
        # Подставляем текущие значения
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
            # Проверяем время
            time_str = self.time_input.value.strip()
            try:
                hour, minute = map(int, time_str.split(":"))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError
            except:
                await interaction.followup.send("❌ Неверный формат времени!", ephemeral=True)
                return
            
            # Проверяем день недели
            weekday_str = self.weekday_input.value.strip().capitalize()
            valid = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье", "Ежедневно"]
            if weekday_str not in valid:
                await interaction.followup.send(f"❌ Неверный день! Доступные: {', '.join(valid)}", ephemeral=True)
                return
            
            # Проверяем напоминание
            try:
                reminder_hours = int(self.reminder_input.value.strip())
                if not (1 <= reminder_hours <= 24):
                    raise ValueError
            except:
                await interaction.followup.send("❌ Напоминание от 1 до 24!", ephemeral=True)
                return
            
            # Обрабатываем канал
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
            
            # Сохраняем
            raid_data["server"] = self.server_input.value.strip()
            raid_data["time"] = time_str
            raid_data["weekday"] = weekday_str
            raid_data["channel_id"] = channel_id
            raid_data["reminder_hours"] = reminder_hours
            
            ANNOUNCEMENT_CHANNEL_ID = channel_id
            
            save_data()
            
            # Подтверждение
            embed = discord.Embed(
                title="✅ НАСТРОЙКИ СОХРАНЕНЫ",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(name="🎮 Сервер", value=f"**{raid_data['server']}**", inline=True)
            embed.add_field(name="🕐 Время", value=f"**{raid_data['time']}**", inline=True)
            embed.add_field(name="📅 День", value=f"**{raid_data['weekday']}**", inline=True)
            embed.add_field(name="📢 Канал", value=f"<#{channel_id}>", inline=True)
            embed.add_field(name="⏰ Напоминание", value=f"За **{reminder_hours}** час(а)", inline=True)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"✅ Настройки вайпа обновлены: {interaction.user.name}")
            
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {str(e)}", ephemeral=True)


class ServerAddModal(discord.ui.Modal, title='➕ ДОБАВЛЕНИЕ СЕРВЕРА'):
    """Модальное окно для добавления сервера в список мониторинга"""
    
    name = discord.ui.TextInput(
        label='🎮 Название сервера',
        placeholder='Например: Rustoria #1',
        required=True,
        max_length=100
    )
    
    day = discord.ui.TextInput(
        label='📅 День вайпа',
        placeholder='Например: Суббота',
        default='Суббота',
        required=True,
        max_length=20
    )
    
    time = discord.ui.TextInput(
        label='🕐 Время вайпа (ЧЧ:ММ)',
        placeholder='Например: 20:00',
        default='20:00',
        required=True,
        max_length=5
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        global monitored_servers
        
        await interaction.response.defer(ephemeral=True)
        
        name = self.name.value.strip()
        day = self.day.value.strip().capitalize()
        time_str = self.time.value.strip()
        
        # Проверяем время
        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except:
            await interaction.followup.send("❌ Неверный формат времени!", ephemeral=True)
            return
        
        # Проверяем день
        valid = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье", "Ежедневно"]
        if day not in valid:
            await interaction.followup.send(f"❌ Неверный день! Доступные: {', '.join(valid)}", ephemeral=True)
            return
        
        # Проверяем дубликат
        for s in monitored_servers:
            if s["name"].lower() == name.lower():
                await interaction.followup.send(f"❌ Сервер **{name}** уже есть в списке!", ephemeral=True)
                return
        
        # Добавляем
        monitored_servers.append({
            "name": name,
            "wipe_day": day,
            "wipe_time": time_str,
            "channel_id": interaction.channel.id
        })
        save_servers()
        
        await interaction.followup.send(
            f"✅ Сервер **{name}** добавлен!\n"
            f"📅 {day} в **{time_str}**",
            ephemeral=True
        )
        print(f"✅ Сервер {name} добавлен")


class ServerDeleteModal(discord.ui.Modal, title='🗑️ УДАЛЕНИЕ СЕРВЕРА'):
    """Модальное окно для удаления сервера"""
    
    name = discord.ui.TextInput(
        label='🎮 Название сервера для удаления',
        placeholder='Введи название точно как в списке',
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        global monitored_servers
        
        await interaction.response.defer(ephemeral=True)
        
        name = self.name.value.strip()
        
        for i, server in enumerate(monitored_servers):
            if server["name"].lower() == name.lower():
                monitored_servers.pop(i)
                save_servers()
                await interaction.followup.send(
                    f"✅ Сервер **{name}** удалён!",
                    ephemeral=True
                )
                print(f"✅ Сервер {name} удалён")
                return
        
        # Если не найден — показываем список
        if monitored_servers:
            servers_list = "\n".join([f"• {s['name']}" for s in monitored_servers])
            await interaction.followup.send(
                f"❌ Сервер **{name}** не найден!\n\n"
                f"**Доступные сервера:**\n{servers_list}",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ Сервер **{name}** не найден!\n"
                f"Список серверов пуст. Добавь через `/vipeset_servers`",
                ephemeral=True
            )

# ====================================================
# МЕНЮ УПРАВЛЕНИЯ СЕРВЕРАМИ
# ====================================================

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
    
    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except:
                pass
    
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

# ====================================================
# КОМАНДЫ
# ====================================================

@bot.tree.command(name="vipeset", description="Настройка основного вайпа")
@app_commands.default_permissions(administrator=True)
async def vipeset(interaction: discord.Interaction):
    """Открывает модальное окно настройки вайпа"""
    await interaction.response.send_modal(VipeSetModal())


@bot.tree.command(name="vipeset_servers", description="Управление списком серверов")
@app_commands.default_permissions(administrator=True)
async def vipeset_servers(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    view = ServersManageView(author_id=interaction.user.id)
    
    embed = discord.Embed(
        title="⚙️ УПРАВЛЕНИЕ СЕРВЕРАМИ",
        description="➕ **Добавить сервер** — добавить новый\n"
                   "🗑️ **Удалить сервер** — удалить из списка",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    
    message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    view.message = message


@bot.tree.command(name="vipelist", description="Показывает список всех серверов с вайпами")
async def vipelist(interaction: discord.Interaction):
    """РАБОЧАЯ команда — показывает все сервера"""
    await interaction.response.defer()
    
    if not monitored_servers:
        embed = discord.Embed(
            title="📋 СПИСОК СЕРВЕРОВ",
            description="Список пуст.\n\n"
                       "Администраторы могут добавить сервера командой `/vipeset_servers`.",
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
                status = "🟡 МЕНЕЕ ЧАСА!"
            elif days == 0:
                status = f"⏳ {hours}ч {minutes}мин"
            else:
                status = f"⏳ {days}д {hours}ч"
        else:
            status = "❌ Ошибка"
        
        embed.add_field(
            name=f"🎮 {server['name']}",
            value=f"📅 **{server.get('wipe_day', 'Не указан')}**\n"
                  f"🕐 **{server.get('wipe_time', '20:00')}**\n"
                  f"⏳ До вайпа: **{status}**",
            inline=False
        )
    
    embed.set_footer(text="Используй /vipeset_servers чтобы добавить/удалить сервер")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="вайп", description="Показывает расписание основного вайпа")
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
    embed.add_field(name="📢 Канал", value=f"<#{raid_data['channel_id']}>" if raid_data.get('channel_id') else "❌ Не установлен", inline=True)
    embed.add_field(name="⏰ Напоминание", value=f"За **{raid_data['reminder_hours']}** час(а)", inline=True)
    
    await interaction.followup.send(embed=embed)

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
