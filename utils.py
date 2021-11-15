import math
import matplotlib.pyplot as plt
import lxml.etree as etree

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

"""
    Utility to compute covariance and correlation between standard average of sentiment and average sharing (retweets + likes)
"""
def compute_cov_corr(df, avgSharing, stdAvgSum, totalTweetsProcessed, excludeNeutralTweets):

    E = 0
    Dx = 0
    Dy = 0

    for index, tweet in df.iterrows():
        if not(excludeNeutralTweets) or tweet['sa'] != 0.0:
            x = (tweet['retweet_count'] + tweet['favorite_count'] - avgSharing)
            y = (tweet['sa'] - stdAvgSum)
            E += x * y
            Dx += pow(x,2)
            Dy += pow(y, 2)
    
    covariance = E / totalTweetsProcessed
    correlation = E / math.sqrt(Dx * Dy)

    return covariance, correlation

"""
    Routine to find standard deviation between given average (standard or weighted)
"""
def std_devs(df, date, stdAvgs, wgtAvgs, excludeNeutralTweets):
    stdDevSADay = 0
    stdDevWADay = 0
    count = 0
    totSharing = 0

    for index, tweet in df.loc[df['created_at'] == date].iterrows():
        if not(excludeNeutralTweets) or tweet['sa'] != 0.0:
            stdDevSADay += pow(tweet['sa'] - stdAvgs[date], 2)

            sharing = (tweet['favorite_count'] + tweet['retweet_count'] + 1)
            totSharing += pow(sharing, 2)
            stdDevWADay += pow(tweet['sa'] * sharing - wgtAvgs[date], 2)

            count += 1

    stdDevSADay = math.sqrt(stdDevSADay/count)
    stdDevWADay = math.sqrt(stdDevWADay/totSharing)
    
    return stdDevSADay, stdDevWADay

"""
    Function to plot a mean vector, with relative standard deviation, with additional parameters regarding position of a text description on dates and filename of plot
"""
def plot(df, avgs, devs, posTextY, dates_text, filename):
    print(WARNING + "Plotting... ", end="")
    plt.figure(figsize=(len(avgs.keys())+10, 10.0))
    plt.ylabel("Average sentiment")
    plt.xlabel("Dates")
    plt.grid(True)
    plt.subplots_adjust(left=0.05, bottom=0.3, top=0.9, wspace=0, hspace=0)
    plt.tick_params(axis='x', which='major', labelsize=12)
    plt.xticks(range(len(avgs)), df.created_at.unique(), rotation=0)
    plt.title("Temporal variation of public sentiment")
    topStdAvg = []
    botStdAvg = []

    for date in avgs.keys():
        topStdAvg.append(avgs[date] + devs[date])
        botStdAvg.append(avgs[date] - devs[date])

    plt.plot(topStdAvg, 'g:', label = 'Standard Deviation +')
    plt.plot(botStdAvg, 'r:', label = "Standard Deviation -")
    plt.plot(avgs.values(), "b-",label = "Sentiment", lw = 3)
    plt.legend(loc='upper right', bbox_to_anchor=(1.115, 1), fontsize = 13)
    plt.text(-1, posTextY, dates_text, horizontalalignment='left', verticalalignment='center', bbox=dict(facecolor='red', alpha=0.3), fontsize = 16)
    plt.savefig(filename)
    plt.close()
    print(OKGREEN + "Plot saved in \"" + filename + "\"" + ENDC)

"""
    Parses collected tweets as nodes in gexf format, which links are quotes of other tweets. For each day, a specific graph is created, static and directed. Attributes of a node are:
            'id_str'
            'full_text'
            'created_at'
            'username'
            'retweet_count'
            'sa'

        If a tweet retrieved is a quote ('is_quote_status' == True) then another node is created (and linked) containing:
            'quoted_tweet_id'
            'quoted_tweet_username'
            'quoted_tweet_full_text'
"""
def gexf_parser(df, date):
    # Wrapping qualified XML names (providen from XMLSchema-instance)
    attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
    gexf = etree.Element('gexf', {attr_qname : 'http://www.gexf.net/1.3draft  http://www.gexf.net/1.3draft/gexf.xsd'}, nsmap={None : 'http://graphml.graphdrawing.org/xmlns/graphml'}, version = '1.3')

    graph = etree.SubElement(gexf, 'graph', defaultedgetype = 'directed', mode =  'static', timeformat='datetime')
    attributes = etree.SubElement(graph, 'attributes', {'class' : 'node', 'mode' : 'static'})
    etree.SubElement(attributes, 'attribute', {'id':'id', 'title':'id', 'type' : 'string'})
    etree.SubElement(attributes, 'attribute', {'id':'user', 'title':'user', 'type' : 'string'})
    etree.SubElement(attributes, 'attribute', {'id':'text', 'title':'text', 'type' : 'string'})
    etree.SubElement(attributes, 'attribute', {'id':'sentiment', 'title':'sentiment', 'type' : 'float'})
    etree.SubElement(attributes, 'attribute', {'id':'in_degree', 'title':'in_degree', 'type' : 'integer'})
    etree.SubElement(attributes, 'attribute', {'id':'out_degree', 'title':'out_degree', 'type' : 'integer'})
    etree.SubElement(attributes, 'attribute', {'id':'sharing', 'title':'sharing', 'type' : 'integer'})

    nodes = etree.SubElement(graph, 'nodes')
    edges = etree.SubElement(graph, 'edges')
    filename = "GEXF/GEXF_" + str(date) + ".gexf"
    print(WARNING + "Creating gexf file for " + str(date) + "... " + ENDC, end="")

    for tweet in df.loc[df['created_at'] == date].to_dict(orient='records'):
        node = etree.SubElement(nodes, 'node', id = tweet['id_str'], Label = tweet['id_str'])
        attvalues = etree.SubElement(node, 'attvalues')

        etree.SubElement(attvalues, 'attvalue', {'for' : 'user', 'value' : tweet['username']})
        etree.SubElement(attvalues, 'attvalue', {'for' : 'text', 'value' : tweet['full_text']})
        etree.SubElement(attvalues, 'attvalue', {'for' : 'sentiment', 'value' : str(tweet['sa'])})
        etree.SubElement(attvalues, 'attvalue', {'for' : 'in_degree', 'value' : str(tweet['retweet_count'])})
        sharing = tweet['retweet_count'] + tweet['favorite_count']
        etree.SubElement(attvalues, 'attvalue', {'for' : 'sharing', 'value' : str(sharing)})

        if tweet['is_quote_status']:
            etree.SubElement(attvalues, 'attvalue', {'for' : 'out_degree', 'value' : '1'})
            etree.SubElement(edges, 'edge', {'id' : tweet['id_str'], 'source' : tweet['id_str'], 'target' : tweet['quoted_tweet_id']})
            node = etree.SubElement(nodes, 'node', id = tweet['quoted_tweet_id'], Label = tweet['quoted_tweet_id'])
            attvalues = etree.SubElement(node, 'attvalues')
            etree.SubElement(attvalues, 'attvalue', {'for' : 'user', 'value' : tweet['quoted_tweet_username']})
            etree.SubElement(attvalues, 'attvalue', {'for' : 'text', 'value' : tweet['quoted_tweet_full_text']})
        else:
            etree.SubElement(attvalues, 'attvalue', {'for' : 'out_degree', 'value' : '0'})

    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(etree.tostring(gexf, encoding='utf8', method='xml').decode('utf-8'))
        print(OKGREEN + filename + " created" + ENDC)