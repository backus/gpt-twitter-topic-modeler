import os
import pathlib
import json
from hashlib import md5
import pathlib
import logging
import argparse

from dotenv import load_dotenv
import tweepy
import openai
import tiktoken


class TweetScraper:
    def __init__(self, api, data_dir, username):
        self.api = api
        self.data_dir = pathlib.Path(data_dir) / 'tweets' / username
        self.username = username

        self.logger = logging.getLogger('TweetScraper')
        self.logger.handlers.clear()
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def all_tweets(self):
        user = self.api.get_user(screen_name=self.username)
        user_id = user.id_str

        max_id = None
        all_tweets = []

        while True:
            tweets = self.__download_tweets(user_id, max_id)
            if not tweets:
                break
            all_tweets.extend(tweets)
            max_id = tweets[-1]['id'] - 1

        self.logger.info(f'Downloaded a total of {len(all_tweets)} tweets.')
        return all_tweets

    def __get_cache_filename(self, user_id, max_id):
        hash_input = f'{user_id}-{max_id}' if max_id else f'{user_id}-None'
        cache_key = md5(hash_input.encode('utf-8')).hexdigest()
        prefix = f'{max_id}' if max_id else 'start'
        return self.data_dir / f'{prefix}-{cache_key}.json'

    def __save_tweets_to_file(self, tweets, filepath):
        filepath.write_text(json.dumps([tweet._json for tweet in tweets]))

    def __download_tweets(self, user_id, max_id=None):
        cache_file = self.__get_cache_filename(user_id, max_id)
        if cache_file.exists():
            self.logger.debug(f'Loading tweets from cache: {cache_file}')
            return json.loads(cache_file.read_text())
        else:
            self.logger.info(f'Downloading tweets (max_id: {max_id})')
            tweets = tweepy.Cursor(self.api.user_timeline, user_id=user_id,
                                   max_id=max_id, tweet_mode='extended').items(200)
            tweets = list(tweets)
            self.__save_tweets_to_file(tweets, cache_file)
            return [tweet._json for tweet in tweets]


class CLI:
    PROJECT_ROOT = pathlib.Path(__file__).parent

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            '--data-dir', type=str, default=str(CLI.PROJECT_ROOT / 'data'))
        self.parser.add_argument('--username', type=str, required=True)
        self.parser.add_argument(
            '--openai-model', type=str, default=GPTTopicModel.DEFAULT_MODEL)

    def parse_args(self):
        args = self.parser.parse_args()
        return {
            "data_dir": pathlib.Path(args.data_dir),
            "username": args.username,
            "openai_model": args.openai_model
        }


class Bootstrap:
    def __init__(self):
        load_dotenv()

        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.twitter_consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
        self.twitter_consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
        self.twitter_token = os.getenv("TWITTER_TOKEN")
        self.twitter_secret = os.getenv("TWITTER_SECRET")

    def setup_openai(self):
        openai.api_key = self.openai_api_key

    def twitter_client(self):
        twitter_auth = tweepy.OAuthHandler(
            self.twitter_consumer_key, self.twitter_consumer_secret)
        twitter_auth.set_access_token(self.twitter_token, self.twitter_secret)
        twitter = tweepy.API(twitter_auth, wait_on_rate_limit=True)
        return twitter


class GPTTopicModel:
    DEFAULT_MODEL = 'gpt-3.5-turbo'

    CHAT_PRELUDE = {
        "role": "system",
        "content": "\n".join([
                "The user will provide you a list of tweets.",
                "Each tweet is separated by \"===\".",
                "Provide 5 most common topics (as in topic modeling) from the tweets.",
                "For each topic, then proivde 5 sub-topics paired with a sentiment in 1-2 words.",
                "Each topic should be at most 1-2 words.",
                "For example: one topic output might look like:",
                "Basketball",
                "  - Pickup basketball - enthsiastic",
                "  - NBA - indifferent",
                "  - March Madness - annoyed",
                "  - Shoes - Excited",
                "  - Lebron James - Angry",
                "Print each topic on a new line. Do not prefix with a number or a bullet. Do not say anything else."
        ])
    }

    MAX_TOKENS_PER_MODEL = {
        'gpt-4': 8_192,
        'gpt-3.5-turbo': 4096,
    }

    def __init__(self, tweet_texts, data_dir, model):
        self.tweet_texts = tweet_texts
        self.data_dir = data_dir / "topics" / model
        self.model = model

    def generate_topics(self):
        return self.__chunked_tweets()

    def __chunked_tweets(self):
        encoding = tiktoken.encoding_for_model(self.model)
        chunks = []
        current_chunk = []
        current_cunk_size = 0

        for tweet in self.tweet_texts:
            size = len(encoding.encode(tweet))
            if current_cunk_size + size > self.__max_chunk_size():
                chunks.append(current_chunk)
                current_chunk = []
                current_cunk_size = 0
            current_chunk.append(tweet)
            current_cunk_size += size

        if len(current_chunk) > 0:
            chunks.append(current_chunk)

        return chunks

    def __max_chunk_size(self):
        ceiling = GPTTopicModel.MAX_TOKENS_PER_MODEL[self.model]
        return ceiling - 1000  # Leave room


def main():
    args = CLI().parse_args()
    bootstrap = Bootstrap()

    bootstrap.setup_openai()
    twitter = bootstrap.twitter_client()

    scraper = TweetScraper(twitter, args['data_dir'], args['username'])
    tweets = scraper.all_tweets()
    tweet_texts = [tweet['full_text'] for tweet in tweets]

    modeler = GPTTopicModel(
        tweet_texts, args['data_dir'], args['openai_model']
    )
    print(modeler.generate_topics())


if __name__ == '__main__':
    main()
