from googleapiclient.discovery import build
import re
import datetime
from dateutil.relativedelta import relativedelta
import json
import requests



def toIsoString(dateObject):
  return dateObject.strftime("%Y-%m-%dT%H:%M:%SZ") 

def getNMonthsOldDate(n):
  today = datetime.date.today()
  past_date = today - relativedelta(months=n)
  return past_date

#print(toIsoString(getNMonthsOldDate(2)))


api_key = 'your_key_here';

custom_link_with_ending_slash = 'youtube.com\/c\/(.*?)\/'
custom_link_with_no_ending = 'youtube.com\/c\/(.*)'
custom_link_without_c = 'youtube.com\/(.*)'

channel_url_with_ending_slash = 'youtube.com\/channel\/(.*?)\/'
channel_url_with_no_ending = 'youtube.com\/channel\/(.*)'

youtube_url_with_dot = 'youtu.be\/(.*)'
youtube_watch_video_url = 'youtube.com\/watch\?v\=(.*)'
youtube_watch_video_url_with_timestamp = 'youtu.be\/(.*)?'

youtube_user_url = 'youtube.com\/user\/(.*)'

youtube_service = build('youtube','v3', developerKey=api_key)

USER = 'user'
CHANNEL = 'channel'
VIEWING = 'viewing'
CUSTOM = 'custom'

def classifyUrl(youtubeurl):
  if re.search(youtube_user_url, youtubeurl):
    return USER

  elif re.search(channel_url_with_ending_slash, youtubeurl) or re.search(channel_url_with_no_ending, youtubeurl):
    return CHANNEL

  elif re.search(youtube_url_with_dot, youtubeurl) or re.search(youtube_watch_video_url, youtubeurl) or re.search(youtube_watch_video_url_with_timestamp, youtubeurl):
    return VIEWING

  elif re.search(custom_link_with_ending_slash, youtubeurl) or re.search(custom_link_with_no_ending, youtubeurl) or re.search(custom_link_without_c, youtubeurl):
    return CUSTOM

#classifyUrl('https://youtu.be/b2yZgFWWS-g')

def getCustomUrlId(custom_url):
  if re.search(custom_link_with_ending_slash, custom_url):
    return re.search(custom_link_with_ending_slash, custom_url).groups()[0]
  
  if re.search(custom_link_with_no_ending, custom_url):
    return re.search(custom_link_with_no_ending, custom_url).groups()[0]

  if re.search(custom_link_without_c, custom_url):
    return re.search(custom_link_without_c, custom_url).groups()[0]

def getChannelIdFromChannelUrl(channelUrl):
  if re.search(channel_url_with_ending_slash, channelUrl):
    return re.search(channel_url_with_ending_slash, channelUrl).groups()[0]

  if re.search(channel_url_with_no_ending, channelUrl):
    return re.search(channel_url_with_no_ending, channelUrl).groups()[0]

def getVideoIdFromVideoUrl(videoUrl):
  if re.search(youtube_url_with_dot, videoUrl):
    return re.search(youtube_url_with_dot, videoUrl).groups()[0]

  if re.search(youtube_watch_video_url, videoUrl):
    return re.search(youtube_watch_video_url, videoUrl).groups()[0]

  if re.search(youtube_watch_video_url_with_timestamp, videoUrl):
    return re.search(youtube_watch_video_url_with_timestamp, videoUrl).groups()[0]


#print(getVideoIdFromVideoUrl('https://www.youtube.com/watch?v=MGN6dNDq6Fs'))

def getUserIdFromUserUrl(userUrl):
  if re.search(youtube_user_url, userUrl):
    return re.search(youtube_user_url, userUrl).groups()[0]

#print(getUserIdFromUserUrl('https://www.youtube.com/user/AddictedA1'))

def getChannelIdFromVideoId(videoId):
  request = youtube_service.videos().list(
    part="snippet",
    id=videoId
  )
  response = request.execute()
  return response['items'][0]['snippet']['channelId']

#print(getChannelIdFromVideoId('MGN6dNDq6Fs'))

def getChannelDetailsFromUserId(userId):
  request = youtube_service.channels().list(
    part="snippet, contentDetails, statistics",
    forUsername=userId
  )
  response = request.execute()
  return {
    'id': response['items'][0]['id'],
    'title': response['items'][0]['snippet']['title'],
    'description': response['items'][0]['snippet']['description'],
    'thumbnails': response['items'][0]['snippet']['thumbnails'],
    'statistics': response['items'][0]['statistics']
  }

#print(getChannelDetailsFromUserId('AddictedA1'))

def getChannelDetailFromCustomUrlId(customUrlId):
  request = youtube_service.search().list(
    part="snippet",
    maxResults="1",
    q=customUrlId,
    type="channel"
  )

  response = request.execute()
  if len(response['items']) > 0:
    return {
      'id': response['items'][0]['id']['channelId'],
      'title': response['items'][0]['snippet']['title'],
      'description': response['items'][0]['snippet']['description'],
      'thumbnails': response['items'][0]['snippet']['thumbnails']
    }
  else:
    return {}

#print(getChannelDetailFromCustomUrlId('TrendingviralChannel'))


def getChannelDetailsFromChannelId(channelId):
  request = youtube_service.channels().list(
    part="snippet, contentDetails, statistics",
    id=channelId,
  )
  response = request.execute()
  return {
    'id': response['items'][0]['id'],
    'title': response['items'][0]['snippet']['title'],
    'description': response['items'][0]['snippet']['description'],
    'thumbnails': response['items'][0]['snippet']['thumbnails'],
    'statistics': response['items'][0]['statistics']
  }

def getChannelStatisticsFromChannelId(channelId):
  request = youtube_service.channels().list(
    part="statistics",
    id=channelId,
  )
  response = request.execute()
  return {
    'statistics': response['items'][0]['statistics']
  }

numberOfVideosThresholdToIgnoreMonthlyVideos = 25

def getVideosFromChannelId(channelId, fromMonth = 1):
  maxResultsCount = numberOfVideosThresholdToIgnoreMonthlyVideos + 1
  request = youtube_service.activities().list(
    part="contentDetails", 
    channelId=channelId,
    maxResults=maxResultsCount,
    publishedAfter=toIsoString(getNMonthsOldDate(fromMonth))
  )
  response = request.execute()
  return {'items': response['items'], 'pageInfo': response['pageInfo']}


def areVideosPresentInResults(items):
  i = 0
  foundVideo = False
  while i < len(items):
    result = items[i]
    if 'contentDetails' in result and 'upload' in result['contentDetails'] and 'videoId' in result['contentDetails']['upload']:
      foundVideo = True
    i += 1
  return foundVideo


#some youtubers may have a lot of uploads - and some may have very few - so we try to get data for more months in case someone has very few, also try to only get the videos not other type of activity
def tryToGetVideosForYoutubers(channelId):
  areVideosStillEmpty = True
  fromMonth = 1
  videos_response = ''
  while areVideosStillEmpty:
    videos_response = getVideosFromChannelId(channelId, fromMonth)
    if areVideosPresentInResults(videos_response['items']):
      areVideosStillEmpty = False
      break
    fromMonth += 1

  i = 0
  filtered_video_response = []
  while i < len(videos_response['items']):
    result = videos_response['items'][i]
    if 'contentDetails' in result and 'upload' in result['contentDetails'] and 'videoId' in result['contentDetails']['upload']:
      filtered_video_response.append(result)
    i += 1
   #['pageInfo']['totalResults'] 
  return {'items': filtered_video_response, 'pageInfo': {'totalResults': len(filtered_video_response)}}


#tryToGetVideosForYoutubers('UCQ_PBHyuILW2CKjVDuwhW4w')


def getVideoDetailsFromVideoId(videoId):
  request = youtube_service.videos().list(
    part='statistics',
    id=videoId
  )
  response = request.execute()
  return response['items'][0]['statistics']

#getVideoDetailsFromVideoId('MGN6dNDq6Fs')



def calculateAverageViewsFromStatistics(statistics):
  averageViews = int(int(statistics['viewCount']) / int(statistics['videoCount']))
  return averageViews

def getChannelDetails(channelId):
  videoResult = tryToGetVideosForYoutubers(channelId)
  channelDetails = getChannelDetailsFromChannelId(channelId)
  allChannelDetails = channelDetails.copy()
  channelStatistics = allChannelDetails['statistics']
  allChannelDetails['average_views'] = int(channelStatistics['viewCount']) / int(channelStatistics['videoCount'])
  video_details = []
  index = 0
  videos = videoResult['items']
  average_views = 0
  #get all youtube videos from the result
  if(videoResult['pageInfo']['totalResults'] <= numberOfVideosThresholdToIgnoreMonthlyVideos):
    while index < len(videos):
      video_id = videos[index]['contentDetails']['upload']['videoId']
      videoDetail = getVideoDetailsFromVideoId(video_id)
      video_details.append(videoDetail)
      index += 1
    index = 0
    while index < len(video_details):
      average_views += int(video_details[index]['viewCount'])
      index += 1
    average_views = average_views / index
    allChannelDetails['average_views'] = average_views

  return allChannelDetails


def findChannelIdFromCustomUrl(url):
  page = requests.get(url)
  source = page.text
  result = source.find('"channelUrl"')
  if result != -1:
    channel =  source[result+14:result+70]
    channelId = channel.find('channel/')
    return channel[channelId + 8:]
  return False

def getAllDetailsFromAnyUrl(url):
  typeOfUrl = classifyUrl(url)
  channelDetails = {}
  channelId = ''
  if typeOfUrl == USER:
    user_id = getUserIdFromUserUrl(url)
    if user_id:
      channelDetails = getChannelDetailsFromUserId(user_id)
      channelId = channelDetails['id']
  elif typeOfUrl == CHANNEL:
    channelId = getChannelIdFromChannelUrl(url)
    if channelId:
      channelDetails = getChannelDetailsFromChannelId(channelId)
  elif typeOfUrl == VIEWING:
    video_id = getVideoIdFromVideoUrl(url)
    if video_id:
      channelId = getChannelIdFromVideoId(video_id)
      channelDetails = getChannelDetailsFromChannelId(channelId)
  elif typeOfUrl == CUSTOM:
    channelId = findChannelIdFromCustomUrl(url);
    if channelId:
      channelDetails = getChannelDetailsFromChannelId(channelId)
    """ if custom_url_id:
      channelDetails = getChannelDetailFromCustomUrlId(custom_url_id)
      if 'id' in channelDetails:
        channelId = channelDetails['id']
        statisticsData = getChannelStatisticsFromChannelId(channelId)
        channelDetails['statistics'] = statisticsData['statistics'] """
  if 'statistics' in channelDetails:
    channelDetails['average_views'] = calculateAverageViewsFromStatistics(channelDetails['statistics'])

  
  if channelId:
    videoResult = tryToGetVideosForYoutubers(channelId)
    video_details = []
    video_ids = []
    index = 0
    videos = videoResult['items']
    average_views = 0

    if videoResult['pageInfo']['totalResults'] <= numberOfVideosThresholdToIgnoreMonthlyVideos and len(videos) > 0:
      while index < len(videos):
        videoContent = videos[index]['contentDetails']
        if videoContent and 'upload' in videoContent and 'videoId' in videoContent['upload']:
          video_id = videoContent['upload']['videoId']
          videoDetail = getVideoDetailsFromVideoId(video_id)
          video_details.append(videoDetail)
        index += 1
      index = 0
      while index < len(video_details):
        average_views += int(video_details[index]['viewCount'])
        index += 1
      average_views = int(average_views / index)
      channelDetails['average_views_from_last_month_video'] = average_views
    index = 0
    while index < len(videos) and len(videos) > 0:
      videoContent = videos[index]['contentDetails']
      if videoContent and 'upload' in videoContent and 'videoId' in videoContent['upload']:
        video_id = videoContent['upload']['videoId']
        video_ids.append(video_id)
      index += 1
    index = 0
    channelDetails['video_ids'] = video_ids
      
  print(json.dumps(channelDetails, indent=2))
    
getAllDetailsFromAnyUrl('https://youtube.com/c/NamasteBike')




#findChannelIdFromCustomUrl('https://youtube.com/c/ExploreTheUnseen2')


youtube_service.close()


