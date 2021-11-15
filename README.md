# PublicFigurePublicOpinion
Project for Social Networks exam, consisting in tweets fetching and analyses 

------

## tweet_fetchet.py

### Authentication
This script uses tweepy API to interface with Twitter (you will need to get a Twitter Development Account and writing the credentials in a text file named "Keys of Twitter application.txt" (see example in the repository).

### Query building
If the authentication succedes, the user is promped to submit a query, composed by the keywords of interest.
Additional parameters allow to set desired behavior:
- retweets retrieving, day from which starting retrieving (at most 7 days before the current date, because of the limitations of the free version of Twitter API). 
- how many tweets per day to download *at most*. Tweets retrieving has a strict temporal limit, and the download will be delayed to avoid interruption of service from Twitter API.

### Query Processing

The results are collected and the following attributes are saved:
- ID
- Date
- user_name
- full_text
- favourites_count (*likes*)
- retweets_count
- quoted (if it's not empty, the current tweet is the quote of another one, which is saved with the same attributes)

Tweets are retrieved querying tweepy, then they are saved in a JSON file following this naming scheme:
(RAW) Tweets(**Keywords**) by **start_date** (**start_time**) #**Tweets_per_day**.json

Another copy, by default, is saved as a .txt in *Logs* folder.


## tweet_analyzer.py
This script searches for JSON files with the same naming scheme used by tweet_fetcher.py
The user can select, through CLI, which files have to be processed, then, a tweet dictionary is rebuilt and loaded in a Pandas Dataframe, sorted by creation date.
Sentiment analysis, through *vaderSentiment* library (https://github.com/cjhutto/vaderSentiment) is performed on the retrieved tweets, attaching to each tweet its sentiment polarity, ranging from -1 (negative tweet) to +1 (positive tweet). The *favorite_count* of a tweet represents its weight and influence.
Several statistics are computed on the retrieved tweets, on the whole dataset and on each day: 
- Arithmetic Mean
- Standard Deviation
- Weighted Average
- Standard Deviation of the weights

Additional statistical measures are available considering the *degree* as the sum of retweet_count and favorite_count (+1, to keep in consideration even the writer of the tweet):
- Covariance (between sentiment and degree)
- Correlation (between sentiment and de

The computed statistics are used to generate several plots.
