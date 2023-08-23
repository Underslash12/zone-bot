# zone_bot.py

# TODO track name changes using on_guild_channel_update event

import discord
import random
import time

SERVER_ID = 633788616765603870

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
guild: discord.Guild = None
zones: list[discord.VoiceChannel] = None
warp_zones: dict[str, discord.VoiceChannel] = None

@client.event
async def on_ready():
    global guild, zones, warp_zones

    print(f'We have logged in as {client.user}')
    
    guild = client.get_guild(SERVER_ID)
    zones = await get_zones()
    warp_zones = await get_warp_zones()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('ping'):
        await message.channel.send('pong')

# get a list of the warp zones as VoiceChannel objects
async def get_warp_zones() -> dict[str, discord.VoiceChannel]:
    zone_fields = guild.categories
    warp_field = list(filter(lambda cat: cat.name.upper() == "THE WARP ZONE", zone_fields))[0]
    warp_zones = warp_field.channels

    return {zone.name: zone for zone in warp_zones}

# get a list of the zones as VoiceChannel objects
async def get_zones() -> list[discord.VoiceChannel]:
    zone_fields = guild.categories
    zone_fields = list(filter(lambda cat: cat.name.upper().find("ZONE ZONE") >= 0, zone_fields))

    zones = []
    for field in zone_fields:
        zones.extend(field.channels)

    return zones

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # return if user leaves call
    if after == None:
        return
    
    # verify user joined a warp zone
    for channel in warp_zones.values():
        if after.channel.id == channel.id:
            break
    else:
        return
    
    # switch case for the different warp zone functions
    if after.channel.id == warp_zones["The Roll The Zone"].id:
        await on_join_roll_the_zone(member, before, after)
    elif after.channel == warp_zones["The Party Zone"]:
        await on_join_party_zone(member, before, after)
    elif after.channel == warp_zones["The Co-Op Zone"]:
        pass
    elif after.channel == warp_zones["The No Zone"]:
        pass
    elif after.channel == warp_zones["The David Zone"]:
        await on_join_david_zone(member, before, after)
    else:
        raise ValueError("Zone name doesn't match warp zone name")

# sends the user to a random zone
async def on_join_roll_the_zone(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    random_zone = random.choice(zones)
    await member.move_to(random_zone)

# sends the user to the first most populated zone
async def on_join_party_zone(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    largest_zone = zones[0]
    for zone in zones:
        if len(zone.members) > len(largest_zone.members):
            largest_zone = zone
    await member.move_to(largest_zone)

# sends the users down the zones 1 by 1 until they hit a populated zone
# rate limit is about 1/sec and it takes about 0.2-0.3 secs to move, so 0.8 doens't really rate limit
async def on_join_david_zone(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    for i in range(len(zones)):
        time.sleep(0.8) # get second opinion on initial pause or not
        if len(zones[i].members) > 0:
            await member.move_to(zones[i])
            break
        else:
            await member.move_to(zones[i])

with open("token.txt", "r") as token_file:
    client.run(token_file.read())