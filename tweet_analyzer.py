"""
tweet_analyzer.py is a python script used to take data retrieved by tweet_fetcher.py and making the following analysis:
- Sentiment analysis of tweets, that will be used as internal attribute of the corresponding node
- Construction of a graph, which links will be weighted depending on the coherence between the sentiment of respective nodes
- Average of the sentiment for each day, to make a temporal plot (a file containing events and important date could be provided)
"""

import os
import re
import json
from datetime import datetime
from dateutil import parser

from prettytable import PrettyTable
import tweepy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as sia
import lxml.etree as etree
import pandas as pd
import math
import utils
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt 
import numpy as np
from PIL import Image

# Color ASCII used to change color of prints
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m' # Red
ENDC = '\033[0m' # De-select the current color
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

pt = PrettyTable()
files = []
excludeNeutralTweets = True
df = pd.DataFrame()
hashtags = ""

"""
    SELECTING TWEETS FILE

        A regular expression to detect (RAW).*.json files in the current directory is used to retrieve the tweets downloaded with tweet_fetcher.py
        
        The list of found files is sorted by creation time, in descending order (os.path.getmtime returns the epoc elapsed from file creation, the greater the value the older is the file, so in descending order newest files are the last). If a tweet is duplicated, the last read overwrite the previous ones, keeping most updated information (i.e. Degree and likes).

        Files are shown to the user in a PrettyTable, to allow interactive selection/deselection of which files have to be analyzed inserting corresponding number, or simply pressing Enter to continue.
        State of each file (selected/deselected) is represented by its color (Green/Red)
"""
def select_files():
    global files
    files = [[f, True] for f in sorted(os.listdir('.'), key=os.path.getmtime) if os.path.isfile(f) and re.match(r"^\(RAW\).*.json$", f)]

    # " ", not "" (or the while statement would be False)
    selector = " " 
    color = ""
    # Number assigned to the file | Name of the file
    pt.field_names = ['#', "File name"]
    # Column of file name has to be aligned to the left side
    pt.align["File name"] = "l"

    while selector != "":
        os.system('clear')
        for f in files:
            if f[1]:
                color = OKGREEN
            else:
                color = FAIL
            pt.add_row([color + str(files.index(f)+1), f[0] + ENDC])

        print(pt)
        pt.clear_rows()
        selector = input(OKGREEN + "SELECTED\n" + FAIL + "UNSELECTED\n" + ENDC + BOLD + "Choose files to load (press Enter to continue): " + ENDC)
        if selector != "" and int(selector) > 0 and int(selector) <= len(files):
            files[int(selector)-1][1] = not(files[int(selector)-1][1])

    pt.clear()
    os.system('clear')
    # After the user has chosen which files have to be analyzed, the files list stores only file names f[0] with selector f[1] True
    files = [f[0] for f in files if f[1]]
    print("")

"""
    RETRIEVING TWEETS FROM SPECIFIED FILES

        Interesting properties: 
            id_str (ID)
            created_at (Date of creation)
            user.name (Username)
            full_text (Text of tweet)
            retweet_count (Degree of given tweet)
            favorite_count (likes to the given tweet)
            is_quote_status (if tweet is a quote or not), if True:
                quoted_status.id_str (ID quoted tweet)
                quoted_status.user.name (Username of the creator of quoted tweet)
                quoted_status.full_text (text of quoted tweet)

        Json files are read line by line, using '}{' and '}' as separators. Tweets are rebuilt one by one, cleaned from url and processed by vaderSentiment sentiment analyzer. Date is stored natively in a '%a %b %d %H:%M:%S +0000 %Y' format string (i.e. 'Mon Feb 15 23:55:07 +0000 2021'), which is converted in a datetime object containing only yyyy-mm-dd (.date() invocation).

        'Tweet' class from package 'tweet_parser.tweet' has not been used to allow adding 'sa' field to the tweet (possible with the dictionary) and to automatically avoid duplicates thanks to 'id' as dictionary key. If a duplicate tweet with the same id is found, it replaces the previous one. Considering that json files are read in chronological order, newest tweets replace the oldest ones, keeping always updated informations on a tweet. 'Tweets' dictionary is then used to create Pandas Dataframe 'df', for a smarter handling of records.

        Sentiment is estimated by the analyzer of vaderSentiment library, and only 'compound' component is stored (combination of pos, neg and neu measurements).
        Be aware that sentiment analysis is excluded from quoted tweets, because they could be on different topics, interfering with the measurements.

        Parameters:
            'Tweets' is the dictionary containing all tweets, with their ID as key (unique)

            'tweet' is a dictionary containg last tweet read from the json file, to be processed before being stored in 'Tweets' main dictionary

            'jsonTweet' is the string containing the json definition of the read tweet. Because of the storing of the tweet on multiple lines, it's necessary to read the file line by line to detect boundaries of single tweet ( '}{' and '}' )

            'df' is pandas dataframe in which will be stored the tweets retrieved, making the 'Tweets' dictionary useless

            'analyzer' is an instance of Vader Sentiment Analyzer, which compute sentiment for the text of each tweet, composed as 'pos', 'neu', 'neg' and 'compound' (the last one is a composition of the first three values). Only 'compount' element is stored

            'excludeNeutralTweets' is a flag used to decide if discarting neutral tweets (with 'compound' equals to 0.0) or not. This heavily influences sentiment analysis statistics
"""
def tweets_retrieving():
    global excludeNeutralTweets
    global df
    global hashtags

    Tweets = {}
    tweet = {}
    jsonTweet = ""
    analyzer = sia()
    excludeNeutralTweets = str(input("Do you want to exclude tweets with null sentiment from statistics? [Y/n]: "))
    excludeNeutralTweets = (excludeNeutralTweets != "n" and excludeNeutralTweets != "N")

    for file in files:
        print(WARNING + "Reading file " + file + ENDC)
        f = open(file, "r")
        jsonTweet = ""

        for line in f.readlines():
            if line == "}{\n" or line == "}":
                jsonTweet += "}"
                tweet = json.loads(jsonTweet)
                id = tweet['id_str']
                Tweets[id] = {}
                Tweets[id]['id_str'] = id
                Tweets[id]['full_text'] = ' '.join(word for word in tweet['full_text'].split() if not word.startswith('https:'))
                Tweets[id]['created_at'] = (parser.parse(tweet['created_at'])).date()
                Tweets[id]['username'] = tweet['user']['name']
                Tweets[id]['retweet_count'] = tweet['retweet_count']
                Tweets[id]['favorite_count'] = tweet['favorite_count']
                Tweets[id]['sharing'] = tweet['retweet_count'] + tweet['favorite_count'] + 1
                sa = analyzer.polarity_scores(tweet['full_text'])['compound'] 
                Tweets[id]['sa'] = sa
                Tweets[id]['is_quote_status'] = tweet['is_quote_status']
                for hashtag in tweet['entities']['hashtags']:
                    hashtags += " " + hashtag['text']
                
                # entities.hashtags.text (without'#')

                # if this tweet is a quote, store additional fields
                if tweet['is_quote_status']:
                    Tweets[id]['quoted_tweet_id'] = tweet['quoted_status']['id_str']
                    Tweets[id]['quoted_tweet_username'] = tweet['quoted_status']['user']['name']
                    Tweets[id]['quoted_tweet_full_text'] = ' '.join(word for word in tweet['quoted_status']['full_text'].split() if not word.startswith('https:'))

                jsonTweet = "{"
            else:
                jsonTweet += line
        
    df = pd.DataFrame.from_dict(Tweets, orient='index')
    df.sort_values('created_at', ascending = True, inplace = True)
    print(str(len(df)) + " tweets read")

"""
    STATISTICS
        SENTIMENT ANALYSIS
            Sentiment analysis stored is used to compute weighted and standard average, for each date.
            Weighted average considers a "sharing" parameter, which is the sum of likes and retweets of a tweet, making more influent a tweet that received more interactions, because it "represents" more people (that interacted with it).

        STANDARD DEVIATION
            Standard deviation is computed for both standard and weighted average 

        COVARIANCE AND CORRELATION
            Computed between Sentiment and Sharing, considering only the Standard Average of sentiment (Weighted has an explicit and obvious dependence with Sharing on its own) on all the days considered.

        PLOTTING
            Means (Standard and Weighted) are plotted, with standard deviation, to produce graphic plots in "Plots/" directory
"""
def statistics():
    stdAvgs = {}
    stdDevs = {}
    wgtAvgs = {}
    wgtDevs = {}

    days = 0
    totalTweetsProcessed = 0
    avgSharing = 0

    print(WARNING + "Neutral tweets have been " + ("discarded" if excludeNeutralTweets else "kept") + ENDC)

    print("Computing sentiment analysis statistics... " + ENDC, end="")
    pt.field_names = ["Date", "Standard Average", "Standard Average Deviation", "Weighted Average", "Weighted Average Deviation"]

    # For each date, the weighted average and standard average are computed
    for date in df.created_at.unique(): 
        stdAvgDay = 0.0
        wgtAvgDay = 0.0
        totSharing = 0.0
        count = 0
        days += 1

        for index, tweet in df.loc[df['created_at'] == date].iterrows():
            if not(excludeNeutralTweets) or tweet['sa'] != 0.0:
                stdAvgDay += tweet['sa']
                count += 1

                
                wgtAvgDay += tweet['sa'] * tweet['sharing']
                totSharing += tweet['sharing']

                avgSharing += tweet['sharing']

        # 'count' is used to keep track of tweets processed in each day, then it resets, while 'totalTweetsProcessed' keeps count of all tweets used for statistics
        totalTweetsProcessed += count

        stdAvgDay /= count
        stdAvgs[date] = stdAvgDay

        wgtAvgDay /= (totSharing)
        wgtAvgs[date] = wgtAvgDay
    print(OKGREEN + "Done" + ENDC)
        
    print("Computing sentiment analysis standard deviation... " + ENDC, end="")
    # For each date, the standard deviation is computed for standard and weighted average
    for date in df.created_at.unique(): 
        stdDevSADay, stdDevWADay = utils.std_devs(df, date, stdAvgs, wgtAvgs, excludeNeutralTweets)

        stdDevs[date] = stdDevSADay
        wgtDevs[date] = stdDevWADay

        pt.add_row([date, round(stdAvgs[date], 3), round(stdDevs[date], 3), round(wgtAvgs[date], 3), round(wgtDevs[date], 3)])
        
    # Standard Average of averages/deviations (computed on days considered)
    stdAvgSum = sum(stdAvgs.values()) / days
    wgtAvgSum = sum(wgtAvgs.values()) / days
    stdDevsSum = sum(stdDevs.values()) / days
    wgtAvgSum = sum(wgtDevs.values()) / days
    pt.add_row(['average', round(stdAvgSum, 3), round(stdDevsSum, 3), round(wgtAvgSum, 3), round(wgtAvgSum, 3)])
    print(OKGREEN + "Done" + ENDC)
    print(pt)
    pt.clear()

    print("Computing Covariance and Correlation between Sentiment and Degree... ", end="")
    pt.field_names = ["Average Sharing", "Covariance", "Correlation"]
    avgSharing /= totalTweetsProcessed
    covariance, correlation = utils.compute_cov_corr(df, avgSharing, stdAvgSum, totalTweetsProcessed, excludeNeutralTweets)
    pt.add_row([round(avgSharing, 3), round(covariance, 3), round(correlation, 3)])
    print(OKGREEN + "Done" + ENDC)
    print(pt)
    pt.clear()
    
    dates_text = ""
    for line in open("Dates.txt", "r").readlines():
        dates_text += line

    utils.plot(df, stdAvgs, stdDevs, -0.8, dates_text, "Plots/Temporal variation of public sentiment (Standard Average).png")
    
    utils.plot(df, wgtAvgs, wgtDevs, -1, dates_text, "Plots/Temporal variation of public sentiment (Weighted Average).png")

"""
    GRAPH CREATION
        Invokes repeadetly "gexf_parser" from utils module
"""
def graph_creation():
    # For each date, a new graph is initialized 
    for date in df.created_at.unique():
        utils.gexf_parser(df, date)

def wordCloud():
    print(WARNING + "Creating Word Cloud... ", end="")
    mask = np.array(Image.open("Flag_of_Italy.png"))
    wordcloud = WordCloud(background_color="black", mode="RGBA", max_words=1000, mask=mask).generate(hashtags)

    # create coloring from image
    image_colors = ImageColorGenerator(mask)
    plt.figure(figsize=[7,5])
    plt.imshow(wordcloud.recolor(color_func=image_colors), interpolation="bilinear")
    plt.axis("off")

    plt.savefig("Plots/Wordcloud.png", format="png")
    print(OKGREEN + " Saved in \"Plots/Wordcloud.png\"" + ENDC)
    

if __name__ == "__main__":
    select_files()
    tweets_retrieving()
    statistics()
    graph_creation()
    wordCloud()
    exit()