import discord
import json
import random as rnd
import os
from io import BytesIO
from copy import deepcopy

bot = discord.Bot(activity=discord.Game(name='Loading...'),status=discord.Status.dnd)

print("Loading token")
token_file = open('token.json')
token_file_data = json.load(token_file)
ownerid = token_file_data["owner_id"]
token = token_file_data["token"]
token_file.close()

print("Loading channel data")
channel_data = dict()
if os.path.exists("channels.json"):
	channel_file = open('channels.json')
	channel_data = json.load(channel_file)
	channel_file.close()

num_to_die = {
	1: "1️⃣",
	2: "2️⃣",
	3: "3️⃣",
	4: "4️⃣",
	5: "5️⃣",
	6: "6️⃣"
}

async def response_with_file_fallback(ctx: discord.ApplicationContext,message,eph=False):
	if len(message) > 2000:
		filedata = BytesIO(message.encode('utf-8'))
		await ctx.respond("The message is too long to send. Please view the attached file.",file=discord.File(filedata,filename='response.md'),ephemeral=eph)
		print(f"Sent response to /{ctx.command.qualified_name} as file")
	else:
		await ctx.respond(message,ephemeral=eph)

def save_channel_data():
	with open('channels.json','w') as outfile:
		outfile.write(json.dumps(channel_data))
	print("Saved channel data.")

def cid(ctx: discord.ApplicationContext):
	return str(ctx.channel_id)

def d6():
	return rnd.randint(1,6)

def drop():
	value = d6()
	if value == 6:
		return ("Health",value)
	elif value >= 3:
		return ("Fuel",value)
	else:
		return ("No drop",value)

@bot.event
async def on_ready():
	await bot.change_presence(activity=discord.Game(name='NOVA'),status=discord.Status.online)
	print(f"{bot.user} is ready and online in {len(bot.guilds)} guilds!")

@bot.event
async def on_application_command(ctx):
	args = []
	if ctx.selected_options is not None:
		for argument in ctx.selected_options:
			args.append(f"{argument['name']}:{argument['value']}")
	args = ' '.join(args)
	if len(args) > 0:
		print(f"/{ctx.command.qualified_name} {args}")
	else:
		print(f"/{ctx.command.qualified_name}")

@bot.command(description="Add drops to the drop pool in this channel.")
async def add_drops(ctx, amount: discord.Option(discord.SlashCommandOptionType.integer, "The number of drops to add (or remove, if negative).", required=False, default=1)):
	if amount == 0:
		await ctx.respond("You cannot add 0 drops to the pool.",ephemeral=True)
		return

	c = cid(ctx)

	if amount < 0 and channel_data.get(c,0) <= 0:
		await ctx.respond("There are no drops in the pool to remove.",ephemeral=True)
		return
	
	await ctx.defer()
	
	channel_data[c] = channel_data.get(c,0) + amount
	
	message = ""
	if amount > 1:
		message = f"📥 Added **{amount} drops** to the drop pool."
	elif amount == 1:
		message = f"📥 Added **{amount} drop** to the drop pool."
	elif amount == -1:
		message = f"📤 Removed **{abs(amount)} drop** from the drop pool."
	else:
		message = f"📤 Removed **{abs(amount)} drops** from the drop pool."

	if channel_data.get(c,0) <= 0:
		del channel_data[c]
	
	total = channel_data.get(c,0)
	if total != 1:
		message += f"\n-# There are now **{total} drops** in the pool."
	else:
		message += f"\n-# There is now **{total} drop** in the pool."
	
	await ctx.respond(message)
	save_channel_data()

@bot.command(description="Remove drops from the drop pool in this channel.")
async def remove_drops(ctx, amount: discord.Option(discord.SlashCommandOptionType.integer, "The number of drops to remove (or add, if negative).", required=False, default=1)):
	return await add_drops(ctx,amount*-1)

@bot.command(description="Rolls all drops and clears the pool.")
async def generate_drops(ctx):
	c = cid(ctx)
	amount = channel_data.get(c,0)

	if amount <= 0:
		await ctx.respond("There are no drops in the pool.",ephemeral=True)
		return
	
	await ctx.defer()

	drops = {}

	message = ""

	for i in range(amount):
		type,val = drop()
		drops[type] = drops.get(type,0) + 1
		message += num_to_die[val]
	
	message += "\n## Totals"
	for key in sorted(list(drops.keys())):
		message += f"\n- {key}: {drops[key]}"
	
	message += "\n-# The Sparks should decide who wants the drops generated this round.\n-# Any drops that aren't claimed disappear."

	await response_with_file_fallback(ctx,message)

	del channel_data[c]
	save_channel_data()

@bot.command(description="Shows the help info for this bot.")
async def help(ctx):
	await ctx.defer()
	
	message = "# Commands"
	for cmd in bot.application_commands:
		message += f"\n- {cmd.mention}: {cmd.description}"
	
	await ctx.respond(message)

@bot.command(description="Shuts down the bot. Will not work unless you own the bot.")
async def shutdown(ctx):
	if ctx.author.id == ownerid:
		print(f"Shutdown request accepted ({ctx.author.id})")
		await ctx.defer()
		await save_channel_data()
		await ctx.respond(f"Restarting.")
		await bot.close()
	else:
		print(f"Shutdown request denied ({ctx.author.id})")
		await ctx.respond(f"Only <@{ownerid}> may use this command.",ephemeral=True)

print("Starting bot session")
bot.run(token)