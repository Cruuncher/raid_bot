# bot.py
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = os.getenv('GUILD_CHANNEL')

client = discord.Client()

bot = commands.Bot(command_prefix='!')

async def check_send_notifications(message, reaction):
    if str(reaction.emoji) != "🚀":
        print(f"Skipping send notification. Wrong reaction emoji, got {str(reaction.emoji)}, expected 🚀")
        return

    lines = message.content.split('\n') 
    host_mention = lines[4][6:] 
    if str(host_mention[3:-1]) != str(reaction.user_id):
        print(f"Skipping send notification. Wrong user reacted. got {str(reaction.user_id)}, expected {str(host_mention[2:-1])}")
        return

    mentions_to_send = get_mention_users(lines)

    mention_str = "\n".join(mentions_to_send) 

    message_to_send = f"""Calling 
{mention_str}

{host_mention} is sending raid invites now!
    """

    await message.channel.send(message_to_send)

def get_mention_users(message_lines):
    mentions = []
    for i in range(8, 13):
        user_mention = message_lines[i][3:] 
        if user_mention:
            mentions.append(user_mention)
        else:
            break 
    return mentions

def merge_mentions(reactions, mentions):
    mentions = mentions[:]

    reaction_set = set(reactions) 
    mention_set = set(mentions)

    to_remove = [] 
    for mention in mentions:
        if mention not in reaction_set:
            to_remove.append(mention)

    for removal in to_remove:
        mentions.remove(removal) 

    for reaction in reactions:
        if reaction not in mention_set:
            mentions.append(reaction) 

    return mentions

async def render_raid_message(message):
    lines = message.content.split('\n')
    

    [thumb_reaction] = [reaction for reaction in message.reactions if str(reaction.emoji) == '👍']
    users_in_reaction = [user.mention for user in await thumb_reaction.users().flatten()]
    users_in_mention = get_mention_users(lines)
    mentions = merge_mentions(users_in_reaction, users_in_mention)

    lines = lines[:8]
    lobby_num = 1
    for mention in mentions:
        if mention != client.user.mention:
            lines.append(f'{lobby_num}. {mention}')
            lobby_num += 1
        if lobby_num > 5:
            break

    while lobby_num < 6:
        lines.append(f'{lobby_num}. ')
        lobby_num += 1

    lines.append('')
    lines.append('Hit 👍 to sign up for this raid')
    lines.append("Host hit 🚀 to notify lobby that you're sending invites now")

    await message.edit(content='\n'.join(lines))

@client.event
async def on_ready():
    for guild in client.guilds:
        print(f'Connected to {guild.name}({guild.id})')
        members = '\n - '.join([member.name for member in guild.members])
        print(f'Guild Members:\n - {members}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name != CHANNEL:
        return

    lines = message.content.split('\n') 
    if len(lines) < 4: 
        await message.delete()
        return 

    if not lines[0].lower().startswith('boss: '):
        await message.delete()
        return

    if not lines[1].lower().startswith('time: '):
        await message.delete() 
        return 

    if not lines[2].lower().startswith('location: '):
        await message.delete() 
        return 

    if not lines[3].lower().startswith('friend code: '):
        await message.delete() 
        return 


    boss = lines[0][6:]
    time = lines[1][6:]
    location = lines[2][10:]
    friend_code = lines[3][12:]

    message = await message.channel.send(f"""Calling @everyone
⭐ {boss}
📍 {location}
⏰ {time}
Host: {message.author.mention}
Friend Code: {friend_code}

Lobby:
1.
2.
3.
4.
5.

Hit 👍 to sign up for this raid
Host hit 🚀 to notify lobby that you're sending invites now
""")
    await message.add_reaction("👍")
    await message.add_reaction("🚀")

@client.event 
async def on_raw_reaction_add(reaction):
    channel = client.get_channel(reaction.channel_id)
    message = await channel.fetch_message(reaction.message_id)
    if message.author != client.user:
        return

    await check_send_notifications(message, reaction)

    await render_raid_message(message) 

@client.event 
async def on_raw_reaction_remove(reaction):
    channel = client.get_channel(reaction.channel_id)
    message = await channel.fetch_message(reaction.message_id)
    if message.author != client.user:
        return
    await render_raid_message(message) 


client.run(TOKEN)