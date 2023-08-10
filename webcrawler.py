import requests, os, PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import re
from urllib.parse import urljoin

urls = open("seed.txt").read().strip().split("\n")
print(urls)
urls = ['https://www.lib.ncsu.edu/findingaids/search?all_resources=true&filters%5Bagents%5D%5B%5D=Winstead%2C+Nash+Nicks&filters%5Bresource_category%5D=mss']
filters = open("regex-urlfilter.txt").read().strip().split("\n")
filters = list(filter(lambda x: x.startswith('#') == False and x, filters))
negativefilters = list(filter(lambda x: x.startswith('-'), filters))
negativefilters = "|".join(list(map(lambda x: x.strip('-'),negativefilters)))
positivefilters = list(filter(lambda x: x.startswith('+'), filters))
positivefilters = "|".join(list(map(lambda x: x.strip('+'),positivefilters)))
all_data = {}
process_urls = []
processed_urls = []

def checkUrl(url):
	#negpattern = re.compile(r'{}'.format(negativefilters))
	negmatch = re.search(r'{}'.format(negativefilters), url)
	positivematch = re.search(r'{}'.format(positivefilters), url)
	if positivematch and negmatch == None:
		return True
	else:
		#print(url)
		return False

def getContents(url):
	print(url)
	print(checkUrl(url))
	response = requests.get(url)
	parseContents(response, url)
	

def parseContents(response, original_url):
	if original_url.endswith('.pdf') and response.status_code < 400:
		title = original_url
		content = ''
		page_urls = None
		schemamarkup = {}
		with BytesIO(response.content) as data:
			read_pdf = PyPDF2.PdfReader(data)
			for page in range(len(read_pdf.pages)):
				content += read_pdf.pages[page].extract_text()
	else:
		parsed_html = BeautifulSoup(response.content, "html.parser" )
		content = parsed_html.body.get_text() if parsed_html.body else 'find me no text'
		title = parsed_html.title.get_text() if parsed_html.title else original_url
		page_urls = parsed_html.find_all('a', href=True)
		original_url = original_url.rstrip('/')
		schemamarkup = parsed_html.find("script", {"type": "application/ld+json"})
		for index, url in enumerate(page_urls):
			clean_url = url['href'].rsplit("/#", 1)[0]
			if clean_url.startswith('/'):
				clean_url = urljoin(original_url, clean_url)
			elif 'http' not in clean_url and re.match(r'{}'.format(negativefilters), clean_url) == False:
				origin_url = original_url.replace('https://', '').split('/')[0]
				clean_url = urljoin("https://{}".format(origin_url), clean_url)
			clean_url = clean_url.rstrip('/')
			# print(clean_url)
			# print(checkUrl(clean_url) and clean_url not in process_urls and clean_url not in all_data.keys() and any(url in clean_url for url in urls))
			if checkUrl(clean_url) and clean_url not in process_urls and clean_url not in processed_urls:
				process_urls.append(clean_url)
	all_data[original_url] = {'content': content, 'title': title, 'urls_on_page': page_urls,
		'schemamarkup': schemamarkup, 'status_code': response.status_code
	}
	processed_urls.append(original_url)
	processed_urls.append(response.url)
	try:
		process_urls.remove(original_url)
	except Exception as e:
		print(e)

for url in urls:
	getContents(url)

while len(process_urls) > 0:
	process_urls = list(set(process_urls))
	print(len(process_urls))
	if process_urls[0] not in processed_urls:
		getContents(process_urls[0])
	else:
		print('else statement')
		process_urls.remove(process_urls[0])
print(all_data.keys())
print(len(all_data.keys()))
