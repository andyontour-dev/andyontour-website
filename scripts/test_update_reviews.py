import json
from pathlib import Path
import tempfile
import unittest
from update_reviews import parse_playlist, update, URL, START, END

class ReviewsTest(unittest.TestCase):
    def page(self, videos, url=URL):
        data={'microformat':{'microformatDataRenderer':{'urlCanonical':url}},'contents':{'twoColumnBrowseResultsRenderer':{'tabs':[{'tabRenderer':{'selected':True,'content':{'contents':[{'playlistVideoRenderer':{'videoId':v,'title':{'simpleText':t},'lengthSeconds':'120','isPlayable':True}} for v,t in videos]}}}]}}}
        return 'var ytInitialData = '+json.dumps(data)+';'
    def test_new_video_and_existing_affiliate_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'index.html'
            known='<article><a href="https://www.youtube.com/watch?v=618EbQxiSLo">ENGWE</a><p>10 % Rabatt mit Code: Andy</p><a rel="sponsored" href="https://de.engwe.com/?ref=ANDYONTOUR">Produkt</a></article>'
            p.write_text('before'+START+known+END+'after')
            videos=parse_playlist(self.page([('newVideo123','New <Review>'),('618EbQxiSLo','ENGWE')]))
            update(p,videos); result=p.read_text()
            self.assertIn(known,result); self.assertIn('New &lt;Review&gt;',result); self.assertTrue(result.endswith(END+'after'))
            self.assertFalse(update(p,videos))
    def test_wrong_playlist_rejected(self):
        with self.assertRaises(ValueError): parse_playlist(self.page([('618EbQxiSLo','x')], URL+'wrong'))
    def test_empty_playlist_rejected(self):
        with self.assertRaises(ValueError): parse_playlist(self.page([]))
    def test_duplicate_removed(self):
        self.assertEqual(len(parse_playlist(self.page([('618EbQxiSLo','x')]*2))),1)
