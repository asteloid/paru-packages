# coding: utf-8

from __future__ import unicode_literals
import hashlib
import json
import re
import uuid

# ⚠ Don't use relative imports
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.compat import (
    compat_urllib_parse_quote,
    compat_urllib_parse_unquote,
)
from yt_dlp.utils import (
    ExtractorError,
    js_to_json,
    traverse_obj,
    urljoin,
)


# ℹ️ Instructions on making extractors can be found at:
# 🔗 https://github.com/ytdl-org/youtube-dl#adding-support-for-a-new-site

class ViuOTTNewBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'viu'
    _BASE_API_QUERY = {
        'ver': '1.0',
        'fmt': 'json',
        'aver': '5.0',
        'appver': '2.0',
        'appid': 'viu_desktop',
        'platform': 'desktop',
    }

    def _call_api(self, endpoint, video_id, *args, **kwargs):
        headers = kwargs.setdefault('headers', {})
        headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')
        headers.update({
            'Authorization': self._TOKEN,
            'x-session-id': str(uuid.uuid4()),
            'x-client': 'browser',
            'languageid': 'id',
            'lang_id': 'id',
            'ccode': 'ID',
        })
        kwargs.setdefault('data', b'')
        return self._download_json(
            urljoin('https://um.viuapi.io/', endpoint), video_id, *args, **kwargs)

    def _load_data(self, data_name, data_id, video_id, note, errnote):
        data_res = self._download_json('https://www.viu.com/ott/web/api/%s/load' % data_name, video_id, note=note, errnote=errnote, query={
            **self._BASE_API_QUERY,
            'id': data_id,
            'start': 0,
            'limit': 9999,
            'filter': 'mixed',
            'contentCountry': 'ID',
            'contentFlavour': 'all',
            'regionid': 'all',
            'languageid': 'id',
            'ccode': 'ID',
            'geo': 10,
            'iid': self._DEVICE_ID
        }, headers={
            'Content-Type': 'application/json',
            'X-Client': 'browser',
            'X-Session-Id': self._DEVICE_ID,
            'Authorization': 'Bearer ' + self._TOKEN,
        })['response']

        if data_res.get('message'):
            raise ExtractorError(data_res['message'], expected=True)
        return traverse_obj(data_res, data_name, ('item', ...), expected_type=dict, get_all=False)

    def _update_identity(self):
        self._TOKEN = self._download_json(
            'https://um.viuapi.io/user/identity', None, note='Downloading token', errnote='Unable to download token', query={
                **self._BASE_API_QUERY,
                'iid': self._DEVICE_ID,
            }, headers={
                'Content-Type': 'application/json',
                'X-Client': 'browser',
                'X-Session-Id': str(uuid.uuid4()),
            }, data=json.dumps({'deviceId': self._DEVICE_ID}).encode('utf-8'))['token']

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        login_res = self._download_json('https://um.viuapi.io/user/account', None, note='Logging in', errnote='Unable to log in', query={
                'ver': '1.0',
                'fmt': 'json',
                'aver': '5.0',
                'appver': '2.0',
                'appid': 'viu_desktop',
                'platform': 'desktop',
                'iid': self._DEVICE_ID,
            }, headers={
                'Content-Type': 'application/json',
                'X-Client': 'browser',
                'X-Session-Id': self._DEVICE_ID,
                'Authorization': self._TOKEN,
            }, data=json.dumps({
                'password': hashlib.md5(password.encode('utf-8')).hexdigest(),
                'principal': username,
                'providerCode': 'email'
            }).encode('utf-8'))
        if login_res.get('errorMessage'):
            raise ExtractorError(login_res['errorMessage'], expected=True)

        self._set_cookie('www.viu.com', 'user', compat_urllib_parse_quote(json.dumps({
            'email': username,
            'userName': username,
            'useridtype':'email',
            'newUser': 'false',
            'isVailidateCalled': 'false',
            'isVailidateFetching': 'false',
            'validatePasscodeStatus': '',
            'userId': self._DEVICE_ID,
            'token': self._TOKEN,
            'authLevel': 'STRONG',
            'responseCode': 200,
            **login_res
        }).encode('utf-8')))
        self._update_identity()

    def _real_initialize(self):
        if self._get_cookies('https://www.viu.com/').get('user'):
            decoded_user_cookie = self._parse_json(
                self._get_cookies('https://www.viu.com/')['user'].value, None, transform_source=compat_urllib_parse_unquote, fatal=False)
            if decoded_user_cookie:
                self._DEVICE_ID = decoded_user_cookie['userId']
                self._TOKEN = decoded_user_cookie['token']
                return

        self._DEVICE_ID = str(uuid.uuid4())
        self._update_identity()
        self._login()


class ViuOTTNewIE(ViuOTTNewBaseIE):
    IE_NAME = 'viu:ott:new'
    _VALID_URL = r'https?://(?:www\.)?viu\.com/ott/(?P<lang_code>[a-z]{2})/(?P<country_code>[a-z]{2})/all/video-(?:[\w-]*-)?(?P<id>\d+)'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_detail = self._load_data('clip', video_id, video_id, 'Downloading video details', 'Unable to download video details') or {}

        format_data = self._call_api('drm/v1/content/' + video_id, video_id)
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(format_data['playUrl'], video_id, 'mp4')
        self._sort_formats(formats)
        for name, url in video_detail.items():
            lang, ext = self._search_regex(
                r'^subtitle_(?P<lang>\w+)_(?P<ext>\w+)$', name, 'subtitle metadata', default=(None, None), group=('lang', 'ext'))
            if lang and ext:
                subtitles.setdefault(lang, []).append({
                    'ext': ext,
                    'url': url
                })

        return {
            'id': video_id,
            'title': video_detail.get('display_title') or video_id,
            'display_id': video_detail.get('slug'),
            'description': video_detail.get('description'),
            'creator': video_detail.get('CP_name') or video_detail.get('broadcaster'),
            'series': video_detail.get('movie_album_show_name'),
            'formats': formats,
            'subtitles': subtitles,
        }


class ViuOTTNewPlaylistIE(ViuOTTNewBaseIE):
    IE_NAME = 'viu:ott:new:playlist'
    _VALID_URL = r'https?://(?:www\.)?viu\.com/ott/(?P<lang_code>[a-z]{2})/(?P<country_code>[a-z]{2})/all/playlist-(?:[\w-]*-)?(?P<id>\d+)'

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        playlist_detail = self._load_data(
            'container', 'playlist-' + playlist_id, playlist_id, 'Downloading playlist details', 'Unable to download playlist details')

        return self.playlist_result([
            self.url_result(f'https://www.viu.com/ott/id/id/all/video-{playlist_detail["language"]}-{playlist_detail["contenttype"]}-_-{video["id"]}') for video in playlist_detail['item']],
            playlist_id, playlist_detail.get('title'), playlist_detail.get('description'))