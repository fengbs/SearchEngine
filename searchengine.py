import urllib.request
from bs4 import *
from urllib.parse import urljoin
import sqlite3
import re
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
        cur = self.con.execute("select rowid from %s where %s = '%s'"% (table ,field , value))
        res = cur.fetchone()
        if res == None:
            cur = self.con.execute("insert into %s (%s) values ('%s')" % (table ,field ,value))
            return cur.lastrowid;
        else:
            return res[0]
    #判断是否为空
    def isNULL(self,p):
        if p==None:
            return "None"
        return p;
                    
    #为每个网址建立索引
    def addtoindex(self,url,soup):
        if self.isindexed(url):
            return
        print('Indexing' + url)

        #获取每个单词
        text = self.gettextonly(soup)
        words = self.separatewords(text)

        #得到URL的ID
        urlid = self.getentryid('urllist','url',url)

        #将每个单词与该url关联
        for i in range(len(words)):
            word = words[i]
            if word in ignorewords:continue
            wordid = self.getentryid('wordlist','word',word)
            print(str(self.isNULL(urlid))+" "+str(self.isNULL(wordid))+" "+str(self.isNULL(i))+" "+str(self.isNULL(word)))
            self.con.execute("insert into wordlocation(urlid,wordid,location) values (%d,%d,%d)"% (urlid,wordid,i))
            
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
        u = self.con.execute("select rowid from urllist where url = '%s'" %url).fetchone()
        if u!=None:
            v = self.con.execute('select * from wordlocation where urlid = %d' % u[0]).fetchone()
            if v!=None:return True
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
                        print('%s' % linkText)
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
    def testforTextonly(self,soup):
        str = self.gettextonly(soup)
        print('%s' % str)
class searcher:
    def __init__(self,dbname):
        self.con = sqlite3.connect(dbname)
    def __del__(self):
        self.con.close()
    def getmatchrows(self,q):
        #构造查询的字符串
        fieldlist = 'w0.urlid'
        tablelist = ''
        clauselist = ''
        wordids = []

        #根据空格拆分单词
        words = q.split(' ')
        tablenumber = 0

        for word in words:
            #获取单词id
            wordrow = self.con.execute(
                "select rowid from wordlist where word = '%s'" % word).fetchone()
            if wordrow != None:
                wordid = wordrow[0]
                wordids.append(wordid)
                if tablenumber > 0:
                    tablelist += ','
                    clauselist +=' and '
                    clauselist+='w%d.urlid = w%d.urlid and ' %  (tablenumber -1 ,tablenumber)
                fieldlist += ',w%d.location' % tablenumber
                tablelist += 'wordlocation w%d' % tablenumber
                clauselist += 'w%d.wordid = %d' % (tablenumber,wordid)
                tablenumber+=1
            # 根据各个组分，建立查询
            fullquery = 'select %s from %s where %s' % (fieldlist,tablelist,clauselist)
            print('sql:%s'%fullquery)
            cur = self.con.execute(fullquery)
            rows = [row for row in cur]

            return rows , wordids
    def getscoredlist(self,rows,wordids):
        totalscores = dict([(row[0],0) for row in rows])
        #评价函数
        #weights = [(1.0,self.locationscore( rows ))]
        weights = [(1.0,self.locationscore( rows )),(1.0,self.frequencyscore(rows)),(1.0,self.pagerankscore(rows))]
        for (weight,scores) in weights:
            for url in totalscores:
                totalscores[url] += weight*scores[url]

        return totalscores
    def geturlname(self,id):
        return self.con.execute(
            "select url from urllist where rowid = %d" % id).fetchone()[0]
    def query(self , q):
        rows,wordids= self.getmatchrows(q)
        scores =self.getscoredlist(rows,wordids)
        rankedscores = sorted([(score,url) for (url,score) in scores.items()],reverse = 1)
        for(score,urlid) in rankedscores[0:10]:
            print('%f\t%s' % (score,self.geturlname(urlid)))
    def normalizescores(self,scores,smallIsBetter = 0):
        vsmall = 0.00001#避免被0整除
        if smallIsBetter:
            minscore = min(scores.values())
            return dict([(u,float(minscore)/max(vsmall,l)) for (u,l) in scores.items()])
        else:
            maxscore = max(scores.values())
            if maxscore == 0 : maxscore = vsmall
            return dict([(u,float(c)/maxscore) for (u,c) in scores.items()]) 
    def frequencyscore(self,rows):
        counts = dict ( [ (row[0],0) for row in rows])
        for row in rows: counts [ row[0] ] += 1
        return self.normalizescores(counts)
    def locationscore (self,rows):
        locations = dict ( [ (row[0], 1000000 ) for row in rows ])
        for row in rows:
            loc = sum(row[1:])
            if loc < locations[row[0]]: locations[row[0]] = loc
        return self.normalizescores ( locations,smallIsBetter = 1)
    def distancescore ( self,rows ):
        # 如果仅有一个单词，则得分都一样
        if  len(rows[0]) <= 2 :	return dict ([(row[0] ,1.0 ) for row in rows])
        # 初始化字典，并填写一个很大的数
        mindistance = dict ( [ (row [0],1000000) for row in rows])
        for row in rows:
            dist = sum ( [abs(rows[i] - row[i-1] ) for i in range ( 2 , len(row))])
            if dist < mindistance[row[0]]:mindistance[row[0]] = dist
        return self.normalizescores ( mindistance,smallIsBetter = 1 )
    def inboundlinkscore ( self , rows )
        uniqueurls = set ( [row[0] for row in rows] )
        inboundcount = dict ( [ ( u , self,con.execute( \
        'select count(*) from link where toid = %d' % u ).fetchone()[0] ) \
        for u in uniqueurls ])
        return self.normalizescores (inboundcount)
    def calculatepagerank ( self,iterations = 20 )
        # 清除当前的PageRank表
        self.con.execute ('drop table if exists pagerank');
        self.con.execute ('create table pagerank ( urlid primary key,score)')
        
        #初始化每个URL,令其Pagerank值为1
        self.con.execute ('insert into pagerank select rowid , 1.0 from urllist')
        self.dbcommit();
        
        for i in range (iterations):
            print('iterator %d' % (i))
            for ( urlid,) in self.con.execute( 'select rowid from urllist'):
                pr = 0.15
            
            #循环遍历指向该网页的其他网页
            for ( linker,) in self.con.execute ( 
            'select distinct fromid from link where toid = %d' % urlid):
                #得到链接源对应网页的pagerank值
                linkingpr = self.con.execute(
                'select score from pagerank where urlid = %d' % linker).fetchone()[0]
                #根据链接源求得总的连接数
                linkingcount = self.con.execute (
                'select count(*) from link where fromid = %d' % linker).fetchone()[0]
                pr += 0.85 * (linkingpr/linkingcount)
            self.con.execute ( 
            'update pagerank set score = %f where urlid=%d' % (pr,urlid)
        self.dbcommit() 
    def pagerankscore (self,rows):
        pageranks = dict([row[0] ,self.con.execute('select score from pagerank where urlid = %d ' % row[0]).fetchone()[0]) for row in rows])
        maxrank = max (pageranks.values())
        normalizedscores = dict ([(u,float(l)/maxrank) for (u,l) in pageranks.items()] )
        return normalizedscores 
    def linktextscore ( self, rows , wordids):
        linkscores = dict([row[0],0) for row in rows )
        for wordid in wordids:
            cur = self.con.execute('select link.fromid,link.toid from linkwords,link where wordid = %d and linkid = link.rowid' %wordid)
            for ( fromid,toid ) in cur:
                if toid in linkscores:
                    pr = self.con.execute('select score from pagerank where urlid = %d'% fromid).fetchone()[0]
                    linkscores[toid] += pr
        maxscore = max(linkscores.values())
        normalizedscores = dict([(u,float(1)/maxscore) for (u,l) in linkscores.items()
        return normalizedscores 
