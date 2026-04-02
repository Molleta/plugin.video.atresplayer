import xbmc
import xbmcgui
import xbmcplugin

def list_videos():
    # This function will list videos from the plugin
    videos = [
        {'title': 'Video 1', 'url': 'http://example.com/video1'},
        {'title': 'Video 2', 'url': 'http://example.com/video2'}
    ]
    for video in videos:
        li = xbmcgui.ListItem(label=video['title'])
        xbmcplugin.addDirectoryItem(handle=plugin_handle, url=video['url'], listitem=li)
    xbmcplugin.endOfDirectory(plugin_handle)


def play_video(url):
    # This function will play the selected video
    xbmc.Player().play(url)

# Main plugin handle initialization
plugin_handle = int(sys.argv[1])

# List videos when the plugin is run
list_videos()