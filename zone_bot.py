# zone_bot.py

# TODO track name changes using on_guild_channel_update event

import random
import time
import re

import discord
import discord.app_commands as app_commands

SERVER_ID = 633788616765603870
DEV_ID = 297941435284455444
LIMBO_ROLE_ID = 1147308877466042408
LIMBO_ZONE_ZONE_ID = 1147318332379373569
LIMBO_ZONE_ID = 1147323168013426779

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
guild: discord.Guild = None
tree = app_commands.CommandTree(client)
dev: discord.Member = None
limbo_role: discord.Role = None

zone_fields: list[discord.CategoryChannel] = None
zones: list[discord.VoiceChannel] = None
warp_zones: dict[str, discord.VoiceChannel] = None

# set the globals that contain the various zones
@client.event
async def on_ready():
    global guild, zones, warp_zones, dev, limbo_role, zone_fields
    
    # load zone data
    guild = client.get_guild(SERVER_ID)
    zone_fields = get_zone_fields()
    zones = get_zones()
    warp_zones = get_warp_zones()

    # load limbo vars
    dev = guild.get_member(DEV_ID)
    limbo_role = guild.get_role(LIMBO_ROLE_ID)

    # sync slash commands
    await tree.sync(guild = discord.Object(id = SERVER_ID))

    # send log in message
    print(f"Logged in as {client.user}")

# give info on the use of each zone in the warp zone
@tree.command(name = "warp_zones", guild = discord.Object(id = SERVER_ID))
async def command_warp_zones(interaction: discord.Interaction):
    await interaction.response.send_message("temp")

# add a new zone, creating a zone field if there are more than 50 zones in the zone field
@tree.command(name = "addzone", guild = discord.Object(id = SERVER_ID))
async def command_add_zone(interaction: discord.Interaction, zone: str):
    # await interaction.response.send_message("temp", ephemeral=True)
    # await interaction.response.defer(ephemeral = True, thinking = False)
    if user_has_manage_channels(interaction.user) or interaction.user.id == DEV_ID:
        zone_position = await add_zone(zone)
        zone_field_name = zone_fields[zone_position[0] - 1]
        await interaction.response.send_message(f"Added '{zone}' in {zone_field_name} at position {zone_position[1]}", ephemeral = False)
    else:
        await interaction.response.send_message("L bozo", ephemeral = False)

# actual function to add a zone given a name
# returns the position of the zone as (zone field, zone position)
async def add_zone(zone: str):
    # add a new zone field 
    last_zone_field = zone_fields[-1]
    if len(zone_fields[-1].channels) >= 50:
        next_category_ordinal = title_case(get_ordinal(len(zone_fields) + 1))

        # clone the first zone zone for proper perms and change name and position
        temp_zone_field = await zone_fields[0].clone(name = f"The {next_category_ordinal} Zone Zone")
        await temp_zone_field.edit(position = zone_fields[-1].position + 1)

        # append it to the zone fields array
        last_zone_field = temp_zone_field
        zone_fields.append(last_zone_field)
    
    # create the new zone
    new_zone = await guild.create_voice_channel(name = zone, category = last_zone_field)

    return (len(zone_fields), new_zone.position + 1)

# converts the input num into the english version of the ordinal
# ex: 1 -> first, 2 -> second, 23 -> twenty third
# goes up to 99 because I cant bother to go higher
def get_ordinal(num: int):
    # if the number is invalid
    if type(num) != int or num > 99 or num < 1:
        raise ValueError(f"Ordinal {num} is invalid")

    ones_digit = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth"]
    tens_digit_mod = ["twenty", "thirty", "fourty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    tens_digit = ["tenth"] + list(map(lambda s: s[:-1] + "ieth", tens_digit_mod))
    tens = ["eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth"]

    # first ten just use the ones digit
    # 11 - 19 use the tens array
    if 0 <= num < 10:
        return ones_digit[num - 1]
    elif 10 < num < 20:
        return tens[num - 11]
    
    # if its a multiple of ten, it is special, otherwise, append ones_digit to tens_digit_mod
    if num % 10 == 0:
        return tens_digit[(num // 10) - 1]
    else:
        return tens_digit_mod[(num // 10) - 2] + "-" + ones_digit[(num % 10) - 1]
    
# capitalizes the first letter of every word in a string and lowercases the rest
def title_case(s: str):
    def replace(match):
        matched_str = match.group()
        return matched_str[0].upper() + matched_str[1:].lower()

    return re.sub("\w+", replace, s)

# checks if a user is an admin on the server
def user_is_admin(user: discord.Member):
    # check if user is guild owner
    if user.id == guild.owner_id:
        return True
    
    # check if user has administrator role
    for role in user.roles:
        if role.permissions.administrator:
            return True
    return False

# checks if a user has the ability to manage channels
def user_has_manage_channels(user: discord.Member):
    # both users with manage channels, as well as admins should be able to use this
    if user_is_admin(user):
        return True
    
    # check if user has the specific manage channel perm
    for role in user.roles:
        if role.permissions.manage_channels:
            return True
    return False

# add limbo role to dev
@tree.command(name = "l", guild = discord.Object(id = SERVER_ID))
async def add_limbo_role(interaction: discord.Interaction):
    if interaction.user.id == DEV_ID:
        await dev.add_roles(guild.get_role(LIMBO_ROLE_ID))
        await interaction.response.send_message("Limbo role added", ephemeral = True)
    else:
        await interaction.response.send_message("Dev command only", ephemeral = True)

# remove limbo role from dev
@tree.command(name = "nl", guild = discord.Object(id = SERVER_ID))
async def remove_limbo_role(interaction: discord.Interaction):
    if interaction.user.id == DEV_ID:
        await dev.remove_roles(guild.get_role(LIMBO_ROLE_ID))
        await interaction.response.send_message("Limbo role removed", ephemeral = True)
    else:
        await interaction.response.send_message("Dev command only", ephemeral = True)

# @tree.command(name='test', guild = discord.Object(id = SERVER_ID), )
# @app_commands.describe(option="The name of the zone")
# (name=[
#         app_commands.Choice(name="Option 1", value="1"),
#         app_commands.Choice(name="Option 2", value="2")
#     ])
# async def test(interaction: discord.Interaction, option: app_commands.Choice[str]):
#     pass

# get a list of the warp zones as VoiceChannel objects
def get_warp_zones() -> dict[str, discord.VoiceChannel]:
    zone_fields = guild.categories
    warp_field = list(filter(lambda cat: cat.name.upper() == "THE WARP ZONE", zone_fields))[0]
    warp_zones = warp_field.channels

    return {zone.name: zone for zone in warp_zones}

# get a list of the zones as VoiceChannel objects
def get_zones() -> list[discord.VoiceChannel]:
    zone_fields = guild.categories
    zone_fields = list(filter(
        lambda cat: cat.name.upper().find("ZONE ZONE") >= 0 and cat.name.upper().find("LIMBO") < 0, 
        zone_fields
    ))

    zones = []
    for field in zone_fields:
        zones.extend(field.channels)

    return zones

# get a list of all the zone fields
def get_zone_fields() -> list[discord.CategoryChannel]:
    zone_fields = guild.categories
    zone_fields = list(filter(
        lambda cat: cat.name.upper().find("ZONE ZONE") >= 0 and cat.name.upper().find("LIMBO") < 0, 
        zone_fields
    ))
    return zone_fields

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # remove limbo role on any voice state change
    if member.roles.count(limbo_role) > 0:
        await member.remove_roles(guild.get_role(LIMBO_ROLE_ID))

    # return if user leaves call
    if after == None or after.channel == None:
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
        await on_join_coop_zone(member, before, after)
    elif after.channel == warp_zones["The No Zone"]:
        await on_join_no_zone(member, before, after)
    elif after.channel == warp_zones["The David Zone"]:
        await on_join_david_zone(member, before, after)
    else:
        raise ValueError("Zone name doesn't match warp zone name")

# sends the user to a random zone
async def on_join_roll_the_zone(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # roll a d20 to send the user to limbo
    if random.randint(1, 20) == 20:
        await dev.add_roles(guild.get_role(LIMBO_ROLE_ID))
        await member.move_to(guild.get_channel(LIMBO_ZONE_ID))
    else:
        random_zone = random.choice(zones)
        await member.move_to(random_zone)

# sends the user to the first most populated zone
# if no zone is populated, send the user to the no zone
async def on_join_party_zone(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    largest_zone = zones[0]
    for zone in zones:
        if len(zone.members) > len(largest_zone.members):
            largest_zone = zone

    if len(largest_zone.members) > 0:
        await member.move_to(largest_zone)
    else:
        await member.move_to(warp_zones["The No Zone"])

# sends the user to a zone with 1 person in it
# if there are no zones with a single person in them, send the user to the no zone
async def on_join_coop_zone(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    for zone in zones:
        if len(zone.members) == 1:
            await member.move_to(zone)
            return
    else:
        await member.move_to(warp_zones["The No Zone"])

# sends the user to a random zone that isn't populated
async def on_join_no_zone(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    no_zones = list(filter(lambda z: len(z.members) == 0, zones))
    random_no_zone = random.choice(no_zones)
    await member.move_to(random_no_zone)

# sends the users down the zones 1 by 1 until they hit a populated zone
# rate limit is about 1/sec and it takes about 0.2-0.3 secs to move, so 0.8 doens't really rate limit
async def on_join_david_zone(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # stop if the user disconnects in the middle of the move
    try:
        for i in range(len(zones)):
            time.sleep(0.8) # get second opinion on initial pause or not
            if len(zones[i].members) > 0:
                await member.move_to(zones[i])
                break
            else:
                await member.move_to(zones[i])
    except discord.errors.HTTPException as e:
        pass

# run the bot with the token specified in token.txt
with open("token.txt", "r") as token_file:
    client.run(token_file.read())