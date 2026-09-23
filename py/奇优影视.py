#http://www.qiyoudy.info/
#http://zhuan.qiyo.cc/
#http://www.qiyoudy1.com/
# -*- coding: utf-8 -*-
#!/usr/bin/python
import sys
sys.path.append('..')
from base.spider import Spider
import json
import urllib.parse
import re
from lxml import etree
from urllib.parse import urljoin


class Spider(Spider):

    def getName(self):
        return "奇优影院"

    def init(self, extend):
        pass

    # ==================== 首页分类 + 筛选 ====================
    def homeContent(self, filter):
        result = {}
        cateManual = {
            "电影": "1",
            "电视剧": "2",
            "动漫": "3",
            "综艺": "4",
            "伦理": "6"
        }
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]
        result['class'] = classes

        filters = {
            "1": [{"key": "by", "name": "排序", "value": [{"n": "按时间", "v": "time"}, {"n": "按人气", "v": "hit"}]}],
            "2": [{"key": "by", "name": "排序", "value": [{"n": "按时间", "v": "time"}, {"n": "按人气", "v": "hit"}]}],
            "3": [{"key": "by", "name": "排序", "value": [{"n": "按时间", "v": "time"}, {"n": "按人气", "v": "hit"}]}],
            "4": [{"key": "by", "name": "排序", "value": [{"n": "按时间", "v": "time"}, {"n": "按人气", "v": "hit"}]}],
            "6": [{"key": "by", "name": "排序", "value": [{"n": "按时间", "v": "time"}, {"n": "按人气", "v": "hit"}]}]
        }
        result['filters'] = filters
        return result

    # ==================== 首页推荐 ====================
    def homeVideoContent(self):
        try:
            rsp = self.fetch("http://www.qiyou02.com/")
            root = self.parse_html(rsp.content)
            if not root:
                return {'list': []}

            videos = []
            # 轮播
            for a in root.xpath("//div[contains(@class,'carousel')]//a[contains(@class,'stui-vodlist__thumb')]"):
                try:
                    name = (a.xpath(".//span[@class='pic-text text-center']/text()")
                            or a.xpath("./@title") or ["未知"])[0].strip()
                    style = a.xpath("./@style")[0] if a.xpath("./@style") else ""
                    pic = re.search(r"background:\s*url\((.*?)\)", style)
                    pic = pic.group(1) if pic else ""
                    sid = a.xpath("./@href")[0] if a.xpath("./@href") else ""
                    videos.append({"vod_id": sid, "vod_name": name, "vod_pic": pic, "vod_remarks": "推荐"})
                except:
                    continue

            # 各分类区块列表
            for a in root.xpath("//ul[contains(@class,'stui-vodlist')]//a[contains(@class,'stui-vodlist__thumb')]"):
                try:
                    name = a.xpath("./@title")[0] if a.xpath("./@title") else "未知"
                    pic = a.xpath("./@data-original")[0] if a.xpath("./@data-original") else ""
                    sid = a.xpath("./@href")[0] if a.xpath("./@href") else ""
                    remark = (a.xpath(".//span[@class='pic-text text-right']/text()") or [""])[0]
                    videos.append({"vod_id": sid, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
                except:
                    continue

            return {'list': videos}
        except:
            return {'list': []}

    # ==================== 分类页 ====================
    def categoryContent(self, tid, pg, filter, extend):
        try:
            order = extend.get('by', 'time') if extend else 'time'
            url = f'http://www.qiyou02.com/list/{tid}_{pg}.html?order={order}'
            rsp = self.fetch(url)
            root = self.parse_html(rsp.content)
            if not root:
                return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

            videos = []
            for a in root.xpath("//a[contains(@class,'stui-vodlist__thumb')]"):
                try:
                    name = a.xpath("./@title")[0] if a.xpath("./@title") else "未知"
                    pic = a.xpath("./@data-original")[0] if a.xpath("./@data-original") else ""
                    sid = a.xpath("./@href")[0] if a.xpath("./@href") else ""
                    remark = (a.xpath(".//span[@class='pic-text text-right']/text()") or [""])[0]
                    videos.append({"vod_id": sid, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
                except:
                    continue

            # 分页
            cur = root.xpath("//ul[contains(@class,'stui-page')]//a[@class='active']/text()")
            current_page = int(cur[0]) if cur else pg
            pns = [int(re.search(r'list/\d+_(\d+)\.html', l).group(1)) for l in
                   root.xpath("//ul[contains(@class,'stui-page')]//a[contains(@href,'list')]/@href") if re.search(r'list/\d+_(\d+)\.html', l)]
            total_page = max(pns) if pns else 1

            return {
                'list': videos, 'page': current_page,
                'pagecount': total_page, 'limit': 90, 'total': 999999
            }
        except:
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    # ==================== 详情页 ====================
    def detailContent(self, array):
        try:
            tid = array[0]
            url = f'http://www.qiyoudy1.com{tid}'
            rsp = self.fetch(url)
            root = self.parse_html(rsp.content)
            if not root:
                return {'list': []}

            pic = title = area = director = actor = year = desc = ""
            detail_node = (root.xpath("//div[contains(@class,'stui-content__detail')]") or
                           root.xpath("//div[@class='stui-player__detail']"))
            if detail_node:
                dn = detail_node[0]
                pic = self.get_first(root.xpath("//meta[@property='og:image']/@content") or dn.xpath(".//img/@data-original"))
                title = self.get_first(dn.xpath(".//h1//text()"))
                if not title:
                    pt = self.get_first(root.xpath("//title/text()"))
                    m = re.search(r"《(.*?)》", pt) if pt else None
                    title = m.group(1) if m else ""
                area = self.get_first(root.xpath("//meta[@property='og:video:area']/@content"))
                director = self.get_first(root.xpath("//meta[@property='og:video:director']/@content"))
                actor = self.get_first(root.xpath("//meta[@property='og:video:actor']/@content"))
                yi = self.get_first(root.xpath("//p[@class='data']//text()[contains(.,'年份：')]"))
                year = re.search(r"年份：(\d{4})", yi).group(1) if yi and re.search(r"年份：(\d{4})", yi) else ""
                desc = self.get_first(root.xpath("//meta[@property='og:description']/@content"))

            # 播放线路
            playFrom, playUrl = [], []
            for tab in root.xpath("//ul[contains(@class,'nav-tabs')]/li"):
                tname = self.get_first(tab.xpath(".//a/text()"))
                tid2 = self.get_first(tab.xpath(".//a/@href")).replace("#", "")
                if tname and tid2:
                    pl = root.xpath(f"//div[@id='{tid2}']//ul[contains(@class,'stui-content__playlist')]//a")
                    if pl:
                        playFrom.append(tname)
                        eps = []
                        for ep in pl:
                            en = self.get_first(ep.xpath("./text()")) or "播放"
                            eu = self.get_first(ep.xpath("./@href"))
                            if eu:
                                # 确保播放链接是完整URL
                                full_eu = urljoin("http://www.qiyoudy1.com", eu)
                                eps.append(f"{en}${full_eu}")
                        if eps:
                            playUrl.append("#".join(eps))

            vod = {
                "vod_id": tid, "vod_name": title, "vod_pic": pic,
                "vod_year": year, "vod_area": area,
                "vod_actor": actor, "vod_director": director, "vod_content": desc
            }
            if playFrom and playUrl:
                vod['vod_play_from'] = "$$$".join(playFrom)
                vod['vod_play_url'] = "$$$".join(playUrl)
            return {'list': [vod]}
        except:
            return {'list': []}

    # ==================== 搜索 ====================
    def searchContent(self, key, quick, page='1'):
        try:
            base = "http://www.qiyoudy1.com"

            # ① 先 GET 首页拿 PHPSESSION
            self.fetch(base + "/")

            # ② POST，data 用 dict
            rsp = self.post(base + "/search.php", data={'searchword': key}, headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36",
                "Referer": base + "/",
                "Origin": base,
                "X-Requested-With": "XMLHttpRequest",
            })

            root = self.parse_html(rsp.content)
            if not root:
                return {'list': []}

            videos = []

            # ③ 搜索页是 stui-vodlist__media
            items = root.xpath("//ul[contains(@class,'stui-vodlist__media')]/li")
            if not items:
                items = root.xpath("//ul[contains(@class,'stui-vodlist')]/li")

            for item in items:
                try:
                    thumb = (item.xpath(".//a[contains(@class,'stui-vodlist__thumb')]") or
                             item.xpath(".//a[contains(@href,'/view/')]"))
                    if not thumb:
                        continue
                    thumb = thumb[0]
                    href = self.get_first(thumb.xpath("./@href"))
                    title = self.get_first(thumb.xpath("./@title"))
                    pic = self.get_first(thumb.xpath("./@data-original"))

                    if not title:
                        da = item.xpath(".//div[contains(@class,'detail')]//h4/a")
                        if da:
                            title = self.get_first(da[0].xpath("./text()"))

                    remark = (item.xpath(".//span[contains(@class,'pic-text')]/text()") or
                              item.xpath(".//div[contains(@class,'detail')]//p/text()") or [""])
                    remark = remark[0].strip() if remark else ""

                    if href and title:
                        videos.append({"vod_id": href, "vod_name": title.strip(),
                                       "vod_pic": pic, "vod_remarks": remark})
                except:
                    continue

            # 兜底
            if not videos:
                for a in root.xpath("//a[contains(@href,'/view/')]"):
                    try:
                        href = self.get_first(a.xpath("./@href"))
                        title = (self.get_first(a.xpath("./@title")) or
                                 self.get_first(a.xpath("./text()")))
                        pic = self.get_first(a.xpath("./@data-original"))
                        if href and title:
                            videos.append({"vod_id": href, "vod_name": title.strip(),
                                           "vod_pic": pic, "vod_remarks": ""})
                    except:
                        continue

            seen, unique = set(), []
            for v in videos:
                k = (v['vod_id'], v['vod_name'])
                if k not in seen:
                    seen.add(k)
                    unique.append(v)
            return {'list': unique}
        except Exception as e:
            print(f"[QiYou Search Error] {e}")
            return {'list': []}

    # ==================== 播放（最终方案：返回播放页URL，让客户端WebView加载） ====================
    def playerContent(self, flag, id, vipFlags):
        try:
            # id 已经是完整URL（在detailContent中转换过了）
            play_url = id
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
                "Referer": "http://www.qiyou02.com/",
            }
            # 返回parse=1，让客户端用WebView加载播放页，从而触发iframe中的播放器
            return {"parse": 1, "playUrl": "", "url": play_url, "header": headers}
        except:
            return {"parse": 1, "playUrl": "", "url": id, "header": {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36",
                "Referer": "http://www.qiyou02.com/"
            }}

    # ==================== 辅助 ====================
    def parse_html(self, content, return_content=False):
        for enc in ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']:
            try:
                html = content.decode(enc)
                break
            except:
                continue
        else:
            html = content.decode('utf-8', errors='replace')
        html = self.clean_html(html)
        root = etree.HTML(html)
        return (root, html) if return_content else root

    def get_first(self, arr, default=""):
        return arr[0] if arr else default

    def clean_html(self, h):
        h = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', h)
        for o, n in {'&nbsp;':' ','&amp;':'&','&lt;':'<','&gt;':'>','&quot;':'"'}.items():
            h = h.replace(o, n)
        return h

    def isVideoFormat(self, url):
        return any(f in url for f in ['.m3u8','.mp4','.avi','.mkv','.flv','.webm'])

    def manualVideoCheck(self):
        return True

    def localProxy(self, param):
        return {}
