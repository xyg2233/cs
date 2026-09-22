import { _ } from 'assets://js/lib/cat.js';

const API_KEY = '0ac44ae016490db2204ce0a042db2916';
const BASE_URL = 'https://frodo.douban.com/api/v2';
const HEADERS = {
    'Host': 'frodo.douban.com',
    'Connection': 'Keep-Alive',
    'Referer': 'https://servicewechat.com/wx2f9b06c1de1ccfca/84/page-frame.html',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat'
};

let cookie = '';

async function request(url) {
    let headers = { ...HEADERS };
    if (cookie) headers['Cookie'] = cookie;
    let res = await req(url, { headers: headers, timeout: 10000 });
    if (res?.headers && res.headers['set-cookie']) {
        cookie = Array.isArray(res.headers['set-cookie']) ? res.headers['set-cookie'][0] : res.headers['set-cookie'];
    }
    let content = typeof res === 'string' ? res : (res.content || '');
    return content;
}

function buildTagsString(params) {
    let tags = ['动画'];
    let type = params.get('类型');
    let area = params.get('地区');
    let year = params.get('年代');
    if (type && type !== '') tags.push(type);
    if (area && area !== '') tags.push(area);
    if (year && year !== '') tags.push(year);
    return tags.join(',');
}

function parseItemsToVodList(itemsArray) {
    let list = [];
    for (let item of itemsArray) {
        let id = item.id;
        let vodId = `msearch:${id}`;
        let name = item.title || '';
        let pic = '';
        if (item.pic && item.pic.normal) {
            pic = `${item.pic.normal}@Referer=https://api.douban.com/@User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36`;
        }
        let remarks = '';
        if (item.rating && item.rating.value !== undefined && item.rating.value !== null) {
            let score = item.rating.value;
            remarks = `评分：${score}`;
        } else {
            remarks = '评分：0';
        }
        list.push({
            vod_id: vodId,
            vod_name: name,
            vod_pic: pic,
            vod_remarks: remarks
        });
    }
    return list;
}

function filterItemsWithoutPic(jsonStr) {
    try {
        let obj = JSON.parse(jsonStr);
        let filtered = obj.list.filter(item => item.vod_pic && item.vod_pic !== '');
        obj.list = filtered;
        return JSON.stringify(obj);
    } catch (e) {
        return jsonStr;
    }
}

async function processAnimeContent(pg, extend) {
    let page = parseInt(pg) || 1;
    let start = (page - 1) * 20;
    let sort = extend?.sort || 'T';
    let tags = buildTagsString(new Map(Object.entries(extend || {})));
    let url = `${BASE_URL}/tv/recommend?apikey=${API_KEY}&sort=${sort}&tags=${encodeURIComponent(tags)}&start=${start}&count=20`;
    let html = await request(url);
    let data = JSON.parse(html);
    let items = data.items || [];
    let list = parseItemsToVodList(items);
    let result = {
        page: page,
        pagecount: 999,
        limit: 20,
        total: list.length,
        list: list
    };
    return JSON.stringify(result);
}

async function categoryContent(tid, pg, extend) {
    if (tid === 'anime_hot') {
        return await processAnimeContent(pg, extend);
    }

    let page = parseInt(pg) || 1;
    let start = (page - 1) * 20;
    let url = '';
    let itemsKey = 'items';

    function buildTagsForMovieOrTV(category, ext) {
        let tags = [];
        if (category === 'movie') {
            if (ext?.['类型'] && ext['类型'] !== '') tags.push(ext['类型']);
            if (ext?.['地区'] && ext['地区'] !== '') tags.push(ext['地区']);
            if (ext?.['年代'] && ext['年代'] !== '') tags.push(ext['年代']);
        } else if (category === 'tv') {
            if (ext?.['类型'] && ext['类型'] !== '') tags.push(ext['类型']);
            if (ext?.['电视剧形式'] && ext['电视剧形式'] !== '') tags.push(ext['电视剧形式']);
            if (ext?.['综艺形式'] && ext['综艺形式'] !== '') tags.push(ext['综艺形式']);
            if (ext?.['地区'] && ext['地区'] !== '') tags.push(ext['地区']);
            if (ext?.['平台'] && ext['平台'] !== '') tags.push(ext['平台']);
            if (ext?.['年代'] && ext['年代'] !== '') tags.push(ext['年代']);
        }
        return tags.join(',');
    }

    switch (tid) {
        case 'hot_gaia':
            let sortType = extend?.sort || 'recommend';
            let area = extend?.area || '全部';
            url = `${BASE_URL}/movie/hot_gaia?apikey=${API_KEY}&sort=${encodeURIComponent(sortType)}&area=${encodeURIComponent(area)}&start=${start}&count=20`;
            break;
        case 'tv_hot':
            let tvType = extend?.type || 'tv_hot';
            url = `${BASE_URL}/subject_collection/${tvType}/items?apikey=${API_KEY}&start=${start}&count=20`;
            itemsKey = 'subject_collection_items';
            break;
        case 'show_hot':
            let showType = extend?.type || 'show_hot';
            url = `${BASE_URL}/subject_collection/${showType}/items?apikey=${API_KEY}&start=${start}&count=20`;
            itemsKey = 'subject_collection_items';
            break;
        case 'tv':
            {
                let sort = extend?.sort || 'T';
                let tagsStr = buildTagsForMovieOrTV('tv', extend);
                url = `${BASE_URL}/tv/recommend?apikey=${API_KEY}&sort=${sort}&tags=${encodeURIComponent(tagsStr)}&start=${start}&count=20`;
            }
            break;
        case 'rank_list_movie':
            let movieRank = extend?.榜单 || 'movie_real_time_hotest';
            url = `${BASE_URL}/subject_collection/${movieRank}/items?apikey=${API_KEY}&start=${start}&count=20`;
            itemsKey = 'subject_collection_items';
            break;
        case 'rank_list_tv':
            let tvRank = extend?.榜单 || 'tv_real_time_hotest';
            url = `${BASE_URL}/subject_collection/${tvRank}/items?apikey=${API_KEY}&start=${start}&count=20`;
            itemsKey = 'subject_collection_items';
            break;
        default:
            {
                let sort = extend?.sort || 'T';
                let tagsStr = buildTagsForMovieOrTV('movie', extend);
                url = `${BASE_URL}/movie/recommend?apikey=${API_KEY}&sort=${sort}&tags=${encodeURIComponent(tagsStr)}&start=${start}&count=20`;
            }
            break;
    }

    let html = await request(url);
    let data = JSON.parse(html);
    let items = data[itemsKey] || [];
    let list = parseItemsToVodList(items);
    let result = {
        page: page,
        pagecount: 999,
        limit: 20,
        total: list.length,
        list: list
    };
    return filterItemsWithoutPic(JSON.stringify(result));
}

async function homeContent() {
    let classes = [
        { type_id: 'hot_gaia', type_name: '热门电影' },
        { type_id: 'tv_hot', type_name: '热播剧集' },
        { type_id: 'anime_hot', type_name: '热门动漫' },
        { type_id: 'show_hot', type_name: '热播综艺' },
        { type_id: 'movie', type_name: '电影筛选' },
        { type_id: 'tv', type_name: '电视筛选' },
        { type_id: 'rank_list_movie', type_name: '电影榜单' },
        { type_id: 'rank_list_tv', type_name: '电视剧榜单' }
    ];

    let hotUrl = `${BASE_URL}/subject_collection/subject_real_time_hotest/items?apikey=${API_KEY}&start=0&count=20`;
    let hotHtml = await request(hotUrl);
    let hotData = JSON.parse(hotHtml);
    let hotItems = hotData.subject_collection_items || [];
    let recommendList = parseItemsToVodList(hotItems);

    let filters = {
        "hot_gaia": [
            { "key": "sort", "name": "排序", "value": [{"n":"热度","v":"recommend"},{"n":"最新","v":"time"},{"n":"评分","v":"rank"}] },
            { "key": "area", "name": "地区", "value": [{"n":"全部","v":"全部"},{"n":"华语","v":"华语"},{"n":"欧美","v":"欧美"},{"n":"韩国","v":"韩国"},{"n":"日本","v":"日本"}] }
        ],
        "tv_hot": [
            { "key": "type", "name": "分类", "value": [{"n":"综合","v":"tv_hot"},{"n":"国产剧","v":"tv_domestic"},{"n":"欧美剧","v":"tv_american"},{"n":"日剧","v":"tv_japanese"},{"n":"韩剧","v":"tv_korean"},{"n":"动画","v":"tv_animation"}] }
        ],
        "anime_hot": [
            { "key": "类型", "name": "类型", "value": [{"n":"全部","v":""},{"n":"热血","v":"热血"},{"n":"搞笑","v":"搞笑"},{"n":"恋爱","v":"恋爱"},{"n":"校园","v":"校园"},{"n":"科幻","v":"科幻"},{"n":"奇幻","v":"奇幻"},{"n":"悬疑","v":"悬疑"},{"n":"治愈","v":"治愈"},{"n":"运动","v":"运动"},{"n":"机甲","v":"机甲"},{"n":"少女","v":"少女"},{"n":"少年","v":"少年"}] },
            { "key": "地区", "name": "地区", "value": [{"n":"全部","v":""},{"n":"日本","v":"日本"},{"n":"中国大陆","v":"中国大陆"},{"n":"美国","v":"美国"},{"n":"韩国","v":"韩国"},{"n":"英国","v":"英国"},{"n":"法国","v":"法国"}] },
            { "key": "sort", "name": "排序", "value": [{"n":"近期热度","v":"T"},{"n":"首播时间","v":"R"},{"n":"高分优先","v":"S"}] },
            { "key": "年代", "name": "年代", "value": [{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2010年代","v":"2010年代"},{"n":"2000年代","v":"2000年代"},{"n":"90年代","v":"90年代"},{"n":"更早","v":"更早"}] }
        ],
        "show_hot": [
            { "key": "type", "name": "分类", "value": [{"n":"综合","v":"show_hot"},{"n":"国内","v":"show_domestic"},{"n":"国外","v":"show_foreign"}] }
        ],
        "movie": [
            { "key": "类型", "name": "类型", "value": [{"n":"全部类型","v":""},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"动作","v":"动作"},{"n":"科幻","v":"科幻"},{"n":"动画","v":"动画"},{"n":"悬疑","v":"悬疑"},{"n":"犯罪","v":"犯罪"},{"n":"惊悚","v":"惊悚"},{"n":"冒险","v":"冒险"},{"n":"音乐","v":"音乐"},{"n":"历史","v":"历史"},{"n":"奇幻","v":"奇幻"},{"n":"恐怖","v":"恐怖"},{"n":"战争","v":"战争"},{"n":"传记","v":"传记"},{"n":"歌舞","v":"歌舞"},{"n":"武侠","v":"武侠"},{"n":"情色","v":"情色"},{"n":"灾难","v":"灾难"},{"n":"西部","v":"西部"},{"n":"纪录片","v":"纪录片"},{"n":"短片","v":"短片"}] },
            { "key": "地区", "name": "地区", "value": [{"n":"全部地区","v":""},{"n":"华语","v":"华语"},{"n":"欧美","v":"欧美"},{"n":"中国","v":"中国"},{"n":"美国","v":"美国"},{"n":"中国香港","v":"中国香港"},{"n":"中国台湾","v":"中国台湾"},{"n":"韩国","v":"韩国"},{"n":"日本","v":"日本"},{"n":"英国","v":"英国"},{"n":"法国","v":"法国"},{"n":"菲律宾","v":"菲律宾"},{"n":"德国","v":"德国"},{"n":"意大利","v":"意大利"},{"n":"西班牙","v":"西班牙"},{"n":"印度","v":"印度"},{"n":"泰国","v":"泰国"},{"n":"俄罗斯","v":"俄罗斯"},{"n":"加拿大","v":"加拿大"},{"n":"澳大利亚","v":"澳大利亚"},{"n":"爱尔兰","v":"爱尔兰"},{"n":"瑞典","v":"瑞典"},{"n":"巴西","v":"巴西"},{"n":"丹麦","v":"丹麦"}] },
            { "key": "sort", "name": "排序", "value": [{"n":"近期热度","v":"T"},{"n":"首映时间","v":"R"},{"n":"高分优先","v":"S"}] },
            { "key": "年代", "name": "年代", "value": [{"n":"全部年代","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2010年代","v":"2010年代"},{"n":"2000年代","v":"2000年代"},{"n":"90年代","v":"90年代"},{"n":"80年代","v":"80年代"},{"n":"70年代","v":"70年代"},{"n":"60年代","v":"60年代"},{"n":"更早","v":"更早"}] }
        ],
        "tv": [
            { "key": "类型", "name": "类型", "value": [{"n":"不限","v":""},{"n":"电视剧","v":"电视剧"},{"n":"综艺","v":"综艺"}] },
            { "key": "电视剧形式", "name": "电视剧形式", "value": [{"n":"不限","v":""},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"悬疑","v":"悬疑"},{"n":"动画","v":"动画"},{"n":"武侠","v":"武侠"},{"n":"古装","v":"古装"},{"n":"家庭","v":"家庭"},{"n":"犯罪","v":"犯罪"},{"n":"科幻","v":"科幻"},{"n":"恐怖","v":"恐怖"},{"n":"历史","v":"历史"},{"n":"战争","v":"战争"},{"n":"动作","v":"动作"},{"n":"冒险","v":"冒险"},{"n":"传记","v":"传记"},{"n":"剧情","v":"剧情"},{"n":"奇幻","v":"奇幻"},{"n":"惊悚","v":"惊悚"},{"n":"灾难","v":"灾难"},{"n":"歌舞","v":"歌舞"},{"n":"音乐","v":"音乐"}] },
            { "key": "综艺形式", "name": "综艺形式", "value": [{"n":"不限","v":""},{"n":"真人秀","v":"真人秀"},{"n":"脱口秀","v":"脱口秀"},{"n":"音乐","v":"音乐"},{"n":"歌舞","v":"歌舞"}] },
            { "key": "地区", "name": "地区", "value": [{"n":"全部地区","v":""},{"n":"华语","v":"华语"},{"n":"欧美","v":"欧美"},{"n":"中国","v":"中国"},{"n":"美国","v":"美国"},{"n":"中国香港","v":"中国香港"},{"n":"韩国","v":"韩国"},{"n":"日本","v":"日本"},{"n":"英国","v":"英国"},{"n":"泰国","v":"泰国"},{"n":"中国台湾","v":"中国台湾"},{"n":"意大利","v":"意大利"},{"n":"法国","v":"法国"},{"n":"德国","v":"德国"},{"n":"西班牙","v":"西班牙"},{"n":"俄罗斯","v":"俄罗斯"},{"n":"瑞典","v":"瑞典"},{"n":"巴西","v":"巴西"},{"n":"丹麦","v":"丹麦"},{"n":"印度","v":"印度"},{"n":"加拿大","v":"加拿大"},{"n":"爱尔兰","v":"爱尔兰"},{"n":"澳大利亚","v":"澳大利亚"}] },
            { "key": "sort", "name": "排序", "value": [{"n":"近期热度","v":"T"},{"n":"首播时间","v":"R"},{"n":"高分优先","v":"S"}] },
            { "key": "年代", "name": "年代", "value": [{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2010年代","v":"2010年代"},{"n":"2000年代","v":"2000年代"},{"n":"90年代","v":"90年代"},{"n":"80年代","v":"80年代"},{"n":"70年代","v":"70年代"},{"n":"60年代","v":"60年代"},{"n":"更早","v":"更早"}] },
            { "key": "平台", "name": "平台", "value": [{"n":"全部","v":""},{"n":"腾讯视频","v":"腾讯视频"},{"n":"爱奇艺","v":"爱奇艺"},{"n":"优酷","v":"优酷"},{"n":"湖南卫视","v":"湖南卫视"},{"n":"Netflix","v":"Netflix"},{"n":"HBO","v":"HBO"},{"n":"BBC","v":"BBC"},{"n":"NHK","v":"NHK"},{"n":"CBS","v":"CBS"},{"n":"NBC","v":"NBC"},{"n":"tvN","v":"tvN"}] }
        ],
        "rank_list_movie": [
            { "key": "榜单", "name": "榜单", "value": [{"n":"实时热门电影","v":"movie_real_time_hotest"},{"n":"一周口碑电影榜","v":"movie_weekly_best"},{"n":"豆瓣电影Top250","v":"movie_top250"}] }
        ],
        "rank_list_tv": [
            { "key": "榜单", "name": "榜单", "value": [{"n":"实时热门电视","v":"tv_real_time_hotest"},{"n":"华语口碑剧集榜","v":"tv_chinese_best_weekly"},{"n":"全球口碑剧集榜","v":"tv_global_best_weekly"},{"n":"国内口碑综艺榜","v":"show_chinese_best_weekly"},{"n":"国外口碑综艺榜","v":"show_global_best_weekly"}] }
        ]
    };

    return JSON.stringify({ class: classes, filters: filters, list: recommendList });
}

async function detail(id) {
    let realId = id.replace(/^msearch:/, '');
    let url = `${BASE_URL}/subject/${realId}?apikey=${API_KEY}`;
    let html = await request(url);
    let data = JSON.parse(html);
    let vod = {
        vod_id: id,
        vod_name: data.title || '',
        vod_pic: data.pic?.normal || data.pic?.large || '',
        vod_remarks: data.rating?.value ? `评分：${data.rating.value}` : '评分：0',
        vod_actor: data.actors?.map(a => a.name).join(' / ') || '',
        vod_director: data.directors?.map(d => d.name).join(' / ') || '',
        vod_content: data.intro || '',
        vod_year: data.year ? String(data.year) : '',
        vod_area: data.countries?.join(' / ') || ''
    };
    vod.vod_play_from = '豆瓣详情';
    vod.vod_play_url = '暂无播放源$#';
    return JSON.stringify({ list: [vod] });
}

async function play(flag, id, flags) {
    return JSON.stringify({ parse: 1, url: '' });
}

async function search(wd, quick, pg) {
    let page = parseInt(pg) || 1;
    let start = (page - 1) * 20;
    let url = `${BASE_URL}/movie/search?apikey=${API_KEY}&q=${encodeURIComponent(wd)}&start=${start}&count=20`;
    let html = await request(url);
    let data = JSON.parse(html);
    let items = data.subjects || [];
    let list = parseItemsToVodList(items);
    let result = {
        page: page,
        pagecount: 999,
        limit: 20,
        total: list.length,
        list: list
    };
    return JSON.stringify(result);
}

async function init() {}

export function __jsEvalReturn() {
    return {
        init,
        home: async function(filter) { return await homeContent(); },
        category: async function(tid, pg, filter, extend) { return await categoryContent(tid, pg, extend); },
        detail: async function(id) { return await detail(id); },
        play: async function(flag, id, flags) { return await play(flag, id, flags); },
        search: async function(wd, quick, pg) { return await search(wd, quick, pg); }
    };
}