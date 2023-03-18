import os
import pathlib
import json
from hashlib import md5
import pathlib
import logging

from dotenv import load_dotenv
import tweepy
import openai
import argparse

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
    DEFAULT_MODEL = 'gpt-3.5-turbo'

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--data-dir', type=str, default=str(CLI.PROJECT_ROOT / 'data'))
        self.parser.add_argument('--username', type=str, required=True)
        self.parser.add_argument('--openai-model', type=str, default=CLI.DEFAULT_MODEL)

    def parse_args(self):
        args = self.parser.parse_args()
        return { "data_dir": pathlib.Path(args.data_dir), "username": args.username}

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
        twitter_auth = tweepy.OAuthHandler(self.twitter_consumer_key, self.twitter_consumer_secret)
        twitter_auth.set_access_token(self.twitter_token, self.twitter_secret)
        twitter = tweepy.API(twitter_auth, wait_on_rate_limit=True)
        return twitter

def main():
    args = CLI().parse_args()
    bootstrap = Bootstrap()

    bootstrap.setup_openai()
    twitter = bootstrap.twitter_client()

    scraper = TweetScraper(twitter, args['data_dir'], args['username'])
    scraper.all_tweets()


if __name__ == '__main__':
    main()
