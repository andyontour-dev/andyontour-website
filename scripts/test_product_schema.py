"""Editorial pages must not advertise unsupported product rich-result data."""
import json
from pathlib import Path
import re
import tempfile
import unittest
from review_pages import generate

class ProductSchemaTest(unittest.TestCase):
    def test_known_and_future_reviews_remain_articles_without_incomplete_products(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            known='618EbQxiSLo';future='newVideo123'
            cards=''.join('<article><a href="https://www.youtube.com/watch?v='+vid+'">Video</a><div class="latest-body"><h3>'+title+'</h3><p>Vorstellung</p><a href="https://amzn.to/test" rel="sponsored noopener">Affiliate-Link</a></div></article>' for vid,title in [(known,'ENGWE L20 3.0 Pro'),(future,'Neues Testprodukt')])
            (root/'index.html').write_text('<style>body{color:black}</style><header>Andy on Tour</header><!-- REVIEWS_START -->'+cards+'<!-- REVIEWS_END --><footer>Impressum</footer>')
            (root/'sitemap.xml').write_text('<urlset></urlset>')
            urls=generate(root,descriptions={future:'Im Video stelle ich das neue Produkt mit seinen Bedienelementen vor. Der Praxistest zeigt den Einsatz auf einer Tour.'})
            self.assertEqual(len(urls),2)
            for url in urls:
                text=(root/url.rsplit('/',1)[1]).read_text()
                data=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S).group(1))
                article=data['@graph'][0]['mainEntity']
                self.assertEqual(article['@type'],'Article')
                self.assertTrue(article['headline']);self.assertTrue(article['author']['name'])
                self.assertEqual(article['about']['@type'],'Thing')
                self.assertNotIn('"@type": "Product"',text)
                self.assertNotIn('aggregateRating',text);self.assertNotIn('"offers"',text)
                self.assertIn('https://amzn.to/test',text)

if __name__=='__main__':unittest.main()
