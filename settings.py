solr_index = 'http://solr:8983/solr/nutch'
seed_file = "seed.txt"
crawlmetadata = ['description', 
				 'keywords', 
				 'image', 'imagealt', 
				 'startDate', 'endDate', 
				 'duration', 'location', 
				 'eventStatus']
solrkeys = ['description', 'keywords', 'image', 'image:alt', 'startDate', 'endDate', 'content', 'title', 'url', 'id']
#solrkeys = ['description', 'keywords', 'image', 'imagealt', 'startDate', 'endDate', 'duration', 'location', 'eventStatus', 'content', 'title']
regex_file = "regex-urlfilter.txt"