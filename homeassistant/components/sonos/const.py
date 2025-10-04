"""Constants for the Sonos integration."""
from __future__ import annotations

import datetime

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.const import Platform

DOMAIN = "sonos"
DATA_SONOS_DISCOVERY_MANAGER = "sonos_discovery_manager"

UPNP_ST = "urn:schemas-upnp-org:device:ZonePlayer:1"

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

SUB_FAIL_ISSUE_ID = "subscriptions_failed"
SUB_FAIL_URL = "https://www.home-assistant.io/integrations/sonos/#network-requirements"

# Sonos Internal Media Types
SONOS_ALBUM = "albums"
SONOS_ALBUM_ARTIST = "album_artists"
SONOS_ARTIST = "artists"
SONOS_AUDIO_BOOK = "audio book"
SONOS_COMPOSER = "composers"
SONOS_GENRE = "genres"
SONOS_OTHER_ITEM = "other items"
SONOS_PLAYLISTS = "playlists"
SONOS_RADIO = "radio"
SONOS_SHARE = "share"
SONOS_TRACKS = "tracks"

MEDIA_TYPE_DIRECTORY = MediaClass.DIRECTORY

# UPnP object types
UPNP_OBJECT_CONTAINER = "object.container"
UPNP_OBJECT_ALBUM = "object.container.album.musicAlbum"
UPNP_OBJECT_GENRE = "object.container.genre.musicGenre"
UPNP_OBJECT_COMPOSER = "object.container.person.composer"
UPNP_OBJECT_ARTIST = "object.container.person.musicArtist"
UPNP_OBJECT_PLAYLIST_CONTAINER = "object.container.playlistContainer"
UPNP_OBJECT_PLAYLIST_SAME_ARTIST = "object.container.playlistContainer.sameArtist"
UPNP_OBJECT_ITEM = "object.item"
UPNP_OBJECT_TRACK = "object.item.audioItem.musicTrack"
UPNP_OBJECT_BROADCAST = "object.item.audioItem.audioBroadcast"
UPNP_OBJECT_AUDIOBOOK = "object.item.audioItem.audioBook"

# Sonos Library keys
LIB_KEY_ALBUM = "A:ALBUM"
LIB_KEY_ALBUM_ARTIST = "A:ALBUMARTIST"
LIB_KEY_ARTIST = "A:ARTIST"
LIB_KEY_COMPOSER = "A:COMPOSER"
LIB_KEY_GENRE = "A:GENRE"
LIB_KEY_PLAYLISTS = "A:PLAYLISTS"
LIB_KEY_TRACKS = "A:TRACKS"
LIB_KEY_FOLDERS = "S:"

# Sonos States
SONOS_STATE_PLAYING = "PLAYING"
SONOS_STATE_TRANSITIONING = "TRANSITIONING"

EXPANDABLE_MEDIA_TYPES = [
    MediaType.ALBUM,
    MediaType.ARTIST,
    MediaType.COMPOSER,
    MediaType.GENRE,
    MediaType.PLAYLIST,
    MEDIA_TYPE_DIRECTORY,
    SONOS_ALBUM,
    SONOS_ALBUM_ARTIST,
    SONOS_ARTIST,
    SONOS_GENRE,
    SONOS_COMPOSER,
    SONOS_PLAYLISTS,
    SONOS_SHARE,
]

PLAYABLE_MEDIA_TYPES = [
    MediaType.ALBUM,
    MediaType.ARTIST,
    MediaType.COMPOSER,
    MediaType.CONTRIBUTING_ARTIST,
    MediaType.GENRE,
    MediaType.PLAYLIST,
    MediaType.TRACK,
]

# Mappings
SONOS_TO_MEDIA_CLASSES = {
    SONOS_ALBUM: MediaClass.ALBUM,
    SONOS_ALBUM_ARTIST: MediaClass.ARTIST,
    SONOS_ARTIST: MediaClass.CONTRIBUTING_ARTIST,
    SONOS_COMPOSER: MediaClass.COMPOSER,
    SONOS_GENRE: MediaClass.GENRE,
    SONOS_PLAYLISTS: MediaClass.PLAYLIST,
    SONOS_TRACKS: MediaClass.TRACK,
    SONOS_SHARE: MediaClass.DIRECTORY,
    UPNP_OBJECT_CONTAINER: MediaClass.DIRECTORY,
    UPNP_OBJECT_ALBUM: MediaClass.ALBUM,
    UPNP_OBJECT_GENRE: MediaClass.PLAYLIST,
    UPNP_OBJECT_COMPOSER: MediaClass.PLAYLIST,
    UPNP_OBJECT_ARTIST: MediaClass.ARTIST,
    UPNP_OBJECT_PLAYLIST_SAME_ARTIST: MediaClass.ARTIST,
    UPNP_OBJECT_PLAYLIST_CONTAINER: MediaClass.PLAYLIST,
    UPNP_OBJECT_ITEM: MediaClass.TRACK,
    UPNP_OBJECT_TRACK: MediaClass.TRACK,
    UPNP_OBJECT_BROADCAST: MediaClass.GENRE,
    UPNP_OBJECT_AUDIOBOOK: MediaClass.TRACK,
}

SONOS_TO_MEDIA_TYPES = {
    SONOS_ALBUM: MediaType.ALBUM,
    SONOS_ALBUM_ARTIST: MediaType.ARTIST,
    SONOS_ARTIST: MediaType.CONTRIBUTING_ARTIST,
    SONOS_COMPOSER: MediaType.COMPOSER,
    SONOS_GENRE: MediaType.GENRE,
    SONOS_PLAYLISTS: MediaClass.PLAYLIST,
    SONOS_TRACKS: MediaType.TRACK,
    UPNP_OBJECT_CONTAINER: MEDIA_TYPE_DIRECTORY,
    UPNP_OBJECT_ALBUM: MediaType.ALBUM,
    UPNP_OBJECT_GENRE: MediaClass.PLAYLIST,
    UPNP_OBJECT_COMPOSER: MediaClass.PLAYLIST,
    UPNP_OBJECT_ARTIST: MediaClass.ARTIST,
    UPNP_OBJECT_PLAYLIST_SAME_ARTIST: MediaClass.ARTIST,
    UPNP_OBJECT_PLAYLIST_CONTAINER: MediaClass.PLAYLIST,
    UPNP_OBJECT_TRACK: MediaType.TRACK,
    UPNP_OBJECT_AUDIOBOOK: MediaType.TRACK,
}

MEDIA_TYPES_TO_SONOS: dict[MediaType | str, str] = {
    MediaType.ALBUM: SONOS_ALBUM,
    MediaType.ARTIST: SONOS_ALBUM_ARTIST,
    MediaType.CONTRIBUTING_ARTIST: SONOS_ARTIST,
    MediaType.COMPOSER: SONOS_COMPOSER,
    MediaType.GENRE: SONOS_GENRE,
    MediaType.PLAYLIST: SONOS_PLAYLISTS,
    MediaType.TRACK: SONOS_TRACKS,
    MEDIA_TYPE_DIRECTORY: SONOS_SHARE,
}

SONOS_TYPES_MAPPING = {
    LIB_KEY_ALBUM: SONOS_ALBUM,
    LIB_KEY_ALBUM_ARTIST: SONOS_ALBUM_ARTIST,
    LIB_KEY_ARTIST: SONOS_ARTIST,
    LIB_KEY_COMPOSER: SONOS_COMPOSER,
    LIB_KEY_GENRE: SONOS_GENRE,
    LIB_KEY_PLAYLISTS: SONOS_PLAYLISTS,
    LIB_KEY_TRACKS: SONOS_TRACKS,
    UPNP_OBJECT_ALBUM: SONOS_ALBUM,
    UPNP_OBJECT_GENRE: SONOS_GENRE,
    UPNP_OBJECT_COMPOSER: SONOS_COMPOSER,
    UPNP_OBJECT_ARTIST: SONOS_ALBUM_ARTIST,
    UPNP_OBJECT_PLAYLIST_SAME_ARTIST: SONOS_ARTIST,
    UPNP_OBJECT_PLAYLIST_CONTAINER: SONOS_PLAYLISTS,
    UPNP_OBJECT_ITEM: SONOS_OTHER_ITEM,
    UPNP_OBJECT_TRACK: SONOS_TRACKS,
    UPNP_OBJECT_BROADCAST: SONOS_RADIO,
    UPNP_OBJECT_AUDIOBOOK: SONOS_AUDIO_BOOK,
}

LIBRARY_TITLES_MAPPING = {
    LIB_KEY_ALBUM: "Albums",
    LIB_KEY_ALBUM_ARTIST: "Artists",
    LIB_KEY_ARTIST: "Contributing Artists",
    LIB_KEY_COMPOSER: "Composers",
    LIB_KEY_GENRE: "Genres",
    LIB_KEY_PLAYLISTS: "Playlists",
    LIB_KEY_TRACKS: "Tracks",
    LIB_KEY_FOLDERS: "Folders",
}

# Event and Service Strings
SONOS_CHECK_ACTIVITY = "sonos_check_activity"
SONOS_CREATE_ALARM = "sonos_create_alarm"
SONOS_CREATE_AUDIO_FORMAT_SENSOR = "sonos_create_audio_format_sensor"
SONOS_CREATE_BATTERY = "sonos_create_battery"
SONOS_CREATE_FAVORITES_SENSOR = "sonos_create_favorites_sensor"
SONOS_CREATE_MIC_SENSOR = "sonos_create_mic_sensor"
SONOS_CREATE_SELECTS = "sonos_create_selects"
SONOS_CREATE_SWITCHES = "sonos_create_switches"
SONOS_CREATE_LEVELS = "sonos_create_levels"
SONOS_CREATE_MEDIA_PLAYER = "sonos_create_media_player"
SONOS_FALLBACK_POLL = "sonos_fallback_poll"
SONOS_ALARMS_UPDATED = "sonos_alarms_updated"
SONOS_FAVORITES_UPDATED = "sonos_favorites_updated"
SONOS_MEDIA_UPDATED = "sonos_media_updated"
SONOS_SPEAKER_ACTIVITY = "sonos_speaker_activity"
SONOS_SPEAKER_ADDED = "sonos_speaker_added"
SONOS_STATE_UPDATED = "sonos_state_updated"
SONOS_REBOOTED = "sonos_rebooted"
SONOS_VANISHED = "sonos_vanished"

# Source Types
SOURCE_AIRPLAY = "AirPlay"
SOURCE_LINEIN = "Line-in"
SOURCE_SPOTIFY_CONNECT = "Spotify Connect"
SOURCE_TV = "TV"

# Model Identifiers
MODELS_LINEIN_ONLY = ("CONNECT", "CONNECT:AMP", "PORT", "PLAY:5")
MODELS_TV_ONLY = ("ARC", "BEAM", "PLAYBAR", "PLAYBASE", "ULTRA")
MODELS_LINEIN_AND_TV = ("AMP",)
MODEL_SONOS_ARC_ULTRA = "SONOS ARC ULTRA"

# Attribute Keys
ATTR_SPEECH_ENHANCEMENT_ENABLED = "speech_enhance_enabled"
ATTR_DIALOG_LEVEL = "dialog_level"
ATTR_DIALOG_LEVEL_ENUM = "dialog_level_enum"
ATTR_QUEUE_POSITION = "queue_position"
SPEECH_DIALOG_LEVEL = "speech_dialog_level"

# Timeouts and Intervals
AVAILABILITY_CHECK_INTERVAL = datetime.timedelta(minutes=1)
AVAILABILITY_TIMEOUT = AVAILABILITY_CHECK_INTERVAL.total_seconds() * 4.5
BATTERY_SCAN_INTERVAL = datetime.timedelta(minutes=15)
SCAN_INTERVAL = datetime.timedelta(seconds=10)
DISCOVERY_INTERVAL = datetime.timedelta(seconds=60)
SUBSCRIPTION_TIMEOUT = 1200