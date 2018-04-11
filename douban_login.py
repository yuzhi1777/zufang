import asyncio
import aiohttp
from config import USERNAME, PASSWORD
from model import Topic

login_url = 'https://frodo.douban.com/service/auth2/token'
group_url = 'https://frodo.douban.com/api/v2/group/146409/topics'

headers = {
'User-Agent': 'api-client/0.1.3 com.douban.frodo/5.20.0 iOS/11.2.5 iPhone8,4 network/wifi',
}

Topic.init()

async def login():
    #TODO 从配置文件读账号密码
    payload = {
        'client_id': '0ab215a8b1977939201640fa14c66bab',
        'grant_type': 'password',
        'client_secret': '22b2cf86ccc81009',
        'username': USERNAME,
        'password': PASSWORD}

    async with aiohttp.ClientSession() as session:
        #拿调用api的token
        async with session.post(url=login_url, headers=headers, data=payload) as r:
            json_body = await r.json()
            headers['Authorization'] = 'Bearer ' + json_body['access_token']
        #调group最新的tpoics
        async with session.get(url=group_url, headers=headers, data={'count':100}) as r:
            json_body = await r.json()
            for topic in json_body['topics']:
                print(topic)
                t = Topic()
                t.update_time = topic['update_time']
                t.title = topic['title']
                t.url = topic['url']
                t.create_time = topic['create_time']
                t.comments_count = topic['comments_count']
                t.meta.id = topic['id']
                t.save()
                print(topic['url'])

# TODO
# 1.遍历近一个个月的数据10000条左右
# 2.topics整合进elasticsearch进行搜索


loop = asyncio.get_event_loop()
loop.run_until_complete(login())



# payload = {
#     '_sig':'kOm9I6Q+a2OFj8mq/c+3o+1iAO4=',
# '_ts':'1519445630',
# '_v':'46465',
# 'alt':'json',
# 'apikey':'0ab215a8b1977939201640fa14c66bab',
# 'client_id':'0ab215a8b1977939201640fa14c66bab',
# 'client_secret':'22b2cf86ccc81009',
# 'device_id':'b8050bf7fb5f86669265a82dfc4c1b4be9c2bd24',
# 'douban_udid':'5182201a3bb2ed705598c4bb7d9d340467dccd94',
# 'grant_type':'password',
# 'password':'*********',
# 'redirect_uri':'http://frodo.douban.com',
# 'udid':'b8050bf7fb5f86669265a82dfc4c1b4be9c2bd24',
# 'username':'**********@gmail.com'}



