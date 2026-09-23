var rule = {
//定义获取目标列表函数
getkvods: function (url, strData) {
    let kvods = [];
    let klists = pdfa(fetch(url), strData);
    klists.map((it) => {
        let [kname, kid] = [pdfh(it, 'div&&Text'), pd(it, 'a&&href', HOST)];
        let kpic = pdfh(fetch(kid), '.video-cover&&img&&src');
        kvods.push({
            vod_name: kname,
            vod_pic: kpic,
            vod_remarks: '急救',
            vod_id: `${kid}@${kname}@${kpic}`
        })
    });
    return kvods
},

author: '小可乐/2505/第一版',
title: '急救指南',
类型: '影视',
host: 'https://m.youlai.cn',
hostJs: '',
headers: {'User-Agent': MOBILE_UA},
编码: 'utf-8',
timeout: 5000,

homeUrl: '/jijiu',
url: '/jijiu?fyclass',
filter_url: '',
searchUrl: '/jijiu?**',
detailUrl: '',

limit: 9,
double: false,
class_name: '急救技能&家庭生活&急危重症&常见损伤&动物致伤&海洋急救&中毒急救&意外事故',
class_url: '1&2&3&4&5&6&7&8',
filter_def: {},
pagecount: {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 1, "8": 1}, 

推荐: $js.toString(() => {
let kk = `.list-br3:contains(人)`;
VODS = rule.getkvods(input, kk)
}),
一级: $js.toString(() => {
let [kurl, kid] = input.split('?');
kid = (Number(kid) - 1);
let kk = `.jj-title-li:eq(${kid})&&.list-br3`;
VODS = rule.getkvods(kurl, kk)
}),
搜索: $js.toString(() => {
let [kurl, kwd] = input.split('?');
let kk = `.list-br3:contains(${kwd})`;
VODS = rule.getkvods(kurl, kk)
}),
二级: $js.toString(() => {
let [kid, kname, kpic] = input.split('@');
let khtml = fetch(kid);
let kurls = pdfa(khtml, '#videoWrap').map((it) => { return pdfh(it, '.video-title&&Text') + '$' + pdfh(it, 'source&&src') }).join('#');
VOD = {
    vod_id: kid,
    vod_name: kname,
    vod_pic: kpic,
    type_name: pdfh(khtml, 'title&&Text').split('_')[1],
    vod_remarks: pdfh(khtml, '.doc-hospital-name&&Text'),
    vod_year: '2023',
    vod_area: '中国',
    vod_lang: '国语',
    vod_director: pdfh(khtml, '.doc-medical-title&&Text'),
    vod_actor: pdfh(khtml, '.doc-name&&Text'),
    vod_content: pdfh(khtml, '.img-text-con&&Text'),
    vod_play_from: '👶急救专线',
    vod_play_url: kurls
}
}),

play_parse: true,
lazy: $js.toString(() => {
let kurl = input;
if (/\.(m3u8|mp4)/.test(kurl)) {
    input = { jx: 0, parse: 0, url: kurl, header: {'User-Agent': MOBILE_UA, 'Referer': getHome(kurl)} }
} else {
    input = { jx: 0, parse: 1, url: kurl }
}
}),

filter: {}
}