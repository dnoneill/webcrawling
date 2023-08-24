import requests, os, PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import re, time, json
from urllib.parse import urljoin
import concurrent.futures
import sqlite3
import pysolr
from settings import *

CONNECTIONS = 1000
TIMEOUT = 5
urls = open(seed_file).read().strip().split("\n")
filters = open(regex_file).read().strip().split("\n")
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
	negmatch = re.search(r'{}'.format(negativefilters), url)
	positivematch = re.search(r'{}'.format(positivefilters), url)
	if positivematch and negmatch == None and url not in process_urls and url not in processed_urls:
		return True
	else:
		return False

def getContents(url):
	print(url)
	try:
		response = requests.get(url)
		parseContents(response, url)
	except Exception as e:
		print(e)
		retry_urls.append(url)
		process_urls.remove(url)
		print('*******problem url {}*******'.format(url))
	return 'FALJDFLDAKJFADSLKJFALKDJFALKSJFLKASDJFALSKDJFALKSDJ'
	
def getHTTP(text):
	regex = r"(https?:\S+)(?=\"|'| )"
	text = text if type(text) == str else str(text)
	url = re.findall(regex,text)
	for x in url:
		print('text or doc uri {}'.format(x))
		if checkUrl(x):
			process_urls.append(x)

def all_tags(parsed_html, tag):
	return " ".join(list(map(lambda x: x.get_text(), parsed_html.find_all(tag))))


def parseContents(response, original_url):
	content = ''
	page_urls = None
	title = original_url
	schemamarkup = {}
	metadata = {element: '' for element in crawlmetadata}
	if original_url.lower().endswith('.pdf') and response.status_code < 400:
		with BytesIO(response.content) as data:
			read_pdf = PyPDF2.PdfReader(data)
			for page in range(len(read_pdf.pages)):
				if "/Annots" in read_pdf.pages[page]:
					for annot in read_pdf.pages[page]["/Annots"]:
						obj = annot.get_object()
						if '/A' in obj.keys() and '/URI' in obj['/A'].keys():
							uri = obj['/A']['/URI']
							if checkUrl(uri):
								process_urls.append(uri)
				content += read_pdf.pages[page].extract_text()
	elif (original_url.lower().endswith('.doc') or original_url.lower().endswith('.docx')) and response.status_code < 400:
		content = BytesIO(response.content).read()
		getHTTP(content)
	elif (original_url.lower().endswith('.txt')) and response.status_code < 400:
		content = response.content.decode('utf8').replace("\n", " ").replace("\t", " ").replace("\r", "")
		getHTTP(content)
	else:
		parsed_html = BeautifulSoup(response.content, "html.parser" )
		content = 'find me no text'
		if parsed_html.find("div", {"id": "content"}):
			#print('content tag')
			content = parsed_html.find("div", {"id": "content"}).get_text()
		elif parsed_html.main:
			print('main tag')
			content = parsed_html.main.get_text()
		elif parsed_html.section:
			print('section tag')
			content = all_tags(parsed_html, 'section')
		elif parsed_html.article:
			print('article tag')
			content = all_tags(parsed_html, 'content')
		elif parsed_html.body:
			print('body tag')
			content = parsed_html.body.get_text()
		title = parsed_html.title.get_text() if parsed_html.title else original_url
		for key in metadata:
			get_content = parsed_html.find("meta",  {"property":"og:{}".format(key)})
			get_content = get_content if get_content else parsed_html.find("meta",  {"property":"{}".format(key)})
			get_content = get_content["content"] if get_content else ''
			metadata[key] = get_content
		page_urls = parsed_html.find_all(href=True)
		schemamarkup = parsed_html.find("script", {"type": "application/ld+json"})
		schemamarkup = schemamarkup.get_text("|", strip=True) if schemamarkup else schemamarkup
		if schemamarkup:
			try:
				schema = json.loads(schemamarkup)
				if 'name' in schema.keys():
					title = schema['name']
				for key in metadata:
					if key in schema.keys():
						metadata[key] = schema[key].strip()
			except:
				pass
		title = title.split(' | ')[0]
		data_url = original_url if response.url == original_url and original_url.replace('https://', '').split('/')[0] not in response.url else response.url
		for index, url in enumerate(page_urls):
			clean_url = url['href']
			if 'http' not in clean_url and re.match(r'{}'.format(negativefilters), clean_url) == None:
				clean_url = urljoin(data_url, clean_url)
			clean_url = clean_url.rstrip('/').strip()
			clean_url = clean_url.rsplit("#", 1)[0].strip()
			if checkUrl(clean_url):
				process_urls.append(clean_url)
	content = content if type(content) == str else str(content)
	content = re.sub(' +', ' ', content.replace('\n', ' ')).strip()
	all_data[original_url] = metadata | {'id': original_url, 'url': original_url ,'content': content, 'title': title, 'urls_on_page': page_urls,
		'schemamarkup': schemamarkup, 'status_code': response.status_code, 'redirect_url': response.url
	}
	if solr_index:
		solrdict = {k: v for k, v in all_data[original_url].items() if k in solrkeys}
		solr = pysolr.Solr(solr_index, always_commit=True)
		solr.add([
		    solrdict
		])
	if response.url != original_url:
		all_data[response.url] = all_data[original_url]
	processed_urls.append(original_url)
	processed_urls.append(response.url)
	try:
		process_urls.remove(original_url)
	except Exception as e:
		print('error removign')
		print(e)


def parse_type(sql_keys, key, value):
	fieldtype = sql_keys[key]
	if 'TEXT' in fieldtype:
		return str(value)
	elif fieldtype == 'INTEGER':
		return int(value)

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

conn = sqlite3.connect('crawl_db')
c = conn.cursor()

table = "crawls"

my_keys = {element: 'TEXT' for element in crawlmetadata} | {'id' : 'TEXT PRIMARY KEY', 'content': 'TEXT', 'url': 'TEXT', 'title': 'TEXT','urls_on_page': 'TEXT', 'schemamarkup': 'TEXT', 'status_code': 'INTEGER', 'redirect_url': 'TEXT'}
table_columns = ["{} {}".format(key, value) for key, value in my_keys.items()]
c.execute("CREATE TABLE IF NOT EXISTS {} ({})".format(table, ", ".join(table_columns)))
conn.commit()

for key, value in all_data.items():
	try:
		sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table,
            ','.join(my_keys),
            ','.join(['?']*len(my_keys)))
		c.execute(sql, tuple([parse_type(my_keys, k, v) for k, v in value.items() if k in my_keys]))
		conn.commit()
	except Exception as e:
		print(value['content'])
		print(key)
		print(e)

res = c.execute("SELECT * FROM crawls")
print(res)
print(res.fetchall())

existing = {k:v for k,v in all_data.items() if v['status_code'] < 400 and 'notfound' not in v['redirect_url']}
print(len(all_data.keys()))
print(list(all_data.keys()))
print(len(existing.keys()))
print(existing.keys())
