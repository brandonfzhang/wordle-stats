from discord.ext import commands
import discord
import os
import re

token = []
with open('token.txt') as f:
    token = f.readlines()

intents = discord.Intents.all()
prefix = '!'
bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)
bot.players = {}
bot.scraping = False
bot.blacklist = set()
with open('blacklist.txt') as f:
  blacklist_ids = f.readlines()
  for id in blacklist_ids:
    bot.blacklist.add(int(id))

async def process_message(message, react=False):
  if re.search("Wordle ... ./6\n\n.+", message.content):
    if message.author.id in bot.blacklist:
      if react:
        await message.add_reaction('❌')
      return

    split_message = message.content.split()
    number = split_message[1]
    tries = split_message[2][0]
    if tries < '1' or tries > '6':
      tries = 7
    else:
      tries = int(tries)

    lines = message.content.splitlines()
    #check legitimacy
    if tries == 7:
      if len(lines) != 8:
        return
      for i in range(-1, -tries-1, -1):
        if lines[i] == "🟩🟩🟩🟩🟩":
          return
        for char in lines[i]:
          if char != "🟨" and char != "⬛" and char != "⬜" and char != "🟩":
            return
    else:
      if len(lines) != tries+2 or lines[-1] != "🟩🟩🟩🟩🟩":
        return
      for i in range(-2, -tries-1, -1):
        if lines[i] == "🟩🟩🟩🟩🟩":
          return
        for char in lines[i]:
          if char != "🟨" and char != "⬛" and char != "⬜" and char != "🟩":
            return

    if not message.author.id in bot.players.keys():
      bot.players[message.author.id] = ([0,0,0,0,0,0,0,0], set())
      #0th index is total, 7th index is fails
    if not number in bot.players[message.author.id][1]:
      bot.players[message.author.id][0][tries] += 1
      bot.players[message.author.id][0][0] += 1
      bot.players[message.author.id][1].add(number)
    if react:
      await message.add_reaction('✅')

@bot.event
async def on_ready():
  bot.scraping = True
  wordle_channel = bot.get_channel(token[1])
  async for message in wordle_channel.history(limit=100000):
    await process_message(message)
  bot.scraping = False

@bot.command()
async def help(ctx, *args):
  if len(args) == 0:
    embed=discord.Embed(title="Help", description="**" + prefix + "help** - shows this message\n**" + prefix + "stats** - shows a user's Wordle statistics\n**" + prefix + "leaderboard** - shows the leaderboard based on a certain metric", color=0x78a968)
    await ctx.reply(embed=embed)
  elif len(args) == 1:
    if args[0] == 'help' or args[0] == prefix + 'help':
      embed=discord.Embed(title="Help - " + prefix + "help", description="**Usage:** " + prefix + "help <optional command name>\n**Description:** Sends this help message", color=0x78a968)
      await ctx.reply(embed=embed)
    elif args[0] == 'stats' or args[0] == prefix + 'stats':
      embed=discord.Embed(title="Help - " + prefix + "stats", description="**Usage:** " + prefix + "stats <optional user ping or user id>\n**Description:** Shows the specified user's Wordle statistics. If no user is provided, the sender is used.", color=0x78a968)
      await ctx.reply(embed=embed)
    elif args[0] == 'leaderboard' or args[0] == prefix + 'leaderboard':
      embed=discord.Embed(title="Help - " + prefix + "leaderboard", description="**Usage:** " + prefix + "leaderboard <mean/total/std>\n**Description:** Shows the leaderboard ordered based on the specified statistic. If no statistic is provided, the mean score is assumed.", color=0x78a968)
      await ctx.reply(embed=embed)
    else:
      await ctx.reply("This command follows the following format:\n`" + prefix + "help <optional command name>`")
  else:
    await ctx.reply("This command follows the following format:\n`" + prefix + "help <optional command name>`")

@bot.command()
async def stats(ctx, *args):
  if bot.scraping == True:
    await ctx.reply("Wait until the bot is finished scraping messages first")
    return

  if len(args) == 0:
    if ctx.author.id in bot.blacklist:
      await ctx.reply(the_user.name + "#" + the_user.discriminator + " has been blacklisted")
      return

    if ctx.author.id in bot.players.keys():
      player_stats = bot.players[ctx.author.id][0]
  
      mean = 0.0
      for i in range(1,8):
        mean += i * player_stats[i] / player_stats[0]
  
      esquared = 0.0
      for i in range(1,8):
        esquared += i**2 * player_stats[i] / player_stats[0]
      std = (esquared - mean**2)**0.5
      
      embed=discord.Embed(title="Wordle Stats", description="*Fails are counted as a score of 7 in the calculations*\n\n**Total Games** - " + str(player_stats[0]) + "\n\n**1** - " + str(player_stats[1]) + " (" + str(round(player_stats[1]/player_stats[0]*100,2)) + "%)\n**2** - " + str(player_stats[2]) + " (" + str(round(player_stats[2]/player_stats[0]*100,2)) + "%)\n**3** - " + str(player_stats[3]) + " (" + str(round(player_stats[3]/player_stats[0]*100,2)) + "%)\n**4** - " + str(player_stats[4]) + " (" + str(round(player_stats[4]/player_stats[0]*100,2)) + "%)\n**5** - " + str(player_stats[5]) + " (" + str(round(player_stats[5]/player_stats[0]*100,2)) + "%)\n**6** - " + str(player_stats[6]) + " (" + str(round(player_stats[6]/player_stats[0]*100,2)) + "%)\n**X** - " + str(player_stats[7]) + " (" + str(round(player_stats[7]/player_stats[0]*100,2)) + "%)\n\n**Mean:** " + str(round(mean,2)) + "\n**Standard Deviation:** " + str(round(std,2)), color=0x78a968)
      embed.set_author(name=ctx.author.name + "#" + ctx.author.discriminator, icon_url=ctx.author.avatar.url)
      await ctx.reply(embed=embed)
    else:
      await ctx.reply(ctx.author.name + "#" + ctx.author.discriminator + " has never shared their Wordle scores.")
  elif len(args) == 1:
    id = args[0]
    
    try:
      if args[0][0] == '<' and args[0][1] == '@' and args[0][-1] == '>':
        id = id[2:-1]
      id = int(id)
    except:
      await ctx.reply("This command follows the following format:\n`" + prefix + "stats <optional user ping or user id>`")
      return

    the_user = ctx.guild.get_member(id)
    if the_user is None:
      await ctx.reply("This command follows the following format:\n`" + prefix + "stats <optional user ping or user id>`")
      return

    if id in bot.blacklist:
      await ctx.reply(the_user.name + "#" + the_user.discriminator + " has been blacklisted")
      return

    if id in bot.players.keys():
      player_stats = bot.players[id][0]
  
      mean = 0.0
      for i in range(1,8):
        mean += i * player_stats[i] / player_stats[0]
  
      esquared = 0.0
      for i in range(1,8):
        esquared += i**2 * player_stats[i] / player_stats[0]
      std = (esquared - mean**2)**0.5
      
      embed=discord.Embed(title="Wordle Stats", description="*Fails are counted as a score of 7 in the calculations*\n\n**Total Games** - " + str(player_stats[0]) + "\n\n**1** - " + str(player_stats[1]) + " (" + str(round(player_stats[1]/player_stats[0]*100,2)) + "%)\n**2** - " + str(player_stats[2]) + " (" + str(round(player_stats[2]/player_stats[0]*100,2)) + "%)\n**3** - " + str(player_stats[3]) + " (" + str(round(player_stats[3]/player_stats[0]*100,2)) + "%)\n**4** - " + str(player_stats[4]) + " (" + str(round(player_stats[4]/player_stats[0]*100,2)) + "%)\n**5** - " + str(player_stats[5]) + " (" + str(round(player_stats[5]/player_stats[0]*100,2)) + "%)\n**6** - " + str(player_stats[6]) + " (" + str(round(player_stats[6]/player_stats[0]*100,2)) + "%)\n**X** - " + str(player_stats[7]) + " (" + str(round(player_stats[7]/player_stats[0]*100,2)) + "%)\n\n**Mean:** " + str(round(mean,2)) + "\n**Standard Deviation:** " + str(round(std,2)), color=0x78a968)
      embed.set_author(name=the_user.name + "#" + the_user.discriminator, icon_url=the_user.avatar.url)
      await ctx.reply(embed=embed)
    else:
      await ctx.reply(the_user.name + "#" + the_user.discriminator + " has never shared their Wordle scores.")
  else:
      await ctx.reply("This command follows the following format:\n`" + prefix + "stats <optional user ping or user id>`")

@bot.command()
async def leaderboard(ctx, *args):
  if bot.scraping == True:
    await ctx.reply("Wait until the bot is finished scraping messages first")
    return

  if len(bot.players.items()) == 0:
    await ctx.reply("No one has submitted their Wordle scores yet.")
    return

  async def mean_leaderboard():
    ids_with_means = []
    for pair in bot.players.items():
      mean = 0.0
      for i in range(1,8):
        mean += i * pair[1][0][i] / pair[1][0][0]
      ids_with_means.append((pair[0], mean))

    ids_with_means.sort(key=lambda x:x[1])
    print(ids_with_means)

    description = "*Fails are counted as a score of 7 in the calculations*\n\n"

    for i, pair in enumerate(ids_with_means):
      the_user = ctx.guild.get_member(pair[0])
      description += "**" + str(i+1) + ": " + the_user.name + "#" + the_user.discriminator + "** (" + str(round(pair[1],2)) + ")\n"
    
    embed=discord.Embed(title="Leaderboard (based on mean score)", description=description, color=0x78a968)
    await ctx.reply(embed=embed)
  
  if len(args) == 0:
    await mean_leaderboard()
  elif len(args) == 1:
    if args[0] == "mean":
      await mean_leaderboard()
    elif args[0] == "total":
      ids_with_means = []
      for pair in bot.players.items():
        ids_with_means.append((pair[0], pair[1][0][0]))

      ids_with_means.sort(key=lambda x:x[1], reverse=True)
      print(ids_with_means)

      description = "*Fails are counted as a score of 7 in the calculations*\n\n"

      for i, pair in enumerate(ids_with_means):
        the_user = ctx.guild.get_member(pair[0])
        description += "**" + str(i+1) + ": " + the_user.name + "#" + the_user.discriminator + "** (" + str(round(pair[1],2)) + ")\n"
      
      embed=discord.Embed(title="Leaderboard (based on total games played)", description=description, color=0x78a968)
      await ctx.reply(embed=embed)
    elif args[0] == "std":
      ids_with_means = []
      for pair in bot.players.items():
        mean = 0.0
        for i in range(1,8):
          mean += i * pair[1][0][i] / pair[1][0][0]
    
        esquared = 0.0
        for i in range(1,8):
          esquared += i**2 * pair[1][i] / pair[1][0]
        std = (esquared - mean**2)**0.5
        ids_with_means.append((pair[0], std))

      ids_with_means.sort(key=lambda x:x[1])
      print(ids_with_means)

      description = "*Fails are counted as a score of 7 in the calculations*\n\n"

      for i, pair in enumerate(ids_with_means):
        the_user = ctx.guild.get_member(pair[0])
        description += "**" + str(i+1) + ": " + the_user.name + "#" + the_user.discriminator + "** (" + str(round(pair[1],2)) + ")\n"
      
      embed=discord.Embed(title="Leaderboard (based on standard deviation of score)", description=description, color=0x78a968)
      await ctx.reply(embed=embed)
    else:
      await ctx.reply("This command follows the following format:\n`" + prefix + "leaderboard <mean/total/std>`")
  else:
    await ctx.reply("This command follows the following format:\n`" + prefix + "leaderboard <mean/total/std>`")

@bot.event
async def on_message(message):
  await bot.process_commands(message)
  if re.search("Wordle ... ./6\n\n.+", message.content):
    await process_message(message, react=True)

password = token[0]
bot.run(password)
