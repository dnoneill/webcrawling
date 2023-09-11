# webcrawling


## Quickstart

1. Update seeds.txt to a list of URLs you want to crawl
2. Update regex-urlfilter.txt to include `+` for your website. For example, if you are crawling https://www.lib.ncsu.edu and corresponding links, i.e. https://www.lib.ncsu.edu/events. add +^https://www.lib.ncsu.edu which says that the links should start with https://www.lib.ncsu.edu. If there are specific regex patterns you don't want crawled, update the file with a `-`, i.e. `-[*!@?=]` won't crawl any url with a `?`, `!`, `@` or `=`. You can also add crawl elements. These are pages where you want all the links from the page, but don't want to index them. For example, `crawl([www.lib.ncsu.edu].*(events)((?<!(past))[?]page))` will crawl all links on the pages `https://www.lib.ncsu.edu/events/upcoming?page=[number]`. So you can get all the events on the page without indexing in solr the page.
3. Update the settings.yml file. The fields section if formated as follows:
```
fields:
  'image:alt': <--------- The field in <head> or in the schema.org markup. The script will look in both places for the field.
    solr: 'imagealt' <----- The field where the content will go in your solr index. If you don't add this field, it won't be indexed in solr but it will be added to the database that gets created with the script
    type: 'text' <---- The type of field in solr. i.e. text, date, integer


content_field: <--- Where to look on an html webpage for the content. This allows things like headers to be cut out of content
  tag: "div"
  id: "content"


regex_file: "regex-urlfilter.txt" <-- path to regex file

solr_index: '' <-- url for solr index. If blank it will not update any solr index
seed_file: "seed.txt" <-- path to seed url file
days_between: 1 <-- Number of days between crawls. If the page has been crawled in fewer days than the setting then the script will not get contents of the page. 

```

4. Run the script


* Run a crawl on seed.txt files. Only crawl pages that haven't been crawled based on the days_between setting. For example, if the current day is August 25th and this script is being run. If example.com was crawled August 24th and days_between is set to 2, the page won't be crawled until August 26th at the exact same time as it was crawled before.

```python3 webcrawler.py crawl```

* Run a crawl on seed.txt files. Ignores days_between setting and crawls all pages.

```python3 webcrawler.py crawl --refresh```

* This requires solr_index to be set. It will take the contents of the crawl_db files and index the contents in your solr index.

```python3 webcrawler.py index```

