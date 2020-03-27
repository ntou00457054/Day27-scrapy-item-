# Day27-scrapy-item-


主題 :
1. scrapy 元素定位方法 : 將上份作業的BeautifulSoup的部分更改為scrapy selector 的特殊方法，效率(執行速度)較bs4高，但使用時需要更注重變數的type(如get()、strings、stripped string等)

2. scrapy item儲存方式 : 詳見item.py與pttcrawler程式下半部分

3.補充 : scrapy 實現 bs4中extract()的方法主要有兩種 : (1)使用HtmlXpathSelector ->測試後發現scrapy.select 中並沒有這個東東(網路上的資料寫法是 from scrapy.select import HtmlXpathSelector ，發文時間大約在2013~2015左右)，推測可能是後面版本(那時還是scrapy 1.x.yy版本)被改掉了(2.)使用selector 中的 :not()方法排除特定class或id的tag，extract() 就是把特定區塊存入一個Selector，原先區塊被剔除後仍放回原先的Selector，如 main_content = main_content.css(:not(div.article-meta))

4. 補充 Scrapy 的 Selector 雖說執行快(可視作操作lxml的使用介面)，但寫程式對我來說較BeautifulSoup 難

5.把資料依照item.py定義的class進行儲存，為了避免資料被隨意更動，雖說也可以將資料存入資料庫，但調用上仍沒有比在專案內來的方便
