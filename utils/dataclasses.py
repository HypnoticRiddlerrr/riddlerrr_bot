from dataclasses import dataclass

from twitchio import Channel


@dataclass
class ChannelInfo:
    channel_name: str
    channel: Channel | None = None
    channel_id: int | None = None


@dataclass
class CoinflipPrediction:
    prediction_id: str
    heads_id: str
    tails_id: str
