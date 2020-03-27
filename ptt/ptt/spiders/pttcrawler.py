# -*- coding: utf-8 -*-
import scrapy
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pprint import pprint
import time
from ptt.items import PttItem

#補充 : pycharm replace 的方法 : https://blog.csdn.net/xu380393916/article/details/81077415

class PttCrawlerSpider(scrapy.Spider):
    name = 'ptt'  # 用來執行所呼叫的名字
    start_urls = ['https://www.ptt.cc/bbs/Gossiping/M.1585020445.A.59E.html']  # 抓取連結可能多個，所以放入list,這邊放入一篇文章
    cookies = {'over18': '1'}  # 身分檢驗
    custom_settings = {'logger' : 'error'}

    def start_requests(self): #在pycharm可忽略
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, cookies=self.cookies)
            # python yield : https://blog.blackwhite.tw/2013/05/python-yield-generator.html

    def parse(self, response):

        # 假設網頁回應不是 200 OK 的話, 我們視為傳送請求失敗
        if response.status != 200:
            print('Error - {} is not available to access'.format(response.url))
            return
        # 將網頁回應的 HTML 傳入 BeautifulSoup 解析器, 方便我們根據標籤 (tag) 資訊去過濾尋找
        #soup = BeautifulSoup(response.text) 改用CSS、selectors

        # 取得文章內容主體
        #main_content = soup.find(id='main-content')
        main_content = response.css('#main-content')[0]    #改成scrapy selector 方法
        # 假如文章有屬性資料 (meta), 我們在從屬性的區塊中爬出作者 (author), 文章標題 (title), 發文日期 (date)
        #metas = main_content.select('div.article-metaline')
        metas = main_content.css('div.article-metaline')

        author = ''
        title = ''
        date = ''
        '''
        if metas:
            if metas[0].select('span.article-meta-value')[0]:
                author = metas[0].select('span.article-meta-value')[0].string
            if metas[1].select('span.article-meta-value')[0]:
                title = metas[1].select('span.article-meta-value')[0].string
            if metas[2].select('span.article-meta-value')[0]:
                date = metas[2].select('span.article-meta-value')[0].string
        '''
        if metas:  #抓取發文人的資訊，用scrapy selector 改寫
            if metas[0].css('span.article-meta-value')[0]:
                author = metas[0].css('span.article-meta-value::text')[0]
            if metas[1].css('span.article-meta-value')[0]:
                title = metas[1].css('span.article-meta-value::text')[0]
            if metas[2].css('span.article-meta-value')[0]:
                date = metas[2].css('span.article-meta-value::text')[0]#css用tag 的方式拿string
            # 從 main_content 中移除 meta 資訊（author, title, date 與其他看板資訊）
            #
            # .extract() 方法可以參考官方文件 (from BeautifulSoup)
            #  - https://www.crummy.com/software/BeautifulSoup/bs4/doc/#extract
            # 關於scrapy 如何實現BeautifulSoup中extract的方法
            '''
            @問題 : .extract()的用途為何?@ (原sample)
            for m in metas:
                m.extract() #做完了從tree上移除
            for m in main_content.select('div.article-metaline-right'):    
                m.extract()
            '''
            ''' 尋找extract的方法(版本一不可行)
            #scrapy selector 的 get可以直接對.css() selectors作用 返回一list內有多組字串
            metas.extract()
            main_content.css('div.article-metaline-right').extract() #返回list，element型態為string
            scrapy selector #https://segmentfault.com/a/1190000018559454直接調用結果 : 
            '''
            # 用Xpathselector 的 select()來做到選取以及提取片段
                #將metas 從 main_content移除
            main_content = main_content.css(':not(div.article-metaline)') #選取所有非div.article-metaline的區塊，目的希望與bs4 extract()相同移除程式片段
            main_content = main_content.css(':not(div.article-metaline-right)')

        # 取得留言區主體
        '''
        pushes = main_content.find_all('div', class_='push') #push為他人留言推文(黃字區塊)用pushes記錄下這個部分，下面會處理
        for p in pushes:
            p.extract()
        '''
        pushes = main_content.css('div.push') #使用get_all()返回是string?
        main_content = main_content.css(':not(div.push)')
        # 假如文章中有包含「※ 發信站: 批踢踢實業坊(ptt.cc), 來自: xxx.xxx.xxx.xxx」的樣式
        # 透過 regular expression 取得 IP
        # 因為字串中包含特殊符號跟中文, 這邊建議使用 unicode 的型式 u'...'
        try:
            #ip = main_content.find(text=re.compile(u'※ 發信站:'))
            ip = main_content.css(text=re.compile(u'※ 發信站:'))[0] #??
            ip = re.search('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', ip).group() #可能找不到而進入Exception
        except Exception as e:
            ip = '' #ip設空繼續執行

        # 移除文章主體中 '※ 發信站:', '◆ From:', 空行及多餘空白 (※ = u'\u203b', ◆ = u'\u25c6')
        # 保留英數字, 中文及中文標點, 網址, 部分特殊符號
        #
        # 透過 .stripped_strings 的方式可以快速移除多餘空白並取出文字, 可參考官方文件
        #  - https://www.crummy.com/software/BeautifulSoup/bs4/doc/#strings-and-stripped-strings
        filtered = []
        for v in main_content.css('::text').getall(): #去掉黃字推文，以及上方欄底區塊，對中間部分進行處理
            # 假如字串開頭不是特殊符號或是以 '--' 開頭的, 我們都保留其文字
            v.strip(' \t\n\r') #去掉text的空格，str物件中的strip
            if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--']:
                filtered.append(v)

        # 定義一些特殊符號與全形符號的過濾器
        expr = re.compile(u'[^一-龥。；，：“”（）、？《》\s\w:/-_.?~%()]')
        for i in range(len(filtered)): #把特殊符號去掉
            filtered[i] = re.sub(expr, '', filtered[i]) #re.sub替換字符 : https://blog.csdn.net/zcmlimi/article/details/47709049 、https://www.crifan.com/python_re_sub_detailed_introduction/

        # 移除空白字串, 組合過濾後的文字即為文章本文 (content) up!
        filtered = [i for i in filtered if i]
        content = ' '.join(filtered) #string.join : 用空格昨為間隔

        # 處理留言區
        # p 計算推文數量
        # b 計算噓文數量
        # n 計算箭頭數量
        p, b, n = 0, 0, 0
        messages = []
        for push in pushes:
            # 假如留言段落沒有 push-tag 就跳過
            #if not push.find('span', 'push-tag'):
            if not push.css('span.push-tag')[0]: #find()對應get()
                continue

            # 過濾額外空白與換行符號
            # push_tag 判斷是推文, 箭頭還是噓文
            # push_userid 判斷留言的人是誰
            # push_content 判斷留言內容
            # push_ipdatetime 判斷留言日期時間
            '''
            push_tag = push.find('span', 'push-tag').string.strip(' \t\n\r')
            push_userid = push.find('span', 'push-userid').string.strip(' \t\n\r')
            push_content = push.find('span', 'push-content').strings
            push_content = ' '.join(push_content)[1:].strip(' \t\n\r')
            push_ipdatetime = push.find('span', 'push-ipdatetime').string.strip(' \t\n\r')
            '''
            push_tag = push.css('span.push-tag::text')[0].get().strip(' \t\n\r')
            push_userid = push.css('span.push-userid::text')[0].get().strip(' \t\n\r')
            push_content = push.css('span.push-content::text')[0].getall()
            push_content = ' '.join(push_content)[1:].strip(' \t\n\r')
            push_ipdatetime = push.css('span.push-ipdatetime::text')[0].get().strip(' \t\n\r')
            # 整理打包留言的資訊, 並統計推噓文數量
            messages.append({
                'push_tag': push_tag,
                'push_userid': push_userid,
                'push_content': push_content,
                'push_ipdatetime': push_ipdatetime})
            if push_tag == u'推':
                p += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1

        # 統計推噓文
        # count 為推噓文相抵看這篇文章推文還是噓文比較多
        # all 為總共留言數量
        message_count = {'all': p + b + n, 'count': p - b, 'push': p, 'boo': b, 'neutral': n}

        '''
        data = {
            'url': response.url,
            'article_author': author,
            'article_title': title,
            'article_date': date,
            'article_content': content,
            'ip': ip,
            'message_count': message_count,
            'messages': messages
        }
        yield data
        '''
        # 整理文章資訊，用scrapy item 的方法
        data = PttItem()
        data['url'] = response.url
        data['article_author'] = author
        data['article_title'] = title
        data['article_date'] = date
        data['article_content'] = content
        data['ip'] = ip
        data['message_count'] = message_count
        data['messages'] = messages
        yield data  # 把Data回傳
#補充 :
#Scrapy简介和安装方法 : https://www.youtube.com/watch?v=aDwAmj3VWH4&list=PLDFBYdF-BxV3JpilGQkoMABYoD9pKlgZ_&index=1

#python 專案課程 : https://www.youtube.com/watch?v=7Gqkq4R8DPE&list=PL9OF2bYpo7BPmgkStwEPKt2KQvNQV_uzs




