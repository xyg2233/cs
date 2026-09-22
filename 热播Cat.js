// by 十一、
// 2025.5.17
import { Crypto, _ } from 'assets://js/lib/cat.js';

let siteUrl = '';
let siteKey = '';
let siteType = 0;
let headers = {
    'User-Agent': 'okhttp-okgo/jeasonlzy',
    'Accept-Language': 'zh-CN,zh;q=0.8'
};

async function request(reqUrl, data, header, method) {
    let res = await req(reqUrl, {
        method: method || 'post',
        data: data || '',
        headers: header || headers,
        postType: 'form',
        timeout: 5000,
    });
    return res.content;
}

async function init(cfg) {
    siteKey = cfg.skey;
    siteType = cfg.stype;
    if (cfg.ext) {
        try {
            let words = Crypto.enc.Base64.parse(cfg.ext);
            siteUrl = words.toString(Crypto.enc.Utf8);
        } catch (e) {
            siteUrl = cfg.ext;
        }
    }
}

function getName() {
}

function isVideoFormat(url) {
}

function manualVideoCheck() {
}

function destroy() {
}

async function home(filter) {
    let files = getFiles({});
    let data = JSON.parse(await request(`${siteUrl}/v3/type/top_type`, files, headers, 'post')).data;
    let classes = [];
    let filters = {};
    
    _.forEach(data.list, k => {
        classes.push({
            type_name: k.type_name,
            type_id: k.type_id
        });
        let fts = [];
        _.forEach(k, (v, i) => {
            if (Array.isArray(v) && v.length > 2) {
                fts.push({
                    name: i,
                    key: i,
                    value: _.map(v.filter(j => j && j !== '全部'), j => ({ n: j, v: j }))
                });
            }
        });
        if (fts.length > 0) {
            filters[k.type_id] = fts;
        }
    });
    
    return JSON.stringify({
        class: classes,
        filters: filters
    });
}

async function homeVod() {
    let files = getFiles({});
    let data = JSON.parse(await request(`${siteUrl}/v3/type/tj_vod`, files, headers, 'post')).data;
    let videos = getV(data.cai.concat(data.loop));
    return JSON.stringify({
        list: videos
    });
}

async function category(tid, pg, filter, extend) {
    if (pg <= 0) pg = 1;
    let files = {
        type_id: tid,
        limit: '12',
        page: pg
    };
    _.forEach(extend, (v, k) => {
        if (k === 'extend') k = 'class';
        files[k] = v;
    });
    files = getFiles(files);
    let data = JSON.parse(await request(`${siteUrl}/v3/home/type_search`, files, headers, 'post')).data;
    let videos = getV(data.list);
    return JSON.stringify({
        list: videos,
        page: parseInt(pg),
        pagecount: 9999,
        limit: 90,
        total: 999999
    });
}



async function detail(id) {
    let files = getFiles({ vod_id: id });
    let data = JSON.parse(await request(`${siteUrl}/v3/home/vod_details`, files, headers, 'post')).data;
    let v = data;
    let vod = {
        vod_name: v.vod_name || '',
        type_name: v.type_name || '',
        vod_year: v.vod_year || '',
        vod_area: v.vod_area || '',
        vod_remarks: v.vod_remarks || '',
        vod_actor: v.vod_actor || '',
        vod_director: v.vod_director || '',
        vod_content: v.vod_content || '无'
    };
    
    let froms = [];
    let urls = [];
    _.forEach(v.vod_play_list, (i, o) => {
        froms.push(`线路${o + 1}(${i.flag || ''})`);
        let c = [];
        _.forEach(i.urls, j => {
            let d = {
                url: j.url || '',
                p: i.parse_urls || [],
                r: i.referer || '',
                u: i.ua || ''
            };
            c.push(`${j.name || ''}$${e64(JSON.stringify(d))}`);
        });
        urls.push(c.join('#'));
    });
    
    vod.vod_play_from = froms.join('$$$');
    vod.vod_play_url = urls.join('$$$');
    
    return JSON.stringify({
        list: [vod]
    });
}

async function search(wd, quick, pg = '1') {
    let files = getFiles({
        limit: '12',
        page: pg,
        keyword: wd
    });
    let data = JSON.parse(await request(`${siteUrl}/v3/home/search`, files, headers, 'post')).data;
    let videos = getV(data.list);
    return JSON.stringify({
        list: videos,
        page: pg
    });
}

async function play(flag, id, vipFlags) {
    let ids;
    try {
        ids = JSON.parse(d64(id));
    } catch (e) {
        return JSON.stringify({ parse: 0, url: '', header: {} });
    }

    if (!ids.url) {
        return JSON.stringify({ parse: 0, url: '', header: {} });
    }

    let url = ids.url;
    let parse = 0;
    let h = {};

    if (ids.r) h['Referer'] = ids.r;
    if (ids.u) h['User-Agent'] = ids.u;

    if (ids.p) {
        let isNbyParse = typeof ids.p === 'string' ? ids.p.includes('nby') : Array.isArray(ids.p) && ids.p.some(p => p.includes('nby'));
        let hasNBY = url.includes('NBY');

        if (isNbyParse && !hasNBY) {
            parse = 0;
            url = ids.url;
        } else {
            parse = 1;
            let parseUrl = '';

            if (typeof ids.p === 'string') {
                parseUrl = ids.p;
            }
            else if (Array.isArray(ids.p)) {
                if (ids.p.length === 1) {
                    parseUrl = ids.p[0];
                } else {
                    parseUrl = ids.p.find(p => hasNBY ? p.includes('nby') : !p.includes('nby')) || ids.p[0];
                }
            }

            url = parseUrl + url;

            let isParseFailed = false;
            try {
                let response = await request(url, null, h, 'get');
                let jsonData = JSON.parse(response);
                if (String(jsonData.code) == '200' && jsonData.url) {
                    url = jsonData.url;
                    parse = 0;
                } else {
                    isParseFailed = true;
                }
            } catch (e) {
                isParseFailed = true;
            }

            if (isParseFailed) {
                url = ids.url;
                parse = /NBY|qq\.com|iqiyi\.com|youku\.com|mgtv\.com|bili\.com/i.test(ids.url) ? 1 : 0;
            }
        }
    } else {
        parse = 0;
    }

    return JSON.stringify({
        parse: parse,
        url: url,
        header: h
    });
}


async function localProxy(param) {
    return JSON.stringify({});
}

async function liveContent(url) {
    return JSON.stringify({});
}

function getFiles(p) {
    let t = Math.floor(Date.now() / 1000).toString();
    let s = md5(`7gp0bnd2sr85ydii2j32pcypscoc4w6c7g5spl${t}`);
    let files = {
        sign: s,
        timestamp: t
    };
    if (p) {
        _.forEach(p, (v, k) => {
            files[k] = v;
        });
    }
    return files;
}

function getV(data) {
    let videos = [];
    _.forEach(data, i => {
        if (i.vod_id && i.vod_id.toString() !== '0') {
            videos.push({
                vod_id: i.vod_id,
                vod_name: i.vod_name || '',
                vod_pic: i.vod_pic || i.vod_pic_thumb || '',
                vod_year: i.tag || '',
                vod_remarks: i.vod_remarks || ''
            });
        }
    });
    return videos;
}

function e64(text) {
    try {
        let textBytes = Crypto.enc.Utf8.parse(text);
        let encoded = Crypto.enc.Base64.stringify(textBytes);
        return encoded;
    } catch (e) {
        return '';
    }
}

function d64(encodedText) {
    try {
        let decoded = Crypto.enc.Base64.parse(encodedText).toString(Crypto.enc.Utf8);
        return decoded;
    } catch (e) {
        return '';
    }
}

function md5(text) {
    return Crypto.MD5(text).toString();
}

export function __jsEvalReturn() {
    return {
        init: init,
        getName: getName,
        isVideoFormat: isVideoFormat,
        manualVideoCheck: manualVideoCheck,
        destroy: destroy,
        home: home,
        homeVod: homeVod,
        category: category,
        detail: detail,
        search: search,
        play: play,
        localProxy: localProxy,
        liveContent: liveContent
    };
}