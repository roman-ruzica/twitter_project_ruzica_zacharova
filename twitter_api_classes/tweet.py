class Twitter_user():
    '''
    Class containing timeline (list of all recent tweets), mentions statistics about their posts
    
    '''
    
    def __init__(self, twitter_handle, api):

        self.twitter_handle = twitter_handle
        self.api = twitter.Api(consumer_key=authentification['API_key'],
                  consumer_secret=authentification['API_secret_key'],
                  access_token_key=authentification['Access_token'],
                  access_token_secret=authentification['Access_token_secret'],
                 tweet_mode='extended')
        
    def get_timeline(self):
        self.timeline = self.api.GetUserTimeline(screen_name=self.twitter_handle, count=2)
        
    def get_mentions(self):
        self.mentions = self.api.GetSearch(term=self.twitter_handle,include_entities=True, count=2, result_type='recent')
        
    def gather_tweets(self):
        self.get_mentions()
        self.get_timeline()
        
    def get_account_details(self):
        '''
        requires at least one tweet in the timeline attribute Call get_timeline() or gather_tweets() to construct it
        '''
        self.details = {}
        self.detail_atributes_required = ('favourites_count', 'followers_count', 'friends_count', 'statuses_count')
        self.details = {k: self.timeline[1]._json['user'][k] for k in self.detail_atributes_required}
        print(self.details)
        
        
        
        
    def extract_mention_user_data(self):
        
        self.interesting_atributes = ['screen_name', 'favourites_count', 'followers_count', 'friends_count', 'statuses_count', 'location']
        for num, tweet in enumerate(rajf.mentions, start=0):
            self.mentions[num].user_info = (
                {k: self.mentions[num]._json['user'][k] for k in self.interesting_atributes}
            )
            self.mentions[num].user_info_pd = pd.DataFrame( self.mentions[num].user_info,
                                                           index =  [self.mentions[num].user_info['screen_name']])
        
    def extract_mention_tweet_data(self):    
        
        tweet_attributes = ['full_text', 'lang', 'retweet_count', 'source']
            
        for num, tweet in enumerate(rajf.mentions, start=0):
            self.mentions[num].tweet_info = (
                {k: self.mentions[num]._json[k] for k in tweet_attributes}
            )
            
        
    def generate_mentions_pdf(self):
        self.pdf_list = []
        for num, tweet in enumerate(rajf.mentions, start=0):
            self.mentions[num].tweet_pd = pd.DataFrame( {**self.mentions[num].user_info, **self.mentions[num].tweet_info},
                                                           index =  [self.mentions[num].user_info['screen_name']])
            self.pdf_list = self.pdf_list.append(self.mentions[num].tweet_pd)
        
    def generate_pdf(self):
        self.tweets_pd = pd.concat([self.mentions[num].tweet_pd] for num in list(range(0, len(self.mentions))))
		
		
		
		
		class Comparison_collection():
    '''
    Class containing methods for comparing among different twitter users posts and their mentions posts. 
    '''
    
    def __init__(self,dictionary, authentification):
        '''
        Loads a dictionary with {"full_name":"twitter_handle"} pairs and saves this logic
        also creates an python-twitter API object based on a dictionary with API keys,
        consumer key and secret must be called API_key and API_secret_key respectively,
        access token key and access token secret must be called Access_token and Access_token_secret respectively
        '''

        self.users = dictionary
        
    
        self.api = twitter.Api(consumer_key=authentification['API_key'],
                  consumer_secret=authentification['API_secret_key'],
                  access_token_key=authentification['Access_token'],
                  access_token_secret=authentification['Access_token_secret'],
                 tweet_mode='extended')
    
    def create_user_data(self):
        
        for name in self.users:
            
            self.accounts = {name: Twitter_user(self.users[name], self.api) for name in self.users}
            
    def get_users_tweets(self):
        
        for name in self.users:
            
            self.accounts[name].gather_tweets()
    