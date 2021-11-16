![Wordcloud](https://user-images.githubusercontent.com/27780725/142063351-04fa7996-e867-492f-a828-cc58dbb0fc72.png)

# PublicFigurePublicOpinion
Project for Social Networks exam, consisting in tweets fetching and analysing. The main focus of this work was analyzing the public opinion of a public figure (in this particular case, the then newly elected premier of Italian Government, Mario Draghi) through the sentiment of the tweets containing his name.

------

## Dependencies (all installable through pip/pip3)
- Tweepy (https://www.tweepy.org/)
- vaderSentiment (https://github.com/cjhutto/vaderSentiment)
- Pandas (https://pandas.pydata.org/)
- Dateutil (https://dateutil.readthedocs.io/en/stable/)
- PrettyTable (https://pypi.org/project/prettytable/)
- Lxml (https://pypi.org/project/lxml/)
- Gephi (https://gephi.org/)
- WordCloud (https://pypi.org/project/wordcloud/) 

## tweet_fetchet.py

### Authentication
This script uses tweepy API to interface with Twitter (you will need to get a Twitter Development Account and writing the credentials in a text file named "Keys of Twitter application.txt" (see example in the repository).

### Query building
If the authentication succedes, the user is promped to submit a query, composed by the keywords of interest.
Additional parameters allow to set desired behavior:
- retweets retrieving, day from which starting retrieving (at most 7 days before the current date, because of the limitations of the free version of Twitter API). 
- how many tweets per day to download *at most*. Tweets retrieving has a strict temporal limit (https://developer.twitter.com/en/docs/twitter-api/rate-limits#v2-limits), and the download will be delayed to avoid interruption of service from Twitter API.

### Query Processing

The results are collected and the following attributes are saved:
- ID
- Date
- user_name
- full_text
- favourites_count (*likes*)
- retweets_count![Wordcloud](https://user-images.githubusercontent.com/27780725/142063318-a7cc1f4b-5f24-4d7a-bc1e-1cc3dc09345b.png)

- quoted (if it's not empty, the current tweet is the quote of another one, which is saved with the same attributes)

Tweets are retrieved querying tweepy, then they are saved in a JSON file following this naming scheme:
(RAW) Tweets(**Keywords**) by **start_date** (**start_time**) #**Tweets_per_day**.json

Another copy, by default, is saved as a .txt in *Logs* folder.


## tweet_analyzer.py
This script searches for JSON files with the same naming scheme used by tweet_fetcher.py

### Statistics computation
The user can select, through CLI, which files have to be processed, then, a tweet dictionary is rebuilt and loaded in a Pandas Dataframe, sorted by creation date.
Sentiment analysis, through *vaderSentiment* library is performed on the retrieved tweets, attaching to each tweet its sentiment polarity, ranging from -1 (negative tweet) to +1 (positive tweet). The *favorite_count* of a tweet represents its weight and influence.
Several statistics are computed on the retrieved tweets, on the whole dataset and on each day: 
- Arithmetic Mean
- Standard Deviation
- Weighted Average
- Standard Deviation of the weights
+------------+------------------+----------------------------+------------------+----------------------------+
|    Date    | Standard Average | Standard Average Deviation | Weighted Average | Weighted Average Deviation |
+------------+------------------+----------------------------+------------------+----------------------------+
| 2021-02-15 |      0.238       |           0.429            |       0.05       |           0.176            |
| 2021-02-16 |      0.253       |           0.427            |      -0.008      |           0.189            |
| 2021-02-17 |       0.24       |           0.315            |       0.25       |           0.373            |
| 2021-02-18 |      0.115       |           0.428            |      0.026       |            0.31            |
| 2021-02-19 |      0.079       |           0.461            |      0.255       |           0.463            |
| 2021-02-20 |       0.14       |           0.442            |      0.346       |           0.348            |
| 2021-02-21 |      0.201       |           0.419            |      0.332       |           0.425            |
| 2021-02-22 |      0.284       |           0.414            |      0.441       |           0.512            |
| 2021-02-23 |      0.068       |           0.494            |       0.02       |           0.371            |
|  average   |       0.18       |           0.425            |      0.352       |           0.352            |
+------------+------------------+----------------------------+------------------+----------------------------+

Additional statistical measures are available considering the *degree* as the sum of retweet_count and favorite_count (+1, to keep in consideration even the writer of the tweet):
- Covariance (between sentiment and degree)
- Correlation (between sentiment and degree)
+-----------------+------------+-------------+
| Average Sharing | Covariance | Correlation |
+-----------------+------------+-------------+
|      24.956     |   0.796    |     0.01    |
+-----------------+------------+-------------+

### Outputs 

The computed statistics are used to generate two plots, showing the temporal variation, respectively, of the mean and of the weighted average of the sentiment. It is possible to attach a legend, named as "Dates.txt", under the plots, in which including the important dates related to an event.

![Temporal variation of public sentiment (Standard Average)](https://user-images.githubusercontent.com/27780725/142060346-6324abc0-bb90-46ed-b8d0-52dce01d8a30.png)
![Temporal variation of public sentiment (Weighted Average)](https://user-images.githubusercontent.com/27780725/142060409-e2a540c1-c259-4099-8e73-ece8e2de00cd.png)

For each day, a GEXF (https://gephi.org/gexf/format/index.html) graph is created, containing the tweets connected by the "quoted_tweet" relationship (the original tweet is referret by the quoting one). Through the GUI of Gephi it's possible to change the colours of nodes using their sentiment attribute, and their size using their degree, showing the most shared nodes and their "polarity".
![GephiGraphPos](https://user-images.githubusercontent.com/27780725/142061179-28f9b35e-5260-4800-85f9-b2fd1047ec44.png)

Finally, a WordCloud image is used by mean of "Flag_of_Italy.png" image, displaying most recurrent words as parts of the flag itself.
![Wordcloud](https://user-images.githubusercontent.com/27780725/142063351-04fa7996-e867-492f-a828-cc58dbb0fc72.png)

## utils.py
This python script is simply the "toolbox" containing all specific subroutines used by tweet_analyzer.py, to slim the main code.

--------
## Results
Despite this was a "toy project" with the main focus of developing a Python application able to interface with Twitter and apply some basic principles of Network Analysis, the results showed a substantial incorrelation between the sentiment of a tweet and its popolarity, proving it's not so simple to predict the appreciation of a tweet. The temporal variation graphs showed some meaningful fluctuations in proximity of particular events, even if the considered period of time and amount of data were limited. 
