solr_index = 'http://solr:8983/solr/nutch'
seed_file = "seed.txt"
crawlmetadata = ['description', 
				 'keywords', 
				 'image', 'image:alt', 
				 'startDate', 'endDate', 
				 'duration', 'location', 
				 'eventStatus']
solrkeys = {'description': 'text', 'keywords':'text', 'image': 'text', 'image:alt': 'text', 'startDate': 'date', 'endDate': 'date', 'content': 'text', 'title': 'text', 'url': 'text', 'id': 'text'}
#solrkeys = {'description': 'text', 'keywords':'text', 'image': 'text', 'image:alt': 'text', 'startDate': 'date', 'endDate': 'date', 'content': 'text','duration': 'tex$
regex_file = "regex-urlfilter.txt"