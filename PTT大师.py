# -*- coding: utf-8 -*-
# PTT 视频 最终JS规则版（多线路直接提取）
import re
import sys
import json
from urllib.parse import quote
from base64 import b64decode, b64encode
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""):
        self.host = "https://ptt.red"
        # 使用移动端UA，与JS规则一致
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
            'Referer': self.host + '/zh-cn',
            'Accept': 'text/html'
        }

    def getName(self):
        return "PTT视频"

    def fullPic(self, pic):
        if pic and pic.startswith('/'):
            return self.host + pic
        return pic

    def stripTags(self, html):
        return re.sub(r'<[^>]+>', '', html).strip() if html else ''

    # ---------- 首页 ----------
    def homeContent(self, filter):
        result = {}
        classes = [
            {'type_name': '电视剧', 'type_id': '3'},
            {'type_name': '电影', 'type_id': '1'},
            {'type_name': '动漫', 'type_id': '4'},
            {'type_name': '综艺', 'type_id': '2'},
            {'type_name': '短剧', 'type_id': '66'},
            {'type_name': '体育', 'type_id': '53'}
        ]
        try:
            data = self.fetch(self.host + "/zh-cn", headers=self.headers).text
            doc = pq(data)
            videos = []
            for item in doc('#videos .item').items():
                a = item('.lines a.visited') or item('a.visited').eq(0)
                href = a.attr('href')
                if not href: continue
                vod_id = self.host + href if href.startswith('/') else href
                img = item('img.lazyimage')
                pic = self.fullPic(img.attr('src') or img.attr('data-src') or '')
                name = self.stripTags(a.html() or '')
                year_badge = item('.imagelabel-bottom-left .badge').text()
                count_badge = item('.imagelabel-bottom-right .badge').text()
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': name,
                    'vod_pic': pic,
                    'vod_remarks': f"{year_badge} {count_badge}".strip()
                })
            result['class'] = classes
            result['list'] = videos
        except Exception as e:
            print(f"首页错误: {e}")
            result['class'] = classes
            result['list'] = []
        return result

    # ---------- 分类 ----------
    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        try:
            url = f"{self.host}/zh-cn/p/{tid}?page={pg}"
            data = self.fetch(url, headers=self.headers).text
            doc = pq(data)
            videos = []
            for item in doc('#videos .item').items():
                a = item('.lines a.visited') or item('a.visited').eq(0)
                href = a.attr('href')
                if not href: continue
                vod_id = self.host + href if href.startswith('/') else href
                img = item('img.lazyimage')
                pic = self.fullPic(img.attr('src') or img.attr('data-src') or '')
                name = self.stripTags(a.html() or '')
                year_badge = item('.imagelabel-bottom-left .badge').text()
                count_badge = item('.imagelabel-bottom-right .badge').text()
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': name,
                    'vod_pic': pic,
                    'vod_remarks': f"{year_badge} {count_badge}".strip()
                })
            result['list'] = videos
            result['page'] = pg
            result['pagecount'] = 9999
            result['limit'] = 90
            result['total'] = 999999
        except Exception as e:
            print(f"分类错误: {e}")
            result['list'] = []
        return result

    # ---------- 详情（完全模仿JS规则） ----------
    def detailContent(self, ids):
        result = {}
        try:
            detail_url = ids[0]
            html = self.fetch(detail_url, headers=self.headers).text
            
            # 1. 提取基本信息
            try:
                json_str = html.split('node:')[1].split('},')[0] + '}'
                json_data = json.loads(json_str)
            except:
                json_data = {}
            
            vod_name = json_data.get('title', '')
            vod_pic = self.fullPic(json_data.get('thumbnail', ''))
            year = str(json_data.get('year', ''))
            area = json_data.get('_area', '')
            actors = json_data.get('actors', '')
            director = json_data.get('director', '')
            desc = json_data.get('description', '')
            remarks = json_data.get('note', '')

            # 2. 提取线路和剧集
            doc = pq(html)
            # 线路标签
            v_tabs = doc('.nav-tabs li')
            play_from = []
            play_url = []
            
            if v_tabs:
                lines = []
                for tab in v_tabs.items():
                    a = tab('a')
                    line_name = a.attr('title') or a.text().strip()
                    line_href = a.attr('href')
                    if line_name and line_href:
                        full_href = self.host + line_href if line_href.startswith('/') else line_href
                        lines.append((line_name, full_href))
                # 检查是否有剧集列表
                list2 = doc('.mb-2.fullwidth a')
                if list2:
                    # 需要请求所有线路获取剧集
                    for line_name, line_url in lines:
                        try:
                            line_html = self.fetch(line_url, headers=self.headers).text
                            line_doc = pq(line_html)
                            eps = []
                            for a in line_doc('.mb-2.fullwidth a').items():
                                ep_name = a.text().strip()
                                ep_href = a.attr('href')
                                if ep_href:
                                    full = self.host + ep_href if ep_href.startswith('/') else ep_href
                                    eps.append(f"{ep_name}${full}")
                            if eps:
                                play_from.append(line_name)
                                play_url.append('#'.join(eps))
                        except Exception as e:
                            print(f"获取线路 {line_name} 失败: {e}")
                else:
                    # 无.mb-2.fullwidth，使用 #w1 a 作为默认剧集
                    list1 = doc('#w1 a')
                    eps = []
                    for a in list1.items():
                        ep_name = a.text().strip()
                        ep_href = a.attr('href')
                        if ep_href:
                            full = self.host + ep_href if ep_href.startswith('/') else ep_href
                            eps.append(f"{ep_name}${full}")
                    if eps:
                        play_from.append('默认线路')
                        play_url.append('#'.join(eps))
            
            # 回退：若没有线路，尝试从 .seqs 提取
            if not play_from:
                doc = pq(html)
                eps = []
                for a in doc('.seqs a.seq').items():
                    ep_name = a.text().strip()
                    ep_href = a.attr('href')
                    if ep_href:
                        full = self.host + ep_href if ep_href.startswith('/') else ep_href
                        eps.append(f"{ep_name}${full}")
                if eps:
                    play_from.append('默认线路')
                    play_url.append('#'.join(eps))

            vod = {
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_year': year,
                'vod_area': area,
                'vod_actor': actors,
                'vod_director': director,
                'vod_content': desc,
                'vod_remarks': remarks,
                'vod_play_from': '$$$'.join(play_from),
                'vod_play_url': '$$$'.join(play_url)
            }
            result['list'] = [vod]
        except Exception as e:
            print(f"详情错误: {e}")
            result['list'] = []
        return result

    # ---------- 搜索 ----------
    def searchContent(self, key, quick, pg="1"):
        result = {}
        try:
            url = f"{self.host}/zh-cn/q/{quote(key)}?page={pg}"
            data = self.fetch(url, headers=self.headers).text
            doc = pq(data)
            videos = []
            for item in doc('#videos .item').items():
                a = item('.lines a.visited') or item('a.visited').eq(0)
                href = a.attr('href')
                if not href: continue
                vod_id = self.host + href if href.startswith('/') else href
                img = item('img.lazyimage')
                pic = self.fullPic(img.attr('src') or img.attr('data-src') or '')
                name = self.stripTags(a.html() or '')
                year_badge = item('.imagelabel-bottom-left .badge').text()
                count_badge = item('.imagelabel-bottom-right .badge').text()
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': name,
                    'vod_pic': pic,
                    'vod_remarks': f"{year_badge} {count_badge}".strip()
                })
            result['list'] = videos
            result['page'] = pg
        except Exception as e:
            print(f"搜索错误: {e}")
            result['list'] = []
        return result

    # ---------- 播放 ----------
    def playerContent(self, flag, id, vipFlags):
        result = {}
        try:
            play_url = id if id.startswith('http') else self.host + id
            headers = dict(self.headers)
            headers['Referer'] = play_url
            data = self.fetch(play_url, headers=headers).text
            m = re.search(r'"contentUrl"\s*:\s*"([^"]+)"', data)
            if m:
                content_url = m.group(1).replace('\\/', '/')
            else:
                m = re.search(r'<source\s+src="([^"]+\.m3u8[^"]*)"', data)
                if m:
                    content_url = m.group(1)
                else:
                    result['parse'] = 1
                    result['url'] = play_url
                    result['header'] = headers
                    return result
            if content_url.startswith('http'):
                result['parse'] = 0
                result['url'] = content_url
            else:
                result['parse'] = 1
                result['url'] = play_url
            result['header'] = {
                'User-Agent': self.headers['User-Agent'],
                'Referer': play_url
            }
        except Exception as e:
            print(f"播放错误: {e}")
            result['parse'] = 1
            result['url'] = id
        return result

    def localProxy(self, param):
        return [200, 'text/plain', b'not support']

    def e64(self, text):
        try:
            return b64encode(text.encode('utf-8')).decode('utf-8')
        except:
            return ""

    def d64(self, encoded_text):
        try:
            return b64decode(encoded_text.encode('utf-8')).decode('utf-8')
        except:
            return ""