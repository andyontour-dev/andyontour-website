"""Read only the public Videos tab; atomically refresh three homepage cards.

No credentials, downloads, YouTube changes, Shorts or live-stream tab.
On invalid/empty responses the existing homepage is preserved.
"""
import argparse
import html
import json
from pathlib import Path
import re
import urllib.request

CHANNEL = 'UC2tu_IpwJ0sAdznY6HcVuQg'
URL = f'https://www.youtube.com/channel/{CHANNEL}/videos?hl=de&gl=DE'
START = '<!-- LATEST_VIDEOS_START -->'
END = '<!-- LATEST_VIDEOS_END -->'


def text(value):
    return value.get('simpleText') or ''.join(r.get('text', '') for r in value.get('runs', []))


def parse_videos(page):
    match = re.search(r'(?:var\s+ytInitialData\s*=|window\["ytInitialData"\]\s*=)\s*', page)
    if not match:
        raise ValueError('YouTube-Videoliste fehlt; Homepage bleibt unverändert')
    data, _ = json.JSONDecoder().raw_decode(page[match.end():])
    channel = data.get('metadata', {}).get('channelMetadataRenderer', {}).get('externalId')
    if channel != CHANNEL:
        raise ValueError('YouTube-Kanal stimmt nicht überein')
    tabs = data['contents']['twoColumnBrowseResultsRenderer']['tabs']
    selected = [t['tabRenderer'] for t in tabs if t.get('tabRenderer', {}).get('selected')]
    if len(selected) != 1:
        raise ValueError('Keine eindeutige Videos-Ansicht')
    tab = selected[0]
    endpoint = tab.get('endpoint', {}).get('commandMetadata', {}).get('webCommandMetadata', {}).get('url', '')
    if not endpoint.rstrip('/').endswith('/videos') and tab.get('title') not in ('Videos', 'VIDEOS'):
        raise ValueError('Erwartet wird ausschließlich der Videos-Reiter')
    grid = tab['content']['richGridRenderer']['contents']
    videos = []
    seen = set()
    for item in grid:
        content = item.get('richItemRenderer', {}).get('content', {})
        video = content.get('videoRenderer')
        lockup = content.get('lockupViewModel')
        if lockup:
            if lockup.get('contentType') != 'LOCKUP_CONTENT_TYPE_VIDEO':
                continue
            thumbnail = lockup.get('contentImage', {}).get('thumbnailViewModel', {})
            badges = [b.get('thumbnailBadgeViewModel', {})
                      for overlay in thumbnail.get('overlays', [])
                      for b in overlay.get('thumbnailBottomOverlayViewModel', {}).get('badges', [])]
            duration = next((b.get('text', '') for b in badges
                             if re.fullmatch(r'\d+:\d\d(?::\d\d)?', b.get('text', ''))), '')
            if not duration or any('LIVE' in b.get('badgeStyle', '') or 'UPCOMING' in b.get('badgeStyle', '') for b in badges):
                continue
            title = lockup.get('metadata', {}).get('lockupMetadataViewModel', {}).get('title', {}).get('content', '')
            video = {'videoId': lockup.get('contentId', ''), 'title': {'simpleText': title}, 'lengthText': {'simpleText': duration}}
        if not video:
            continue
        vid = video.get('videoId', '')
        title = text(video.get('title', {})).strip()
        # Scheduled premieres/live items have no normal duration or a live badge.
        badges = json.dumps(video.get('badges', []))
        overlays = json.dumps(video.get('thumbnailOverlays', []))
        if video.get('upcomingEventData') or not video.get('lengthText'):
            continue
        if 'LIVE' in badges or 'LIVE' in overlays or 'UPCOMING' in overlays:
            continue
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid) or not title or vid in seen:
            continue
        if '/shorts/' in json.dumps(video.get('navigationEndpoint', {})):
            continue
        seen.add(vid)
        videos.append({'id': vid, 'title': title})
        if len(videos) == 3:
            return videos
    raise ValueError('Weniger als drei veröffentlichte Langvideos gefunden')


def cards(videos):
    if len(videos) != 3:
        raise ValueError('Genau drei Videos erforderlich')
    parts = []
    for v in videos:
        vid = v['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
            raise ValueError('Ungültige Video-ID')
        title = html.escape(v['title'], quote=True)
        parts.append(f'<a class="latest-card" href="https://www.youtube.com/watch?v={vid}">'
                     f'<div class="latest-image"><img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" '
                     f'alt="Vorschaubild: {title}" loading="lazy" width="480" height="360" referrerpolicy="no-referrer">'
                     '<span class="latest-play" aria-hidden="true">▶</span></div>'
                     f'<div class="latest-body"><h3>{title}</h3><span>Auf YouTube ansehen ↗</span></div></a>')
    return ''.join(parts)


def update(path, videos):
    original = path.read_text(encoding='utf-8')
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError('Eindeutige Video-Markierungen fehlen')
    before, tail = original.split(START)
    _, after = tail.split(END)
    result = before + START + cards(videos) + END + after
    if result != original:
        temporary = path.with_suffix('.html.tmp')
        temporary.write_text(result, encoding='utf-8')
        temporary.replace(path)
    return result != original


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', type=Path, default=Path('index.html'))
    parser.add_argument('--fixture', type=Path)
    args = parser.parse_args()
    if args.fixture:
        page = args.fixture.read_text(encoding='utf-8')
    else:
        request = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'de-DE,de;q=0.9'})
        with urllib.request.urlopen(request, timeout=40) as response:
            page = response.read(8_000_001)
        if len(page) > 8_000_000:
            raise ValueError('YouTube-Antwort unerwartet groß')
        page = page.decode('utf-8')
    videos = parse_videos(page)
    changed = update(args.html, videos)
    print(json.dumps({'changed': changed, 'video_ids': [v['id'] for v in videos]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
