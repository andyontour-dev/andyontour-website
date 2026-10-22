"""Refresh public playlist cards; preserve manually checked product links."""
import html
import json
import re
import urllib.request

PLAYLIST = 'PLdpiB78cPCEMmf00IDlytviC3eEzX3QwV'
URL = 'https://www.youtube.com/playlist?list=' + PLAYLIST
START = '<!-- REVIEWS_START -->'
END = '<!-- REVIEWS_END -->'


def parse_playlist(page):
    match = re.search(r'(?:var\s+ytInitialData\s*=|window\["ytInitialData"\]\s*=)\s*', page)
    if not match or PLAYLIST not in page:
        raise ValueError('Öffentliche Review-Playlist nicht gefunden')
    data, _ = json.JSONDecoder().raw_decode(page[match.end():])
    canonical = data.get('microformat', {}).get('microformatDataRenderer', {}).get('urlCanonical', '')
    if canonical not in (URL, URL.replace('https:', 'http:')):
        raise ValueError('Falsche Review-Playlist')
    tabs = data['contents']['twoColumnBrowseResultsRenderer']['tabs']
    selected = [t['tabRenderer']['content'] for t in tabs if t.get('tabRenderer', {}).get('selected')]
    if len(selected) != 1:
        raise ValueError('Playlist-Ansicht nicht eindeutig')
    videos, seen = [], set()
    def walk(node):
        if isinstance(node, list):
            for item in node: walk(item)
        elif isinstance(node, dict):
            v = node.get('playlistVideoRenderer')
            lock = node.get('lockupViewModel')
            if v:
                vid = v.get('videoId', '')
                title = v.get('title', {}).get('simpleText') or ''.join(r.get('text', '') for r in v.get('title', {}).get('runs', []))
                valid = bool(v.get('isPlayable', True) and (v.get('lengthText') or v.get('lengthSeconds')))
            elif lock:
                vid = lock.get('contentId', '')
                title = lock.get('metadata', {}).get('lockupMetadataViewModel', {}).get('title', {}).get('content', '')
                thumb = lock.get('contentImage', {}).get('thumbnailViewModel', {})
                overlays = json.dumps(thumb.get('overlays', []))
                valid = lock.get('contentType') == 'LOCKUP_CONTENT_TYPE_VIDEO' and bool(re.search(r'"text": "\d+:\d\d(?::\d\d)?"', overlays)) and not any(x in overlays for x in ('BADGE_STYLE_LIVE', 'UPCOMING'))
            else:
                for value in node.values(): walk(value)
                return
            if valid and re.fullmatch(r'[A-Za-z0-9_-]{11}', vid) and title.strip() and vid not in seen:
                seen.add(vid); videos.append({'id': vid, 'title': title.strip()})
    walk(selected[0])
    if not videos:
        raise ValueError('Keine veröffentlichten Review-Videos; bisherige Karten bleiben erhalten')
    return videos


def render_card(video):
    vid = video['id']; title = html.escape(video['title'], quote=True)
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
        raise ValueError('Ungültige Video-ID')
    return (f'<article class="latest-card review-card"><a class="latest-image" href="https://www.youtube.com/watch?v={vid}" aria-label="{title}: Review auf YouTube ansehen">'
            f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="Mein Review: {title}" loading="lazy" width="480" height="360" referrerpolicy="no-referrer"><span class="latest-play" aria-hidden="true">▶</span></a>'
            f'<div class="latest-body"><p class="eyebrow">Produkttest &amp; Unboxing</p><h3>{title}</h3><p>Mein Video aus der Review-Playlist – mit Produktinfos und gegebenenfalls weiterführenden Links in der Videobeschreibung.</p>'
            f'<a class="review-video" href="https://www.youtube.com/watch?v={vid}">Video ansehen ↗</a></div></article>')


def update(path, videos):
    original = path.read_text(encoding='utf-8')
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError('Review-Markierungen fehlen')
    before, tail = original.split(START); current, after = tail.split(END)
    known = {}
    for card in re.findall(r'<article\b.*?</article>', current, re.S):
        match = re.search(r'watch\?v=([A-Za-z0-9_-]{11})', card)
        if match: known[match.group(1)] = card
    # Keep checked product descriptions, affiliate links and discount codes intact.
    parts = [known.get(v['id']) or render_card(v) for v in videos]
    result = before + START + ''.join(parts) + END + after
    if result != original:
        tmp = path.with_suffix('.reviews.tmp'); tmp.write_text(result, encoding='utf-8'); tmp.replace(path)
    return result != original


def refresh(path):
    request = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'de-DE,de;q=0.9'})
    with urllib.request.urlopen(request, timeout=35) as response:
        page = response.read(8_000_001)
    if len(page) > 8_000_000: raise ValueError('Playlist-Antwort zu groß')
    videos = parse_playlist(page.decode('utf-8'))
    return {'changed': update(path, videos), 'review_video_ids': [v['id'] for v in videos]}
