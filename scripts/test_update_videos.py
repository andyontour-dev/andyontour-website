import json
from pathlib import Path
import tempfile
import unittest
from update_videos import CHANNEL, START, END, cards, parse_videos, update


def item(vid, **extra):
    return {'richItemRenderer': {'content': {'videoRenderer': {
        'videoId': vid, 'title': {'simpleText': '<Andy & Tour>'},
        'lengthText': {'simpleText': '10:00'}, **extra}}}}


def page(items, channel=CHANNEL, tab='Videos'):
    return 'var ytInitialData = ' + json.dumps({
        'metadata': {'channelMetadataRenderer': {'externalId': channel}},
        'contents': {'twoColumnBrowseResultsRenderer': {'tabs': [
            {'tabRenderer': {'selected': True, 'title': tab,
                             'content': {'richGridRenderer': {'contents': items}}}}]}}}) + ';'


class UpdateTests(unittest.TestCase):
    def test_only_three_and_ignore_upcoming_short_live_duplicate(self):
        entries = [item('upcoming001', upcomingEventData={'startTime': '9999999999'}),
                   item('shorts00001', navigationEndpoint={'url': '/shorts/shorts00001'}),
                   item('live0000001', badges=[{'style': 'LIVE'}]), item('normal00001'),
                   item('normal00001'), item('normal00002'), item('normal00003'), item('normal00004')]
        self.assertEqual([v['id'] for v in parse_videos(page(entries))], ['normal00001', 'normal00002', 'normal00003'])

    def test_wrong_channel_tab_or_incomplete_response_rejected(self):
        for source in [page([], channel='other'), page([], tab='Shorts'), page([item('normal00001')]), 'bad response']:
            with self.assertRaises(ValueError):
                parse_videos(source)

    def test_html_escaped_and_atomic_bounded_update(self):
        videos = [{'id': 'normal00001', 'title': '<script> & "Title"'}] * 3
        self.assertNotIn('<script>', cards(videos))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'index.html'
            path.write_text('before' + START + 'old' + END + 'after')
            self.assertTrue(update(path, videos))
            self.assertFalse(update(path, videos))
            self.assertTrue(path.read_text().startswith('before' + START))
            self.assertTrue(path.read_text().endswith(END + 'after'))
            path.write_text('no markers')
            with self.assertRaises(ValueError):
                update(path, videos)
            self.assertEqual(path.read_text(), 'no markers')

    def test_current_lockup_schema(self):
        entries = []
        for vid in ['normal00001', 'normal00002', 'normal00003']:
            entries.append({'richItemRenderer': {'content': {'lockupViewModel': {
                'contentId': vid, 'contentType': 'LOCKUP_CONTENT_TYPE_VIDEO',
                'metadata': {'lockupMetadataViewModel': {'title': {'content': 'Andy'}}},
                'contentImage': {'thumbnailViewModel': {'overlays': [
                    {'thumbnailBottomOverlayViewModel': {'badges': [
                        {'thumbnailBadgeViewModel': {'text': '1:10:30'}}]}}]}}}}}})
        self.assertEqual(len(parse_videos(page(entries))), 3)


if __name__ == '__main__':
    unittest.main()
