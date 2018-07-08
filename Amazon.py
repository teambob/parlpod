import boto3
import botocore.errorfactory
import os

class Amazon:
    def __init__(self, bucketName):
        self.s3 = boto3.client("s3")
        self.bucketName = bucketName

    def __checkVideoId(self, videoId):
        try:
            self.s3.head_object(Bucket=self.bucketName, Key='media/{videoId}.m4a'.format(videoId=videoId))
            return True
        except botocore.errorfactory.ClientError:
            return False

    def checkVideoIds(self, videoIds):
        return [videoId for videoId in videoIds if self.__checkVideoId(videoId)]


    def uploadMedia(self, filenames):
        for filename in filenames:
            self.s3.upload_file(Filename=filename, Bucket=self.bucketName, Key='media/{basename}'.format(basename=os.path.basename(filename)))

    def uploadRss(self, filename):
        self.s3.upload_file(Filename=filename, Bucket=self.bucketName, Key='rss/{basename}'.format(basename=os.path.basename(filename)))