import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 보스 데이터 저장을 위한 딕셔너리
bosses = {}

# 보스 클래스 정의
class Boss:
    def __init__(self, name, cooldown):
        self.name = name
        self.cooldown = timedelta(hours=cooldown)
        self.cut_time = None
        self.spawn_time = None
        self.notified = False

    def set_cut_time(self, cut_time):
        self.cut_time = cut_time
        self.spawn_time = self.cut_time + self.cooldown
        self.notified = False

    def reset_times(self):
        self.cut_time = None
        self.spawn_time = None
        self.notified = False

    def get_spawn_time(self):
        return self.spawn_time

# 보스등록 명령어
@bot.command()
async def 보스등록(ctx, name: str, cooldown: int):
    bosses[name] = Boss(name, cooldown)
    await ctx.send(f'{name} 이/가 {cooldown}시간 쿨타임으로 등록되었습니다.')

# 컷 시간 기록 명령어
@bot.command()
async def 컷(ctx, time: str, name: str):
    cut_time = datetime.strptime(time, '%H%M')
    now = datetime.now()
    cut_time = cut_time.replace(year=now.year, month=now.month, day=now.day)
    # 현재 시간보다 컷타임이 늦으면 전날로 설정
    if cut_time > now:
        cut_time -= timedelta(days=1)
    if name in bosses:
        bosses[name].set_cut_time(cut_time)
        spawn_time = bosses[name].get_spawn_time()
        await ctx.send(f'{name} 보스가 {time}에 컷되었습니다. 젠 시간: {spawn_time.strftime("%Y-%m-%d %H:%M")}')
    else:
        await ctx.send(f'{name} 보스가 등록되지 않았습니다.')

# 보탐 명령어
@bot.command()
async def 보탐(ctx):
    if not bosses:
        await ctx.send('등록된 보스가 없습니다.')
        return
    
    response = '```현재 등록된 보스의 젠 시간:\n'
    for boss in bosses.values():
        if boss.spawn_time:
            response += f'{boss.name}: {boss.spawn_time.strftime("%Y-%m-%d %H:%M")}\n'
        else:
            response += f'{boss.name}: 컷 시간이 기록되지 않음\n'
    response += '```'
    await ctx.send(response)

# 보탐초기화 명령어
@bot.command()
async def 보탐초기화(ctx):
    for boss in bosses.values():
        boss.reset_times()
    await ctx.send('모든 보스의 컷 시간이 초기화되었습니다.')

# 보스 젠 시간 체크 태스크
@tasks.loop(seconds=60)
async def check_boss_spawn():
    now = datetime.now()
    for boss in bosses.values():
        if boss.spawn_time:
            if now >= boss.spawn_time:
                channel = discord.utils.get(bot.get_all_channels(), name='일반')  # 알림을 보낼 채널 이름
                if channel:
                    await channel.send(f'{boss.name} 젠 타임입니다!')
                # 다음 젠 시간을 계산
                boss.cut_time = now
                boss.spawn_time = boss.cut_time + boss.cooldown
                boss.notified = False  # 새로운 젠 시간에 대해 다시 알림 설정
            elif not boss.notified and now >= boss.spawn_time - timedelta(minutes=5):
                channel = discord.utils.get(bot.get_all_channels(), name='일반')  # 알림을 보낼 채널 이름
                if channel:
                    await channel.send(f'{boss.name} 보스 젠 5분 전입니다!')
                boss.notified = True  # 5분 전 알림 후 notified 설정

# 봇이 준비되었을 때 실행할 이벤트
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    check_boss_spawn.start()

bot.run('DISCORD_TOKEN')
