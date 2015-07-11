import http.client
import html
import json
import re
from nltk.corpus import stopwords
import os
import codecs

HOST_URL = 'a.4cdn.org'
G_URL = '/g/catalog.json'
G_FILTERS = \
[lambda thread: 
 not('battlestation' in thread['com_lower'] and 'thread' in thread['com_lower']),
 lambda thread:
 not('desktop' in thread['com_lower'] and 'thread' in thread['com_lower']),
 lambda thread:
 not('keyboard' in thread['com_lower'] and 'thread' in thread['com_lower']),
 lambda thread:
 not('general' in thread['com_lower']) or 'generally' in thread['com_lower'],
 lambda thread:
 not('what are you working on' in thread['com_lower']),
 lambda thread:
 not('stupid question' in thread['com_lower']),
 lambda thread:
 not('headphone' in thread['com_lower'] and 'thread' in thread['com_lower'])
]

ADDITIONAL_STOP_WORDS = {"like", "one", "/g/", "may", "-", "thread",
"it's", "i've", "see", "get", "first", "new", "would", "&", "good", 
"right", "way", "thoughts", "guys", "based", "maybe", "i'm",
"ask", "related", "getting", "much", ">", "done", "got", "various"}

K = 50
MAX_BAR_LEN = 20

def grab_and_parse(URL):
    m_http = http.client.HTTPConnection(HOST_URL) 
    m_http.request('GET', G_URL)
    m_response = m_http.getresponse() 
    m_raw_json = m_response.read()
    return json.loads(m_raw_json.decode())

def extract_threads(catalog_json):
    extracted_threads = []
    for page in catalog_json:
        for thread in page["threads"]:
            extracted_threads.append(thread)
    return extracted_threads

def try_get_com(thread):
    try:
        return thread['com']
    except KeyError:
        return ""

def add_lowered(thread):
    thread['com'] = try_get_com(thread)
    thread['com_lower'] = html.unescape(re.sub("<.*?>", "",\
    try_get_com(thread).lower()))
    thread['com_lower'] = re.sub("[\.!?]", "", thread['com_lower'])
    return thread

def remove_stops(thread):
    thread['no_stop'] = ' '.join([word for word in thread['com_lower'].split()\
    if word not in (stopwords.words('english')) and word not in\
    ADDITIONAL_STOP_WORDS])
    return thread

def lowerify_threads(threads):
    lower_threads = map(lambda thread: add_lowered(thread), threads)
    return lower_threads

#assumes we have the lowercase comments
def unstopify_threads(threads):
    unstopped_threads = map(lambda thread: remove_stops(thread), threads)
    return unstopped_threads 

def filter_threads(threads, filters):
    filtered_threads = filter(filters[0], threads)
    for i in range(1, len(G_FILTERS)):
        filtered_threads = filter(filters[i], filtered_threads)
    return list(filtered_threads)

def top_threads(threads):
    return sorted(threads, key=lambda topic: int(topic["replies"]),\
reverse=True)  

#assumes we have no_stop in threads
def most_frequent_words(threads):
    word_counts = {}
    for thread in threads: 
        for word in thread['no_stop'].split():
            if word in word_counts:
                word_counts[word] = word_counts[word] + int(thread['replies'])
            else:
                word_counts[word] = 1
    return sorted(word_counts.items(), key=lambda item: item[1], reverse=True)

def print_kop_tek(best_words):
    rel_max = best_words[0][1] 
    max_len = len('word')
    bars = [0]*K
    result = ""
    for i in range(0, K):
        if len(best_words[i][0]) > max_len:
            max_len = len(best_words[i][0])
        bars[i] = round(MAX_BAR_LEN*best_words[i][1]/rel_max)
    result = result + 'word'.ljust(max_len+1) + '│' + 'count' + "\n"
    result = result + '─'*(max_len+1) + '┼' + '─'*(MAX_BAR_LEN) + "\n"
    for i in range(0, K):
        result = result + (best_words[i][0].ljust(max_len+1) + '│' + '▓'*bars[i] +\
            ' ({0:d})'.format(best_words[i][1])) + "\n"
    return result

def write_kop_tek(graph_string):
    f = codecs.open('ihopenoonereadsthis', 'w', "utf-8")
    f.write(graph_string)
    f.flush()
    #please be atomic
    os.rename('ihopenoonereadsthis', 'koptek.txt')

#best code duplication
def write_top_threads(link_string):
    f = codecs.open('ihopenoonereadsthis2', 'w', "utf-8")
    f.write(link_string)
    f.flush()
    #please be atomic
    os.rename('ihopenoonereadsthis2', 'links')
   

def gen_link(thread, board):
    return "<a href={0}>link</a> {1} <br \> <br \>".format(
        "http://boards.4chan.org/{0}/thread/{1}/".format(board, thread["no"]), 
        html.unescape(re.sub("<.*?>", "", thread['com'])))
        

def main():
    g_json = grab_and_parse(G_URL)
    extracted_threads = extract_threads(g_json)
    lower_threads = lowerify_threads(extracted_threads) 
    unstopped_threads = unstopify_threads(lower_threads)
    filtered_threads = filter_threads(unstopped_threads, G_FILTERS)
    

    top = top_threads(filtered_threads)
    link_string = "" 
    for i in range(0, 5):
        link_string = link_string + gen_link(top[i], 'g')

    top_words = most_frequent_words(filtered_threads)

    write_top_threads(link_string)
    write_kop_tek(print_kop_tek(top_words))

    
    

if __name__ == '__main__':
    main()
