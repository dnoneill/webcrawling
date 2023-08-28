import requests, os, PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import re, time, json
from urllib.parse import urljoin
import concurrent.futures
import sqlite3
import pysolr, yaml
from dateutil import parser

CONNECTIONS = 1000
TIMEOUT = 5
settings = yaml.load(open("settings.yml"), Loader=yaml.FullLoader)
regex_file = settings['regex_file']
urls = open(settings['seed_file']).read().strip().split("\n")
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
solr_index = settings['solr_index']
fields = settings['fields']
solrkeys = {v['solr']: v['type'] for k, v in fields.items() if 'solr' in v.keys()}
solrkeys['id'] = 'text'
solrkeys['url'] = 'text'
content_field = settings['content_field'] if 'content_field' in settings.keys() else None

def checkUrl(url):
	negmatch = re.search(r'{}'.format(negativefilters), url)
	positivematch = re.search(r'{}'.format(positivefilters), url)
	if positivematch and negmatch == None and url not in process_urls and url not in processed_urls and url.strip('/') not in process_urls and url.strip('/') not in processed_urls:
		return True
	else:
		return False

def getContents(url):
	#print(url)
	try:
		response = requests.get(url)
		parseContents(response, url)
	except Exception as e:
		#print(e)
		retry_urls.append(url)
		process_urls.remove(url)
		#print('*******problem url {}*******'.format(url))
	return 'FALJDFLDAKJFADSLKJFALKDJFALKSJFLKASDJFALSKDJFALKSDJ'
	
def getHTTP(text):
	regex = r"(https?:\S+)(?=\"|'| )"
	text = text if type(text) == str else str(text)
	url = re.findall(regex,text)
	for x in url:
		if checkUrl(x):
			process_urls.append(x)

def all_tags(parsed_html, tag):
	return " ".join(list(map(lambda x: x.get_text(), parsed_html.find_all(tag))))


def clean_keys(key):
	return "".join(re.findall("[a-zA-Z]+", key))

def parseContents(response, original_url):
	content = ''
	page_urls = None
	schemamarkup = {}
	data_url = original_url if response.url == original_url and original_url.replace('https://', '').split('/')[0] not in response.url else response.url
	metadata = {'id': data_url, 'title': original_url.rsplit('/', 1)[-1]}
	if original_url.lower().endswith('.pdf') and response.status_code < 400:
		with BytesIO(response.content) as data:
			read_pdf = PyPDF2.PdfReader(data)
			if read_pdf.metadata :
				if read_pdf.metadata.title:
					metadata['title'] = read_pdf.metadata.title
					# print(metadata['title'])
					# print('kfjaldskfjlsak')
				try:
					metadata['keywords'] = read_pdf.metadata.keywords
					# print(metadata['keywords'])
					# print('kfjaldskfjlsak')
				except:
					pass
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
		metadata['title'] = parsed_html.title.get_text() if parsed_html.title else metadata['title']
		if content_field and parsed_html.find(content_field['tag'], {"id": content_field['id']}):
			#print('content tag')
			content = parsed_html.find(content_field['tag'], {"id": content_field['id']}).get_text()
		elif parsed_html.main:
			#print('main tag')
			content = parsed_html.main.get_text()
		elif parsed_html.section:
			#print('section tag')
			content = all_tags(parsed_html, 'section')
		elif parsed_html.article:
			#print('article tag')
			content = all_tags(parsed_html, 'content')
		elif parsed_html.body:
			#print('body tag')
			content = parsed_html.body.get_text()
		for key in fields.keys():
			meta_key = fields[key]['solr'] if 'solr' in fields[key].keys() else key
			get_content = parsed_html.find("meta",  {"property":"og:{}".format(key)})
			get_content = get_content if get_content else parsed_html.find("meta",  {"property":"{}".format(key)})
			get_content = get_content["content"] if get_content else ''
			if get_content:
				metadata[meta_key] = get_content
		page_urls = parsed_html.find_all(href=True)
		schemamarkup = parsed_html.find("script", {"type": "application/ld+json"})
		schemamarkup = schemamarkup.get_text("|", strip=True) if schemamarkup else schemamarkup
		if schemamarkup:
			try:
				schema = json.loads(schemamarkup)
				for key in fields.keys():
					if key in schema.keys() and schema[key]:
						meta_key = fields[key]['solr'] if 'solr' in fields[key].keys() else key
						metadata[meta_key] = schema[key].strip()
			except:
				pass
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
	if 'id_field' in settings.keys() and settings['id_field']:
		metadata['id'] = metadata[settings['id_field']]
	all_data[data_url] = {**metadata, **{'url': data_url ,'content': content, 'urls_on_page': page_urls, 'original_url': original_url,
		'schemamarkup': schemamarkup, 'status_code': response.status_code, 'redirect_url': response.url, 'raw_content': response.content}
	}
	if solr_index and response.status_code < 400 and 'not found' not in metadata['title']:
		solrdict = {k: parse_type(solrkeys, k, v) for k, v in all_data[data_url].items() if k in solrkeys.keys() and v != ''}
		solr = pysolr.Solr(solr_index, always_commit=True)
		solr.add([
		    solrdict
		])
	# if response.url != original_url:
	# 	all_data[response.url] = all_data[original_url]
	processed_urls.append(original_url)
	processed_urls.append(response.url)
	try:
		process_urls.remove(original_url)
		if response.url != original_url and response.url in process_urls:
			process_urls.remove(response.url)
	except Exception as e:
		pass
		print('error removign')
		print(e)


def parse_type(sql_keys, key, value):
	fieldtype = sql_keys[key]
	if 'text' in fieldtype.lower():
		return str(value)
	elif fieldtype.lower() == 'integer':
		return int(value)
	elif fieldtype.lower() == 'date' and value:
		return parser.parse(value).strftime("%Y-%m-%dT%H:%M:%SZ")
	else:
		return str(value)

for url in urls:
	getContents(url)

while len(process_urls) > 0:
	with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
		# print([url for url in process_urls[0:CONNECTIONS]])
		# print('100 urls')
		future_to_url = (executor.submit(getContents(url), url, TIMEOUT) for url in process_urls[0:CONNECTIONS])
		time1 = time.time()
		for future in concurrent.futures.as_completed(future_to_url):
			#print('all_data {}'.format(len(all_data.keys())))
			pass
			#print('process_urls {}'.format(len(process_urls)))
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

my_keys = {**{clean_keys(k): v['type'].upper() for k, v in fields.items()}, **{'id' : 'TEXT PRIMARY KEY', 'urls_on_page': 'TEXT', 'original_url': 'TEXT', 'schemamarkup': 'TEXT', 'status_code': 'INTEGER', 'redirect_url': 'TEXT', 'raw_content': 'TEXT'}}
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
		pass
		# print(value['content'])
		print(key)
		print(e)

res = c.execute("SELECT * FROM crawls")
# print(res)
# print(res.fetchall())

existing = {k:v for k,v in all_data.items() if v['status_code'] < 400 and 'notfound' not in v['redirect_url'] and 'not found' not in v['title']}
# print(len(all_data.keys()))
# print(list(all_data.keys()))
# print(len(existing.keys()))
# print(existing.keys())
