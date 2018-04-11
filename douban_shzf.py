import asyncio
import aiohttp
import time
import re
import urllib
from urllib.parse import urlparse
from config import USERNAME, PASSWORD
from model import Topic

class Crawler():
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.root = 'https://frodo.douban.com/api/v2/group/146409/topics?count=100&start={offset}'
        self.seen_urls = set()
        self.done = []
        self.q = asyncio.Queue(loop=self.loop)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.headers = {'User-Agent': 'api-client/0.1.3 com.douban.frodo/5.20.0 iOS/11.2.5 iPhone8,4 network/wifi'}

        self.t0 = time.time()
        self.t1 = None
        self.count = 0

        self.topic = Topic()

    async def token(self):
        login_url = 'https://frodo.douban.com/service/auth2/token'
        payload = {
            'client_id': '0ab215a8b1977939201640fa14c66bab',
            'grant_type': 'password',
            'client_secret': '22b2cf86ccc81009',
            'username': USERNAME,
            'password': PASSWORD}
        async with self.session.post(url=login_url, headers=self.headers, data=payload) as r:
            json_body = await r.json()
            self.headers['Authorization'] = 'Bearer ' + json_body['access_token']

    def add_url(self, url):
        self.seen_urls.add(url)
        self.q.put_nowait(url)

    async def parse_links(self, resp):
        links = set()

        if resp.status == 200:
            print(resp.content_type)
            if resp.content_type in ('text/html', 'application/xml'):
                text = await resp.text()

                urls = set(re.findall(r'''(?i)href=["']([^\s"'<>]+)''', text))

                for url in urls:
                    # 标准化url
                    normalized = urllib.parse.urljoin(str(resp.url), url)
                    defragmented, frag = urllib.parse.urldefrag(normalized)
                    if 'topic' in urlparse(defragmented).path.split('/'):
                        links.add(defragmented)
                        print(defragmented)
        return links

    # TODO 解析页面内容
    async def parse_josn(self, resp):
        topics = await resp.json()
        print(topics['count'])
        print(topics['start'])
        for topic in topics['topics']:
            self.topic.update_time = topic['update_time']
            self.topic.title = topic['title']
            self.topic.url = topic['url']
            self.topic.create_time = topic['create_time']
            self.topic.comments_count = topic['comments_count']
            self.topic.meta.id = topic['id']
            self.topic.save()

    async def fetch(self, url):
        tries = 0
        while tries < 5:
            try:
                resp = await self.session.get(url=url, headers=self.headers, allow_redirects=False)
                break
            except aiohttp.ClientError as client_error:
                print(client_error)

            tries += 1
        else:
            print('超过尝试次数')

        try:
            await self.parse_josn(resp)
            # links = await self.parse_json(resp)
            # for link in links.difference(self.seen_urls):
            #     self.q.put_nowait(link)
            # self.seen_urls.update(links)

        finally:
            await resp.release()

    async def work(self):
        try:
            while True:
                url = await self.q.get()
                assert url in self.seen_urls
                await self.fetch(url)
                self.q.task_done()
        except asyncio.CancelledError:
            pass

    async def crawl(self):
        await self.token()
        for offset in range(10):
            self.add_url(self.root.format(offset=offset*100))
        workers = [asyncio.Task(self.work(), loop=self.loop) for _ in range(5)]
        self.t0 = time.time()
        await self.q.join()
        self.t1 = time.time()
        for w in workers:
            w.cancel()

def mian():
    loop = asyncio.get_event_loop()
    crawler = Crawler()
    loop.run_until_complete(crawler.crawl())

if __name__ == '__main__':
    mian()

# url = 'frodo.douban.com/api/v2/group/146409/topics?count=100&start=0&apikey=0ab215a8b1977939201640fa14c66bab'