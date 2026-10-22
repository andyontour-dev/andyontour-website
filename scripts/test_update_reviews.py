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

from update_reviews import sync_product_links, read_description

class ProductLinksTest(unittest.TestCase):
    def card(self, label='Zur Dashcam'):
        return '<article><div class="review-links"><a href="https://amzn.to/old" rel="sponsored noopener">'+label+' · Affiliate-Link</a></div><p>Code Andy</p></article>'
    def test_replacement_and_equipment_exclusion(self):
        result=sync_product_links(self.card(), 'Vorgestelltes Produkt:\nDashcam https://amzn.to/new\nKanalmitglied werden\nKamera https://amzn.to/other')
        self.assertIn('https://amzn.to/new',result); self.assertNotIn('https://amzn.to/other',result);self.assertIn('Code Andy',result)
    def test_size_assignment(self):
        result=sync_product_links(self.card('45 Liter'), '35 Liter https://amzn.to/a\n45 Liter https://amzn.to/b\n55 Liter https://amzn.to/c')
        self.assertIn('href="https://amzn.to/b"',result)
    def test_missing_ambiguous_or_untrusted_preserved(self):
        for description in ('', 'https://evil.example/a', 'https://amzn.to/a\nhttps://amzn.to/b'):
            self.assertEqual(sync_product_links(self.card(),description),self.card())
    def test_description_id_checked(self):
        page='var ytInitialPlayerResponse = '+json.dumps({'videoDetails':{'videoId':'618EbQxiSLo','shortDescription':'https://amzn.to/new'}})
        self.assertEqual(read_description(page,'618EbQxiSLo'),'https://amzn.to/new')
        with self.assertRaises(ValueError):read_description(page,'wrong')
