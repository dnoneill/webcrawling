import requests, os, PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import re

urls = open("seed.txt").read().strip().split("\n")
print(urls)
filters = open("regex-urlfilter.txt").read().strip().split("\n")
filters = list(filter(lambda x: x.startswith('#') == False and x, filters))
negativefilters = list(filter(lambda x: x.startswith('-'), filters))
negativefilters = "|".join(list(map(lambda x: x.strip('-'),negativefilters)))
positivefilters = list(filter(lambda x: x.startswith('+'), filters))
positivefilters = "|".join(list(map(lambda x: x.strip('+'),positivefilters)))
all_data = {}
process_urls = []

def checkUrl(url):
	#negpattern = re.compile(r'{}'.format(negativefilters))
	negmatch = re.match(r'{}'.format(negativefilters), url)
	positivematch = re.match(r'{}'.format(positivefilters), url)
	if positivematch and not negmatch:
		return True
	else:
		return False

def getContents(url):
	print(url)
	response = requests.get(url)
	parseContents(response, url)
	

def parseContents(response, original_url):
	if original_url.endswith('.pdf'):
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
			if 'node' in clean_url and 'http' not in clean_url:
				clean_url = os.path.join("https://www.lib.ncsu.edu", clean_url)
			elif 'http' not in clean_url:
				clean_url = os.path.join(original_url, clean_url)
			clean_url = clean_url.rstrip('/')
			# print(clean_url)
			# print(checkUrl(clean_url) and clean_url not in process_urls and clean_url not in all_data.keys() and any(url in clean_url for url in urls))
			if checkUrl(clean_url) and response.url not in process_urls and response.url not in all_data.keys() and any(url in response.url for url in urls) and clean_url not in process_urls and clean_url not in all_data.keys() and any(url in clean_url for url in urls):
				process_urls.append(clean_url)
	all_data[response.url] = {'content': content, 'title': title, 'urls_on_page': page_urls,
		'schemamarkup': schemamarkup, 'status_code': response.status_code
	}
	try:
		process_urls.remove(original_url)
	except Exception as e:
		print(e)

for url in urls:
	getContents(url)

while len(process_urls) > 0:
	process_urls = list(set(process_urls))
	getContents(process_urls[0])
print(all_data.keys())
print(len(all_data.keys()))
