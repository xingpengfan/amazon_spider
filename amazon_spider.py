#-*- coding: utf-8 -*-
'''Amazon_spider'''

import re
import csv
import time
import urllib3
from bs4 import BeautifulSoup

class AmazonURL(object):
    def __init__(self):
        user_agent = '''Mozilla/5.0 (Windows NT 6.1; WOW64)
                        AppleWebKit/535.19 (KHTML, like Gecko)
                        Chrome/18.0.1025.142 Safari/535.19'''
        self.headers = {'User-Agent': user_agent}
        self.http_pool = urllib3.connection_from_url("http://www.amazon.cn/",
                                                     timeout=15, maxsize=5,
                                                     headers=self.headers)

    def urlopen(self, url):
        res = self.http_pool.urlopen('GET', url, headers=self.headers)
        return res.data

def crawl_product_review():
    client = AmazonURL()
    base_url = "http://www.amazon.cn/product-reviews/{product_id}/ref=cm_cr_pr_show_all?ie=UTF8&showViewpoints=1&sortBy=recent&pageNumber={page}"
    f = open("product_id.txt")
    print 'Amazon spider is starting...'
    result = {}
    for line in f:
        # 找max_page_num
        product_id = line.strip()
        resp = client.urlopen(base_url.format(product_id=product_id, page=1))
        product_soup = BeautifulSoup(resp)
        try:
            pagination = product_soup.find('ul', {"class": "a-pagination"})
            split_pagination = re.compile('>(.*?)<')
            find_max = split_pagination.findall(str(pagination))
            while '' in find_max:
                find_max.remove('')
            for num in find_max:
                if num == '\xe4\xb8\x8b\xe4\xb8\x80\xe9\xa1\xb5':
                    max_num = int(find_max[find_max.index(num)-1].replace(',',''))
            min_num = max_num - 30 # 爬31页，每页10条
            if min_num < 1:
                min_num = 1
        except Exception,e:
            max_num = 1
            min_num = 1
            print e

        # 爬评分
        scores = []
        print 'crawling product %s' % product_id
        print 'max_num is %d, min_num is %d' % (int(max_num), int(min_num))
        for page_num in range(int(min_num), int(max_num)+1)[::-1]:
            try:
                tmp = []
                tmp = crawl_grades(product_id, page_num)
                if tmp == []:
                    time.sleep(1)
                    tmp = crawl_grades(product_id, page_num)
                if tmp == []:
                    time.sleep(1)
                    tmp = crawl_grades(product_id, page_num)
                print tmp
                scores.extend(tmp)
            except Exception,e:
                h = open("log.txt", "a")
                h.write(str(product_id) + ' ' + str(page_num) + ' ' + str(e) + '\n')
                h.close()
        result[product_id] = scores
    f.close()

    # 写数据
    with open('result.csv', 'wb') as g:
        g.write('\xEF\xBB\xBF')
        writer = csv.writer(g)
        for item in result:
            line = []
            line.append(item)
            line.extend(result[item])
            writer.writerow(line)
    g.close()
    print 'ending...'

def crawl_grades(product_id, page_num):
    '''爬每页评分'''
    client = AmazonURL()
    print 'crawling page %d' % int(page_num)
    grades = []
    review_base_url = "http://www.amazon.cn/product-reviews/{product_id}/ref=cm_cr_pr_btm_link_{page1}?ie=UTF8&showViewpoints=1&sortBy=recent&pageNumber={page2}"
    review_resp = client.urlopen(review_base_url.format(product_id=product_id, page1=page_num, page2=page_num))
    review_soup = BeautifulSoup(review_resp)
    reviews = review_soup.findAll("div", {"class": "a-section review"})
    for each_review in reviews:
        review_score = re.search(r'alt">(.*?) 颗', str(each_review)).group(1)
        grades.append(review_score)
    return grades[::-1]
    
if __name__ == '__main__':
    crawl_product_review()
