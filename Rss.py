import feedparser
import logging
import os
import rfeed
import urllib

class RssReader:
    def __getVideoIdFromRssItem(self, item):
        url = urllib.parse.urlparse(item['link'])
        return urllib.parse.parse_qs(url.query)['videoID'][0]


    def getTitleAndVideoIds(self, rssUrl='http://parlview.aph.gov.au/browse.php?&rss=1'):
        feed = feedparser.parse( rssUrl )
        return [{'title': item['title'], 'video_id': self.__getVideoIdFromRssItem(item)} for item in feed['items']]

class RssWriter:
    def __init__(self, urlPrefix, directory):
        self.urlPrefix = urlPrefix
        self.directory = directory

    def __createItem(self, item):
        link = self.urlPrefix + 'media/' + item['video_id'] + '.m4a'
        return rfeed.Item(title=item['title'], enclosure=rfeed.Enclosure(url=link, length=0, type='audio/mp4'), guid=rfeed.Guid(link), pubDate=item['date'])

    def generateFeed(self, podcast, feedName):

        items = [self.__createItem(item) for item in podcast]
        feed = rfeed.Feed(title='Non-official podcast of the Parliament of Australia', description='Non-official podcast of the Parliament of Australia', link='https://parlpod.datapunch.net', items=items)
        with open(os.path.join(self.directory, feedName+'.xml'), 'w') as f:
            f.write(feed.rss())

if __name__ == '__main__':
    logging.basicConfig()
    reader = RssReader()
    print(reader.getTitleAndVideoIds())