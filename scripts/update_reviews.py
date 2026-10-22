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
    parts = []
    for v in videos:
        card = known.get(v['id']) or render_card(v)
        if 'description' in v:
            card = sync_product_links(card, v['description'])
        from review_pages import slug
        detail = '<a class="review-detail text-link" href="' + slug(v['id']) + '">Ausführlicher Produkttest →</a>'
        card = re.sub(r'<a class="review-detail.*?</a>', '', card, flags=re.S)
        card = card.replace('</div></article>', detail + '</div></article>')
        parts.append(card)
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
    for video in videos:
        try:
            request = urllib.request.Request('https://www.youtube.com/watch?v=' + video['id'], headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'de-DE,de;q=0.9'})
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read(8_000_001)
            if len(raw) > 8_000_000: raise ValueError('Videoantwort zu groß')
            video['description'] = read_description(raw.decode('utf-8'), video['id'])
        except Exception as error:
            print('Produktlinks unverändert für ' + video['id'] + ': ' + str(error))
    changed = update(path, videos)
    from review_pages import generate
    pages = generate(path.parent)
    return {'changed': changed, 'review_video_ids': [v['id'] for v in videos], 'product_pages': pages}


def read_description(page, video_id):
    match = re.search(r'(?:var\s+ytInitialPlayerResponse\s*=|ytInitialPlayerResponse\s*=)\s*', page)
    if not match: raise ValueError('Videobeschreibung nicht lesbar')
    data, _ = json.JSONDecoder().raw_decode(page[match.end():])
    details = data.get('videoDetails', {})
    if details.get('videoId') != video_id or not isinstance(details.get('shortDescription'), str):
        raise ValueError('Videobeschreibung nicht eindeutig')
    return details['shortDescription']


def product_links(description):
    # Only the primary product section, never the channel's general equipment list.
    description = re.split(r'Trinkgeld\s*:|Kanalmitglied werden|Amazon Ideenlisten\s*:|Verwendete Kameras\s*:|Produktmerkmale\s*:|Fan Artikel\s*:', description, maxsplit=1, flags=re.I)[0]
    links = []
    from urllib.parse import urlsplit
    for line in description.splitlines():
        for raw in re.findall(r'https?://[^\s<>]+', line):
            url = raw.rstrip('.,;!)]}')
            parts = urlsplit(url)
            host = (parts.hostname or '').lower()
            allowed = host in ('amzn.to', 'amzn.eu', 'link.amazon', 'amazon.de', 'www.amazon.de', 'de.engwe.com', 'engwe.com')
            if not allowed or parts.username or parts.password or '...' in url or parts.scheme != 'https': continue
            if any(v['url'] == url for v in links): continue
            label = re.sub(r'https?://[^\s<>]+', '', line).strip(' ➡️❌:*–-')
            size = re.search(r'\b(35|45|55)\s*(?:Liter|L)\b', label, re.I)
            key = size.group(1) if size else ('de' if host == 'de.engwe.com' or '(DE)' in label else 'primary')
            links.append({'url': url, 'key': key, 'label': label})
    return links


def sync_product_links(card, description):
    links = product_links(description)
    if not links: return card
    match = re.search(r'<div class="review-links">(.*?)</div>', card, re.S)
    if match:
        def replace_link(anchor):
            label = html.unescape(re.sub('<[^>]+>', '', anchor.group(0)))
            size = re.search(r'\b(35|45|55)\s*Liter\b', label, re.I)
            if size: candidates = [v for v in links if v['key'] == size.group(1)]
            elif 'E-Bike' in label: candidates = [v for v in links if v['key'] == 'de'] or links
            else: candidates = links
            # Multiple unrelated URLs must not silently replace one product button.
            if len(candidates) != 1: return anchor.group(0)
            return re.sub(r'href="[^"]*"', 'href="'+html.escape(candidates[0]['url'], quote=True)+'"', anchor.group(0), count=1)
        content = re.sub(r'<a\b[^>]*>.*?</a>', replace_link, match.group(1), flags=re.S)
        return card[:match.start(1)] + content + card[match.end(1):]
    # For new reviews only an unambiguous primary product is inserted automatically.
    if len(links) == 1:
        block = '<div class="review-links"><a href="'+html.escape(links[0]['url'], quote=True)+'" rel="sponsored noopener" target="_blank">Zum Produkt · Affiliate-Link ↗</a></div>'
        card = card.replace('</div></article>', block+'</div></article>')
    return card
