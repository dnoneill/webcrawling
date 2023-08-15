import requests, os, PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import re, time, json
from urllib.parse import urljoin
import concurrent.futures
import sqlite3
CONNECTIONS = 100
TIMEOUT = 5
missing_urls = ['https://www.lib.ncsu.edu/software/fl-studio-1', 'https://www.lib.ncsu.edu/archivedexhibits/patents/Engineering.htm', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings9.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit3b.html', 'https://www.lib.ncsu.edu/events/documentary-film-talking-black-america-performance-traditions', 'https://www.lib.ncsu.edu/findingaids/mss00418', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/linneaus.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/CALS.htm', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/visiting.html', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/gadwall.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/browse3.html', 'https://www.lib.ncsu.edu/findingaids/mss00402', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/events.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/browse2.html', 'https://www.lib.ncsu.edu/news/special-collections/archival-terms-explained-part-2', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/sld002.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/text.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/sld003.htm', 'https://www.lib.ncsu.edu/findingaids/mc00406/summary', 'https://www.lib.ncsu.edu/archivedexhibits/women/1890.htm', 'https://www.lib.ncsu.edu/archivedexhibits/sports/hoops.html', 'https://www.lib.ncsu.edu/events/immersive-highlights-university-history-exhibit-3', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/desc1.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/timeline-lib.php', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit7a.html', 'https://www.lib.ncsu.edu/events/author-event-dr-gladys-kalema-zikusoka-author-walking-gorillas', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit8a.html', 'https://www.lib.ncsu.edu/events/de-stress-fest-inking-some-manga', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/westwoodwork.htm', 'https://www.lib.ncsu.edu/findingaids/mc00297', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit2.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/introduction.htm', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/thomas_leake.php', 'https://www.lib.ncsu.edu/archivedexhibits/women/1901.htm', 'https://www.lib.ncsu.edu/archivedexhibits/pulitzer/home.html', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/intro.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/index.html', 'https://www.lib.ncsu.edu/findingaids/mc00240', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/voyages.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/thistory.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/biography.htm', 'https://www.lib.ncsu.edu/archivedexhibits/patents/index.html', 'https://www.lib.ncsu.edu/case-statement/faculty.php', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tliterature.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/faculty.html', 'https://www.lib.ncsu.edu/case-statement/graduates.php', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/bibliography.php', 'https://www.lib.ncsu.edu/events/stress-busters-drop-space-3', 'https://www.lib.ncsu.edu/news/pentair-foundation-supports-stem-programing-instruction-at-the-ncsu-libraries', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit8b.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/early.html', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/scijo.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit5.html', 'https://www.lib.ncsu.edu/archivedexhibits/women/1980.htm', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/about.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings6.htm', 'https://www.lib.ncsu.edu/findingaids/ua012_025', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit3c.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit4b.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit2b.html', 'https://www.lib.ncsu.edu/do/open-research/scholarly-sharing', 'https://www.lib.ncsu.edu/findingaids/mc00518', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/college.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/Design.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tfarm.html', 'https://www.lib.ncsu.edu/software/blackmagic-media-express', 'https://www.lib.ncsu.edu/events/femme-making-night-makerspace-1', 'https://www.lib.ncsu.edu/jobs/ehra/experiential-learning-services-librarian-we-are-no-longer-taking-applications-position', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/index.html', 'https://www.lib.ncsu.edu/software/microstation-connect', 'https://www.lib.ncsu.edu/news/victoria-rind-and-her-amazing-wearables', 'https://www.lib.ncsu.edu/archivedexhibits/sports/boom.html', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/lattylet.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/learn.html', 'https://www.lib.ncsu.edu/events/femme-game-night-2', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/text2.html', 'https://www.lib.ncsu.edu/findingaids/mc00205', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/timeline.html', 'https://www.lib.ncsu.edu/do/data-management/what-is-a-dmp', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/huntlibrary.php', 'https://www.lib.ncsu.edu/archivedexhibits/wells/help.html', 'https://www.lib.ncsu.edu/archivedexhibits/sports/credits.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit3a.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/albert_lambert.php', 'https://www.lib.ncsu.edu/archivedexhibits/smith/awards.html', 'https://www.lib.ncsu.edu/events/crafting-resilience-drop-space-6', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/gadover.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/tipp.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/recent.html', 'https://www.lib.ncsu.edu/jobs/ehra/makerspace-librarian-we-are-no-longer-taking-applications-position', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/foxquiz.html', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/mastawds.htm', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/index.php', 'https://www.lib.ncsu.edu/events/postponed-global-film-series-grazing-amazon', 'https://www.lib.ncsu.edu/news/ncsu-libraries-demos-virtual-reality-gear-for-lending', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/parking.html', 'https://www.lib.ncsu.edu/spaces/south-theater', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/desc2.html', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/book.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tecon.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit4c.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings3.htm', 'https://www.lib.ncsu.edu/news/special-collections/student-spotlight-ellie-beal-special-collections-desk-assistant', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit8c.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings1.htm', 'https://www.lib.ncsu.edu/events/making-space-cotton-candy-conversation-jackie-morin', 'https://www.lib.ncsu.edu/news/do-you-know-your-animals%3F', 'https://www.lib.ncsu.edu/archivedexhibits/wells/credits.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/PDF/bennett.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tculture.html', 'https://www.lib.ncsu.edu/archivedexhibits/sports/index.html', 'https://www.lib.ncsu.edu/news/alumni-lead-private-support-of-ncsu-libraries%E2%80%99-makerspace', 'https://www.lib.ncsu.edu/events/femme-making-night-makerspace-0', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit4a.html', 'https://www.lib.ncsu.edu/findingaids/ua016_001', 'https://www.lib.ncsu.edu/hunt/in-the-news', 'https://www.lib.ncsu.edu/events/femme-making-night-makerspace', 'https://www.lib.ncsu.edu/archivedexhibits/wells/nomenclature.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings4.htm', 'https://www.lib.ncsu.edu/archivedexhibits/smith/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/sports/changes.html', 'https://www.lib.ncsu.edu/archivedexhibits/sports/battlefield.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tentom.html', 'https://www.lib.ncsu.edu/citationbuilder/assets/minus-square-solid.svg', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/early.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/ebhenderson.php', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/timeline.php', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings7.htm', 'https://www.lib.ncsu.edu/news/special-collections/anatomy-finding-aid', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/home.html', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/pressphotos.htm', 'https://www.lib.ncsu.edu/archivedexhibits/smith/images/adlai%20stevenson%20story.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/dedication.php', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings8.htm', 'https://www.lib.ncsu.edu/archivedexhibits/women/1960.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit7.html', 'https://www.lib.ncsu.edu/findingaids/mss00399', 'https://www.lib.ncsu.edu/archivedexhibits/women/2000.htm', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/credits.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings5.htm', 'https://www.lib.ncsu.edu/archivedexhibits/patents/PDF/foodexpo.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/wells/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/credits.html', 'https://www.lib.ncsu.edu/citationbuilder/assets/plus-square-solid.svg', 'https://www.lib.ncsu.edu/workshops/signup', 'https://www.lib.ncsu.edu/events/stress-busters-drop-space-2', 'https://www.lib.ncsu.edu/findingaids/mc00003', 'https://www.lib.ncsu.edu/archivedexhibits/wells/about.html', 'https://www.lib.ncsu.edu/archivedexhibits/smith/writer.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit8.html', 'https://www.lib.ncsu.edu/archivedexhibits/sports/trappings.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/forestry.htm', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/darwin.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit4.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/VetMed.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/browse4.html', 'https://www.lib.ncsu.edu/findingaids/mc00535', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/matsbio.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit6.html', 'https://www.lib.ncsu.edu/archivedexhibits/pams/index.php', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/peter_ihrie.php', 'https://www.lib.ncsu.edu/case-statement/community.php', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings2.htm', 'https://www.lib.ncsu.edu/archivedexhibits/women/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/content/Images_Centennial/Img_008', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/intro.html', 'https://www.lib.ncsu.edu/archivedexhibits/women/1970.htm', 'https://www.lib.ncsu.edu/archivedexhibits/smith/career.html', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/gadmodel.htm', 'https://www.lib.ncsu.edu/findingaids/mss00401', 'https://www.lib.ncsu.edu/archivedexhibits/women/1930.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/young.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/wallace_riddick.php', 'https://www.lib.ncsu.edu/findingaids/mc00401', 'https://www.lib.ncsu.edu/events/documentary-film-screening-only-doctor', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit3.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit2a.html', 'https://www.lib.ncsu.edu/shout-outs/single/84671', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/matshouse.htm', 'https://www.lib.ncsu.edu/archivedexhibits/patents/textiles.htm', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/life.html', 'https://www.lib.ncsu.edu/archivedexhibits/sports/gridiron.html', 'https://www.lib.ncsu.edu/archivedexhibits/women/1920.htm', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/centennial.php', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/support.php', 'https://www.lib.ncsu.edu/events/stress-buster-come-make-slime', 'https://www.lib.ncsu.edu/archivedexhibits/patents/Pams.htm', 'https://www.lib.ncsu.edu/news/the-nubian-message-goes-digital', 'https://www.lib.ncsu.edu/archivedexhibits/wells/histories.html', 'https://www.lib.ncsu.edu/stories/modeling-continental-erosion-and-mountaintop-mining-library', 'https://www.lib.ncsu.edu/news/%E2%80%9Cthe-dynamic-sun%E2%80%9D-combines-solar-physics-and-visualization', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/creation.php', 'https://www.lib.ncsu.edu/news/special-collections/archival-terms-explained', 'https://www.lib.ncsu.edu/jobs/ehra/ask-us-librarian-we-are-no-longer-taking-applications-position', 'https://www.lib.ncsu.edu/case-statement/students.php', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit7b.html', 'https://www.lib.ncsu.edu/hunt/building-hunt', 'https://www.lib.ncsu.edu/archivedexhibits/women/1940.htm', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/nelsonhall.php', 'https://www.lib.ncsu.edu/archivedexhibits/wells/browse.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/resources.php', 'https://www.lib.ncsu.edu/archivedexhibits/wells/collections.html', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/julian.htm', 'https://www.lib.ncsu.edu/archivedexhibits/women/1950.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/victorian.html', 'https://www.lib.ncsu.edu/events/global-film-series-rafiki', 'https://www.lib.ncsu.edu/archivedexhibits/women/1990.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/prelinn.html', 'https://www.lib.ncsu.edu/news/ncsu-libraries-receives-lsta-grant-to-continue-digitization-of-agricultural-documents', 'https://www.lib.ncsu.edu/archivedexhibits/smith/bibliography.html', 'https://www.lib.ncsu.edu/events/femme-making-night-makerspace-2', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/access.html']
urls = open("seed.txt").read().strip().split("\n")
#urls = ['http://127.0.0.1:4000']
print(urls)
filters = open("regex-urlfilter.txt").read().strip().split("\n")
filters = list(filter(lambda x: x.startswith('#') == False and x, filters))
negativefilters = list(filter(lambda x: x.startswith('-'), filters))
negativefilters = "|".join(list(map(lambda x: x.strip('-'),negativefilters)))
positivefilters = list(filter(lambda x: x.startswith('+'), filters))
positivefilters = "|".join(list(map(lambda x: x.strip('+'),positivefilters)))
all_data = {}
process_urls = []
processed_urls = []
retry_urls = []

def checkUrl(url):
	#negpattern = re.compile(r'{}'.format(negativefilters))
	negmatch = re.search(r'{}'.format(negativefilters), url)
	positivematch = re.search(r'{}'.format(positivefilters), url)
	if positivematch and negmatch == None:
		return True
	else:
		#print(url)
		return False

#print(;fa;dlskfa;lsdkfl;af)
def getContents(url):
	# print('get contents')
	print(url)
	# print(checkUrl(url))
	#print(url)
	if url in missing_urls:
		print('missing url is getting got: {}'.format(url))
	try:
		response = requests.get(url)
		parseContents(response, url)
	except Exception as e:
		print(e)
		retry_urls.append(url)
		process_urls.remove(url)
		print('problem url {}$$$$$$$'.format(url))
	return 'FALJDFLDAKJFADSLKJFALKDJFALKSJFLKASDJFALSKDJFALKSDJ'
	

def parseContents(response, original_url):
	content = ''
	page_urls = None
	title = original_url
	schemamarkup = {}
	if original_url.lower().endswith('.pdf') and response.status_code < 400:
		with BytesIO(response.content) as data:
			read_pdf = PyPDF2.PdfReader(data)
			for page in range(len(read_pdf.pages)):
				content += read_pdf.pages[page].extract_text()
	elif (original_url.lower().endswith('.doc') or original_url.lower().endswith('.docx')) and response.status_code < 400:
		content = BytesIO(response.content).read()
	elif (original_url.lower().endswith('.txt')):
		content = response.content.replace("\n", " ").replace("\t", " ").replace("\r", "")
	else:
		parsed_html = BeautifulSoup(response.content, "html.parser" )
		content = parsed_html.body.get_text() if parsed_html.body else 'find me no text'
		title = parsed_html.title.get_text() if parsed_html.title else original_url
		page_urls = parsed_html.find_all('a', href=True)
		schemamarkup = parsed_html.find("script", {"type": "application/ld+json"})
		schemamarkup = schemamarkup.get_text("|", strip=True) if schemamarkup else schemamarkup
		data_url = original_url if response.url == original_url and original_url.replace('https://', '').split('/')[0] not in response.url else response.url
		for index, url in enumerate(page_urls):
			clean_url = url['href']
			if 'http' not in clean_url and re.match(r'{}'.format(negativefilters), clean_url) == None:
				clean_url = urljoin(data_url, clean_url)
			print(clean_url)
			clean_url = clean_url.rstrip('/').strip()
			print(clean_url)
			#print(checkUrl(clean_url) and clean_url not in process_urls and clean_url not in all_data.keys() and any(url in clean_url for url in urls))
			clean_url = clean_url.rsplit("#", 1)[0].strip()
			if clean_url in missing_urls:
				print(clean_url)
				print(checkUrl(clean_url))
				print(clean_url not in process_urls)
				print(clean_url not in processed_urls)
				if clean_url in all_data.keys():
					print('in all data keys')
			print(checkUrl(clean_url))
			if checkUrl(clean_url) and clean_url not in process_urls and clean_url not in processed_urls:
				process_urls.append(clean_url)
				if clean_url in missing_urls:
					print('its in there')
	all_data[original_url] = {'content': content, 'title': title, 'urls_on_page': page_urls,
		'schemamarkup': schemamarkup, 'status_code': response.status_code
	}
	if response.url != original_url:
		all_data[response.url] = all_data[original_url]
	processed_urls.append(original_url)
	processed_urls.append(response.url)
	try:
		process_urls.remove(original_url)
	except Exception as e:
		print('error removign')
		print(e)

for url in urls:
	getContents(url)

while len(process_urls) > 0:
	with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
		# print([url for url in process_urls[0:CONNECTIONS]])
		# print('100 urls')
		future_to_url = (executor.submit(getContents(url), url, TIMEOUT) for url in process_urls[0:CONNECTIONS])
		time1 = time.time()
		for future in concurrent.futures.as_completed(future_to_url):
			print('all_data {}'.format(len(all_data.keys())))
			pass
			print('process_urls {}'.format(len(process_urls)))
	time2 = time.time()
	# process_urls = list(set(process_urls))
	# print(len(process_urls))
	# if process_urls[0] not in processed_urls:
	# 	getContents(process_urls[0])
	# else:
	# 	print('else statement')
	# 	process_urls.remove(process_urls[0])
print(list(all_data.keys()))
conn = sqlite3.connect('crawl_db')
c = conn.cursor()
c.execute('''
          CREATE TABLE IF NOT EXISTS crawls
          ([crawl_url] TEXT PRIMARY KEY, [content] TEXT, [jsondata] TEXT)
          ''')
conn.commit()

for key, value in all_data.items():
	c.execute('''
      INSERT OR REPLACE INTO crawls (crawl_url, content, jsondata)
          VALUES
            (?, ?, ?)
    ''', (key, value['content'], value['schemamarkup']))
	conn.commit()

print(len(all_data.keys()))
