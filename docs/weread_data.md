# 小结：目前获得微信阅读信息的几种方式

## 1. 请求书架(`shelf`)

返回数据格式：

```html
<!DOCTYPE html> 
<html lang="zh-cmn"> 
<head></head> 
<body class="wr\_Windows wr\_Desktop wr\_page\_shelf wr\_whiteTheme"> 
  <div id="app" data-server-rendered="true" class="app"> </div> 
  <script nonce="DD49C12D98586D21BF4E409F945608A9"> 
    window.\_\_INITIAL\_STATE\_\_ = { 
      "OS": "Windows", "platform": "desktop", "deviceInfo": "Windows\_desktop", "httpReferer": "https%3A%2F%2Fweread.qq.com%2Fweb%2Fshelf", "error": null, 
      "user": { "vid": 420028218, "skey": "", "name": "", "avatar": "", "gender": 0, "pf": null }, 
      "config": {}, 
      "isWhiteTheme": true, "isNavBarShown": true, "isFooterShown": false, "isShelfFullShown": false, "pageName": "nd\_wrwebnjlogic\_shelf\_index", "pageTitle": "", "pageKeywords": "", "pageDescription": "", "pageBodyClass": "wr\_Windows wr\_Desktop wr\_page\_shelf wr\_whiteTheme", "customReaderStyle": "", "ldJsonPayload": {}, "environment": "production", 
      "sState": { "user": { "vid": { "vid": 501257 }, "avatar": "", "name": "" }, 
      "shelf": { "books": [] } }, 
      "route": { 
        "path": "\\u002Fweb\\u002Fshelf", "hash": "", "query": {}, "params": {}, "fullPath": "\\u002Fweb\\u002Fshelf", "meta": {}, "from": { "name": null, "path": "\\u002F", "hash": "", "query": {}, "params": {}, "fullPath": "\\u002F", "meta": {} } }, "shelf": { "miniShelf": [], "archive": [], "books": [], "uploadCount": 0, "bookProgress": [], "balanceIOS": 0, "balanceAndroid": 0, "memberCardSummary": {}, 
        "booksAndArchives": [{ 
          "bookId": "23976240", 
          "title": "我的名字叫红（珍藏版）", 
          "author": "[土]奥尔罕·帕慕克", 
          "translator": "沈志兴", 
          "cover": "https:\\u002F\\u002Fcdn.weread.qq.com\\u002Fweread\\u002Fcover\\u002F35\\u002FYueWen\_23976240\\u002Ft6\_YueWen\_23976240.jpg", 
          "version": 42857223, 
          "format": "epub", 
          "type": "book", 
          "price": 99, 
          "originalPrice": 0, 
          "soldout": 0, 
          "bookStatus": 1, 
          "payingStatus": 2, 
          "payType": 1048577, 
          "limitShareChat": 0, 
          "centPrice": 9900, 
          "category": "精品小说-社会小说", 
          "categories": [{ "categoryId": 100000, "subCategoryId": 100001, "categoryType": 0, "title": "精品小说-社会小说" }, { "categoryId": 300000, "subCategoryId": 300004, "categoryType": 0, "title": "文学-经典作品" }], 
          "hasLecture": 0, 
          "finished": 1, 
          "maxFreeChapter": 13, 
          "maxFreeInfo": { "maxFreeChapterIdx": 13, "maxFreeChapterUid": 13, "maxFreeChapterRatio": 68 }, 
          "free": 0, 
          "mcardDiscount": 0, 
          "ispub": 1, 
          "extra\_type": 5, 
          "totalWords": 333789, 
          "publishTime": "2018-10-01 00:00:00", 
          "lastChapterIdx": 64, 
          "paperBook": { "skuId": "12445690" }, 
          "copyrightChapterUids": [2], 
          "inStoreBookId": "", 
          "blockSaveImg": 0, 
          "language": "zh", 
          "isTraditionalChinese": false, 
          "hideUpdateTime": false, 
          "isEPUBComics": 0, 
          "isVerticalLayout": 0, 
          "isShowTTS": 1, 
          "webBookControl": 0, 
          "selfProduceIncentive": false, 
          "isAutoDownload": 1, 
          "newRating": 834, 
          "newRatingCount": 2082, 
          "newRatingDetail": { "good": 1757, "fair": 298, "poor": 27, "recent": 32, "title": "脍炙人口" }, 
          "secret": 0, 
          "readUpdateTime": 1774963804, 
          "finishReading": 1, 
          "paid": 0, 
          "updateTime": 1764316600, 
          "lastChapterCreateTime": 0, 
          "bookType": 0, 
          "isAudio": false, 
          "isTrial": false, 
          "hide": false, 
          "indexId": "23976240" },
        {} ]} 
  </script>
<body>
```

## 2. 请求笔记本（`notebooks`）

返回数据格式：

```json
{
    "synckey": 1775010860,
    "totalBookCount": 65,
    "noBookReviewCount": 0,
    "books": [
        {
            "bookId": "27258789",
            "book": {
                "bookId": "27258789",
                "title": "江南三部曲",
                "author": "格非",
                "cover": "https://cdn.weread.qq.com/weread/cover/28/yuewen_27258789/t6_yuewen_272587891720177433.jpg",
                "version": 91768653,
                "format": "epub",
                "type": 0,
                "price": 106.2,
                "originalPrice": 0,
                "soldout": 0,
                "bookStatus": 1,
                "payingStatus": 2,
                "payType": 1048577,
                "centPrice": 10620,
                "categories": [
                    {
                        "categoryId": 100000,
                        "subCategoryId": 100021,
                        "categoryType": 0,
                        "title": "精品小说-年代小说"
                    }
                ],
                "hasLecture": 0,
                "finished": 1,
                "maxFreeChapter": 13,
                "maxFreeInfo": {
                    "maxFreeChapterIdx": 13,
                    "maxFreeChapterUid": 212,
                    "maxFreeChapterRatio": 37
                },
                "free": 0,
                "mcardDiscount": 0,
                "ispub": 1,
                "extra_type": 5,
                "cpid": 24367662,
                "publishTime": "2024-06-01 00:00:00",
                "lastChapterIdx": 165,
                "paperBook": {
                    "skuId": ""
                },
                "copyrightChapterUids": [
                    201,
                    203,
                    253,
                    302
                ],
                "inStoreBookId": "",
                "blockSaveImg": 0,
                "language": "zh",
                "isTraditionalChinese": false,
                "hideUpdateTime": false,
                "isEPUBComics": 0,
                "isVerticalLayout": 0,
                "isShowTTS": 1,
                "webBookControl": 0,
                "selfProduceIncentive": false,
                "isAutoDownload": 1
            },
            "reviewCount": 0,
            "reviewLikeCount": 0,
            "reviewCommentCount": 0,
            "noteCount": 1,
            "bookmarkCount": 0,
            "sort": 1731822010
        },
        {
            "bookId": "3300014124",
            "book": {
                "bookId": "3300014124",
                "title": "亲密关系（第6版）",
                "author": "[美]罗兰·米勒",
                "translator": "王伟平",
                "cover": "https://cdn.weread.qq.com/weread/cover/24/3300014124/t6_3300014124.jpg",
                "version": 1778018734,
                "format": "epub",
                "type": 0,
                "price": 138,
                "originalPrice": 0,
                "soldout": 0,
                "bookStatus": 1,
                "payingStatus": 2,
                "payType": 1048577,
                "centPrice": 13800,
                "categories": [
                    {
                        "categoryId": 800000,
                        "subCategoryId": 800007,
                        "categoryType": 0,
                        "title": "心理-亲密关系"
                    }
                ],
                "hasLecture": 0,
                "finished": 1,
                "maxFreeChapter": 12,
                "maxFreeInfo": {
                    "maxFreeChapterIdx": 12,
                    "maxFreeChapterUid": 110,
                    "maxFreeChapterRatio": 19
                },
                "free": 0,
                "mcardDiscount": 0,
                "ispub": 1,
                "extra_type": 5,
                "cpid": 5256588,
                "publishTime": "2015-06-01 00:00:00",
                "lastChapterIdx": 25,
                "paperBook": {
                    "skuId": ""
                },
                "copyrightChapterUids": [
                    100
                ],
                "inStoreBookId": "",
                "blockSaveImg": 1,
                "language": "zh-CN",
                "isTraditionalChinese": false,
                "hideUpdateTime": false,
                "isEPUBComics": 0,
                "isVerticalLayout": 0,
                "isShowTTS": 1,
                "webBookControl": 0,
                "selfProduceIncentive": false,
                "isAutoDownload": 1
            },
            "reviewCount": 6,
            "reviewLikeCount": 11,
            "reviewCommentCount": 0,
            "noteCount": 75,
            "bookmarkCount": 0,
            "sort": 1711173490
        },
```



## 3. 请求某本书的阅读状态（`redInfo`）

在读中书本返回数据格式，以《江南三部曲》为例：

```json
{
    "bookId": "27258789",
    "book": {
        "appId": "106948369",
        "bookVersion": 2096488054,
        "reviewId": "",
        "chapterUid": 224,
        "chapterOffset": 1149,
        "chapterIdx": 25,
        "updateTime": 1732429732,
        "synckey": 243072567,
        "repairOffsetTime": 0,
        "readingTime": 4506,
        "progress": 8,
        "isStartReading": 1,
        "ttsTime": 102,
        "startReadingTime": 1731821185,
        "installId": "",
        "recordReadingTime": 0
    },
    "canFreeRead": 0,
    "timestamp": 1775020740
}
```

已读完书本返回数据格式，以《无名之毒》为例：

```json
{
    "bookId": "3300024184",
    "book": {
        "appId": "106948369",
        "bookVersion": 554602170,
        "reviewId": "",
        "chapterUid": 30,
        "chapterOffset": 11647,
        "chapterIdx": 30,
        "updateTime": 1705470777,
        "synckey": 876658558,
        "repairOffsetTime": 0,
        "readingTime": 9456,
        "progress": 100,
        "isStartReading": 1,
        "ttsTime": 0,
        "startReadingTime": 1704873719,
        "installId": "",
        "recordReadingTime": 0,
        "finishTime": 1705469233
    },
    "canFreeRead": 0,
    "timestamp": 1775026808
}
```



# DevTools 调试工具

```typescript
async function testGetBookInfo(bookId) {
    try {
        const response = await fetch(`https://weread.qq.com/web/book/getProgress?bookId=${bookId}`, {
            method: 'GET',
            credentials: 'include',  // 携带 Cookie
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            }
        });
        
        if (!response.ok) {
            console.error('请求失败:', response.status);
            return null;
        }
        
        const data = await response.json();
        console.log('API 返回数据:', data);
        return data;
    } catch (error) {
        console.error('请求出错:', error);
        return null;
    }
}

testGetBookInfo('27258789')
```

