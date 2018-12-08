import boto3
import botocore.exceptions
import logging
import os

class Amazon:
    def __init__(self, bucketName):
        self.s3 = boto3.client("s3")
        self.bucketName = bucketName

    def __checkVideoId(self, videoId):
        try:
            self.s3.head_object(Bucket=self.bucketName, Key='media/{videoId}.m4a'.format(videoId=videoId))
            return True
        except botocore.exceptions.ClientError:
            return False

    def __getS3VideoIds(self):
        return [os.path.splitext(os.path.basename(path['Key']))[0] for path in self.s3.list_objects_v2(Bucket=self.bucketName, Prefix='media/').get('Contents', list())]

    def checkVideoIds(self, videoIds):
        s3VideoIds = self.__getS3VideoIds()
        logging.info("s3VideoIds: %s", ",".join(s3VideoIds))
        return list(set(videoIds).intersection(s3VideoIds))
        #return [videoId for videoId in videoIds if not self.__checkVideoId(videoId)]


    def uploadMedia(self, filenames):
        for filename in filenames:
            logging.debug("Uploading {filename}".format(filename=filename))
            self.s3.upload_file(Filename=filename, Bucket=self.bucketName, Key='media/{basename}'.format(basename=os.path.basename(filename)))

    def uploadRss(self, filename):
        self.s3.upload_file(Filename=filename, Bucket=self.bucketName, Key='rss/{basename}'.format(basename=os.path.basename(filename)))
