from Match import Match
from shutil import rmtree


class MatchManager:
    def __init__(self, bot, sources):
        self.matches = {}
        self.bot = bot
        self.sources = sources
        self.stats = {}

    def can_create_match(self, channel_id):
        channel = self.bot.get_channel(channel_id)
        if not channel.is_nsfw():
            return False
        if channel_id in self.matches.keys():
            return False
        return True

    def create_match(self, channel_id, category, players):
        match = Match(self, self.bot, self.sources, channel_id, category, players)
        self.matches[channel_id] = match
        return match

    def end_match(self, match: Match):
        self.matches.pop(match.channel_id)
        rmtree('./cache/{}'.format(match.channel_id))

    async def add_vote(self, channel_id, message_id, player, emoji):
        if channel_id not in self.matches.keys() or emoji not in ['1️⃣', '2️⃣'] or message_id != self.matches[channel_id].image_message.id or player.name not in self.matches[channel_id].players:
            return
        await self.matches[channel_id].add_vote(player, emoji)
