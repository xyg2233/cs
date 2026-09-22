# -*- coding: utf-8 -*-
import sys
import re
import requests
from urllib.parse import quote

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    def init(self, extend=""):
        self.host = "https://www.ddys24.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
            "Referer": self.host + "/",
            "Origin": self.host
        }

    def getName(self):
        return "低端影视"

    def isVideoFormat(self, url):
        return bool(re.search(r'\.(m3u8|mp4|flv|avi|mkv|mov|ts)(\?|$)', url or "", re.I))

    def manualVideoCheck(self):
        return False

    def homeContent(self, filter):
        return {
            "class": [
                {"type_id": "1", "type_name": "电影"},
                {"type_id": "2", "type_name": "电视剧"},
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "4", "type_name": "动漫"},
                {"type_id": "42", "type_name": "豆瓣Top250"}
            ]
        }

    def homeVideoContent(self):
        return {"list": self.parseList(self.get(self.host + "/"))}

    def categoryContent(self, tid, pg, filter, extend):
        url = self.host + "/ddvodtype/" + str(tid) + ".html" if str(pg) == "1" else self.host + "/ddvodtype/" + str(tid) + "-" + str(pg) + ".html"
        html = self.get(url)
        if not html and str(pg) != "1":
            html = self.get(self.host + "/ddvodshow/" + str(tid) + "--------" + str(pg) + "---.html")
        return {
            "page": int(pg),
            "pagecount": 999,
            "limit": 24,
            "total": 999999,
            "list": self.parseList(html)
        }

    def detailContent(self, ids):
        vid = ids[0]
        url = vid if str(vid).startswith("http") else self.host + "/ddvoddetail/" + str(vid) + ".html"
        html = self.get(url)
        name = self.clean(self.match(html, r'<h1[^>]*class=["\']title["\'][^>]*>(.*?)</h1>') or self.match(html, r'<title>《?([^《》_]+?)》?'))
        pic = self.fix(self.match(html, r'<img[^>]+data-original=["\']([^"\']+)') or self.match(html, r'<a[^>]+class=["\'][^"\']*v-thumb[^"\']*["\'][^>]+data-original=["\']([^"\']+)'))
        remarks = self.clean(self.match(html, r'<span class=["\']pic-text[^"\']*["\'][^>]*>(.*?)</span>'))
        desc = self.clean(self.match(html, r'<span class=["\']detail-content["\'][^>]*>(.*?)</span>') or self.match(html, r'<span class=["\']detail-sketch["\'][^>]*>(.*?)</span>') or self.match(html, r'<meta name=["\']description["\'] content=["\']([^"\']+)'))
        actor = self.clean(self.match(html, r'主演：</span>([\s\S]*?)</p>'))
        director = self.clean(self.match(html, r'导演：</span>([\s\S]*?)</p>'))
        area = self.clean(self.match(html, r'地区：</span>([\s\S]*?)<span'))
        year = self.clean(self.match(html, r'年份：</span>([\s\S]*?)</p>'))
        play_from = []
        play_url = []
        blocks = re.findall(r'<div class="stui-pannel-ddy1102-cbox b playlist mb">([\s\S]*?)</div>\s*</div>\s*</div>', html)
        if not blocks:
            blocks = re.findall(r'<ul class="stui-content_ddy1102-cplaylist clearfix">([\s\S]*?)</ul>', html)
        for i, block in enumerate(blocks):
            eps = []
            for m in re.finditer(r'<a[^>]+href=["\']([^"\']*?/ddvodplay/[^"\']+)["\'][^>]*>(.*?)</a>', block):
                u = self.fix(m.group(1))
                t = self.clean(m.group(2)) or "播放"
                if u:
                    eps.append(t + "$" + u)
            if eps:
                line = self.clean(self.match(block, r'<h3 class=["\']title["\'][^>]*>(.*?)</h3>')) or "线路" + str(i + 1)
                play_from.append(line)
                play_url.append("#".join(eps))
        if not play_url:
            eps = []
            for m in re.finditer(r'<a[^>]+href=["\']([^"\']*?/ddvodplay/' + str(vid) + r'-[^"\']+)["\'][^>]*>(.*?)</a>', html):
                u = self.fix(m.group(1))
                t = self.clean(m.group(2)) or "播放"
                if u:
                    eps.append(t + "$" + u)
            if eps:
                play_from.append("线路W")
                play_url.append("#".join(eps))
        if not play_url:
            u = self.fix(self.match(html, r'href=["\']([^"\']*?/ddvodplay/' + str(vid) + r'-1-1\.html)["\']'))
            if u:
                play_from.append("线路W")
                play_url.append("播放$" + u)
        return {
            "list": [{
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": remarks,
                "vod_year": year,
                "vod_area": area,
                "vod_actor": actor,
                "vod_director": director,
                "vod_content": desc,
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_url)
            }]
        }

    def searchContent(self, key, quick, pg="1"):
        k = quote(key)
        # 【关键修复】根据HTML源码修正搜索URL：action="/ddvodsearch/-------------.html" 且参数为 wd
        url = self.host + "/ddvodsearch/-------------.html?wd=" + k + "&page=" + str(pg)
        html = self.get(url)

        # 兜底：如果GET失败，尝试POST提交搜索
        if not html or "ddvoddetail" not in html:
            try:
                r = requests.post(
                    self.host + "/index.php/vod/search.html",
                    data={"wd": key, "page": pg},
                    headers=self.headers, timeout=15
                )
                r.encoding = "utf-8"
                html = r.text
            except:
                pass

        # 优先使用通用解析，如果搜不到（因为搜索页结构不同），使用专用解析
        results = self.parseList(html)
        if not results:
            results = self._parseSearch(html)
        return {"list": results, "page": int(pg)}

    def _parseSearch(self, html):
        """
        【关键修复】专用解析搜索结果页。
        针对结构：<li class="active clearfix"> -> <div class="thumb"> -> <a class="v-thumb ...">
        配合：<div class="detail"> -> <h3 class="title"><a>标题</a>
        """
        res = []
        seen = set()
        # 正则详解：
        # 1. 匹配 li 块
        # 2. 匹配 thumb 里的 a 标签，提取 href(vid) 和 data-original(pic)
        # 3. 匹配 span.pic-text(remarks)
        # 4. 匹配 detail 下的 h3>a 里的标题(name)
        pattern = (
            r'<li[^>]*class="[^"]*active[^"]*clearfix[^"]*">\s*'
            r'<div class="thumb">\s*'
            r'<a[^>]+class="[^"]*stui-vodlist_ddy1102-cthumb[^"]*"[^>]+'
            r'href="(/ddvoddetail/(\d+)\.html)"[^>]+'
            r'data-original="([^"]*)"[^>]*>[\s\S]*?'
            r'<span class="pic-text[^"]*">([^<]*)</span>[\s\S]*?'
            r'<h3[^>]*>\s*<a[^>]+href="/ddvoddetail/\2\.html"[^>]*>([^<]+)</a>'
        )
        for m in re.finditer(pattern, html, re.S):
            vid = m.group(2)
            if vid in seen:
                continue
            seen.add(vid)
            res.append({
                "vod_id": vid,
                "vod_name": self.clean(m.group(5)),  # 标题来自 h3>a
                "vod_pic": self.fix(m.group(3)),     # 图片来自 data-original
                "vod_remarks": self.clean(m.group(4))# 备注来自 pic-text
            })

        # 二次兜底：如果上面的复杂正则因网站改版失效，用松散匹配保底
        if not res:
            for m in re.finditer(
                r'<a[^>]+class="[^"]*stui-vodlist_ddy1102-cthumb[^"]*"[^>]+'
                r'href="(/ddvoddetail/(\d+)\.html)"[^>]+'
                r'data-original="([^"]*)"',
                html, re.S
            ):
                vid = m.group(2)
                if vid in seen:
                    continue
                seen.add(vid)
                # 尝试找附近的标题
                name_match = re.search(r'href="/ddvoddetail/' + vid + r'\.html"[^>]*>([^<]+)</a>', html)
                name = self.clean(name_match.group(1)) if name_match else "未知标题"
                res.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": self.fix(m.group(3)),
                    "vod_remarks": ""
                })
        return res

    def playerContent(self, flag, id, vipFlags):
        return {"parse": 1, "url": id, "header": self.headers}

    def localProxy(self, param):
        return [404, "text/plain", "", ""]

    def destroy(self):
        return "正在Destroy"

    def get(self, url):
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except Exception:
            return ""

    def match(self, text, rule):
        m = re.search(rule, text or "", re.S)
        return m.group(1) if m else ""

    def clean(self, text):
        return re.sub(r"\s+", " ", re.sub(r"<.*?>", "", text or "")).replace("&nbsp;", " ").replace("&amp;", "&").strip()

    def fix(self, url):
        if not url:
            return ""
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.host + url
        return url

    def parseList(self, html):
        res = []
        seen = set()
        # 优先匹配首页/分类页的结构
        for m in re.finditer(r'<a[^>]+class=["\'][^"\']*stui-vodlist_ddy1102-cthumb[^"\']*["\'][^>]+href=["\']([^"\']*?/ddvoddetail/(\d+)\.html)["\'][^>]*title=["\']([^"\']+)["\'][^>]*(?:data-original=["\']([^"\']+)["\'])?[\s\S]*?</a>', html or "", re.S):
            vid = m.group(2)
            if vid in seen:
                continue
            seen.add(vid)
            block = m.group(0)
            pic = m.group(4) or self.match(block, r'data-original=["\']([^"\']+)') or self.match(block, r'src=["\']([^"\']+\.(?:jpg|jpeg|png|webp|gif)[^"\']*)')
            remarks = self.clean(self.match(block, r'<span class=["\']pic-text[^"\']*["\'][^>]*>(.*?)</span>'))
            name = self.clean(m.group(3))
            if name:
                res.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": self.fix(pic),
                    "vod_remarks": remarks
                })
        # 如果上面的没匹配到，尝试宽松匹配
        if not res:
            for m in re.finditer(r'href=["\']([^"\']*?/ddvoddetail/(\d+)\.html)["\'][^>]*title=["\']([^"\']+)["\'][\s\S]{0,500}?(?:data-original|src)=["\']([^"\']+)["\']', html or "", re.S):
                vid = m.group(2)
                if vid in seen:
                    continue
                seen.add(vid)
                res.append({
                    "vod_id": vid,
                    "vod_name": self.clean(m.group(3)),
                    "vod_pic": self.fix(m.group(4)),
                    "vod_remarks": ""
                })
        return res
