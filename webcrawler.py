import requests, os, PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO

urls = open("seed.txt").read().strip().split("\n")
print(urls)
all_data = {}
process_urls = []

def getContents(url):
	response = requests.get(url)
	parseContents(response, url)
	

def parseContents(response, original_url):
	print(original_url)
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
			if url['href'] and url['href'].startswith("tel:") == False and url['href'].startswith("mailto:") == False and url['href'].startswith("#") == False:
				clean_url = url['href'].rsplit("/#", 1)[0]
				clean_url = clean_url if 'http' in clean_url else os.path.join(original_url, clean_url)
				clean_url = clean_url.rstrip('/')
				if clean_url not in process_urls and clean_url not in all_data.keys() and any(url in clean_url for url in urls):
					process_urls.append(clean_url)
	all_data[original_url] = {'content': content, 'title': title, 'urls_on_page': page_urls,
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
