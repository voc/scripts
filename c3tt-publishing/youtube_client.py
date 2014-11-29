#!/usr/bin/python3
#    Copyright (C) 2014  derpeter
#    derpeter@berlin.ccc.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Call like this:
#     try:
#         youtubeUrl = publish_youtube(ticket, config['youtube']['secret'])
#         setTicketProperties(ticket_id, {'YouTube.Url': youtubeUrl}, url, group, host, secret)
#     except RuntimeError as err:
#         setTicketFailed(ticket_id, "Publishing failed: \n" + str(err), url, group, host, secret)
#         logging.error("Publishing failed: \n" + str(err))
#         sys.exit(-1)

import logging, requests, json, mimetypes, os
logger = logging.getLogger()

# publish a file on youtube
def publish_youtube(ticket, clientId, clientSecret):
    logger.info("publishing Ticket %s (%s) to youtube" % (ticket['Fahrplan.ID'], ticket['Fahrplan.Title']))

    if not 'Publishing.YouTube.Token' in ticket:
        raise RuntimeError('Property "Publishing.YouTube.Token" missing in ticket - did you set the YouTube-Properties on the Project?')

    accessToken = getFreshToken(ticket['Publishing.YouTube.Token'], clientId, clientSecret)
    channelId = getChannelId(accessToken)
    videoId = uploadVideo(ticket, accessToken, channelId)
    addToPlaylists(ticket, videoId, accessToken, channelId)

    videoUrl = 'https://www.youtube.com/watch?v='+videoId
    logger.info("successfully published Ticket to %s" % videoUrl)
    return videoUrl

def uploadVideo(ticket, accessToken, channelId):
    metadata = {
        'snippet':
        {
            'title': str(ticket['Fahrplan.Title']),
            'description': "%s\n\n%s" % (ticket['Fahrplan.Abstract'], ticket['Fahrplan.Person_list']),
            'channelId': channelId,
        },
        'status':
        {
            'privacyStatus': ticket.get('Publishing.YouTube.Privacy', 'private'),
            'embeddable': True,
            'publicStatsViewable': True,
            'license': 'creativeCommon',
        },
    }

    if 'Publishing.YouTube.Tags' in ticket:
        metadata['snippet']['tags'] = ticket['Publishing.YouTube.Tags'].split(',')

    # 1 => Film & Animation
    # 2 => Autos & Vehicles
    # 10 => Music
    # 15 => Pets & Animals
    # 17 => Sports
    # 18 => Short Movies
    # 19 => Travel & Events
    # 20 => Gaming
    # 21 => Videoblogging
    # 22 => People & Blogs
    # 23 => Comedy
    # 24 => Entertainment
    # 25 => News & Politics
    # 26 => Howto & Style
    # 27 => Education
    # 28 => Science & Technology
    # 30 => Movies
    # 31 => Anime/Animation
    # 32 => Action/Adventure
    # 33 => Classics
    # 34 => Comedy
    # 35 => Documentary
    # 36 => Drama
    # 37 => Family
    # 38 => Foreign
    # 39 => Horror
    # 40 => Sci-Fi/Fantasy
    # 41 => Thriller
    # 42 => Shorts
    # 43 => Shows
    # 44 => Trailers
    if 'Publishing.YouTube.Category' in ticket:
        metadata['snippet']['categoryId'] = int(ticket['Publishing.YouTube.Category'])

    localfile = str(ticket['Publishing.Path']) + str(ticket['Fahrplan.ID']) + "." + ticket['EncodingProfile.Extension']
    (mimetype, encoding) = mimetypes.guess_type(localfile)
    size = os.stat(localfile).st_size

    logger.debug('guessed mimetype for file %s as %s and its size as %u bytes' % (localfile, mimetype, size))

    r = requests.post(
        'https://www.googleapis.com/upload/youtube/v3/videos',
        params={
            'uploadType': 'resumable',
            'part': 'snippet,status'
        },
        headers={
            'Authorization': 'Bearer '+accessToken,
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Upload-Content-Type': mimetype,
            'X-Upload-Content-Length': size,
        },
        data=json.dumps(metadata)
    )

    if 200 != r.status_code:
        raise RuntimeError('Video creation failed with error-code %u: %s' % (r.status_code, r.text))

    if not 'location' in r.headers:
        raise RuntimeError('Video creation did not return a location-header to upload to: %s' % (r.headers,))

    logger.info('successfully created video and received upload-url from %s' % (r.headers['server'] if 'server' in r.headers else '-'))
    logger.debug('uploading video-data to %s' % r.headers['location'])
    with open(localfile, 'rb') as fp:
        r = requests.put(
            r.headers['location'],
            headers={
                'Authorization': 'Bearer '+accessToken,
                'Content-Type': mimetype,
            },
            data=fp
        )

        if 200 != r.status_code or 201 != r.status_code:
            raise RuntimeError('uploading video failed with error-code %u: %s' % (r.status_code, r.text))

    video = r.json()

    youtubeurl = 'https://www.youtube.com/watch?v='+video['id']
    logger.info('successfully uploaded video as %s', youtubeurl)

    return video['id']

def getFreshToken(refreshToken, clientId, clientSecret):
    logger.debug('fetching fresh Access-Token on behalf of the refreshToken %s' % refreshToken)
    r = requests.post(
        'https://accounts.google.com/o/oauth2/token',
        data={
            'client_id': clientId,
            'client_secret': clientSecret,
            'refresh_token': refreshToken,
            'grant_type': 'refresh_token',
        }
    )

    if 200 != r.status_code:
        raise RuntimeError('fetching a fresh authToken failed with error-code %u: %s' % (r.status_code, r.text))

    data = r.json()
    if not 'access_token' in data:
        raise RuntimeError('fetching a fresh authToken did not return a access_token: %s' % r.text)

    logger.info("successfully fetched Access-Token %s" % data['access_token'])
    return data['access_token']

def getChannelId(accessToken):
    logger.debug('fetching Channel-Info on behalf of the accessToken %s' % accessToken)
    r = requests.get(
        'https://www.googleapis.com/youtube/v3/channels',
        headers={
            'Authorization': 'Bearer '+accessToken,
        },
        params={
            'part': 'id,brandingSettings',
            'mine': 'true',
        }
    )

    if 200 != r.status_code:
        raise RuntimeError('fetching a fresh authToken failed with error-code %u: %s' % (r.status_code, r.text))

    data = r.json()
    channel = data['items'][0]

    logger.info("successfully fetched Chanel-ID %s with name %s" % (channel['id'], channel['brandingSettings']['channel']['title']))
    return channel['id']

def addToPlaylists(ticket, videoId, accessToken, channelId):
    # TODO playlist by Album+Track, Album+Type, Album+Room, Album+Day

    ticketPlaylists = [ticket['Meta.Album'],]
    if 'Fahrplan.Track' in ticket:
        ticketPlaylists.append('%s — Track %s' % (ticket['Meta.Album'], ticket['Fahrplan.Track']))

    if 'Fahrplan.Type' in ticket:
        ticketPlaylists.append('%s — Type %s' % (ticket['Meta.Album'], ticket['Fahrplan.Type']))

    if 'Fahrplan.Day' in ticket:
        ticketPlaylists.append('%s — Day %s' % (ticket['Meta.Album'], ticket['Fahrplan.Day']))

    if 'Fahrplan.Room' in ticket:
        ticketPlaylists.append('%s — Room %s' % (ticket['Meta.Album'], ticket['Fahrplan.Room']))

    logger.debug('adding video to the following playlists: %s', ticketPlaylists)
    logger.debug('fetching list of playlists')
    r = requests.get(
        'https://www.googleapis.com/youtube/v3/playlists',
        params={
            'part': 'id,snippet',
            'channelId': channelId,
        },
        headers={
            'Authorization': 'Bearer '+accessToken,
        }
    )

    if 200 != r.status_code:
        raise RuntimeError('fetching list of playlists failed with error-code %u: %s' % (r.status_code, r.text))

    playlists = r.json()
    playlistIds = {}
    for item in playlists['items']:
        if item['snippet']['title'] in ticketPlaylists:
            playlistIds[ item['snippet']['title'] ] = item['id']

    logger.debug('found existing playlists with matching names: %s' % (playlistIds,))
    for name in ticketPlaylists:
        if not name in playlistIds:
            logger.debug('creating playlist "%s"' % name)
            r = requests.post(
                'https://www.googleapis.com/youtube/v3/playlists',
                params={
                    'part': 'snippet,status',
                },
                headers={
                    'Authorization': 'Bearer '+accessToken,
                    'Content-Type': 'application/json; charset=UTF-8',
                },
                data=json.dumps({
                    "status": {
                        "privacyStatus": "private"
                    },
                    "snippet": {
                        "title": name
                    }
                })
            )

            if 200 != r.status_code:
                raise RuntimeError('creating playlist failed with error-code %u: %s' % (r.status_code, r.text))

            playlist = r.json()
            playlistIds[name] = playlist['id']
            logger.info('created playlist "%s" as %s' % (name, playlist['id']))

    logger.debug('final list of playlists add the videos to is: %s' % (playlistIds,))
    for name in playlistIds:
        logger.debug('adding video to playlist "%s" (%s)' % (name, playlistIds[name]))
        s = json.dumps({
            "snippet": {
                "playlistId": playlistIds[name],
                "resourceId": {
                  "kind": 'youtube#video',
                  "videoId": videoId,
                }
            }
        })
        print(s)
        r = requests.post(
            'https://www.googleapis.com/youtube/v3/playlistItems',
            params={
                'part': 'snippet',
            },
            headers={
                'Authorization': 'Bearer '+accessToken,
                'Content-Type': 'application/json; charset=UTF-8',
            },
            data=s
        )

        if 200 != r.status_code:
            raise RuntimeError('adding video to playlist failed with error-code %u: %s' % (r.status_code, r.text))

        logger.info('successfully added video to playlist "%s" (%s)' % (name, playlistIds[name]))
