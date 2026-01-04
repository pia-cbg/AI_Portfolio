# from .llm_parser import extract_schedule
# from src.utils.config import SCHEDULE_BOT_TOKEN, AMADDA_CHANNEL_ID
# from src.bots.schedule_bot.utils.auth_manager import has_token, generate_auth_url
# from src.bots.schedule_bot.utils.gcal_api import add_event
# import discord

# intents = discord.Intents.default()
# intents.guilds = True
# intents.members = True
# intents.message_content = True
# intents.reactions = True
# client = discord.Client(intents=intents)

# WELCOME_MSG_PREFIX = "안녕하세요! 저는 일정 관리 봇입니다."
# SCHEDULE_EMOJI = "📅"
# user_states = {}

# @client.event
# async def on_ready():
#     now = discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S")
#     for guild in client.guilds:
#         channel = guild.get_channel(AMADDA_CHANNEL_ID)
#         if not channel or not channel.permissions_for(guild.me).send_messages:
#             continue
#         async for msg in channel.history(limit=50):
#             if (
#                 msg.author == client.user
#                 and msg.content.startswith(WELCOME_MSG_PREFIX)
#             ):
#                 await msg.delete()
#         last_welcome = await channel.send(
#             f"{WELCOME_MSG_PREFIX} (서버 재시작: {now})\n"
#             "아래 📅 이모지를 클릭하시면 DM으로 안내를 받아볼 수 있어요!\n"
#             "일정을 자유롭게 DM으로 남기세요!"
#         )
#         await last_welcome.add_reaction(SCHEDULE_EMOJI)

# @client.event
# async def on_reaction_add(reaction, user):
#     if user.bot:
#         return
#     if (
#         reaction.message.guild
#         and str(reaction.emoji) == SCHEDULE_EMOJI
#         and reaction.message.author == client.user
#         and reaction.message.content.startswith(WELCOME_MSG_PREFIX)
#     ):
#         try:
#             await user.send(
#                 "안녕하세요! DM 안내입니다.\n"
#                 "일정을 자유롭게 입력하시면 AI가 도와드립니다."
#             )
#         except Exception:
#             pass

# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return
#     # DM만 받음
#     if message.channel.type != discord.ChannelType.private:
#         return

#     user_id = message.author.id
#     text = message.content.strip()
#     state = user_states.get(user_id)

#     ### 1. 구글 인증 안된 경우: 안내 & 인증 링크 제공
#     if not has_token(user_id):
#         auth_url = generate_auth_url(user_id)
#         await message.channel.send(
#             f"구글 인증이 필요합니다!\n"
#             f"아래 링크에서 인증해 주세요 👇\n"
#             f"{auth_url}\n\n"
#             f"*인증 후 다시 일정을 입력하시면 자동 등록됩니다!*"
#         )
#         return

#     ### 2. 인증된 유저만 일정→캘린더 등록로직 진입!
#     try:
#         result = extract_schedule(text, state)
#         user_states[user_id] = result.get('state', {})

#         event = result.get('event')
#         missing = result.get('missing', [])
#         response = result.get('response', "처리 결과가 없습니다.")
#         debug = result.get('debug', [])

#         if missing:
#             if debug:
#                 response += '\n[DEBUG]\n' + '\n'.join(debug)
#             await message.channel.send(response)
#             return

#         if not event:
#             if debug:
#                 response += '\n[DEBUG]\n' + '\n'.join(debug)
#             await message.channel.send(
#                 "일정 정보를 해석하지 못했습니다.\n"
#                 "(아래는 원본 응답/상태 정보 입니다)\n"
#                 f"{response}"
#             )
#             return

#         # 3. 파싱된 일정 → 구글 캘린더에 등록
#         try:
#             url = add_event(event, user_id)  # gcal_api의 add_event 함수: htmlLink 반환
#             summary = (
#                 f"일정 등록이 완료되었습니다!\n"
#                 f"제목: {event.get('summary')}\n"
#                 f"시작: {event.get('start', {}).get('dateTime')}\n"
#                 f"종료: {event.get('end', {}).get('dateTime')}\n"
#                 f"{event.get('description', '')}\n"
#                 f"[캘린더에서 보기]({url})"
#             )
#         except Exception as reg_error:
#             summary = f"구글 캘린더 등록 중 예외가 발생했습니다:\n{reg_error}"

#         if debug:
#             summary += '\n[DEBUG]\n' + '\n'.join(debug)
#         await message.channel.send(summary)

#     except Exception as e:
#         await message.channel.send(f"처리 중 예외가 발생했습니다: {e}")

# client.run(SCHEDULE_BOT_TOKEN)