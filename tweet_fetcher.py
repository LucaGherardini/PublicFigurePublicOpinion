"""
tweet_fectcher.py is a python script used to retrieve tweets with user-defined keywords, in a specific time-frame (limited to 7 days in the past)

Using specific credentials (CREDENTIALS RETRIEVING section), a connection is established (AUTHENTICATION section), in order to allow the user to define his own query (QUERY DEFINITION section).
The script uses internal parameters (INITIALIZING PARAMETERS section) to handle data retrieved (PROCESSING QUERY)
"""

import tweepy
import datetime as dt
import re
import time
import os
import sys
import traceback
from prettytable import PrettyTable
import json

""" 
CREDENTIALS RETRIEVING

Credentials are stored in a text file named "Keys of Twitter application.txt", that
is read line-by-line, storing keys read in respective variables
"""

Credentials = {}

print("Opening credential text file... ", end="")
with open("Keys of Twitter application.txt", "r") as f:
    for line in f:

        if line.startswith("API key:"):
            Credentials["CONSUMER_KEY"] = line.split(": ")[1].replace("\n", "")

        if line.startswith("API key secret:"):
            Credentials["CONSUMER_SECRET"] = line.split(": ")[1].replace("\n", "")

        if line.startswith("Access token: "):
            Credentials["ACCESS_TOKEN"] = line.split(": ")[1].replace("\n", "")

        if line.startswith("Access token secret: "):
            Credentials["ACCESS_TOKEN_SECRET"] = line.split(": ")[1].replace("\n", "")

print("Credentials retrieved")
for key, value in Credentials.items():
    print(key + ": " + value)

print("")

""" 
AUTHENTICATION 

Using retrieved credentials, authentication is made
"""

print("Authenticating... ", end="")
# Consumer Key and Secret
auth = tweepy.OAuthHandler(Credentials["CONSUMER_KEY"], Credentials["CONSUMER_SECRET"])
# Access Token and Secret
auth.set_access_token(Credentials["ACCESS_TOKEN"], Credentials["ACCESS_TOKEN_SECRET"])
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify = True)
print("Authenticated")

print("")

"""
QUERY DEFINITION

Ask user for keywords of interest for the tweets to retrieve (retweets are ignored for slimmer storage)
and the date to start searching (N.B.: as specified in documentation, "...the search index has a 7-day limit. In other words, no tweets will be found for a date older than one week")

Retweets can be filtered by the API (suggested, because retweets have reduced utility and can be summarized by the field 'retweet_count' of a tweet)

Start date of retrieving (by default, 8 days before)

https://docs.tweepy.org/en/v3.10.0/api.html#tweepy-api-twitter-api-wrapper 
(api.search(), 'until' parameter)
"""

keywords = input("Insert the keywords of interest: ")

retweets = True
if input("Do you want to retrieve retweets?[y/N]: ") != ("y" or "Y"):
    retweets = False
    keywords += " -filter:retweets"


day = dt.timedelta(days=1)
default_start_date = dt.date.today()-(day*8)
start_date = input("Insert the data you want to start searching by (yyyy-mm-dd)[" + str(default_start_date) + " by default]: ")

if start_date == "":
    start_date = default_start_date
else:
    start_date = start_date.split('-')
    start_date = dt.date(int(start_date[0]), int(start_date[1]), int(start_date[2]))

end_date = dt.date.today()
total_days = (end_date + day - start_date).days

try:
    tweets_to_retrieve = int(input("How many Tweets do you want to retrieve PER DAY?[1000 by default]: "))
except:
    tweets_to_retrieve = 1000

if tweets_to_retrieve <= 0:
    tweets_to_retrieve = 1000

qt = PrettyTable()
qt.field_names = ["Keywords", "Start", "Retweets?", "# Tweets to retrieve per day", "# Total Tweets"]
qt.add_row([str(keywords), str(start_date), str(retweets), str(tweets_to_retrieve), str(tweets_to_retrieve * total_days)])
print(qt)

"""
INITIALIZING PARAMETERS

'pt' is the PrettyTable used to store data (to print in text file)
'RAWTweetFile' is the file that will contain the gross representation of tweets retrieved
'TweetFile' contains the PrettyTable representation, for a clearer view for manual analysis
'num_tweets' is the tweets retrieved counter is initialized
'seconds_to_wait' specify how many seconds awaiting at each "chunk" (100 tweets) to avoit rate limit exceeding 
(cooldown is about 20 minutes). This is done because of the connection expiring for too long inactivity.
"""
pt = PrettyTable()
pt.field_names = ["ID", "Date(YYYY-MM-DD)", "Username", "Tweet text", "Favourites Count", "Retweets Count", "Quotes Tweet"]
pt.align = "l"

RAWTweetFile = "(RAW) Tweets (" + keywords + ") by " + str(start_date) +" (" + str(dt.datetime.now()) + ") #" + str(tweets_to_retrieve) +".json"
TweetFile = "Logs/Tweets (" + keywords + ") by " + str(start_date) +" (" + str(dt.datetime.now()) + ") #" + str(tweets_to_retrieve) +".txt"

fr = open(RAWTweetFile, "w+")
f = open(TweetFile, "w+")

# seconds to wait for each tweet to don't exceed rate limit (300 tweets every 15 minutes, 1 tweet every 3 seconds).
# if tweets to retrieve in total are less than 300, there is no need to slow download
seconds_to_wait = 0
if (tweets_to_retrieve) * total_days > 300:
    seconds_to_wait = 3

print("Pause per tweet is of " + str(seconds_to_wait) + " seconds")

"""
PROCESSING QUERY

Tweets are stored in two format:

- Raw tweets, stored in the RAW file named consequently 

- Tweets stored in a pretty table, to allow manual analysis, in a format containing:
    - id_str of the tweet
    - created_at "yyyy-mm-dd", with of 10 characters length (standard date record of a tweet contains hh:mm:ss in addition, not requested for this project)
    - user name of who created the tweet
    - text of the tweet
    - favourites_count of the likes to the tweet
    - number of retweets

    Only tweets written in italian are considered (lang="it")
    tweet_mode parameter specifies the type of Status object returned, which is "extended", to allow retrieving full text of tweet
"""


print("Retrieving, please wait...")
try:
    while start_date <= end_date:
        print("Getting tweets of : " + str(start_date))
        tweets = tweepy.Cursor(api.search, 
                            q=keywords,
                            lang="it",
                            since=str(start_date),
                            until=str(start_date+day),
                            tweet_mode="extended",
                            #include_rts = retweets,
                            monitor_rate_limit=True, 
                            wait_on_rate_limit=True,
                            wait_on_rate_limit_notify = True,
                            retry_count = 5, #retry 5 times
                            retry_delay = 60, #seconds to wait for retry
                            retry_errors=set([401, 404, 429, 500, 503])
        ).items(tweets_to_retrieve)

        start_date += day # date goes forward of 1 day
        num_tweets = 0

        for tweet in tweets:
            num_tweets+=1

            # For convenience, ID is retrieved by id_str field, which is the string format of tweet ID
            id = tweet.id_str

            # date is extracted, keeping only yyyy-mm-dd informations (first 10 characters)
            date = str(tweet.created_at)[:10]

            user_name = str(tweet.user.name)

            # full text of the tweet is (from inside to outside):
            # deprived of "\n" to keep all text on a single line (replace builtin function call)
            # deprived of urls(re.sub external function call)
            full_text = re.sub(r"http\S+", "", tweet.full_text.replace("\n", ""))

            favourites_count = str(tweet.favorite_count)

            retweets_count = str(tweet.retweet_count)

            quoted = ""
            if tweet.is_quote_status == True:
                quoted = tweet.quoted_status_id_str + " | " + tweet.quoted_status.user.name + " | " + tweet.quoted_status.full_text

            #fr.write(str(tweet) + "\n")
            json.dump(tweet._json, fr, sort_keys = True, indent = 4)

            pt.add_row([id, date, user_name, full_text, favourites_count, retweets_count, quoted])

            time.sleep(seconds_to_wait)

        time.sleep(seconds_to_wait)
        print("Got " + str(num_tweets) + " tweets for this day")

except tweepy.error.TweepError:
    traceback.print_exc() 
    print("Error occurred, saving and quitting...")

f.write(pt.get_string())
f.close()

fr.close()

print("Tweets saved in \"" + TweetFile +"\" and \"" + RAWTweetFile + "\"")

# Notify sound (requires 'sox' package on Linux)
duration = 2  # seconds
freq = 440  # Hz
os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))