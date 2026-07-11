from pathlib import Path
from typing import Dict, List

from src.utils import read_json, write_json


class RetweetTracker:
    def __init__(self, history_path: str):
        self.history_path = Path(history_path)
        self.data = read_json(self.history_path, {"retweets": {}})
        self.data.setdefault("retweets", {})

    def has_retweeted(self, retweeter_name: str, tweet_id: str) -> bool:
        return tweet_id in self.data["retweets"].get(retweeter_name, [])

    def mark_retweeted(self, retweeter_name: str, tweet_id: str) -> None:
        self.data["retweets"].setdefault(retweeter_name, [])
        if tweet_id not in self.data["retweets"][retweeter_name]:
            self.data["retweets"][retweeter_name].append(tweet_id)
            self.save()

    def get_retweeted_ids(self, retweeter_name: str) -> List[str]:
        return list(self.data["retweets"].get(retweeter_name, []))

    def save(self) -> None:
        write_json(self.history_path, self.data)
