import asyncio
import aiohttp
import time
from lxml import html
import re
import urllib
from urllib.parse import urlparse

class Crawler():
    def __init__(self, roots, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.roots = roots
        self.seen_urls = set()
        self.done = []
        self.q = asyncio.Queue(loop=self.loop)
        self.session = aiohttp.ClientSession(loop=self.loop)
        for root in roots:
            self.add_url(root)

        self.t0 = time.time()
        self.t1 = None

    def add_url(self, url):
        self.seen_urls.add(url)
        self.q.put_nowait(url)

    # def split_url(self, url):
    #     return urlparse(url).path.split('/')
    #
    # def url_allowed(self, url):
    #     if self.exclude and re.search(self.exclude, url):
    #         return False
    #     parts = urllib.parse.urlparse(url)
    #     if parts.scheme not in ('http', 'https'):
    #         print('skipping non-http scheme in %r', url)
    #         return False
    #     host, port = urllib.parse.splitport(parts.netloc)
    #     if not self.host_okay(host):
    #         print('skipping non-root host in %r', url)
    #         return False
    #     return True

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


    async def fetch(self, url):
        tries = 0
        while tries < 5:
            try:
                resp = await self.session.get(url, allow_redirects=False)
                break
            except aiohttp.ClientError as client_error:
                print(client_error)

            tries += 1
        else:
            print('超过尝试次数')

        try:
            links = await self.parse_links(resp)
            for link in links.difference(self.seen_urls):
                self.q.put_nowait(link)
            self.seen_urls.update(links)

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
        workers = [asyncio.Task(self.work(), loop=self.loop) for _ in range(5)]
        self.t0 = time.time()
        await self.q.join()
        self.t1 = time.time()
        for w in workers:
            w.cancel()


if __name__ == '__main__':
    roots = ['https://m.douban.com/group/146409/?start={}'.format(_) for _ in range(25,1000,25)]
    loop = asyncio.get_event_loop()
    crawler = Crawler(roots=roots, loop=loop)
    loop.run_until_complete(crawler.crawl())
