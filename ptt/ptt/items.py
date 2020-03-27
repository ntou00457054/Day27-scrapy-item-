# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PttItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    #將前一份作業pttcrawler 中的 data(一個dict)轉變成物件的儲存型態，因為dict可以被隨意添加修改，可能會修改到原本的值
    #另一種做法是將資料丟入資料庫Mongode
    url = scrapy.Field()  #scrapy.Field
    article_id = scrapy.Field()
    article_author = scrapy.Field()
    article_title = scrapy.Field()
    article_date = scrapy.Field()
    article_content = scrapy.Field()
    ip = scrapy.Field()
    message_count = scrapy.Field()
    messages = scrapy.Field()
