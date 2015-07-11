import http.client
import html
import json
import re
from nltk.corpus import stopwords
import os
import codecs

HOST_URL = 'a.4cdn.org'
G_URL = '/g/catalog.json'

def G_DESKTOP_FILTER(thread):
    return 'desktop' in thread['com_lower'] and 'thread' in thread['com_lower']

def G_BATTLESTATION_FILTER(thread):
    return 'battlestation' in thread['com_lower'] and 'thread' in thread['com_lower']

G_FILTERS = \
[lambda thread: 
 not(G_BATTLESTATION_FILTER(thread)),
 lambda thread:
 not(G_DESKTOP_FILTER(thread)),
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


ADDITIONAL_STOP_WORDS = {"like", "one", "/g/", "may", "-", "thread","someone",
"it's", "i've", "see", "get", "first", "new", "would", "&", "good", "even",
"right", "way", "thoughts", "guys", "based", "maybe", "i'm", "let's", "could",
"ask", "related", "getting", "much", ">", "done", "got", "various", "looks",
"back", "best", "user", "might", "link", "use", "threads", "you're"}

K = 50
MAX_BAR_LEN = 20
MAX_IMAGES = 5

def grab_and_parse(URL):
    m_http = http.client.HTTPConnection(HOST_URL) 
    m_http.request('GET', URL)
    m_response = m_http.getresponse() 
    m_raw_json = m_response.read()
    return json.loads(m_raw_json.decode())

def grab_and_parse_thread(thread, board):
    thread_url = "/{0}/thread/{1}.json".format(board, thread["no"])
    return grab_and_parse(thread_url)

def extract_threads(catalog_json):
    extracted_threads = []
    for page in catalog_json:
        for thread in page["threads"]:
            extracted_threads.append(thread)
    return extracted_threads

def try_get_com(thread):
    try:
        com = ""
        sub = ""
        com = thread['com']
        sub = thread['sub']
        return sub + " " + com
    except KeyError:
        return sub + " " + com

def add_lowered(thread):
    thread['com'] = try_get_com(thread)
    thread['com_lower'] = html.unescape(re.sub("<.*?>", "",\
    try_get_com(thread).lower()))
    thread['com_lower'] = re.sub("[\.!?,:]", "", thread['com_lower'])
    return thread

def remove_stops(thread):
    thread['no_stop'] = ' '.join([word for word in thread['com_lower'].split()\
    if word not in (stopwords.words('english')) and word not in\
    ADDITIONAL_STOP_WORDS and len(word) > 2])
    return thread

def lowerify_threads(threads):
    lower_threads = map(lambda thread: add_lowered(thread), threads)
    return lower_threads

#assumes we have the lowercase comments
def unstopify_threads(threads):
    unstopped_threads = map(lambda thread: remove_stops(thread), threads)
    return list(unstopped_threads)

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

def write_kop_tek(write_string, filename):
    f = codecs.open('ihopenoonereadsthis', 'w', "utf-8-sig")
    #f.write(u'\uffef')
    f.write(write_string)
    f.flush()
    #please be atomic
    os.rename('ihopenoonereadsthis', filename)

def gen_link(thread, board):
    return "<a href={0}>link</a> {1} <br \> <br \>".format(
        "http://boards.4chan.org/{0}/thread/{1}/".format(board, thread["no"]), 
        html.unescape(re.sub("<.*?>", "", thread['com'])))

def get_battlestation_thread(threads):
    max_replies = 0
    cur_thread = None
    for thread in threads:
        if G_BATTLESTATION_FILTER(thread):
            if int(thread["replies"]) > max_replies:
                cur_thread = thread
    return cur_thread

def get_desktop_thread(threads):
    max_replies = 0
    cur_thread = None
    for thread in threads:
        if G_DESKTOP_FILTER(thread):
            if int(thread["replies"]) > max_replies:
                cur_thread = thread
    return cur_thread

def get_posts_reply_counts(thread, board):
    thread_posts = grab_and_parse_thread(thread, board)["posts"]
    replies = {}
    for post in thread_posts:
        if "com" in post.keys():
            beg = 0
            while beg < len(post["com"]):
                pos = post["com"].find('#p', beg)
                if pos > 0: 
                    #TODO: replace this constant later
                    raw_reply_str = post["com"][pos+2:pos+25]
                    reply_str = ""
                    for c in raw_reply_str:
                        if c.isdigit():
                            reply_str = reply_str + c
                        else:
                            break
                    if reply_str in replies:
                        replies[int(reply_str)] = replies[reply_str] + 1
                    else:
                        replies[int(reply_str)] = 1
                    beg = pos + 1
                else:
                    beg = len(post["com"])
    for post in thread_posts:
        if post["no"] in replies.keys():
            post["replies"] = replies[post["no"]]
        else:
            post["replies"] = 0
    return thread_posts


def print_top_special_thread(thread_type, threads, board):
    if thread_type == 'Battlestation': 
        special_thread = get_battlestation_thread(threads)
    else:
        special_thread = get_desktop_thread(threads)
    return_string = thread_type + " Thread Not Found"
    if special_thread is None:
        return return_string
    posts = get_posts_reply_counts(special_thread, board)
    return_string = gen_link(special_thread, board)
    i = 0    
    for post in sorted(posts, key=lambda post: post["replies"], reverse=True):
        if "tim" in post:
            return_string = return_string + '<a \
href="http://i.4cdn.org/{0}/{1}{2}"><img src="http://i.4cdn.org/{0}/{1}s.jpg" \
height="100"><br \><br \><br \>'.format(board,post["tim"],post["ext"])
            i = i+1
        if i >= MAX_IMAGES:
            break
    print(return_string)
    return(return_string)

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

    write_kop_tek(link_string, "links")
    write_kop_tek(print_kop_tek(top_words), "koptek.txt")

    battlestation_string = print_top_special_thread("Battlestation", unstopped_threads, 'g') 
    desktop_string = print_top_special_thread("Desktop", unstopped_threads, 'g') 

    write_kop_tek(battlestation_string, "battlestation")
    write_kop_tek(desktop_string, "desktop")

if __name__ == '__main__':
    main()
