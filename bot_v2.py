from MatchManager import MatchManager
from discord.ext import commands
import discord
import json
import os

with open('./sources.json') as f:
    sources = json.load(f)
bot = commands.Bot(command_prefix='-', intents=discord.Intents().all())
match_manager = MatchManager(bot, sources)


@bot.event
async def on_ready():
    print('Bobsbot Ready!')


@bot.command()
async def start(ctx, *, arguments):
    global match_manager
    arguments = arguments.split(' ')
    if len(arguments) < 2:
        return await ctx.send('In order to start a new match you have to provide a category and at least one user')
    if not match_manager.can_create_match(ctx.channel.id):
        return await ctx.send('Unable to create a new match in this channel')
    category = arguments.pop(0)
    if category not in sources.keys():
        return await ctx.send(f'Category not found, valid categories are {list(sources.keys())}')
    channel_players = list(map(lambda x: x.name, ctx.channel.members))
    online_players = list(map(lambda x: x.name, [p for p in ctx.channel.members if p.status != discord.Status.offline]))
    for player in arguments:
        if player not in channel_players:
            return await ctx.send(f'Player {player} isn\'t in the channel')
        if player not in online_players:
            return await ctx.send(f'Player {player} is offline')
    match = match_manager.create_match(ctx.channel.id, category, arguments)
    await match.start()


@bot.command()
async def categories(ctx):
    global sources
    await ctx.send('Available categories: {}'.format(', '.join(list(sources.keys()))))


@bot.event
async def on_reaction_add(reaction, user):
    await match_manager.add_vote(reaction.message.channel.id, reaction.message.id, user, reaction.emoji)


bot.run(os.environ.get('TOKEN'))
