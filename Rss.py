import feedparser
import logging
import os
import rfeed
import urllib


def __getVideoIdFromRssItem(item):
    url = urllib.parse.urlparse(item['link'])
    return urllib.parse.parse_qs(url.query)['videoID'][0]


def getTitleAndVideoIds(rssUrl='http://parlview.aph.gov.au/browse.php?&rss=1'):
    feed = feedparser.parse( rssUrl )
    return [(item['title'], __getVideoIdFromRssItem(item)) for item in feed['items']]

def generateFeed(podcast, urlPrefix, feedName, directory):
    items = [rfeed.Item(title=item[0], link=urlPrefix+'media/'+item[1]+'.m4a') for item in podcast]
    feed = rfeed.Feed(title='Non-official podcast of the Parliament of Australia', description='Non-official podcast of the Parliament of Australia', link='https://parlpod.datapunch.net', items=items)
    with open(os.path.join(directory, feedName+'.xml'), 'w') as f:
        f.write(feed.rss())

if __name__ == '__main__':
    logging.basicConfig()
    print(getTitleAndVideoIds())