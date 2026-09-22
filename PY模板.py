# coding=utf-8
import sys
import os
import re
import json
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    """電視爬蟲通用模板 - 適用於蜂蜜影視/TVBox"""
    
    # ==================== 基本配置 ====================
    
    def getName(self):
        """返回爬蟲名稱"""
        return "網站名稱"  # 例如: "小宝影院"
    
    def init(self, extend=""):
        """初始化配置"""
        self.host = "https://example.com"  # 網站主域名
        print(f"Initialized with host: {self.host}")
    
    def getDependence(self):
        """依賴的第三方庫"""
        return ["bs4"]  # 使用BeautifulSoup解析HTML
    
    def header(self):
        """請求頭設置 - 模擬瀏覽器"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    # ==================== 工具方法 ====================
    
    def build_full_url(self, url):
        """
        將相對路徑補全為完整URL
        支持: 完整URL、//開頭、/開頭、./開頭、相對路徑
        """
        if not url or not isinstance(url, str):
            return ''
        
        url = url.strip()
        
        # 已經是完整URL
        if url.startswith('http://') or url.startswith('https://'):
            return url
            
        # 無效值過濾
        if not url or url in ['null', 'undefined', '']:
            return ''
        
        # 協議相對URL
        if url.startswith('//'):
            return 'https:' + url
        
        # 根相對URL
        if url.startswith('/'):
            return self.host + url
        
        # 當前目錄相對URL
        if url.startswith('./'):
            return self.host + url[1:]
        
        # 普通相對路徑
        return self.host + '/' + url
    
    def extract_pic(self, element):
        """
        從HTML元素中提取圖片URL - 多種方式兼容
        支持: data-original, src, style background-image
        """
        pic = ''
        
        # 方法1: 從img標籤提取
        img = element.find('img') if hasattr(element, 'find') else None
        if img:
            pic = img.get('data-original', '') or img.get('src', '')
        
        # 方法2: 從元素本身的data-original
        if not pic:
            pic = element.get('data-original', '')
        
        # 方法3: 從元素本身的src
        if not pic:
            pic = element.get('src', '')
        
        # 方法4: 從style中的background-image
        if not pic:
            style = element.get('style', '')
            match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
            if match:
                pic = match.group(1)
        
        return self.build_full_url(pic) if pic else ''
    
    def extract_remark(self, element):
        """提取備註信息（如 HD中字、更新至XX集）"""
        remark = ''
        remark_span = element.find('span', class_='pic-text') if hasattr(element, 'find') else None
        if remark_span:
            remark = remark_span.text.strip()
        return remark
    
    # ==================== 首頁功能 ====================
    
    def homeContent(self, filter):
        """
        返回分類列表和首頁推薦
        參數 filter: 是否啟用篩選功能
        返回: {"class": 分類列表, "list": 推薦視頻列表, "filters": 篩選條件(可選)}
        """
        result = {}
        
        # ===== 1. 分類列表 =====
        # 格式: [{"type_id": "ID", "type_name": "名稱"}, ...]
        classes = [
            {"type_id": "1", "type_name": "電影"},
            {"type_id": "2", "type_name": "電視劇"},
            {"type_id": "3", "type_name": "動漫"},
            {"type_id": "4", "type_name": "綜藝"},
            # ... 根據實際網站添加
        ]
        result["class"] = classes
        
        # ===== 2. 可選：篩選條件 =====
        # 如果需要篩選功能，可以添加 filters
        filters = {}
        # 示例格式：
        # filters["分類ID"] = [
        #     {"key": "sort", "name": "排序", "value": [{"n": "時間", "v": "time"}, {"n": "人氣", "v": "hits"}]},
        #     {"key": "area", "name": "地區", "value": [{"n": "大陸", "v": "大陸"}, {"n": "香港", "v": "香港"}]},
        # ]
        result["filters"] = filters
        
        # ===== 3. 首頁推薦視頻 =====
        videos = []
        try:
            rsp = self.fetch(self.host, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            # ---- 3.1 輪播圖推薦 ----
            # 根據實際網站修改選擇器
            slide_items = soup.select('.carousel .item a')  # 示例選擇器
            for item in slide_items:
                href = item.get('href', '')
                if href:
                    videos.append({
                        "vod_id": self.build_full_url(href),
                        "vod_name": item.get('title', '') or item.text.strip(),
                        "vod_pic": self.extract_pic(item),
                        "vod_remarks": "輪播推薦"
                    })
            
            # ---- 3.2 普通推薦列表 ----
            # 根據實際網站修改選擇器
            vod_items = soup.select('.vodlist .item')  # 示例選擇器
            for item in vod_items:
                link = item.find('a')
                if link and link.get('href'):
                    videos.append({
                        "vod_id": self.build_full_url(link.get('href')),
                        "vod_name": link.get('title', '') or link.text.strip(),
                        "vod_pic": self.extract_pic(item),
                        "vod_remarks": self.extract_remark(item)
                    })
            
            # ===== 4. 去重並限制數量 =====
            seen = set()
            unique_videos = []
            for v in videos:
                if v['vod_id'] not in seen and v['vod_name']:
                    seen.add(v['vod_id'])
                    unique_videos.append(v)
                    if len(unique_videos) >= 20:  # 通常顯示20個
                        break
            
            result["list"] = unique_videos
            
        except Exception as e:
            print(f"homeContent error: {e}")
            result["list"] = []
        
        return result
    
    def homeVideoContent(self):
        """
        返回首頁推薦視頻
        有些應用會單獨調用這個方法
        """
        return self.homeContent(False)
    
    # ==================== 分類頁功能 ====================
    
    def categoryContent(self, tid, pg, filter, extend):
        """
        返回分類頁內容
        參數:
            tid: 分類ID
            pg: 頁碼
            filter: 是否篩選
            extend: 篩選條件字典 {"key": "value"}
        返回: {"list": 視頻列表, "pagecount": 總頁數, "page": 當前頁, "limit": 每頁數量, "total": 總數}
        """
        result = {}
        try:
            # ===== 1. 構建URL =====
            # 根據實際網站的分頁規則修改
            if pg == 1:
                url = f"{self.host}/list/{tid}.html"
            else:
                url = f"{self.host}/list/{tid}/page/{pg}.html"
            
            # ===== 2. 處理篩選條件 =====
            if extend:
                # 根據實際網站的篩選規則修改
                params = []
                if extend.get('area'):
                    params.append(f"area/{urllib.parse.quote(extend['area'])}")
                if extend.get('year'):
                    params.append(f"year/{extend['year']}")
                # 構建篩選URL
                url = f"{self.host}/show/{tid}/{'/'.join(params)}.html"
                if pg > 1:
                    url = f"{self.host}/show/page/{pg}/{'/'.join(params)}.html"
            
            print(f"Fetching category: {url}")
            rsp = self.fetch(url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            # ===== 3. 提取視頻列表 =====
            videos = []
            # 根據實際網站修改選擇器
            vod_items = soup.select('.vodlist .item')  # 示例選擇器
            for item in vod_items:
                link = item.find('a')
                if link and link.get('href'):
                    videos.append({
                        "vod_id": self.build_full_url(link.get('href')),
                        "vod_name": link.get('title', '') or link.text.strip(),
                        "vod_pic": self.extract_pic(item),
                        "vod_remarks": self.extract_remark(item)
                    })
            
            result["list"] = videos
            
            # ===== 4. 提取總頁數 =====
            page_info = soup.find('ul', class_='page')  # 根據實際修改
            if page_info:
                # 方法1: 從移動端顯示獲取 "1/100"
                mobile_span = page_info.find('span', class_='visible-xs')
                if mobile_span:
                    page_text = mobile_span.text.strip()
                    match = re.search(r'/(\d+)', page_text)
                    if match:
                        result["pagecount"] = int(match.group(1))
                    else:
                        result["pagecount"] = 1
                else:
                    # 方法2: 從頁碼鏈接獲取最大頁碼
                    page_links = page_info.find_all('a')
                    max_page = 1
                    for link in page_links:
                        href = link.get('href', '')
                        match = re.search(r'/page/(\d+)', href)
                        if match:
                            page_num = int(match.group(1))
                            if page_num > max_page:
                                max_page = page_num
                    result["pagecount"] = max_page if max_page > 1 else 1
            else:
                result["pagecount"] = 1
            
            result["page"] = pg
            result["limit"] = len(videos)
            result["total"] = result["pagecount"] * 20  # 估算總數
            
        except Exception as e:
            print(f"categoryContent error: {e}")
            result = {
                "list": [],
                "pagecount": 1,
                "page": pg,
                "limit": 0,
                "total": 0
            }
        
        return result
    
    # ==================== 詳情頁功能 ====================
    
    def detailContent(self, ids):
        """
        返回詳情頁內容
        參數 ids: 視頻ID或ID列表
        返回: {"list": [視頻詳情]}
        """
        result = {}
        try:
            # ===== 1. 處理ID =====
            if isinstance(ids, list):
                vid = ids[0]
            else:
                vid = ids
            
            vid = self.build_full_url(vid)
            
            print(f"Fetching detail: {vid}")
            rsp = self.fetch(vid, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            # ===== 2. 初始化視頻對象 =====
            vod = {
                "vod_id": vid,
                "vod_name": "",
                "vod_pic": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_area": "",
                "vod_year": "",
                "vod_remarks": "",
                "vod_play_from": "",
                "vod_play_url": ""
            }
            
            # ===== 3. 提取基本信息 =====
            # 標題
            title_tag = soup.find('h1')  # 根據實際修改
            if title_tag:
                vod["vod_name"] = title_tag.text.strip()
            
            # 封面
            pic = self.extract_pic(soup)
            if pic:
                vod["vod_pic"] = pic
            
            # ===== 4. 提取元數據 =====
            # 根據實際網站修改選擇器和解析邏輯
            info_items = soup.select('.info-item')  # 示例選擇器
            for item in info_items:
                text = item.text
                if '主演' in text:
                    vod["vod_actor"] = self.extract_text_after(text, '主演')
                elif '導演' in text:
                    vod["vod_director"] = self.extract_text_after(text, '導演')
                elif '地區' in text:
                    vod["vod_area"] = self.extract_text_after(text, '地區')
                elif '年份' in text:
                    vod["vod_year"] = self.extract_text_after(text, '年份')
            
            # 簡介
            desc = soup.find('div', class_='description')  # 根據實際修改
            if desc:
                vod["vod_content"] = desc.text.strip()
            
            # ===== 5. 提取播放地址 =====
            play_froms = []
            play_urls = []
            
            # ---- 5.1 提取播放源名稱 ----
            tab_links = soup.select('.source-tabs a')  # 根據實際修改
            for tab in tab_links:
                play_froms.append(tab.text.strip())
            
            if not play_froms:
                play_froms = ["默認源"]
            
            # ---- 5.2 提取播放列表 ----
            tab_panes = soup.select('.tab-content .tab-pane')  # 根據實際修改
            for i, pane in enumerate(tab_panes):
                if i >= len(play_froms):
                    break
                
                episodes = []
                # 根據實際修改播放列表選擇器
                playlist = pane.find('ul', class_='episode-list')
                if playlist:
                    links = playlist.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if href and href != 'javascript:;':
                            episode_name = link.text.strip()
                            if episode_name:
                                play_url = self.build_full_url(href)
                                if play_url:
                                    episodes.append(f"{episode_name}${play_url}")
                
                if episodes:
                    play_urls.append('#'.join(episodes))
            
            # ---- 5.3 如果沒找到，嘗試直接獲取 ----
            if not play_urls:
                playlist = soup.find('ul', class_='episode-list')  # 根據實際修改
                if playlist:
                    episodes = []
                    links = playlist.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if href and href != 'javascript:;':
                            episode_name = link.text.strip()
                            if episode_name:
                                play_url = self.build_full_url(href)
                                if play_url:
                                    episodes.append(f"{episode_name}${play_url}")
                    if episodes:
                        play_urls.append('#'.join(episodes))
                        play_froms = ["默認源"]
            
            vod["vod_play_from"] = '$$$'.join(play_froms)
            vod["vod_play_url"] = '$$$'.join(play_urls)
            
            result["list"] = [vod]
            
        except Exception as e:
            print(f"detailContent error: {e}")
            result["list"] = []
        
        return result
    
    # ==================== 搜索功能 ====================
    # 重要: 蜂蜜影視要求3個參數 (key, quick, pg)
    
    def searchContent(self, key, quick, pg=1):
        """
        搜索內容 - 標準方法 (3個參數)
        參數:
            key: 搜索關鍵字
            quick: 是否快速搜索
            pg: 頁碼
        """
        print(f"【搜索】關鍵字: {key}, 頁碼: {pg}")
        return self._do_search(key, pg)
    
    def search(self, key):
        """備用搜索方法 (2個參數) - 兼容其他應用"""
        print("【備用搜索】search")
        return self._do_search(key, 1)
    
    def find(self, key):
        """備用搜索方法 (2個參數)"""
        print("【備用搜索】find")
        return self._do_search(key, 1)
    
    def query(self, key):
        """備用搜索方法 (2個參數)"""
        print("【備用搜索】query")
        return self._do_search(key, 1)
    
    def searchPage(self, key, pg):
        """搜索分頁方法 (2個參數)"""
        print(f"【搜索分頁】關鍵字: {key}, 頁碼: {pg}")
        return self._do_search(key, pg)
    
    def _do_search(self, key, pg=1):
        """
        核心搜索邏輯
        所有搜索方法都調用這個
        """
        result = {}
        videos = []
        try:
            # ===== 1. 構建搜索URL =====
            # 根據實際網站修改URL格式
            if pg == 1:
                search_url = f"{self.host}/search.html?wd={urllib.parse.quote(key)}"
            else:
                search_url = f"{self.host}/search/page/{pg}/wd/{urllib.parse.quote(key)}.html"
            
            print(f"搜索URL: {search_url}")
            
            rsp = self.fetch(search_url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            # ===== 2. 提取搜索結果 =====
            # 根據實際網站修改選擇器
            search_items = soup.select('.search-list li')  # 示例選擇器
            for item in search_items:
                # 提取標題和鏈接
                link = item.find('a')
                if not link or not link.get('href'):
                    continue
                
                vod_id = self.build_full_url(link.get('href'))
                title = link.get('title', '') or link.text.strip()
                
                # 提取圖片
                pic = self.extract_pic(item)
                
                # 提取備註
                remark = self.extract_remark(item)
                
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
            
            result["list"] = videos
            print(f"找到 {len(videos)} 個結果")
            
            # ===== 3. 提取總頁數 =====
            page_info = soup.find('ul', class_='page')
            if page_info:
                mobile_span = page_info.find('span', class_='visible-xs')
                if mobile_span:
                    page_text = mobile_span.text.strip()
                    match = re.search(r'/(\d+)', page_text)
                    result["pagecount"] = int(match.group(1)) if match else 1
                else:
                    result["pagecount"] = 1
            else:
                result["pagecount"] = 1
            
            result["page"] = pg
            result["limit"] = len(videos)
            result["total"] = result["pagecount"] * len(videos) if videos else 0
            
        except Exception as e:
            print(f"搜索錯誤: {e}")
            import traceback
            traceback.print_exc()
            result = {"list": [], "pagecount": 1, "page": pg, "limit": 0, "total": 0}
        
        return result
    
    # ==================== 播放功能 ====================
    
    def playerContent(self, ids, flag, ext):
        """
        返回播放器內容
        參數:
            ids: 播放地址ID
            flag: 播放源標識
            ext: 擴展參數
        返回: {"parse": 解析方式, "url": 播放地址, "header": 請求頭}
        """
        result = {}
        try:
            play_url = ids
            print(f"播放請求 - ID: {play_url}, Flag: {flag}")
            
            # ===== 1. 處理特殊情況 =====
            # 如果播放地址需要從頁面提取
            if not self.is_video_url(play_url):
                play_url = self.extract_video_url(play_url)
            
            # ===== 2. 返回播放信息 =====
            # parse=0: 直接播放; parse=1: 嗅探模式
            result["parse"] = 1  # 推薦使用嗅探模式
            result["playUrl"] = ""
            result["url"] = play_url
            result["header"] = json.dumps(self.header())
            
        except Exception as e:
            print(f"playerContent error: {e}")
            result = {
                "parse": 1,
                "playUrl": "",
                "url": ids if ids else "",
                "header": json.dumps(self.header())
            }
        
        return result
    
    def is_video_url(self, url):
        """判斷是否為直接視頻URL"""
        if not url:
            return False
        video_exts = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.wmv', '.mov']
        return any(ext in url.lower() for ext in video_exts)
    
    def extract_video_url(self, page_url):
        """
        從播放頁提取真實視頻URL
        根據實際網站修改提取邏輯
        """
        try:
            rsp = self.fetch(page_url, headers=self.header())
            # 方法1: 提取 player_aaaa 變量
            match = re.search(r'var player_aaaa\s*=\s*({.*?});', rsp.text, re.DOTALL)
            if match:
                player_data = json.loads(match.group(1))
                return player_data.get('url', page_url)
            
            # 方法2: 提取 iframe
            soup = BeautifulSoup(rsp.text, 'html.parser')
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                return self.build_full_url(iframe.get('src'))
            
        except Exception as e:
            print(f"提取視頻URL錯誤: {e}")
        
        return page_url
    
    # ==================== 輔助方法 ====================
    
    def isVideoFormat(self, url):
        """判斷是否為視頻格式"""
        return self.is_video_url(url)
    
    def manualVideoCheck(self):
        """手動視頻檢查"""
        pass
    
    def localProxy(self, param):
        """
        本地代理 - 用於處理m3u8文件
        當 parse=0 且需要代理時使用
        """
        return None
    
    def extract_text_after(self, text, keyword):
        """提取關鍵字後的文本"""
        if keyword in text:
            return text.split(keyword)[-1].strip()
        return ""
    
    def destroy(self):
        """銷毀時清理"""
        pass