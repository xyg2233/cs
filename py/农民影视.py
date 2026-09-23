# -*- coding: utf-8 -*-
# by @嗷呜
import concurrent.futures
import json
import re
import sys
import time
from base64 import b64decode, b64encode
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        self.host = "https://vip.wwgz.cn:5200"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': self.host + '/',
            'Accept': 'text/html'
        }
        self.cateConfig = {
            "12": [{"key": "cateId", "name": "类型", "value": [{"n": "国产剧", "v": "12"}]}],
            "4": [{"key": "cateId", "name": "类型", "value": [{"n": "动漫", "v": "4"}]}],
            "1": [{"key": "cateId", "name": "类型", "value": [{"n": "电影", "v": "1"}]}],
            "2": [{"key": "cateId", "name": "类型", "value": [{"n": "电视剧", "v": "2"}]}],
            "3": [{"key": "cateId", "name": "类型", "value": [{"n": "综艺", "v": "3"}]}],
            "26": [{"key": "cateId", "name": "类型", "value": [{"n": "短剧", "v": "26"}]}]
        }
        self.filterConfig = {}

    def getName(self):
        return "农民影视"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        result = {}
        classes = [
            {'type_name': '国产剧', 'type_id': '12'},
            {'type_name': '动漫', 'type_id': '4'},
            {'type_name': '电影', 'type_id': '1'},
            {'type_name': '电视剧', 'type_id': '2'},
            {'type_name': '综艺', 'type_id': '3'},
            {'type_name': '短剧', 'type_id': '26'}
        ]
        try:
            data = self.fetch(self.host, headers=self.headers).text
            doc = pq(data)
            videos = []
            seen_ids = set()
            for item in doc('.globalPicList li:has(img)').items():
                vod_id = self.host + item('a').attr('href')
                if vod_id not in seen_ids:
                    seen_ids.add(vod_id)
                    pic_url = item('img').attr('data-echo') or item('img').attr('data-src') or item('img').attr('src')
                    if pic_url and 'pic.lzzypic.com' in pic_url:
                        pic_url = pic_url.replace('https://pic.lzzypic.com', 'https://img.lzzyimg.com')
                    videos.append({
                        'vod_id': vod_id,
                        'vod_name': item('.sTit').text(),
                        'vod_pic': pic_url,
                        'vod_remarks': item('.sBottom').text()
                    })
            result['class'] = classes
            result['filters'] = self.cateConfig
            result['list'] = videos
        except Exception as e:
            print(f"首页数据获取失败: {str(e)}")
            result['class'] = classes
            result['filters'] = self.cateConfig
            result['list'] = []
        return result

    def homeVideoContent(self):
        pass

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        try:
            if tid == "4-dm":
                url = "https://www.wwgz.cn/vod-list-id-4-pg-{}-order--by-hits-class-0-year-0-letter--area-大陆-lang-.html".format(pg)
            else:
                cateId = tid
                url = f"{self.host}/vod-list-id-{cateId}-pg-{pg}.html"
                
            data = self.fetch(url, headers=self.headers).text
            doc = pq(data)
            
            videos = []
            for item in doc('.globalPicList li').items():
                pic_url = item('img').attr('data-echo') or item('img').attr('data-src') or item('img').attr('src')
                if pic_url and 'pic.lzzypic.com' in pic_url:
                    pic_url = pic_url.replace('https://pic.lzzypic.com', 'https://img.lzzyimg.com')
                videos.append({
                    'vod_id': self.host + item('a').attr('href'),
                    'vod_name': item('.sTit').text(),
                    'vod_pic': pic_url,
                    'vod_remarks': item('.sBottom').text()
                })
            
            result['list'] = videos
            result['page'] = pg
            result['pagecount'] = 9999
            result['limit'] = 90
            result['total'] = 999999
        except Exception as e:
            print(f"分类数据获取失败: {str(e)}")
            result['list'] = []
            result['page'] = pg
            result['pagecount'] = 1
            result['limit'] = 90
            result['total'] = 0
        return result

    def detailContent(self, ids):
        result = {}
        try:
            url = ids[0]
            data = self.fetch(url, headers=self.headers).text
            doc = pq(data)
            
            play_from = []
            play_url = []

            tab_box = doc('#leftTabBox')
            if tab_box:
                # 只取线路标签：.hd 下的 ul li
                tabs = tab_box('.hd ul li')
                # 只取剧集区域：.bd 下的 .numList
                num_lists = tab_box('.bd .numList')
                
                for i in range(min(len(tabs), len(num_lists))):
                    line_name = tabs.eq(i).text().strip()
                    if not line_name:
                        continue
                    num_list = num_lists.eq(i)
                    episodes = []
                    # 保持倒序（可根据需要删除 [::-1] 改为正序）
                    for ep in reversed(list(num_list('li a').items())):
                        ep_name = ep.text().strip()
                        ep_href = ep.attr('href')
                        if not ep_href:
                            continue
                        full_url = self.host + ep_href if ep_href.startswith('/') else ep_href
                        episodes.append(f"{ep_name}${full_url}")
                    if episodes:
                        play_from.append(line_name)
                        play_url.append('#'.join(episodes))
            
            vod = {
                'vod_name': doc('h1 a').text(),
                'vod_year': doc('span:contains("年代：")').text().replace('年代：', ''),
                'vod_area': '',
                'vod_actor': doc('.sDes:contains("主演:")').text().replace('主演:', ''),
                'vod_director': '',
                'vod_content': doc('.detail-con p').text().replace('简介:', ''),
                'vod_play_from': '$$$'.join(play_from),
                'vod_play_url': '$$$'.join(play_url)
            }
            result['list'] = [vod]
        except Exception as e:
            print(f"详情数据获取失败: {str(e)}")
            result['list'] = []
        return result

    def searchContent(self, key, quick, pg="1"):
        result = {}
        try:
            url = f"{self.host}/index.php?m=vod-search"
            data = {'wd': key}
            headers = {
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.host + '/'
            }
            html = self.post(url, data=data, headers=headers).text
            doc = pq(html)
            
            videos = []
            for item in doc('#data_list li').items():
                pic_url = item('.lazyload').attr('data-src')
                if pic_url and 'pic.lzzypic.com' in pic_url:
                    pic_url = pic_url.replace('https://pic.lzzypic.com', 'https://img.lzzyimg.com')
                videos.append({
                    'vod_id': self.host + item('a').attr('href'),
                    'vod_name': item('.sTit').text(),
                    'vod_pic': pic_url,
                    'vod_remarks': item('.sDes').eq(-1).text()
                })
            
            result['list'] = videos
            result['page'] = pg
        except Exception as e:
            print(f"搜索数据获取失败: {str(e)}")
            result['list'] = []
            result['page'] = pg
        return result

    # ---------- 新 playerContent ----------
    def playerContent(self, flag, id, vipFlags):
        """
        播放处理（最终版）：
        播放页 → mac_url → 切加密串 → api.wwgz.cn:520/player/ → 抠 m3u8 → 直链返回
        全程不本地解密，绕开环境 bug
        """
        result = {}
        try:
            # 兼容旧格式（@ 分隔）
            if '@' in id:
                ids = id.split('@')
                if not ids[0]:
                    raise Exception('未找到播放地址')
                js_url = f"{self.host}/player/{ids[0]}.js"
                js_data = self.fetch(js_url, headers=self.headers).text
                jxurl = re.search(r'http.*?url=', js_data).group()
                data = self.fetch(f"{jxurl}{ids[1]}", headers=self.headers).text
                matches = re.findall(r'http.*?url=', data)
                if matches:
                    url = []
                    for i, x in enumerate(matches):
                        js = {'jx': x, 'id': ids[1]}
                        purl = f"{self.getProxyUrl()}&wdict={self.e64(json.dumps(js))}"
                        url.extend([f'线路{i + 1}', purl])
                else:
                    url = re.search(r"url='(.*?)'", data).group(1)
                if not url:
                    raise Exception('未找到播放地址')
                result['parse'] = 0
                result['url'] = url
                result['header'] = self.headers
                return result

            # ---- 新逻辑：标准播放页 ----
            # 1. 补全播放页 URL
            if not id.startswith('http'):
                play_url = self.host + ('' if id.startswith('/') else '/') + id
            else:
                play_url = id

            # 2. 请求播放页，抠 mac_url
            html = self.fetch(play_url, headers=self.headers).text
            ms = re.search(r"var\s+mac_url\s*=\s*'([^']+)'", html)
            if not ms:
                ms = re.search(r'var\s+mac_url\s*=\s*"([^"]+)"', html)
            if not ms:
                raise Exception("未找到 mac_url")
            mac_raw = ms.group(1)

            # 3. 解析 src/num
            sm = re.search(r'-src-(\d+)', play_url)
            nm = re.search(r'-num-(\d+)', play_url)
            if not sm or not nm:
                raise Exception("URL 无法解析 src/num")
            src_idx = int(sm.group(1)) - 1
            num_idx = int(nm.group(1)) - 1

            # 4. 切出当前集加密串
            line = mac_raw.split('$$$')[src_idx]
            ep = line.split('#')[num_idx]
            enc = ep.split('$', 1)[1] if '$' in ep else ep

            # 5. 请求解析接口，拿 DMPlayer 页
            api_url = f"https://api.wwgz.cn:520/player/?url={enc}"
            phtml = self.fetch(api_url, headers=self.headers).text

            # 6. 从 DMPlayer 页抠 m3u8（多兜底）
            m3u8 = None
            # 6a. "url":"...m3u8"
            m = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', phtml)
            if m:
                m3u8 = m.group(1)
            # 6b. config.url = "..."
            if not m3u8:
                m = re.search(r'config\.url\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']', phtml)
                if m:
                    m3u8 = m.group(1)
            # 6c. video src
            if not m3u8:
                m = re.search(r'<video[^>]+src\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']', phtml)
                if m:
                    m3u8 = m.group(1)

            if not m3u8:
                raise Exception("DMPlayer 页未抠到 m3u8")

            # 补全协议
            if m3u8.startswith('//'):
                m3u8 = 'https:' + m3u8
            elif m3u8.startswith('/'):
                m3u8 = 'https://vip.123pan.cn' + m3u8

            # 7. 直链返回，parse=0
            result['parse'] = 0
            result['url'] = m3u8
            result['header'] = {
                'User-Agent': self.headers['User-Agent'],
                'Referer': 'https://vip.123pan.cn/',   # 123pan 防盗链
                'Origin': 'https://vip.123pan.cn',
            }

        except Exception as e:
            print(f"播放异常: {e}")
            result['parse'] = 1
            result['url'] = id
            result['header'] = self.headers
        return result

    def localProxy(self, param):
        try:
            wdict = json.loads(self.d64(param['wdict']))
            url = f"{wdict['jx']}{wdict['id']}"
            data = self.fetch(url, headers=self.headers).text
            doc = pq(data)
            html = doc('script').eq(-1).text()
            url = re.search(r'src="(.*?)"', html).group(1)
            return [302, 'text/html', None, {'Location': url}]
        except Exception as e:
            print(f"代理处理失败: {str(e)}")
            return [500, 'text/plain', str(e).encode('utf-8')]

    def liveContent(self, url):
        pass

    def e64(self, text):
        try:
            text_bytes = text.encode('utf-8')
            encoded_bytes = b64encode(text_bytes)
            return encoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Base64编码错误: {str(e)}")
            return ""

    def d64(self, encoded_text):
        try:
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Base64解码错误: {str(e)}")
            return ""
