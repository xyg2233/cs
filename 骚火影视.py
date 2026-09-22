# -*- coding: utf-8 -*-
# 基础版 by @嗷呜 · 补全优化 by AI
import re
import sys
import base64
from urllib.parse import urlparse, quote
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    # =========================================================
    # 类级静态headers模板（不修改它，init里做copy）
    # =========================================================
    BASE_HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="130", "Google Chrome";v="130"',
        'sec-ch-ua-platform': '"Android"',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    }

    def init(self, extend=""):
        # ① 动态拿可用域名（核心：避免写死域名被CF干）
        self.host = self._gethost()
        # ② copy一份，避免修改类属性污染
        self.h = dict(self.BASE_HEADERS)
        self.h['referer'] = self.host + '/'
        self.log(f'[骚火] host={self.host}')

    def getName(self):
        return '骚火影视'

    def isVideoFormat(self, url):
        return 0

    def manualVideoCheck(self):
        return 0

    def destroy(self):
        return 'ok'

    # ==================== 首页分类 ====================
    def homeContent(self, filter):
        d = self._pq('/')
        classes = []
        seen_tid = set()

        # 从顶部导航抓分类
        sel_nav = '.top_bar.clearfix a, .menu_list a, .nav_list a, .top_nav a'
        for a in d(sel_nav).items():
            href = (a.attr('href') or '').strip()
            name = a.text().strip()
            if not href or not name:
                continue
            if name in ('首页', '主页', 'Home', ''):
                continue
            m = re.search(r'/list/(\d+)', href)
            if m:
                tid = m.group(1)
                if tid not in seen_tid:
                    seen_tid.add(tid)
                    classes.append({'type_id': tid, 'type_name': name})

        # 兜底（导航抓空时保底）
        if not classes:
            classes = [
                {'type_id': '1', 'type_name': '电影'},
                {'type_id': '2', 'type_name': '电视剧'},
                {'type_id': '20', 'type_name': '国产剧'},
                {'type_id': '4', 'type_name': '动漫'},
            ]

        # 筛选器（和原版一致）
        filters = {
            '1': {'name': '类型', 'key': 'tid', 'value': [
                {'n': '喜剧','v':'6'},{'n':'爱情','v':'7'},{'n':'恐怖','v':'8'},
                {'n':'动作','v':'9'},{'n':'科幻','v':'10'},{'n':'战争','v':'11'},
                {'n':'犯罪','v':'12'},{'n':'动画','v':'13'},{'n':'奇幻','v':'14'},
                {'n':'剧情','v':'15'},{'n':'冒险','v':'16'},{'n':'悬疑','v':'17'},
                {'n':'惊悚','v':'18'},{'n':'其它','v':'19'},
            ]},
            '2': {'name': '类型', 'key': 'tid', 'value': [
                {'n': '大陆剧','v':'20'},{'n':'港剧','v':'21'},{'n':'韩剧','v':'22'},
                {'n':'美剧','v':'23'},{'n':'日剧','v':'24'},{'n':'英剧','v':'25'},
                {'n':'台剧','v':'26'},{'n':'其它','v':'27'},
            ]},
        }

        return {
            'class': classes,
            'filters': filters,
            'list': self._parse_vlist(d),   # 首页推荐位
        }

    def homeVideoContent(self):
        return {'list': []}

    # ==================== 分类页（补全分页）====================
    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if str(pg).isdigit() else 1
        # 优先用筛选子类型
        use_tid = (extend.get('tid') or str(tid)).strip()
        path = f'/list/{use_tid}-{pg}.html'
        d = self._pq(path)
        videos = self._parse_vlist(d)

        # 尝试从分页控件拿真实总页
        pagecount = self._guess_pagecount(d, pg)
        return {
            'list': videos,
            'page': pg,
            'pagecount': pagecount,
            'limit': 90,
            'total': pagecount * 90,
        }

    # ==================== 详情页（多层兜底）====================
    def detailContent(self, ids):
        path = ids[0] if isinstance(ids, list) else ids
        d = self._pq(path)
        vod = {'vod_id': path}

        # 片名
        vod['vod_name'] = (d('.v_title a, h1.title, .play_title').eq(0).text() or '').strip()
        # 封面
        img_src = (
            d('.v_pic img, .poster img').eq(0).attr('data-original')
            or d('.v_pic img, .poster img').eq(0).attr('src') or ''
        )
        vod['vod_pic'] = self._full_url(img_src)
        # 状态/备注
        vod['vod_remarks'] = (d('.v_note, .play_state').eq(0).text() or '').strip()
        # 简介
        vod['vod_content'] = ((d('.p_txt.show_part, .detail_desc, .v_info_box p').eq(0).text() or '').strip())[:500]

        # —— 播放线路 ——
        from_names, url_groups = [], []

        # 主流结构：.play_from .anthology-tab → ul.play_list
        from_lis = list(d('.play_from li, .anthology-tab li, .from_list li').items())
        play_lists = list(d('ul.play_list, .anthology-list').items())

        if from_lis and play_lists:
            for i, li in enumerate(from_lis):
                from_names.append(li.text().strip() or f'线路{i+1}')
                eps = []
                container = play_lists[i] if i < len(play_lists) else d
                for a in container('a').items():
                    href = (a.attr('href') or '').strip()
                    txt = (a.text() or '').strip()
                    if href and txt:
                        eps.append(f'{txt}${href}')
                url_groups.append('#'.join(eps[::-1]))
        else:
            # 兜底：直接在整个页面扫播放链接
            eps = []
            for a in d('a[href*=".m3u8"], a[href*="/play/"]').items():
                href = (a.attr('href') or '').strip()
                txt = (a.text() or '').strip() or href.split('/')[-1]
                if href:
                    eps.append(f'{txt}${href}')
            if eps:
                from_names = ['默认线路']
                url_groups = ['#'.join(eps[::-1])]

        vod['vod_play_from'] = '$$$'.join(from_names)
        vod['vod_play_url'] = '$$$'.join(url_groups)
        return {'list': [vod]}

    # ==================== 搜索（补全）====================
    def searchContent(self, key, quick, pg='1'):
        try:
            q = quote(key)
            # maxcms通用搜索URL（shdy2.com也是这个规则）
            d = self._pq(f'/s----------.html?wd={q}')
            videos = self._parse_vlist(d)
            return {'list': videos, 'pagecount': 1}
        except Exception as e:
            self.log(f'[骚火][搜索失败] {e}')
            return {'list': []}

    # ==================== 播放（保留作者逆向逻辑）====================
    def playerContent(self, flag, id, vipFlags):
        raw_id = id
        purl = id if id.startswith('http') else (self.host.rstrip('/') + '/' + id.lstrip('/'))

        try:
            resp = self.fetch(purl, headers=self.h, timeout=10)
            html = resp.text

            # 走 iframe → api.php 的解密链路
            iframe_src = (
                pq(html)('.play_box iframe, section iframe, iframe[src*="/play/"]').eq(0).attr('src')
                or ''
            )
            if iframe_src and not iframe_src.startswith('http'):
                iframe_src = self.host.rstrip('/') + '/' + iframe_src.lstrip('/')

            if iframe_src:
                ir = self.fetch(iframe_src, headers=self.h, timeout=10)
                sd = pq(ir.text)('body script').html() or ''
                jdata = self._extract_vals(sd)
                if jdata.get('key'):
                    jdata['key'] = self._hhh(jdata['key'])
                    parsed = urlparse(iframe_src)
                    api = f'{parsed.scheme}://{parsed.netloc}/api.php'
                    ph = dict(self.h)
                    ph['origin'] = f'{parsed.scheme}://{parsed.netloc}'
                    ph['referer'] = iframe_src
                    ph['content-type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
                    ph['x-requested-with'] = 'XMLHttpRequest'
                    jjb = self.post(api, headers=ph, data=jdata).json()
                    return {
                        'parse': 0,
                        'url': jjb.get('url', ''),
                        'header': {
                            'User-Agent': self.h['user-agent'],
                            'Referer': self.host + '/',
                        }
                    }

            # 降级1：页面里直接找m3u8
            m = re.search(r'["\'](?:file|url)["\']\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', html)
            if m:
                return {'parse': 0, 'url': m.group(1), 'header': {'Referer': self.host+'/', 'User-Agent': self.h['user-agent']}}

            # 降级2：交APP内置解析
            return {'parse': 1, 'url': purl, 'header': {'Referer': self.host+'/', 'User-Agent': self.h['user-agent']}}

        except Exception as e:
            self.log(f'[骚火][播放失败] {e}')
            return {'parse': 1, 'url': purl, 'header': {'Referer': self.host+'/', 'User-Agent': self.h['user-agent']}}

    def localProxy(self, param):
        return None

    def liveContent(self, url):
        return None

    # ======================================================
    # ==========  内部工具方法（原版保留/加固） ============
    # ======================================================

    def _gethost(self, timeout=5):
        """
        原版动态域名逻辑：
        1) 尝试 shapp.us 拿跳转域名
        2) fallback 直接 shdy2.com
        """
        probes = [
            ('http://shapp.us', '.content-top ul li a'),
            ('https://shdy2.com', None),
        ]
        for src, sel in probes:
            try:
                r = self.fetch(src, headers=self.BASE_HEADERS, timeout=timeout)
                if r.status_code == 200:
                    if sel:
                        for a in pq(r.text)(sel).items():
                            h = (a.attr('href') or '').strip()
                            if h and h.startswith('http'):
                                try:
                                    t = self.fetch(h, headers=self.BASE_HEADERS, timeout=3)
                                    if t.status_code == 200:
                                        self.log(f'[骚火][gethost] 命中={h}')
                                        return h.rstrip('/')
                                except:
                                    pass
                    else:
                        return src.rstrip('/')
            except:
                pass
        return 'https://shdy2.com'

    def _pq(self, path='', timeout=10):
        """请求 + 包装 pyquery（统一入口，方便以后加缓存/重试）"""
        url = path if path.startswith('http') else (self.host.rstrip('/') + '/' + path.lstrip('/'))
        r = self.fetch(url, headers=self.h, timeout=timeout)
        raw = r.text
        # pyquery有时喜欢str有时bytes
        return pq(raw.encode('utf-8', errors='replace') if isinstance(raw, str) else raw)

    def _full_url(self, src):
        if not src:
            return ''
        if src.startswith('http'):
            return src
        base = self.host.rstrip('/')
        src = src.lstrip('/')
        return f'{base}/{src}'

    def _parse_vlist(self, d):
        """
        通用：从各种列表容器里抠影片卡片
        （原版 getlist 的增强版：选择器更宽 + 去重 + 容错）
        """
        videos = []
        seen = set()
        # 先试 .grid_box ul li（最常见）
        container = d('.grid_box ul li, .public-list-box, .index_item, .search-box li')
        if container.length == 0:
            container = d('li').parent().find('li') or d('li')

        for li in container.items():
            # 找带影片链接的a
            a = (
                li('a[href*="/movie/"]').eq(0)
                or li('a[href*=".html"]').eq(0)
            )
            href = (a.attr('href') or '').strip()
            name = (a.attr('title') or a.text()).strip()
            if not href or not name or '/movie/' not in href:
                continue
            if href in seen:
                continue
            seen.add(href)

            img = li('img').eq(0)
            pic = (img.attr('data-original') or img.attr('src') or '').strip()
            pic = self._full_url(pic)
            remark = (li('.v_note, .note').text() or '').strip()
            videos.append({
                'vod_id': href,
                'vod_name': name,
                'vod_pic': pic,
                'vod_remarks': remark,
            })
        return videos

    def _guess_pagecount(self, d, cur_pg):
        """从分页a标签猜最大页"""
        max_pg = cur_pg
        for a in d('a[href*="list/"]').items():
            m = re.search(r'/list/\d+-(\d+)\.html', a.attr('href') or '')
            if m:
                p = int(m.group(1))
                max_pg = max(max_pg, p)
        return max(max_pg, cur_pg + 1)

    # ---- 原版 hhh / extract_values（一字不改保留） ----
    def _extract_vals(self, text):
        if not text:
            return {}
        um = re.search(r'var\s+url\s*=\s*"([^"]+)"', text)
        tm = re.search(r'var\s+t\s*=\s*"([^"]+)"', text)
        km = re.search(r'var\s+key\s*=\s*hhh\("([^"]+)"\)', text)
        am = re.search(r'var\s+act\s*=\s*"([^"]+)"', text)
        pm = re.search(r'var\s+play\s*=\s*"([^"]+)"', text)
        return {
            'url': um.group(1) if um else '',
            't': tm.group(1) if tm else '',
            'key': km.group(1) if km else '',
            'act': am.group(1) if am else '',
            'play': pm.group(1) if pm else '',
        }

    def _hhh(self, t):
        ee = {
            "0Oo0o0O0":"a","1O0bO001":"b","2OoCcO2":"c","3O0dO0O3":"d",
            "4OoEeO4":"e","5O0fO0O5":"f","6OoGgO6":"g","7O0hO0O7":"h",
            "8OoIiO8":"i","9O0jO0O9":"j","0OoKkO0":"k","1O0lO0O1":"l",
            "2OoMmO2":"m","3O0nO0O3":"n","4OoOoO4":"o","5O0pO0O5":"p",
            "6OoQqO6":"q","7O0rO0O7":"r","8OoSsO8":"s","9O0tO0O9":"t",
            "0OoUuO0":"u","1O0vO0O1":"v","2OoWwO2":"w","3O0xO0O3":"x",
            "4OoYyO4":"y","5O0zO0O5":"z","0OoAAO0":"A","1O0BBO1":"B",
            "2OoCCO2":"C","3O0DDO3":"D","4OoEEO4":"E","5O0FFO5":"F",
            "6OoGGO6":"G","7O0HHO7":"H","8OoIIO8":"I","9O0JJO9":"J",
            "0OoKKO0":"K","1O0LLO1":"L","2OoMMO2":"M","3O0NNO3":"N",
            "4OoOOO4":"O","5O0PPO5":"P","6OoQQO6":"Q","7O0RRO7":"R",
            "8OoSSO8":"S","9O0TTO9":"T","0OoUO0":"U","1O0VVO1":"V",
            "2OoWWO2":"W","3O0XXO3":"X","4OoYYO4":"Y","5O0ZZO5":"Z"
        }
        o = base64.b64decode(t).decode('utf-8', errors='replace')
        n, i = '', 0
        while i < len(o):
            hit = False
            for k in sorted(ee.keys(), key=len, reverse=True):
                if o[i:i+len(k)] == k:
                    n += ee[k]
                    i += len(k)
                    hit = True
                    break
            if not hit:
                i += 1
        return n


# 必须保留
spider = Spider()
