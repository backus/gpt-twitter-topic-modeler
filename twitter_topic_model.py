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

'''
A class named CLI that parses the following CLI arguments using argparse:
    --data-dir (str) (optional): The directory where the data will be stored.
    --username (str) (required): The Twitter username to scrape.
'''
class CLI:
    PROJECT_ROOT = pathlib.Path(__file__).parent

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--data-dir', type=str, default=str(CLI.PROJECT_ROOT / 'data'))
        self.parser.add_argument('--username', type=str, required=True)

    def parse_args(self):
        args = self.parser.parse_args()
        return { "data_dir": pathlib.Path(args.data_dir), "username": args.username}

def main():
    args = CLI().parse_args()
    load_dotenv()

    openai.api_key = os.getenv('OPENAI_API_KEY')

    twitter_auth = tweepy.OAuthHandler(os.getenv("TWITTER_CONSUMER_KEY"), os.getenv("TWITTER_CONSUMER_SECRET"))
    twitter_auth.set_access_token(os.getenv("TWITTER_TOKEN"), os.getenv("TWITTER_SECRET"))
    twitter = tweepy.API(twitter_auth, wait_on_rate_limit=True)

    scraper = TweetScraper(twitter, args['data_dir'], args['username'])
    scraper.all_tweets()


if __name__ == '__main__':
    main()
