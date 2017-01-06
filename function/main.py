import tweepy
import datadog
import os
from tweepy import OAuthHandler
from tweepy import TweepError
from base64 import b64decode

consumer_key    = os.environ['TWITTER_CONSUMER_KEY']
consumer_secret = os.environ['TWITTER_CONSUMER_SECRET']
access_token    = os.environ['TWITTER_ACCESS_TOKEN']
access_secret   = os.environ['TWITTER_ACCESS_SECRET']

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)

dd_opts = {
    'api_key': os.environ['DATADOG_API_KEY'],
    'app_key': os.environ['DATADOG_APP_KEY']
}

dd_prefix = os.environ['DATADOG_METRIC_PREFIX']

datadog.initialize(**dd_opts)

def handle(event, context):

    for account in os.environ['ACCOUNTS'].split(';'):

        me = api.get_user(account)

        datadog.api.Metric.send(metric="%s.status_count" % (dd_prefix),
                                points=me.statuses_count,
                                tags=["account:%s" % (account)])

        datadog.api.Metric.send(metric="%s.followers_count" % (dd_prefix),
                                points=me.followers_count,
                                tags=["account:%s" % (account)])

        datadog.api.Metric.send(metric="%s.friends_count" % (dd_prefix),
                                points=me.friends_count,
                                tags=["account:%s" % (account)])

        datadog.api.Metric.send(metric="%s.favourites_count" % (dd_prefix),
                                points=me.favourites_count,
                                tags=["account:%s" % (account)])

        print "%s: tweets: %i" %    (account, me.statuses_count)
        print "%s: followers: %i" % (account, me.followers_count)
        print "%s: following: %i" % (account, me.friends_count)
        print "%s: likes: %i" %     (account, me.favourites_count)
