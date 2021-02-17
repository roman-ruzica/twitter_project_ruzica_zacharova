# Twitter bank comparer

This project serves to download timeline and mentions (tweets) about any twitter users (in my example, banks)

I wasn't able to get the requirements.txt running, I suspect because my pip does not know the versions which conda installed. However, if you install 3.8 compatible packages, you should be fine.

## API access

You will need twitter_dict.txt file, which contains API keys and access tokens in a json format that reads into python dictionary. 

TwitterUser class is used to get all information deemed useful about tweets @username, as well as the last 3200 tweets on their timeline (API limit).

ComparisonCollection class is a collection class: it might consist of many TwitterUsers, and concatenates their information into a usable pandas dataframe or csv. The two dataframes are: 
1. timeline: all tweets on each users timeline, as well as the tweet it was replying to, if it was replying to any, along with information about their poster.
2. mentions: tweets which contain the username in their body of tweet are returned, along with information about their poster.

Analysis part with examples on how the data might be used is included.