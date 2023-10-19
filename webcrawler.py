import requests, os, PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import re, time, json
from urllib.parse import urljoin
import concurrent.futures
import sqlite3
import pysolr, yaml
from dateutil import parser as dateparser
import logging
from datetime import datetime, timedelta,timezone
import gc, csv
from time import sleep
import argparse

gc.set_threshold(0)

CONNECTIONS = 1000
TIMEOUT = 5
settings = yaml.load(open("settings.yml"), Loader=yaml.FullLoader)
regex_file = settings['regex_file']
urls = open(settings['seed_file']).read().strip().split("\n")
filterfile = open(regex_file).read().strip().split("\n")
filters = list(filter(lambda x: x and x.startswith('#') == False and x.startswith('crawl') == False, filterfile))
negativefilters = list(filter(lambda x: x.startswith('-'), filters))
negativefilters = "|".join(list(map(lambda x: x.strip('-'),negativefilters)))
positivefilters = list(filter(lambda x: x.startswith('+'), filters))
positivefilters = "|".join(list(map(lambda x: x.strip('+'),positivefilters)))
crawlitems = list(filter(lambda x: x and x.startswith('crawl'), filterfile))
crawlitems = "|".join(list(map(lambda x: x and x.split('crawl')[-1], crawlitems)))
deadlinkfieldnames = ['on page', 'url', 'link', 'anchor', 'code']

all_data = {}
process_urls = []
processed_urls = []
retry_urls = []
crawlonly = []
solr_index = settings['solr_index']
fields = settings['fields']
solrkeys = {v['solr']: v['type'] for k, v in fields.items() if 'solr' in v.keys()}
solrkeys['id'] = 'text'
solrkeys['url'] = 'text'
content_field = settings['content_field'] if 'content_field' in settings.keys() else None
db_name = 'crawl_db'
table = "crawls"
external_links_db = "external_links_db"
external_db_fields = {'id' : 'TEXT PRIMARY KEY', 'url': 'TEXT', 'on_pages': 'TEXT'}
logging.basicConfig(filename="errors_webcrawling.log", level=logging.WARNING)

def clean_keys(key):
	return "".join(re.findall("[a-zA-Z]+", key))

my_keys = {**{clean_keys(k): v['type'].upper() for k, v in fields.items()}, **{'id' : 'TEXT PRIMARY KEY', 'url': 'TEXT', 'urls_on_page': 'TEXT', 'original_url': 'TEXT', 'schemamarkup': 'TEXT', 'status_code': 'INTEGER', 'redirect_url': 'TEXT', 'raw_content': 'TEXT', 'crawled': 'DATE'}}

def checkUrl(url):
	if (checkIndex(url) or checkCrawl(url)) and 'http' in url and url not in process_urls and url not in processed_urls and url.strip('/') not in process_urls and url.strip('/') not in processed_urls:
		if args.refresh is False:
			conn, c = connectToDB()
			query = "SELECT crawled, status_code FROM {} WHERE original_url = '{}' OR id = '{}'".format(table, url, url)
			res = c.execute(query)
			dbitem = res.fetchone()
			crawled = dateparser.parse(dbitem[0]) if dbitem != None else datetime.now(timezone.utc) - timedelta(days=3*365)
			status_code = dbitem[1] if dbitem != None else 200
			if (datetime.now(timezone.utc) - crawled).days < settings['days_between'] and status_code < 399:
				return False
			else:
				return True
		else:
			return True
	else:
		return False

def checkIndex(url):
	negmatch = re.search(r'{}'.format(negativefilters), url)
	positivematch = re.search(r'{}'.format(positivefilters), url)
	if positivematch and negmatch == None:
		return True
	else:
		return False

def checkCrawl(url):
	if crawlitems and re.search(r'{}'.format(crawlitems), url) != None:
		return True
	else:
		return False

def getContents(url):
	#print(url)
	try:
		response = requests.get(url)
		parseContents(response, url)
	except Exception as e:
		retry_urls.append(url)
		if url in process_urls:
			process_urls.remove(url)
		logging.warning('*******problem url {}\n{}*******'.format(url, e))

def getHTTP(text):
	regex = r"(https?:\S+)(?=\"|'| )"
	text = text if type(text) == str else str(text)
	url = re.findall(regex,text)
	for x in url:
		if checkUrl(x):
			process_urls.append(x)

def all_tags(parsed_html, tag):
	return " ".join(list(map(lambda x: x.get_text(separator=u' '), parsed_html.find_all(tag))))


def writeToDB(value, my_keys=my_keys, db_name=db_name):
	conn, c = connectToDB(db_name)
	try:
		sql = 'INSERT or IGNORE INTO {} ({}) VALUES ({})'.format(table,
            ','.join(my_keys.keys()),
            ','.join(['?']*len(my_keys)))
		c.execute(sql, tuple([parse_type(my_keys, k, v) for k, v in value.items() if k in my_keys]))
		conn.commit()
	except Exception as e:
		logging.warning('*******problem writing {} to db: {}'.format(value['url'], e))
	conn.close()

def indexInSolr(all_data):
	isindexable = all_data['status_code'] < 400 and 'not found' not in all_data['title'] and checkIndex(all_data['original_url'])
	if solr_index and isindexable:
		solrdict = {k: parse_type(solrkeys, k, v) for k, v in all_data.items() if k in solrkeys.keys() and v != ''}
		solr = pysolr.Solr(solr_index, always_commit=True)
		solr.add([
		    solrdict
		])
	elif solr_index and checkIndex(all_data['original_url']):
		logging.warning('*******{} responded {}*******'.format(all_data['original_url'], all_data['status_code']))

def deleteFromSolr(items):
	for item in items:
		solr = pysolr.Solr(solr_index, always_commit=True)
		solr.delete(id='{}'.format(item))

def parseContents(response, original_url):
	content = ''
	page_urls = None
	schemamarkup = {}
	data_url = original_url if response.url == original_url and original_url.replace('https://', '').split('/')[0] not in response.url else response.url
	metadata = {key: '' for key in my_keys}
	metadata['id'] = data_url
	metadata['title'] = original_url.rsplit('/', 1)[-1]

	if original_url.lower().endswith('.pdf') and response.status_code < 400:
		with BytesIO(response.content) as data:
			read_pdf = PyPDF2.PdfReader(data)
			if read_pdf.metadata :
				if read_pdf.metadata.title:
					metadata['title'] = read_pdf.metadata.title
				try:
					metadata['keywords'] = read_pdf.metadata.keywords
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
		metadata['title'] = parsed_html.title.get_text(separator=u' ') if parsed_html.title else metadata['title']
		if content_field and parsed_html.find(content_field['tag'], {"id": content_field['id']}):
			content = parsed_html.find(content_field['tag'], {"id": content_field['id']}).get_text(separator=u' ')
		elif parsed_html.main:
			content = parsed_html.main.get_text(separator=u' ')
		elif parsed_html.section:
			content = all_tags(parsed_html, 'section')
		elif parsed_html.article:
			content = all_tags(parsed_html, 'content')
		elif parsed_html.body:
			content = parsed_html.body.get_text(separator=u' ')
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
			if 'http' not in clean_url:
				if re.match(r'{}'.format(negativefilters), clean_url) == None:
					clean_url = urljoin(data_url, clean_url)
				elif checkCrawl(urljoin(data_url, clean_url)):
					clean_url = urljoin(data_url, clean_url)
			clean_url = clean_url.rstrip('/').strip()
			clean_url = clean_url.rsplit("#", 1)[0].strip()
			if checkUrl(clean_url):
				process_urls.append(clean_url)
			elif 'http' in clean_url and clean_url != data_url and checkIndex(clean_url) == False and checkCrawl(clean_url) == False:
				conn, c = connectToDB(external_links_db, True)
				query = "SELECT * FROM {} WHERE id = '{}'".format(table, clean_url)
				res = c.execute(query)
				dbitem = res.fetchone()
				on_pages = dbitem['on_pages'] + ', ' + data_url if dbitem != None and data_url not in dbitem['on_pages'] else data_url
				value = {'id': clean_url, 'url': clean_url, 'on_pages': on_pages}
				writeToDB(value, external_db_fields, external_links_db)

	content = content if type(content) == str else str(content)
	content = re.sub(' +', ' ', content.replace('\n', ' ')).strip()
	if 'id_field' in settings.keys() and settings['id_field']:
		metadata['id'] = metadata[settings['id_field']]
	metadata['crawled'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
	all_data = {**metadata, **{'url': data_url ,'content': content, 'urls_on_page': page_urls, 'original_url': original_url,
		'schemamarkup': schemamarkup, 'status_code': response.status_code, 'redirect_url': response.url, 'raw_content': response.content}
	}
	writeToDB(all_data)
	indexInSolr(all_data)
	processed_urls.append(original_url)
	processed_urls.append(response.url)
	try:
		process_urls.remove(original_url)
		if response.url != original_url and response.url in process_urls:
			process_urls.remove(response.url)
	except Exception as e:
		pass


def parse_type(sql_keys, key, value):
	fieldtype = sql_keys[key]
	if 'text' in fieldtype.lower():
		return str(value)
	elif fieldtype.lower() == 'integer':
		return int(value)
	elif fieldtype.lower() == 'date' and value:
		return dateparser.parse(value).strftime("%Y-%m-%dT%H:%M:%SZ")
	else:
		return str(value)

def connectToDB(db_name=db_name, rows=False):
	conn = sqlite3.connect(db_name)
	if rows:
		conn.row_factory = sqlite3.Row
	c = conn.cursor()
	return conn, c

def checkDB(db_name=db_name, my_keys=my_keys):
	conn, c = connectToDB(db_name)
	table_columns = ["{} {}".format(key, value) for key, value in my_keys.items()]
	c.execute("CREATE TABLE IF NOT EXISTS {} ({})".format(table, ", ".join(table_columns)))
	c.execute("select * from {} limit 1".format(table))
	col_name=[i[0] for i in c.description]
	missing_columns = list(filter(lambda x: x not in col_name, my_keys.keys()))
	if len(missing_columns) > 0:
		for col in missing_columns:
			c.execute("ALTER TABLE {} ADD COLUMN {} {}".format(table, col, my_keys[col]))
	conn.commit()
	conn.close()

def writeRow(dictionary, raw_content):
	with open('deadlnks.csv', 'a', newline='') as f:
		writer = csv.DictWriter(f, fieldnames=deadlinkfieldnames)
		parsed_html = BeautifulSoup(raw_content, "html.parser")
		partialurl = dictionary['url'].split('edu/')[-1]
		for links in parsed_html.findAll("a", href=lambda href: href and partialurl in href):
			dictionary['anchor'] = links.get_text(separator=u' ')
			dictionary['link'] = links
			writer.writerow(dictionary)
		f.close()

def requestsGet(externalitem):
	try:
		response = requests.get(externalitem['url'])
		status_code = response.status_code
	except:
		status_code = 500
	if status_code > 299:
		conn, c = connectToDB(db_name, True)
		on_pages = externalitem['on_pages'].split(', ')
		for page in on_pages:
			res = c.execute("SELECT * FROM {} WHERE original_url = '{}' OR id = '{}'".format(table, page, page))
			pagecontent = res.fetchone()
			if pagecontent:
				writeRow({'url':externalitem['url'], 'code': status_code, 'on page': page}, pagecontent['raw_content'])
			# else:
			# 	print(externalitem['url'])

def checkExternalLinks():
	conn, c = connectToDB(external_links_db, True)
	query = "SELECT * FROM {}".format(table)
	res = c.execute(query)
	externaldbitems = list(map(lambda x: dict(x), res.fetchall()))
	with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
			future_to_url = (executor.submit(requestsGet(externalitem), externalitem, TIMEOUT) for externalitem in externaldbitems[0:len(externaldbitems)])
			for future in concurrent.futures.as_completed(future_to_url):
				pass
			gc.collect()
def main():
	if args.function:
		if args.function == 'index':
			if settings['solr_index']:
				conn, c = connectToDB(db_name, True)
				res = c.execute("SELECT * FROM {}".format(table))
				crawls = res.fetchall()
				for item in crawls:
					indexInSolr(dict(item))
			else:
				print('\n You are missing the variable "solr_index" which is set in the settings.yml file. Please update the file with the correct variable and try running again. \n')
		elif args.function == 'deadlinks':
			conn, c = connectToDB(db_name, True)
			query = "SELECT * FROM {} WHERE status_code > 299".format(table)
			res = c.execute(query)
			dbitems = list(map(lambda x: dict(x), res.fetchall()))
			with open('deadlnks.csv', 'w', newline='') as f:
				writer = csv.DictWriter(f, fieldnames=deadlinkfieldnames)
				writer.writeheader()
			for item in dbitems:
				query = "SELECT * FROM {} WHERE urls_on_page LIKE '%{}%' OR urls_on_page LIKE '%{}%'".format(table, item['url'], item['original_url'])
				res = c.execute(query)
				for on_page in res.fetchall():
					writeRow({'url': item['url'], 'code': item['status_code'], 'on page': on_page['url']}, item['raw_content'])
			checkExternalLinks()
			
		elif args.function == 'crawl':
			checkDB()
			checkDB(external_links_db, external_db_fields)
			for url in urls:
				getContents(url)
			while len(process_urls) > 0:
				with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
					future_to_url = (executor.submit(getContents(url), url, TIMEOUT) for url in process_urls[0:CONNECTIONS])
					for future in concurrent.futures.as_completed(future_to_url):
						pass
					gc.collect()
			if args.refresh is True:
				conn, c = connectToDB(db_name, True)
				res = c.execute("SELECT id FROM {} WHERE crawled < '{}'".format(table, datetime.now(timezone.utc) - timedelta(days=1)))
				deleteitems = list(map(lambda x: x['id'], res.fetchall()))
				res2 = c.execute("SELECT * FROM {}".format(table))
				c.execute("DELETE FROM {} WHERE id IN ({})".format(table, ', '.join('?' for item in deleteitems)), tuple(deleteitems))
				conn.commit()
				if settings['solr_index']:
					deleteFromSolr(list(deleteitems))
				conn.close()	
	else:
		print('\n You are missing required positional argument crawl or index. i.e. python3 webcrawler.py crawl or python3 webcrawler.py index. \n')

if __name__ == '__main__':
	parser=argparse.ArgumentParser(
	description='''Webcrawling script for crawling a list of webpages.''')
	parser.add_argument('--refresh', action='store_true', help='True or False value; will delete db and crawl all pages from scratch.')
	parser.add_argument('--includexternal', action='store_true', help='True or False value; will delete db and crawl all pages from scratch.')
	parser.add_argument('function', default=None, help='The name of what you want the the script to do. Options are: index, crawl and deadlinks')
	args=parser.parse_args()
	main()
	