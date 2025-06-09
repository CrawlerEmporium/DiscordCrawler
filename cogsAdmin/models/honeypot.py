class Honeypot:
    def __init__(self, guildId: int, channelId):
        self.guildId = guildId
        self.channelId = channelId

    @classmethod
    def from_data(cls, data):
        return cls(data['guildId'], data['channelId'])

    def to_dict(self):
        return {
            'guildId': self.guildId,
            'channelId': self.channelId
        }
