# -*- coding: utf-8 -*-
import sys
import os
import urllib.parse
import requests
import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
from http.cookiejar import MozillaCookieJar

# --- CONFIGURACIÓN BÁSICA ---
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

MAIN_CHANNEL = "5a6b32667ed1a834493ec03b"
SERIES_CAT = "5a6a1b22986b281d18a512b8"
PROGRAMAS_CAT = "5a6a1ba0986b281d18a512b9"

# --- LOGIN / COOKIES PERSISTENTES ---

ADDON_ID = "plugin.video.atresplayer.omegaP1"
ADDON_DATA = xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}")
if not os.path.isdir(ADDON_DATA):
    os.makedirs(ADDON_DATA, exist_ok=True)

COOKIES_PATH = os.path.join(ADDON_DATA, "cookies_atres.dat")

SESSION = requests.Session()
CJ = MozillaCookieJar()

def load_cookies():
    if os.path.isfile(COOKIES_PATH):
        try:
            CJ.load(COOKIES_PATH, ignore_discard=True, ignore_expires=True)
            SESSION.cookies = CJ
        except:
            try:
                os.remove(COOKIES_PATH)
            except:
                pass

def save_cookies():
    try:
        CJ.save(COOKIES_PATH, ignore_discard=True, ignore_expires=True)
    except:
        pass

load_cookies()

# RELLENA ESTO CON TU CUENTA GRATUITA
USER_EMAIL = "email"
USER_PASSWORD = "password"

AUTH_COOKIES = None

def login():
    global AUTH_COOKIES

    if AUTH_COOKIES:
        return AUTH_COOKIES

    if not USER_EMAIL or USER_EMAIL == "TU_CORREO_AQUI":
        AUTH_COOKIES = ""
        return AUTH_COOKIES

    url = "https://api.atresplayer.com/auth/v1/login"
    headers = {
        "User-Agent": UA,
        "Origin": "https://www.atresplayer.com",
        "Referer": "https://www.atresplayer.com/"
    }
    payload = {
        "email": USER_EMAIL,
        "password": USER_PASSWORD,
        "remember": True
    }

    try:
        r = SESSION.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code != 200:
            AUTH_COOKIES = ""
            return AUTH_COOKIES

        for c in r.cookies:
            CJ.set_cookie(c)
        save_cookies()
        SESSION.cookies = CJ

        AUTH_COOKIES = "; ".join([f"{k}={v}" for k, v in SESSION.cookies.items()])
    except:
        AUTH_COOKIES = ""

    return AUTH_COOKIES

# --- HELPERS HTTP ---

def _normalize_url(url):
    if url.startswith('/'):
        url = "https://api.atresplayer.com" + url
    sep = '&' if '?' in url else '?'
    if 'v=' not in url:
        url += f"{sep}v=v2"
    return url

def get_json(url):
    headers = {
        'User-Agent': UA,
        'Referer': 'https://www.atresplayer.com/',
        'Origin': 'https://www.atresplayer.com'
    }
    try:
        url = _normalize_url(url)
        r = requests.get(url, headers=headers, timeout=15)
        return r.json()
    except:
        return {}

def get_json_auth(url):
    cookies = login()
    headers = {
        'User-Agent': UA,
        'Referer': 'https://www.atresplayer.com/',
        'Origin': 'https://www.atresplayer.com'
    }
    if cookies:
        headers['Cookie'] = cookies
    try:
        url = _normalize_url(url)
        r = SESSION.get(url, headers=headers, timeout=15)
        return r.json()
    except:
        return {}

def fix_image(img_path):
    if not img_path or not img_path.startswith('http'):
        return ""
    return img_path + "1280x720.jpg"

# --- NAVEGACIÓN ---

def menu_principal():
    cats = [
        ("📺 Directos (TV y FAST)", "https://api.atresplayer.com/client/v1/row/live", "MODO_GRID"),

        ("🎬 Series",
         f"/client/v1/row/search?entityType=ATPFormat&sectionCategory=true&mainChannelId={MAIN_CHANNEL}&categoryId={SERIES_CAT}&defaultSortType=THE_MOST&size=30",
         "MODO_GRID"),

        ("🎭 Programas",
         f"/client/v1/row/search?entityType=ATPFormat&sectionCategory=true&mainChannelId={MAIN_CHANNEL}&categoryId={PROGRAMAS_CAT}&defaultSortType=THE_MOST&size=30",
         "MODO_GRID"),

        ("🕒 Últimos 7 días",
         f"/client/v1/page/u7d/{MAIN_CHANNEL}",
         "MODO_U7D"),
    ]

    for t, u, m in cats:
        u_dir = f"{BASE_URL}?mode={m}&url={urllib.parse.quote_plus(u)}"
        xbmcplugin.addDirectoryItem(HANDLE, u_dir, xbmcgui.ListItem(label=t), True)

    xbmcplugin.endOfDirectory(HANDLE)

# --- LISTADO GENERAL (GRID) ---

def listar_grid(url):
    data = get_json(url)

    if isinstance(data, dict) and 'items' in data and isinstance(data['items'], list):
        rows = [{'items': data['items']}]
    else:
        rows = data.get('rows') or data.get('sections') or data.get('itemRows') or []

    for row in rows:
        if row.get("href") and not row.get("items") and not row.get("tiles") and not row.get("itemRows"):
            sub = get_json(row["href"])
            for key in ("items", "tiles", "itemRows"):
                if key in sub:
                    row[key] = sub[key]

        items = row.get('items') or row.get('tiles') or row.get('itemRows') or []

        if not items and 'link' in row:
            items = [row]

        for item in items:
            link = item.get('link')
            if not link:
                continue

            titulo = item.get('title', item.get('name', 'Sin título'))
            img = fix_image(item.get('image', {}).get('pathHorizontal', ''))
            url_api = link.get('href')
            p_type = link.get('pageType', '')

            if p_type == "LIVE_CHANNEL":
                v_type = "live"
                is_folder = False
            elif p_type == "VIDEO":
                v_type = "video"
                is_folder = False
            elif p_type == "RECORDING":
                v_type = "recording"
                is_folder = False
            elif p_type == "EPISODE":
                v_type = "episode"
                is_folder = False
            else:
                v_type = None
                is_folder = True

            if is_folder:
                u = f"{BASE_URL}?mode=MODO_TEMPORADAS&url={urllib.parse.quote_plus(url_api)}"
            else:
                v_id = url_api.strip('/').split('/')[-1]
                u = f"{BASE_URL}?mode=MODO_PLAY&id={v_id}&type={v_type}"

            li = xbmcgui.ListItem(label=titulo)
            li.setArt({'thumb': img, 'poster': img, 'fanart': img})

            if not is_folder:
                li.setProperty('IsPlayable', 'true')

            xbmcplugin.addDirectoryItem(HANDLE, u, li, is_folder)

    pageInfo = data.get("pageInfo")
    if pageInfo and pageInfo.get("hasNext"):
        next_page = pageInfo["pageNumber"] + 1
        base = url.split("?")[0]
        params = url.split("?")[1] if "?" in url else ""
        params += f"&page={next_page}"
        next_url = base + "?" + params

        u = f"{BASE_URL}?mode=MODO_GRID&url={urllib.parse.quote_plus(next_url)}"
        xbmcplugin.addDirectoryItem(HANDLE, u, xbmcgui.ListItem(label="➡️ Página siguiente"), True)

    xbmcplugin.endOfDirectory(HANDLE)

# --- U7D (solo episodios grabados) ---

def listar_u7d(url):
    data = get_json(url)
    rows = data.get("rows", [])

    for row in rows:
        href = row.get("href")
        if not href:
            continue

        sub = get_json(href)
        items = sub.get("itemRows", [])

        for item in items:
            link = item.get("link", {})
            href_ep = link.get("href")
            if not href_ep:
                continue

            v_id = href_ep.strip("/").split("/")[-1]
            titulo = item.get("title", "Episodio")
            img = fix_image(item.get("image", {}).get("pathHorizontal", ""))

            u = f"{BASE_URL}?mode=MODO_PLAY&id={v_id}&type=recording"

            li = xbmcgui.ListItem(label=titulo)
            li.setArt({"thumb": img, "poster": img, "fanart": img})
            li.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(HANDLE, u, li, False)

    xbmcplugin.endOfDirectory(HANDLE)

# --- EPISODIOS ---

def _listar_items_como_episodios(items):
    for item in items:
        link = item.get('link') or {}
        href = link.get('href')
        if not href:
            continue

        p_type = link.get('pageType', 'VIDEO')

        if p_type == "RECORDING":
            v_type = "recording"
        elif p_type == "LIVE_CHANNEL":
            v_type = "live"
        elif p_type == "VIDEO":
            v_type = "video"
        else:
            v_type = "episode"

        v_id = href.strip('/').split('/')[-1]
        titulo = item.get('title', 'Episodio')
        img = fix_image(item.get('image', {}).get('pathHorizontal', ''))
        u = f"{BASE_URL}?mode=MODO_PLAY&id={v_id}&type={v_type}"

        li = xbmcgui.ListItem(label=titulo)
        li.setArt({'thumb': img, 'poster': img, 'fanart': img})
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(HANDLE, u, li, False)

# --- TEMPORADAS / EPISODIOS ---

def listar_temporadas(url):
    data = get_json(url)

    if data.get("pageType") == "SEASON":
        rows = data.get("rows", [])
        for row in rows:
            if row.get("type") == "EPISODE" and row.get("href"):
                sub = get_json(row["href"])
                items = sub.get("items") or sub.get("itemRows") or sub.get("tiles") or []
                _listar_items_como_episodios(items)
                xbmcplugin.endOfDirectory(HANDLE)
                return

    for key in ("items", "itemRows", "tiles"):
        if key in data and isinstance(data[key], list):
            _listar_items_como_episodios(data[key])
            xbmcplugin.endOfDirectory(HANDLE)
            return

    seasons = data.get('seasons', [])
    if seasons:
        for season in seasons:
            href = season.get("link", {}).get("href")
            if not href:
                continue

            titulo = season.get('title', 'Temporada')
            u = f"{BASE_URL}?mode=MODO_TEMPORADAS&url={urllib.parse.quote_plus(href)}"
            xbmcplugin.addDirectoryItem(HANDLE, u, xbmcgui.ListItem(label=titulo), True)

        xbmcplugin.endOfDirectory(HANDLE)
        return

    rows = data.get('rows') or data.get('sections') or data.get('itemRows') or []

    for row in rows:
        for key in ("items", "itemRows", "tiles"):
            if key in row and isinstance(row[key], list):
                _listar_items_como_episodios(row[key])

    for row in rows:
        href = row.get("href")
        if not href:
            continue
        sub = get_json(href)
        for key in ("items", "itemRows", "tiles"):
            if key in sub and isinstance(sub[key], list):
                _listar_items_como_episodios(sub[key])

    xbmcplugin.endOfDirectory(HANDLE)

# --- DRM / WIDEVINE ---

def play_drm_mpd(mpd_url, license_url, cookies, user_agent=UA):
    headers = {
        "User-Agent": user_agent,
        "Cookie": cookies or ""
    }

    header_string = "&".join([f"{k}={urllib.parse.quote(v)}" for k, v in headers.items() if v])
    license_key = f"{license_url}|{header_string}|R{{SSM}}|"

    li = xbmcgui.ListItem(path=mpd_url)
    li.setProperty("inputstream", "inputstream.adaptive")
    li.setProperty("inputstream.adaptive.license_type", "com.widevine.alpha")
    li.setProperty("inputstream.adaptive.license_key", license_key)
    li.setProperty("inputstream.adaptive.stream_headers", header_string)

    xbmcplugin.setResolvedUrl(HANDLE, True, li)

# --- REPRODUCCIÓN 
def reproducir(v_id, v_type):
    """
    Versión estable: usa los endpoints clásicos player/v1/*
    pero siempre autenticados con get_json_auth()
    """

    if v_type == "recording":
        url_api = f"https://api.atresplayer.com/player/v1/recording/{v_id}?v=v2&visitorId=kodi_v2"

    elif v_type == "live":
        url_api = f"https://api.atresplayer.com/player/v1/live/{v_id}?v=v2&visitorId=kodi_v2"

    elif v_type in ("episode", "EPISODE", "ATPEpisode"):
        url_api = f"https://api.atresplayer.com/player/v1/episode/{v_id}?v=v2&visitorId=kodi_v2"

    elif v_type in ("video", "VIDEO", "ATPVideo"):
        url_api = f"https://api.atresplayer.com/player/v1/video/{v_id}?v=v2&visitorId=kodi_v2"

    else:
        url_api = f"https://api.atresplayer.com/player/v1/episode/{v_id}?v=v2&visitorId=kodi_v2"

    # 🔴 ANTES: data = get_json(url_api)
    # 🟢 AHORA: SIEMPRE AUTENTICADO
    data = get_json_auth(url_api)

    sources = data.get('sourcesLive') or data.get('sources') or []

    stream_url = ""
    manifest_type = ""
    for s in sources:
        if 'src' in s:
            stream_url = s['src']
            t = s.get('type', '').lower()
            if 'dash' in t:
                manifest_type = 'mpd'
            else:
                manifest_type = 'hls'
            break

    if stream_url:
        ref = "https://www.atresplayer.com/"
        headers_string = (
            f"User-Agent={urllib.parse.quote(UA)}"
            f"&Referer={urllib.parse.quote(ref)}"
            f"&Origin={urllib.parse.quote('https://www.atresplayer.com')}"
        )

        li = xbmcgui.ListItem(path=stream_url + "|" + headers_string)
        li.setProperty('inputstream', 'inputstream.adaptive')
        if manifest_type:
            li.setProperty('inputstream.adaptive.manifest_type', manifest_type)
        li.setProperty('inputstream.adaptive.stream_headers', headers_string)
        li.setProperty('inputstream.adaptive.manifest_headers', headers_string)

        if manifest_type == "hls":
            li.setProperty('inputstream.adaptive.m3u8_force_master', 'true')

        xbmcplugin.setResolvedUrl(HANDLE, True, li)
    else:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        xbmcgui.Dialog().ok("Atresplayer", "Error de acceso: Contenido Premium o bloqueado.")


# --- ROUTER ---

if len(sys.argv) >= 3:
    args = urllib.parse.parse_qs(sys.argv[2].lstrip('?'))
    mode = args.get('mode', [None])[0]
    if not mode:
        menu_principal()
    elif mode == "MODO_GRID":
        listar_grid(args.get('url', [""])[0])
    elif mode == "MODO_U7D":
        listar_u7d(args.get('url', [""])[0])
    elif mode == "MODO_TEMPORADAS":
        listar_temporadas(args.get('url', [""])[0])
    elif mode == "MODO_PLAY":
        reproducir(args.get('id', [""])[0], args.get('type', ['video'])[0])
else:
    menu_principal()
