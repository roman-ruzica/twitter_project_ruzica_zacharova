

import json
import pandas as pd
import requests
import twitter
import itertools
import time
import datetime

class TwitterUser():
    '''
    twitter_handle(string) - twitter username
    authtentification(dict) - dictionary with API keys and access tokens
    
    Class containing timeline (list of all recent tweets), mentions (all tweets where they were tagged), statistics about the posts and users themselves.
    Methods are used to extract all neccesary data and output it as csv file.
    note that a maximum of 3200 posts retrieved per API endpoint - We expect around 3200 timeline tweets and 3200 mentions maximum per account.
    
    The class is used to extract all relevant data about user's tweets and mentions through twitter API and gather them in pandas dataframe
    '''
    
    def __init__(self, twitter_handle, authentification):

        self.inquiry_pd =[]
        self.authentification = authentification
        self.timeline_tweet_pd=[]
        self.twitter_handle = twitter_handle
        self.rate_limiter_getstatus_ts = datetime.datetime.now()
        self.rate_limiter_getstatus_counter = 0
        self.interesting_user_atributes = ['screen_name', 'favourites_count', 'followers_count', 'friends_count', 'statuses_count', 'location']
        self.interesting_tweet_attributes = ['full_text', 'lang', 'retweet_count','created_at', 'source']
        self.api_cons = twitter.Api(consumer_key=self.authentification['API_key'],
                  consumer_secret=self.authentification['API_secret_key'],
                  access_token_key=self.authentification['Access_token'],
                  access_token_secret=self.authentification['Access_token_secret'],
                 tweet_mode='extended')
        
    # First of all, get as much tweets as possible through each endpoint.
    # we iterate over tweets, always checking if the call returned additional tweets.
    def get_timeline(self):
        timeline = self.api_cons.GetUserTimeline(screen_name=self.twitter_handle, count=200)
        earliest_tweet = min(timeline, key=lambda x: x.id).id
        print("getting tweets before:", earliest_tweet)

        while True:
            tweets = self.api_cons.GetUserTimeline(
                screen_name=self.twitter_handle, max_id=earliest_tweet, count=200
            )
            new_earliest = min(tweets, key=lambda x: x.id).id

            if not tweets or new_earliest == earliest_tweet:
                break
            else:
                earliest_tweet = new_earliest
                print("getting tweets before:", earliest_tweet)
                timeline += tweets

        self.timeline = timeline

    def get_mentions(self):
        mentions = self.api_cons.GetSearch(term=self.twitter_handle ,include_entities=True, count=200, result_type='recent')
        earliest_tweet_mentions = min(mentions, key=lambda x: x.id).id
        print("getting mentions before:", earliest_tweet_mentions)

        while True:
            mentions_add = self.api_cons.GetSearch(
                term=self.twitter_handle, max_id=earliest_tweet_mentions, include_entities=True, count=200, result_type='recent'
            )
            new_earliest = min(mentions_add, key=lambda x: x.id).id

            if not mentions_add or new_earliest == earliest_tweet_mentions:
                break
            else:
                earliest_tweet_mentions = new_earliest
                print("getting mentions before:", earliest_tweet_mentions)
                mentions += mentions_add
        self.mentions = mentions

# define a method that calls both methods to gather all tweets relevant to the account
    def gather_relevant_tweets(self):
        self.get_mentions()
        self.get_timeline()

        
# extract profile details for the username from arbitrarily chosen tweet
    def get_account_details(self):
        '''
        requires at least one tweet in the timeline attribute Call get_timeline() or gather_tweets() to construct it
        '''
        self.details = {}
        self.detail_atributes_required = ('favourites_count', 'followers_count', 'friends_count', 'statuses_count')
        self.details = {k: self.timeline[1]._json['user'][k] for k in self.interesting_user_atributes}
        print(self.details)
        
        
        
        
    def extract_mention_user_data(self):
        for mention in self.mentions:
            mention.user_info = {k: mention._json['user'][k] for k in self.interesting_user_atributes}
        
    def extract_mention_tweet_data(self):    
        for mention in self.mentions:
            mention.tweet_info = {k: mention._json[k] for k in self.interesting_tweet_attributes}
        
## Now extract timeline information for the user. If the timeline tweet is a inquiry to another tweet, also gather those tweets and gather information from them
    def generate_mentions_pdf(self):
        self.mentions_pd_list = []
        for num, tweet in enumerate(self.mentions, start=0):
            self.mentions_pd_list.append(pd.DataFrame( {**self.mentions[num].user_info, **self.mentions[num].tweet_info},
                                                           index =  [self.mentions[num].user_info['screen_name']])
                                   )
            
        self.mentions_pd = pd.concat(self.mentions_pd_list)
        
    def extract_timeline_tweet_data(self):
        for tl_tweet in self.timeline:
            tl_tweet.tweet_info ={k: tl_tweet._json[k] for k in self.interesting_tweet_attributes}
            tl_tweet.og_tweet_info = {**self.details, **tl_tweet.tweet_info}
        
        
    def get_inquired_to_tweet(self):
        ## using enumeration to have an easy way to handle api rate limiting
        for timeline_tweet in self.timeline:
            if (self.rate_limiter_getstatus_counter+1)%899 == 0:
                time_to_wait = max(0, (15*60) - max(0,(datetime.datetime.now() - self.rate_limiter_getstatus_ts).total_seconds()))
                print(f"sleeping at {datetime.datetime.now()} for {time_to_wait} seconds")
                time.sleep(time_to_wait)
            if timeline_tweet.in_reply_to_status_id is None:
                timeline_tweet.inquiry_tweet = None
            else:
                self.rate_limiter_getstatus_counter +=1
                try:
                    timeline_tweet.inquiry_tweet = self.api_cons.GetStatus(timeline_tweet.in_reply_to_status_id)

                except (twitter.TwitterError, TypeError, ValueError): 
                    timeline_tweet.inquiry_tweet = None
                else:
                    pass

    def retry_inquired_to_tweet(self):
    ## not only rate limiting, but other unexpected problems might arise. If we have status id of the tweet the account is inquirying to, but no associated tweet, retry to get the tweet
        for timeline_tweet in self.timeline:
            if (self.rate_limiter_getstatus_counter+1)%899 == 0:
                time_to_wait = max(0, (15*60) - max(0,(datetime.datetime.now() - self.rate_limiter_getstatus_ts).total_seconds()))
                print(f"sleeping at {datetime.datetime.now()} for {time_to_wait} seconds")
                time.sleep(time_to_wait)
                self.rate_limiter_getstatus_ts = datetime.datetime.now()

            if timeline_tweet.in_reply_to_status_id is None:
                pass
            else:
                if timeline_tweet.inquiry_tweet is None:
                    self.rate_limiter_getstatus_counter +=1
                    try:
                        timeline_tweet.inquiry_tweet = self.api_cons.GetStatus(timeline_tweet.in_reply_to_status_id)

                    except (twitter.TwitterError, TypeError, ValueError): 
                        timeline_tweet.inquiry_tweet = None
                else:
                    pass


                
                
    def extract_inquiry_tweet_info(self):
        self.inquiry_atributes_required = ( 'created_at', 'full_text', 'retweet_count', 'favorite_count')
        self.inquiry_user_required = ('screen_name', 'followers_count', 'friends_count', 'statuses_count', "favourites_count")
        for num in list(range(0, len(self.timeline))):


            try:
                self.timeline[num].inquiry_tweet_info = {k: self.timeline[num].inquiry_tweet._json[k] for k in self.inquiry_atributes_required}
            except:
                self.timeline[num].inquiry_tweet_info = {k: None for k in self.inquiry_atributes_required}

            try:
                self.timeline[num].user_info = {k: self.timeline[num].inquiry_tweet._json['user'][k] for k in self.inquiry_user_required}
            except: 
                self.timeline[num].user_info = {k: None for k in self.inquiry_user_required}

    def generate_timeline_pdf(self):
        self.inquiry_pd = []
        for num in list(range(0, len(self.timeline))):
                self.timeline[num].inquiry_info = {**self.timeline[num].user_info, **self.timeline[num].inquiry_tweet_info}

                self.timeline[num].inquiry_info = add_prefix_to_dict(self.timeline[num].inquiry_info, "inquiry_")

                self.timeline[num].concat_info = {**self.timeline[num].og_tweet_info, **self.timeline[num].inquiry_info}
                self.inquiry_pd.append(pd.DataFrame(self.timeline[num].concat_info,
                                                       index =  [num])
                                )
        self.timeline_pd = pd.concat(self.inquiry_pd)    
        
    def do_all(self):
        self.gather_relevant_tweets()
        self.get_account_details()
        self.extract_mention_user_data()
        self.extract_mention_tweet_data()
        self.extract_timeline_tweet_data()
        self.get_inquired_to_tweet()
        self.retry_inquired_to_tweet()
        self.extract_inquiry_tweet_info()
        self.generate_timeline_pdf()
        self.generate_mentions_pdf()
        
class ComparisonCollection():
    '''
    A collection of twitter 
    '''
    def __init__(self,username_dictionary, authentification):

        self.users = username_dictionary
        self.authentification = authentification
        self.accounts = []
        self.rate_limiter_getstatus_ts = datetime.datetime.now()
        self.rate_limiter_getstatus_counter = 0
        self.api_cons = twitter.Api(consumer_key=self.authentification['API_key'],
                  consumer_secret=self.authentification['API_secret_key'],
                  access_token_key=self.authentification['Access_token'],
                  access_token_secret=self.authentification['Access_token_secret'],
                 tweet_mode='extended')
        
    def create_twitter_profiles(self):
        
        for name in self.users:
            
            self.accounts.append(TwitterUser(self.users[name], self.authentification))
            
    def create_all_dataframes(self):
        self.rate_limiter_getstatus_handover_counter = 0
        for acct in self.accounts:
            acct.rate_limiter_getstatus_counter = self.rate_limiter_getstatus_handover_counter
            acct.rate_limiter_getstatus_ts = self.rate_limiter_getstatus_ts
            acct.do_all()
            self.rate_limiter_getstatus_handover_ts = acct.rate_limiter_getstatus_ts
            self.rate_limiter_getstatus_handover_counter = name.rate_limiter_getstatus_counter
            
    def concatenate_tl_dataframe(self):
        timeline_list = []
        for acct in self.accounts:    
            timeline_list.append(acct.timeline_pd)
        self.timeline_pd = pd.concat(timeline_list)
        
        
    def concatenate_mentions_dataframe(self):
        timeline_list = []
        for acct in self.accounts: 
            timeline_list.append(acct.mentions_pd)
        self.mentions_pd = pd.concat(timeline_list)
        
        
    def write_tl_csv(self):
            self.timeline_pd.to_csv("timeline.csv")
    
    def write_mentions_csv(self):
            self.mentions_pd.to_csv("mentions.csv")
            
    def do_all_for_all(self):
        self.create_twitter_profiles()
        self.create_all_dataframes()
        self.concatenate_tl_dataframe()
        self.concatenate_mentions_dataframe()
        self.write_tl_csv()
        self.write_mentions_csv()
        
def add_prefix_to_dict(dictionary_to_change, prefix_to_add):
    init_dict_keys = list(dictionary_to_change.keys())
    changed_list = ["reply_" + s for s in init_dict_keys]
    final_dict = dict(zip(changed_list, list(dictionary_to_change.values())))
    return final_dict