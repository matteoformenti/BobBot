from discord.ext.commands.bot import Bot
from PIL import Image
import requests
import discord
import random
import os


class Match:
    def __init__(self, match_manager, bot: Bot, sources, channel_id, category, players):
        self.bot = bot
        self.sources = sources
        self.channel_id = channel_id
        self.category = category
        self.players = players
        self.images = []
        self.votes = {}
        self.winning_image = None
        self.opposing_image = None
        self.image_message = None
        self.current_round = 1
        self.match_manager = match_manager

    @staticmethod
    def valid_image(filename):
        for ext in ['jpg', 'jpeg', 'webp']:
            if filename.endswith(ext):
                return True
        return False

    async def start(self):
        for player in self.players:
            self.votes[player] = 0
        subreddits = '+'.join(self.sources[self.category])
        message = await self.bot.get_channel(self.channel_id).send('Preparing match...')
        response = requests.get(f'https://reddit.com/r/{subreddits.rstrip()}.json?limit=100&t=year', headers={'User-Agent': 'discord bot NSFW tournament'})
        if response.status_code != 200:
            return
        response = response.json()
        if not os.path.exists('./cache/{}'.format(self.channel_id)):
            os.makedirs('./cache/{}'.format(self.channel_id))
        for post in response['data']['children']:
            if len(self.images) >= 15:
                break
            if 'url' in post['data'].keys() and Match.valid_image(post['data']['url']):
                image = {
                    'id': post['data']['id'],
                    'subreddit': post['data']['subreddit'],
                    'title': post['data']['title'],
                    'author': post['data']['author'],
                    'url': post['data']['url'],
                    'filename': './cache/{}/{}'.format(self.channel_id, os.path.basename(post['data']['url'].rstrip()))
                }
                image_data = requests.get(post['data']['url'].rstrip(), headers={'User-Agent': 'discord bot NSFW tournament'}).content
                image_handle = open(image['filename'], 'wb')
                image_handle.write(image_data)
                image_handle.close()
                self.images.append(image)
                await message.edit(content='Downloaded image {}/15'.format(len(self.images)))
        self.winning_image = self.images.pop(0)
        self.opposing_image = self.images.pop(0)
        await message.delete()
        await self.round()

    async def round(self):
        for player in self.players:
            self.votes[player] = 0
        text = '**ROUND {}**\nr/{}: {}\nr/{}: *{}*'.format(self.current_round, self.winning_image['subreddit'], self.winning_image['title'], self.opposing_image['subreddit'], self.opposing_image['title'])
        file = discord.File(self.merge(self.winning_image, self.opposing_image))
        if self.image_message is not None:
            await self.image_message.delete()
        self.image_message = await self.bot.get_channel(self.channel_id).send(content=text, file=file)
        await self.image_message.clear_reactions()
        await self.image_message.add_reaction('1️⃣')
        await self.image_message.add_reaction('2️⃣')

    async def add_vote(self, player, emoji):
        if self.votes[player.name] == 0:
            if emoji == '1️⃣':
                self.votes[player.name] = 1
            if emoji == '2️⃣':
                self.votes[player.name] = 2
        for player in self.votes.keys():
            if self.votes[player] == 0:
                return
        return await self.end_round()

    async def end_round(self):
        votes_1 = 0
        votes_2 = 0
        self.current_round = self.current_round + 1
        for player in self.votes.keys():
            if self.votes[player] == 1:
                votes_1 = votes_1 + 1
            if self.votes[player] == 2:
                votes_2 = votes_2 + 1
        while votes_1 == votes_2:
            votes_1 = random.randint(0, 10)
            votes_2 = random.randint(0, 10)
        if len(self.images) == 0:
            if votes_1 < votes_2:
                self.winning_image = self.opposing_image
            return await self.end_match()
        else:
            if votes_1 > votes_2:
                self.opposing_image = self.images.pop(0)
            else:
                self.winning_image = self.opposing_image
                self.opposing_image = self.images.pop(0)
            return await self.round()

    async def end_match(self):
        await self.image_message.delete()
        text = '**WINNING IMAGE**\n{}\nr/{} *u/{}*'.format(self.winning_image['title'], self.winning_image['subreddit'], self.opposing_image['author'])
        file = discord.File(self.winning_image['filename'])
        await self.bot.get_channel(self.channel_id).send(content=text, file=file)
        return self.match_manager.end_match(self)

    def merge(self, img1, img2):
        img1 = Image.open(img1['filename']).convert('RGBA')
        img2 = Image.open(img2['filename']).convert('RGBA')
        height = 600
        ratio_img1 = img1.size[0] / img1.size[1]
        ratio_img2 = img2.size[0] / img2.size[1]
        img1 = img1.resize((int(height * ratio_img1), height))
        img2 = img2.resize((int(height * ratio_img2), height))
        final_image = Image.new('RGBA', (img1.size[0] + img2.size[0] + 10, height))
        final_image.paste(im=img1, box=(0, 0))
        final_image.paste(im=img2, box=(img1.size[0] + 10, 0))
        path = './cache/{}/temp.png'.format(self.channel_id)
        if os.path.exists(path):
            os.remove(path)
        final_image.save(path)
        return path
