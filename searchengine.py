import urllib.request
from bs4 import *
from urllib.parse import urljoin
import sqlite3 
#忽略单词列表
ignorewords = set(['the', 'of', 'to' , 'and' , 'a', 'in' , 'is' , 'it'])
class crawler:
    #初始化类 传入数据库名称
    def __init__(self,dbname):
        self.con = sqlite3.connect(dbname)
    def __def__(self):
        self.con.close()
    def dbcommit(self):
        self.con.commit()
    #获取条目id 如果条目不存在，加入数据库
    def getentryid(self,table,field,value,createnew = True):
        return None
    #为每个网址建立索引
    def addtoindex(self,url,soup):
        print('Indexing %s' % url)
    #在html中提取文字
    def gettextonly(self,soup):
        v=soup.string
        if v == None:
            c = soup.contents
            resulttext = ''
            for t in c:
                subtext = self.gettextonly(t)
                resulttext += subtext+'\n'
            return resulttext
        else:
            return v.strip()
    #分割词汇
    def separatewords(self,text):
        splitter = re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s!='']
    #如果url已经建立索引，那么返回True
    def isindexed(self,url):
        return False
    #添加一个关联两个网页的连接
    def addlinkref(self ,urlForm,urlTo,linkText):
        pass
    #从某网页广搜并建立索引
    def crawl(self , pages , depth = 2):
        for i in range(depth):
            newpages = set()
            for page in pages:
                try:
                    c = urllib.request.urlopen(page)
                except:
                    print('could not open page %s' % page)
                    continue
                soup = BeautifulSoup(c.read(), "html.parser")
                self.addtoindex(page,soup)
                
                links = soup('a')
                for link in links:
                    if('href' in dict(link.attrs)):
                        url = urljoin(page,link['href'])
                        if url.find("'") != -1:continue
                        url = url.split('#')[0] #去掉位置部分
                        if url[0:4] == 'http' and not self.isindexed(url):
                            newpages.add(url)
                        linkText = self.gettextonly(link)
                        self.addlinkref(page,url,linkText)
                self.dbcommit()
            pages = newpages
        
            
    #创建数据库表
    def createindextables(self):
        self.con.execute('create table urllist(url)')
        self.con.execute('create table wordlist(word)')
        self.con.execute('create table wordlocation(urlid,wordid,location)')
        self.con.execute('create table link(fromid integer,toid,integer)')
        self.con.execute('create table linkwords(wordid , linkid)')
        self.con.execute('create index wordidx on wordlist(word)')
        self.con.execute('create index urlidx on urllist(url)')
        self.con.execute('create index wordurlidx on wordlocation(wordid)')
        self.con.execute('create index urltoidx on link(toid)')
        self.con.execute('create index urlfromidx on link(fromid)')
        self.dbcommit()
        
    
    
