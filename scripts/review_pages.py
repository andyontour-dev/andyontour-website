"""Build crawlable editorial pages from the same reviewed product cards."""
import html,json,re
from pathlib import Path

SLUGS={'618EbQxiSLo':'engwe-l20-3-pro-test.html','Y1cipABFo8M':'hcalory-kompressor-kuehlbox-test.html','aVDBd8X6euc':'navycrest-q7-dashcam-test.html'}
COPY={
'618EbQxiSLo':('ENGWE L20 3.0 Pro im Test: E-Bike-Review','Mein ENGWE L20 3.0 Pro Review: Das faltbare E-Bike im Video bei Andy on Tour. Mit persönlichem Testbericht, Produktlink und Rabattcode Andy.',[
('Das ENGWE L20 3.0 Pro im Video','In diesem E-Bike-Review stelle ich das ENGWE L20 3.0 Pro vor. Das faltbare Fahrrad ergänzt die Themen unterwegs sein, Touren und mobile Ausrüstung auf meinem Kanal. Das Video richtet sich an alle, die sich vor einem Kauf einen persönlichen Eindruck vom Modell verschaffen möchten.'),
('Persönlicher Eindruck statt Datenblatt','Wie wirkt das E-Bike im praktischen Einsatz? Mein ausführliches YouTube-Video ist die Grundlage dieser Vorstellung. Sieh dir dort den Test an und bilde dir ein eigenes Urteil. Die Videoaufnahmen und meine Erläuterungen helfen dir dabei, das Modell kennenzulernen.'),
('Produktlink und Rabattcode','Den Link zum ENGWE-Shop und meinen gültigen Rabattcode Andy findest du auf dieser Seite. Mit dem Code erhältst du 10 % Rabatt. Aktuelle Produktdetails, Preise und Bedingungen zeigt der Anbieter beim Kauf.')]),
'Y1cipABFo8M':('Hcalory Kompressor-Kühlbox im Test: 35, 45 & 55 Liter','Hcalory Kompressor-Kühlbox im Review und Praxistest bei Andy on Tour. Video ansehen und Produktlinks für 35, 45 und 55 Liter entdecken.',[
('Eine Kühlbox für unterwegs','Kühle Getränke und Lebensmittel sind auf längeren Touren ein wichtiges Thema. In meinem Review und Praxistest stelle ich die Hcalory Kompressor-Kühlbox vor. Damit ergänzt das Video meine Inhalte über LKW-Alltag, Reisen und Ausrüstung für unterwegs.'),
('35, 45 oder 55 Liter','Die Produktlinks führen zu den drei Größen mit 35, 45 und 55 Litern. Achte bei der Auswahl auf die Größe und den Platz, den du im Fahrzeug zur Verfügung hast. Die jeweils aktuellen Maße und technischen Angaben findest du beim Anbieter.'),
('Den Praxistest ansehen','Das YouTube-Video zeigt meine Vorstellung und meinen praktischen Eindruck von der Kühlbox. Schaue dir das Review an, bevor du dich für eine Variante entscheidest. Über die gekennzeichneten Produktlinks kannst du anschließend die passende Größe beim Anbieter aufrufen.')]),
'aVDBd8X6euc':('NAVYCREST Q7 Dashcam im Test: Review für LKW & PKW','NAVYCREST Q7 4K-Dashcam im Review bei Andy on Tour: Unboxing, Vorstellung im LKW und Videotest. Mit passendem Produktlink zur Dashcam.',[
('Dashcam-Review aus dem Fahreralltag','In diesem Video stelle ich die NAVYCREST Q7 Dashcam für LKW und PKW vor. Das Unboxing und Review passt zu meinen Truck-Dokus und zur Ausrüstung, die im Fahreralltag interessant sein kann. Im Mittelpunkt steht das konkrete Modell aus meinem Video.'),
('Front- und Heckkamera im Video','Das vorgestellte Set besteht aus Front- und Heckkamera. Im Video zeige ich das Auspacken und den Anschluss im LKW und beschäftige mich mit der Bedienung. Den vollständigen Eindruck findest du im verlinkten Review auf meinem YouTube-Kanal.'),
('Zum getesteten Modell','Über den gekennzeichneten Produktlink gelangst du zur Dashcam. Vergleiche vor dem Kauf die Modellbezeichnung und den Lieferumfang beim Anbieter mit dem im Video vorgestellten Set. Diese Seite ist eine redaktionelle Videovorstellung und kein eigener Onlineshop.')])}


def slug(vid):return SLUGS.get(vid,'review-'+vid+'.html')


def generate(root, descriptions=None):
    descriptions = descriptions or {}
    source=(root/'index.html').read_text();style=re.search(r'<style>(.*?)</style>',source,re.S).group(1)
    header=re.search(r'<header>.*?</header>',source,re.S).group(0)
    header=re.sub(r'href="#', 'href="index.html#',header)
    footer=re.search(r'<footer>.*?</footer>',source,re.S).group(0)
    cards=re.findall(r'<article\b.*?</article>',source.split('<!-- REVIEWS_START -->')[1].split('<!-- REVIEWS_END -->')[0],re.S)
    urls=[]
    for card in cards:
        vid=re.search(r'watch\?v=([A-Za-z0-9_-]{11})',card).group(1);filename=slug(vid);url='https://andyontour.com/'+filename
        title,description,sections=COPY.get(vid,(html.unescape(re.search(r'<h3>(.*?)</h3>',card,re.S).group(1))+' – Produkttest bei Andy on Tour','Produkttest und Videovorstellung von Andy on Tour. Das vollständige Review auf YouTube ansehen.',[]))
        if vid not in COPY:
            generated = description_text(html.unescape(re.search(r'<h3>(.*?)</h3>',card,re.S).group(1)), descriptions.get(vid, ''))
            if generated:
                title,description,sections = generated
        # Existing affiliate links and confirmed codes are taken from the hourly updated card.
        detail=re.search(r'<div class="latest-body">(.*)</div></article>',card,re.S).group(1)
        detail=re.sub(r'<a class="review-detail[^\"]*".*?</a>','',detail,flags=re.S)
        schema={'@context':'https://schema.org','@graph':[{'@type':'WebPage','@id':url+'#page','url':url,'name':title,'description':description,'inLanguage':'de','breadcrumb':{'@id':url+'#breadcrumb'},'mainEntity':{'@type':'Article','headline':title,'description':description,'author':{'@type':'Person','name':'Andy','url':'https://andyontour.com/#ueber-mich'},'image':'https://i.ytimg.com/vi/'+vid+'/hqdefault.jpg','about':{'@type':'Product','name':html.unescape(re.search(r'<h3>(.*?)</h3>',card,re.S).group(1))},'isBasedOn':'https://www.youtube.com/watch?v='+vid}},{'@type':'BreadcrumbList','@id':url+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':1,'name':'Startseite','item':'https://andyontour.com/'},{'@type':'ListItem','position':2,'name':'Produkttests','item':'https://andyontour.com/#reviews'},{'@type':'ListItem','position':3,'name':title,'item':url}]}]}
        schema_json = json.dumps(schema,ensure_ascii=False).replace('<', chr(92)+'u003c')
        head=f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} | Andy on Tour</title><meta name="description" content="{html.escape(description,quote=True)}"><link rel="canonical" href="{url}"><meta property="og:type" content="article"><meta property="og:title" content="{html.escape(title,quote=True)}"><meta property="og:description" content="{html.escape(description,quote=True)}"><meta property="og:url" content="{url}"><meta property="og:image" content="https://i.ytimg.com/vi/{vid}/hqdefault.jpg"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/favicon.ico"><style>{style}.product-layout{{display:grid;grid-template-columns:1.2fr 1fr;gap:35px;align-items:start}}.product-layout img{{width:100%}}.product-text{{max-width:850px}}.product-text h2{{font-size:28px;margin:30px 0 12px}}@media(max-width:760px){{.product-layout{{grid-template-columns:1fr}}}}</style><script type="application/ld+json">{schema_json}</script></head>'
        body=f'<body>{header}<main><section class="section"><div class="wrap"><nav aria-label="Brotkrumennavigation"><a href="index.html">Startseite</a> / <a href="index.html#reviews">Produkttests</a></nav><p class="eyebrow" style="margin-top:30px">Andy on Tour · Produkttest</p><h1 style="font-size:clamp(32px,5vw,52px)">{html.escape(title)}</h1><p>{html.escape(description)}</p><div class="product-layout"><a href="https://www.youtube.com/watch?v={vid}" aria-label="Vollständiges Review auf YouTube ansehen"><img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="Videotest: {html.escape(title,quote=True)}" width="480" height="360"><span class="button gold">Vollständiges Video auf YouTube ansehen ↗</span></a><div>{detail}</div></div><div class="product-text">'+''.join('<h2>'+html.escape(h)+'</h2><p>'+html.escape(p)+'</p>' for h,p in sections)+'</div><p class="affiliate-note"><strong>Werbung · Affiliate-Links.</strong> Als Amazon-Partner verdiene ich an qualifizierten Verkäufen. Auch andere gekennzeichnete Partnerlinks können mir eine Provision bringen.</p><p><a class="text-link" href="index.html#reviews">Weitere Produkttests &amp; Empfehlungen →</a></p></div></section></main>'+footer+'</body></html>'
        (root/filename).write_text(head+body);urls.append(url)
    p=root/'sitemap.xml';s=p.read_text();s=re.sub(r'\s*<url><loc>https://andyontour.com/(?:engwe-l20-3-pro-test|hcalory-kompressor-kuehlbox-test|navycrest-q7-dashcam-test|review-[A-Za-z0-9_-]+)\.html</loc></url>','',s)
    s=s.replace('</urlset>',''.join('  <url><loc>'+u+'</loc></url>\n' for u in urls)+'</urlset>');p.write_text(s)
    return urls


def description_text(video_title, raw):
    """Extract product-specific source text without treating it as instructions.

    No model calls, invented experiences, ratings or prices. Generic channel
    promotion, tracking links and product-section footer are excluded.
    """
    raw = html.unescape(raw or '')
    raw = re.split(r'Kanalmitglied werden|Trinkgeld\s*:|Amazon Ideenlisten\s*:|Verwendete Kameras\s*:|Fan Artikel\s*:|So[cz]ial Media\s*:|Musik by|Die mit .*gekennzeichneten Links|MERCH\s*:',raw,maxsplit=1,flags=re.I)[0]
    paragraphs=[];buffer=[]
    def flush():
        if buffer:
            chunk=' '.join(buffer).strip()
            if len(chunk)>=65 and len(chunk.split())>=9 and chunk not in paragraphs:paragraphs.append(chunk[:1100])
            buffer.clear()
    for line in raw.splitlines():
        line=line.strip()
        if not line:flush();continue
        if re.search(r'https?://|www\.|#[\w]+|@\w+|\b\d+[.,]?\d*\s*(?:€|EUR|Euro)|Rabatt|Gutschein|Promotion|Discount|Affiliate|Provision',line,re.I):
            flush();continue
        # Source instructions or markup must never become generated editorial claims.
        if re.search(r'<[^>]+>|ignore.*instruction|system prompt|ignoriere.*anweisung|passwort|api.?key',line,re.I):
            flush();continue
        if re.fullmatch(r'[\W_\d]+',line) or len(line)<5:continue
        line=re.sub(r'^[^\wÄÖÜäöüß]+','',line).strip()
        if re.match(r'^\d{1,2}:\d{2}\s',line):continue
        if re.search(r'LINKS ZU MEINER|Gezeigtes Produkt|Vorgestelltes Produkt',line,re.I):continue
        buffer.append(line)
    flush()
    if not paragraphs:return None
    title=re.sub(r'\s+',' ',video_title).strip()
    title=re.sub(r'\s*#[\w]+','',title).strip()
    if len(title)>95:title=title[:92].rsplit(' ',1)[0]+'…'
    intro='In diesem Produkttest von Andy on Tour geht es um „'+title+'“. Die Videobeschreibung liefert dazu folgende Angaben.'
    sections=[('Das Produkt im Überblick',intro),('Angaben aus der Videobeschreibung',' '.join(paragraphs[:2]))]
    if len(paragraphs)>2:sections.append(('Weitere Funktionen und Einsatzmöglichkeiten',' '.join(paragraphs[2:5])))
    sections.append(('Das vollständige Review ansehen','Die vollständige Vorstellung findest du im verlinkten YouTube-Video. Dort kannst du dir einen eigenen Eindruck vom Produkt verschaffen. Die Produktangaben auf dieser Seite stammen aus der zugehörigen Videobeschreibung.'))
    snippet=paragraphs[0]
    meta=title+': '+snippet
    if len(meta)>158:meta=meta[:155].rsplit(' ',1)[0]+'…'
    return title,meta,sections
