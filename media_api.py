import requests

S = requests.Session()
URL = "https://en.wikipedia.org/w/api.php"

#Function to serach for the most similar page title to the keyword
def page_title(target):
    
    PARAMS = {
        "action": "opensearch",     #Which action to perform.(Search the wiki using the OpenSearch protocol.)
        "search": target,           #Search string.
        "limit": "1",               #Maximum number of results to return.
        "format": "json"            #The format of the output.
    }

    r = S.get(url=URL, params=PARAMS)
    data = r.json()
    keyword = data[1][0]
    keyword = keyword.replace(" ","_")

    return keyword

#Function to scrape for information using the page title provided by the page_title function
def scrape(target):
    
    keyword = page_title(target)

    PARAMS = {
        "action": "query",          #Which action to perform.(Fetch data from and about MediaWiki.)
        "prop": "extracts",         #Which properties to get for the queried pages.(Returns plain-text or limited HTML extracts of the given pages.)
        "exsentences": "10",        #How many sentences to return.
        "exlimit": "1",             #How many extracts to return.
        "titles": keyword,          #A list of titles to work on.
        "formatversion": "2",       #Output formatting(Modern format)
        "format": "json",           #The format of the output.
        "explaintext": "1"          #Return extracts as plain text instead of limited HTML.
    }

    r = S.get(url=URL, params=PARAMS)
    data = r.json()
    content = data['query']['pages'][0]['extract']
  
    return content