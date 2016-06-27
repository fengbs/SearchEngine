#import searchengine
#pagelist = ['http://hebei.iabe.cn/public/Test_List.aspx?TiMuXiaoLeiLiuShuiHao=9']
#crawler = searchengine.crawler('')
#crawler.crawl(pagelist)

#database
#import searchengine
#crawler =searchengine.crawler('searchindex.db')
#crawler.createindextables()

#建立索引
import searchengine
crawler = searchengine.crawler('searchindex.db')
pages = ['http://lib.iscas.ac.cn:8080/web/guest/dianziziyuanyilanbiao']
crawler.crawl(pages)
