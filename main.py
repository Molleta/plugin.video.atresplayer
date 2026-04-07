# -*- coding: utf-8 -*-
import sys
import urllib.parse
import requests
import xbmcgui
import xbmcplugin

# --- CONFIGURACIÓN ---
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
HEADERS = {
    'User-Agent': UA,
    'Referer': 'https://www.atresplayer.com/',
    'Origin': 'https://www.atresplayer.com'
}

def get_json(url):
    try:
        if url.startswith('/'): url = "https://api.atresplayer.com" + url
        # Añadimos v=v2 que es crítico para los nuevos endpoints
        sep = '&' if '?' in url else '?'
        if 'v=v2' not in url: url += f"{sep}v=v2"
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        return response.json()
    except:
        return {}

def fix_image(img_path):
    if not img_path or not img_path.startswith('http'): return ""
    return img_path.replace('_FORMAT_', '1280x720') if '_FORMAT_' in img_path else img_path + "1280x720.jpg"

# --- NAVEGACIÓN ---

def menu_principal():
    cats = [
        ("📺 Directos", "https://api.atresplayer.com/client/v1/row/live", "MODO_GRID"),
        ("🎬 Series", "https://api.atresplayer.com/client/v1/page/series", "MODO_GRID"),
        ("🎭 Programas", "https://api.atresplayer.com/client/v1/page/programs", "MODO_GRID")
    ]
    for titulo, url, modo in cats:
        u = f"{BASE_URL}?mode={modo}&url={urllib.parse.quote_plus(url)}"
        xbmcplugin.addDirectoryItem(HANDLE, u, xbmcgui.ListItem(label=titulo), isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

def listar_grid(url):
    data = get_json(url)
    rows = data.get('itemRows', data.get('rows', data.get('sections', [])))
    
    for row in rows:
        items = row.get('items', row.get('itemRows', [row] if 'link' in row else []))
        for item in items:
            link = item.get('link')
            if not link: continue
            
            titulo = item.get('title', 'Sin título')
            img = fix_image(item.get('image', {}).get('pathHorizontal', ''))
            url_api = link.get('href')
            page_type = link.get('pageType', '')
            
            if page_type in ["LIVE_CHANNEL", "VIDEO"]:
                v_id = url_api.strip('/').split('/')[-1]
                v_type = "live" if page_type == "LIVE_CHANNEL" else "video"
                u = f"{BASE_URL}?mode=MODO_PLAY&id={v_id}&type={v_type}"
                folder = False
            else:
                u = f"{BASE_URL}?mode=MODO_TEMPORADAS&url={urllib.parse.quote_plus(url_api)}"
                folder = True
            
            li = xbmcgui.ListItem(label=titulo)
            li.setArt({'thumb': img, 'poster': img, 'fanart': img})
            if not folder:
                li.setProperty('IsPlayable', 'true')
                li.setInfo('video', {'title': titulo, 'plot': item.get('description', '')})
            xbmcplugin.addDirectoryItem(HANDLE, u, li, isFolder=folder)
            
    xbmcplugin.endOfDirectory(HANDLE)

def listar_temporadas(url):
    data = get_json(url)
    sections = data.get('sections', [data] if 'items' in data or 'episodes' in data else [])
    
    for sec in sections:
        items = sec.get('items', []) or sec.get('episodes', []) or sec.get('itemRows', [])
        for item in items:
            link = item.get('link')
            if not link or not link.get('href'): continue
            
            titulo = item.get('title', 'Contenido')
            img = fix_image(item.get('image', {}).get('pathHorizontal', ''))
            v_id = link.get('href').strip('/').split('/')[-1]
            u = f"{BASE_URL}?mode=MODO_PLAY&id={v_id}&type=video"
            
            li = xbmcgui.ListItem(label=titulo)
            li.setArt({'thumb': img, 'fanart': img})
            li.setInfo('video', {'title': titulo, 'plot': item.get('description', '')})
            li.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(HANDLE, u, li, isFolder=False)
            
    xbmcplugin.endOfDirectory(HANDLE)

def reproducir(v_id, v_type):
    # Añadimos parámetros v=v2 y visitorId para validar los Directos/FAST
    visitor_id = "fda183e704c"
    endpoints = [
        f"https://api.atresplayer.com/player/v1/{v_type}/{v_id}?NODRM=true&v=v2&visitorId={visitor_id}",
        f"https://api.atresplayer.com/client/v1/player/{v_type}/{v_id}?NODRM=true&v=v2"
    ]
    
    stream_url = ""
    manifest_type = ""
    
    for url in endpoints:
        data = get_json(url)
        sources = data.get('sources', data.get('sourcesLive', []))
        for s in sources:
            stype = s.get('type', '').lower()
            if 'mpegurl' in stype or '.m3u8' in s.get('src', ''):
                stream_url = s['src']
                manifest_type = 'hls'
                break
            elif 'dash' in stype:
                stream_url = s['src']
                manifest_type = 'mpd'
        if stream_url: break

    if stream_url:
        # Referer dinámico según sea Live o Video para evitar el rechazo del servidor
        ref = f"https://www.atresplayer.com/directos/{v_id}/" if v_type == "live" else "https://www.atresplayer.com/"
        pipe = f"|User-Agent={urllib.parse.quote(UA)}&Referer={urllib.parse.quote(ref)}&Origin={urllib.parse.quote('https://www.atresplayer.com')}"
        
        li = xbmcgui.ListItem(path=stream_url + pipe)
        li.setProperty('inputstream', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type', manifest_type)
        # Solo Widevine si NO es live (para evitar falsos errores en canales FAST)
        if v_type != "live":
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
        
        xbmcplugin.setResolvedUrl(HANDLE, True, li)
    else:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        xbmcgui.Dialog().ok("Atresplayer", "Contenido no disponible (Premium o Error de Stream).")

# --- ROUTER ---
if len(sys.argv) >= 3:
    params = urllib.parse.parse_qs(sys.argv[2].lstrip('?'))
    mode = params.get('mode', [None])[0]
    
    if not mode: menu_principal()
    elif mode == "MODO_GRID": listar_grid(params.get('url')[0])
    elif mode == "MODO_TEMPORADAS": listar_temporadas(params.get('url')[0])
    elif mode == "MODO_PLAY": reproducir(params.get('id')[0], params.get('type', ['video'])[0])
else:
    menu_principal()
