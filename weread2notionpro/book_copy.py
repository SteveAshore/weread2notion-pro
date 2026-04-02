import pendulum
from weread2notionpro.notion_helper import NotionHelper
from weread2notionpro.weread_api import WeReadApi
from weread2notionpro import utils
from weread2notionpro.config import book_properties_type_dict, tz

TAG_ICON_URL = "https://www.notion.so/icons/tag_gray.svg"
USER_ICON_URL = "https://www.notion.so/icons/user-circle-filled_gray.svg"
BOOK_ICON_URL = "https://www.notion.so/icons/book_gray.svg"
rating = {"poor": "⭐️", "fair": "⭐️⭐️⭐️", "good": "⭐️⭐️⭐️⭐️⭐️"}


# ==================== 数据结构转换函数 ====================

def build_shelf_cache(bookshelf_books):
    """
    将书架数据转换为以 bookId 为键的字典
    
    返回: {bookId: book_data}
    """
    cache = {}
    
    # 从 booksAndArchives 提取（主要数据来源，已经通过get_bookshelf()函数获取）
    for item in bookshelf_books:
        if "bookId" not in item:
            continue
        
        book_id = item.get("bookId")
        # 标准化字段名，统一新旧格式
        cache[book_id] = {
            "bookId": book_id,
            "title": item.get("title"),
            "author": item.get("author"),
            "cover": item.get("cover"),
            "isbn": item.get("isbn"),
            "intro": item.get("intro"),
            "categories": item.get("categories", []),
            "newRating": item.get("newRating"),
            "newRatingDetail": item.get("newRatingDetail"),
            "price": item.get("price"),
            "totalWords": item.get("totalWords"),
            "lastChapterIdx": item.get("lastChapterIdx"),
            "finishReading": item.get("finishReading"),     # 0=未读完, 1=已读完
            "readUpdateTime": item.get("readUpdateTime"),
            "updateTime": item.get("updateTime"),           # 加入书架的时间
            # 标记来源
            "_from_shelf": True,
        }
    
    return cache


def merge_shelf_and_notebook(shelf_cache, notebook_list):
    """
    合并书架数据和笔记本数据
    
    策略：
    - 书架数据为主，包含完整的书籍信息
    - 笔记本数据补充：笔记数量、划线数量、排序时间戳
    - 只在笔记本中但不在书架中的书，也需要处理
    """
    merged = shelf_cache.copy()
    
    for nb in notebook_list:
        book_id = nb.get("bookId")
        if not book_id:
            continue
            
        if book_id in merged:
            # 更新已有数据（补充笔记相关信息）
            merged[book_id]["noteCount"] = nb.get("noteCount", 0)
            merged[book_id]["bookmarkCount"] = nb.get("bookmarkCount", 0)
            merged[book_id]["reviewCount"] = nb.get("reviewCount", 0)
            merged[book_id]["sort"] = nb.get("sort", 0)
        else:
            # 新书（只在笔记本中）
            book = nb.get("book", {})
            merged[book_id] = {
                "bookId": book_id,
                "title": book.get("title"),
                "author": book.get("author"),
                "cover": book.get("cover"),
                "isbn": book.get("isbn"),
                "intro": book.get("intro"),
                "categories": book.get("categories"),
                "newRating": book.get("newRating", 0),
                "newRatingDetail": book.get("newRatingDetail",{}),
                "noteCount": nb.get("noteCount", 0),
                "bookmarkCount": nb.get("bookmarkCount", 0),
                "reviewCount": nb.get("reviewCount", 0),
                "sort": nb.get("sort", 0),
                "price": book.get("price"),
                "totalWords": book.get("totalWords", 0),
                "lastChapterIdx": book.get("lastChapterIdx"),
                "finishReading": book.get("finishReading", 0),     # 0=未读完, 1=已读完
                "readUpdateTime": book.get("readUpdateTime", 0),
                "updateTime": book.get("updateTime", 0),           # 加入书架的时间
                "_from_notebook": True,  # 标记来源
            }
    
    return merged


def parse_read_info(read_info):
    """
    解析阅读进度信息，统一字段名
    
    新 API 返回格式: {book: {readingTime, progress, isStartReading, finishTime, ...}}
    """
    if not read_info or "book" not in read_info:
        return {}
    
    book_data = read_info.get("book", {})
    
    # 提取字段
    readingTime = book_data.get("readingTime", 0)
    progress = book_data.get("progress", 0)
    isStartReading = book_data.get("isStartReading", 0)
    finishTime = book_data.get("finishTime", 0)
    startReadingTime = book_data.get("startReadingTime", 0)
    updateTime = book_data.get("updateTime", 0)
    
    # 推断阅读状态: 1=想读, 2=在读, 4=已读
    if finishTime > 0:
        marked_status = 4  # 已读完
    elif isStartReading == 1 or progress > 0 or readingTime > 0:
        marked_status = 2  # 在读
    else:
        marked_status = 1  # 想读

    # totalReadDay 处理逻辑
    totalReadDay = 0
    if startReadingTime > 0 and finishTime > 0:     # 阅读完的书籍
        totalReadDay = utils.get_days_between(startReadingTime, finishTime)
    elif startReadingTime > 0 and updateTime > 0:   # 在读的书籍
        totalReadDay = utils.get_days_between(startReadingTime, updateTime)
    else:
        totalReadDay = 0
    
    return {
        "readingTime": readingTime,
        "readingProgress": progress,
        "markedStatus": marked_status,
        "totalReadDay": totalReadDay,  # 新 API 不再提供此字段，该字段为计算得出
        "startReadingTime": startReadingTime,
        "updateTime": updateTime,
        "finishedDate": finishTime,
        "_raw": read_info,
    }


# ==================== 业务逻辑函数 ====================

def should_sync_book(book_id, notion_book, shelf_book, read_info):
    """
    判断书籍是否需要同步
    
    返回: (should_sync, reason)
    - 新书：需要同步
    - 已有书：根据阅读时间判断是否变化
    """
    # 新书必须同步
    if notion_book is None:
        return True, "新书"
    
    if not read_info:
        return False, "无阅读信息"
    
    # 检查阅读时间是否变化
    old_time = notion_book.get("readingTime") or 0
    new_time = read_info.get("readingTime") or 0
    print(f"old time: {old_time}, new time: {new_time}")
    
    if new_time > old_time:
        return True, f"阅读时间变化 ({old_time} -> {new_time})"
    
    # 检查阅读进度是否变化。 TODO: 确认notion_book中处理阅读进度的逻辑
    old_progress = (notion_book.get("阅读进度") or 0) * 100
    new_progress = read_info.get("readingProgress") or 0
    print(f"old progress: {old_progress:.1f}, new progress: {new_progress:.1f}")
    
    if abs(new_progress - old_progress) > 1:  # 进度变化超过 1%
        return True, f"阅读进度变化 ({old_progress:.1f}% -> {new_progress:.1f}%)"
    
    # 检查笔记数量是否变化（如果有笔记数据）
    old_note_count = notion_book.get("noteCount", 0)
    new_note_count = read_info.get("noteCount") or 0
    print(f"old note count: {old_note_count}, new note count: {new_note_count}")
    if old_note_count != new_note_count:
        return True, f"笔记数量变化 ({old_note_count} -> {new_note_count})"
    
    # 检查划线数量是否变化（如果有划线数据）
    old_bookmark_count = notion_book.get("bookmarkCount", 0)
    new_bookmark_count = read_info.get("bookmarkCount", 0)
    print(f"old bookmark count: {old_bookmark_count}, new bookmark count: {new_bookmark_count}")
    if old_bookmark_count != new_bookmark_count:
        return True, f"划线数量变化 ({old_bookmark_count} -> {new_bookmark_count})"

    return False, "无需更新"


def prepare_book_data(book_id, shelf_book, read_info, archive_name=None):
    """
    准备要写入 Notion 的书籍数据
    
    合并书架数据和阅读信息，统一字段格式，并过滤掉原始 API 的冗余字段
    """
    # 合并数据（阅读信息优先级更高）
    merge_book = {**shelf_book, **read_info}
    
    # 添加书架分类
    if archive_name:
        merge_book["书架分类"] = archive_name
    
    # 计算阅读状态
    marked_status = merge_book.get("markedStatus", 1)
    if marked_status == 4:
        status = "已读"
    elif marked_status == 2:
        status = "在读"
    else:
        status = "想读"
    merge_book["阅读状态"] = status
    
    # 计算阅读进度（转换为 0-1 的小数）
    merge_book["阅读进度"] = (merge_book.get("readingProgress") or 0) / 100
    
    # 处理封面链接
    cover = (merge_book.get("cover") or "").replace("/s_", "/t7_")
    if not cover or not cover.strip() or not cover.startswith("http"):
        cover = BOOK_ICON_URL
    merge_book["封面"] = cover
    merge_book["cover"] = cover  # 保留辅助键，供创建/更新页面时设置 icon/cover 使用
    
    # 处理评分
    merge_book["评分"] = merge_book.get("newRating")
    newRatingDetail = merge_book.get("newRatingDetail", {})
    myRating = newRatingDetail.get("myRating") if newRatingDetail else None
    if myRating:
        merge_book["我的评分"] = rating.get(myRating, myRating)
    else:
        merge_book["我的评分"] = "未评分"
    
    # 处理阅读时间日期（避免 0 值导致写入 1970-01-01）
    start_time = merge_book.get("startReadingTime")
    if start_time:
        merge_book["开始阅读时间"] = start_time
    
    update_time = merge_book.get("updateTime")
    if update_time:
        merge_book["最后阅读时间"] = update_time
    
    finished_time = merge_book.get("finishedDate")
    if finished_time:
        merge_book["时间"] = finished_time
    
    merge_book["阅读天数"] = merge_book.get("totalReadDay", 0)
    merge_book["阅读时长"] = merge_book.get("readingTime", 0)  # 保持秒为单位，与判断逻辑一致
    
    # 补充缺失的键名映射
    if "sort" in merge_book:
        merge_book["Sort"] = merge_book.get("sort")
    
    # 保留 create_book_page / update_book_page 需要的辅助键，其余过滤
    allowed_keys = set(book_properties_type_dict.keys()) | {"title", "author", "categories", "cover", "isbn", "intro"}
    clean_book = {k: v for k, v in merge_book.items() if k in allowed_keys}
    
    return clean_book


def create_book_page(book_id, book_data, notion_helper, weread_api):
    """
    创建新书到 Notion
    """
    # 准备属性
    properties = {
        "书名": utils.get_title(book_data.get("title")),
        "BookId": utils.get_rich_text(book_id),
        "链接": utils.get_url(weread_api.get_url(book_id)),
    }
    
    # 可选字段
    if book_data.get("isbn"):
        properties["ISBN"] = utils.get_rich_text(book_data.get("isbn"))
    
    if book_data.get("intro"):
        properties["简介"] = utils.get_rich_text(book_data.get("intro"))
    
    # 处理作者关系
    if book_data.get("author"):
        author_names = [x.strip() for x in book_data.get("author").split(" ") if x.strip()]
        author_ids = [
            notion_helper.get_relation_id(name, notion_helper.author_database_id, USER_ICON_URL)
            for name in author_names
        ]
        properties["作者"] = utils.get_relation(author_ids)
    
    # 处理分类关系
    if book_data.get("categories"):
        category_ids = [
            notion_helper.get_relation_id(
                cat.get("title"), notion_helper.category_database_id, TAG_ICON_URL
            )
            for cat in book_data.get("categories")
        ]
        properties["分类"] = utils.get_relation(category_ids)
    
    # 添加其他属性
    other_props = utils.get_properties(book_data, book_properties_type_dict)
    properties.update(other_props)
    
    # 创建页面
    parent = {"database_id": notion_helper.book_database_id, "type": "database_id"}
    result = notion_helper.create_book_page(
        parent=parent,
        properties=properties,
        icon=utils.get_icon(book_data.get("cover")),
    )
    
    return result.get("id")


def update_book_page(book_id, page_id, book_data, notion_helper):
    """
    更新已有的书籍页面
    
    更新内容：阅读状态、进度、时间、评分、封面、作者、分类
    """
    # 准备属性（包含可更新的字段）
    properties = utils.get_properties(book_data, book_properties_type_dict)
    
    # 更新作者关系
    if book_data.get("author"):
        author_names = [x.strip() for x in book_data.get("author").split(" ") if x.strip()]
        author_ids = [
            notion_helper.get_relation_id(name, notion_helper.author_database_id, USER_ICON_URL)
            for name in author_names
        ]
        properties["作者"] = utils.get_relation(author_ids)
    
    # 更新分类关系
    if book_data.get("categories"):
        category_ids = [
            notion_helper.get_relation_id(
                cat.get("title"), notion_helper.category_database_id, TAG_ICON_URL
            )
            for cat in book_data.get("categories")
        ]
        properties["分类"] = utils.get_relation(category_ids)
    
    # 更新页面（包含封面和图标）
    result = notion_helper.update_page(
        page_id=page_id,
        properties=properties,
        cover=utils.get_icon(book_data.get("cover")),
        icon=utils.get_icon(book_data.get("cover")),
    )
    
    return result.get("id")


# ==================== 主函数 ====================

def main():
    # 初始化 API 客户端
    weread_api = WeReadApi()
    notion_helper = NotionHelper()
    
    print("=" * 50)
    print("微信读书书架同步")
    print("=" * 50)
    
    # 1. 获取书架和笔记本数据
    print("\n[1/4] 获取书架数据...")
    bookshelf = weread_api.get_bookshelf()
    shelf_cache = build_shelf_cache(bookshelf)
    print(f"  ✓ 书架书籍: {len(shelf_cache)} 本")
    
    print("\n[2/4] 获取笔记本数据...")
    notebook_list = weread_api.get_notebooklist()
    print(f"  ✓ 笔记本书籍: {len(notebook_list)} 本")
    
    # 合并数据
    all_books = merge_shelf_and_notebook(shelf_cache, notebook_list)
    print(f"  ✓ 合并后书籍: {len(all_books)} 本")
    
    # 处理书架分类（bookshelf 为 booksAndArchives 列表，archive 项为列表中的对象）
    archive_dict = {}
    for item in bookshelf:
        if item.get("type") == "archive" or "bookIds" in item:
            for book_id in item.get("bookIds", []):
                archive_dict[book_id] = item.get("name")
    print(f"  ✓ 书架分类: {len(set(archive_dict.values()))} 个")
    
    # 2. 获取 Notion 已有书籍
    print("\n[3/4] 获取 Notion 已有书籍...")
    notion_books = notion_helper.get_all_book()
    print(f"  ✓ Notion 书籍: {len(notion_books)} 本")
    
    # 3. 分类处理（使用缓存避免重复 API 调用）
    print("\n[4/4] 检查书籍同步状态...")
    new_books = []
    update_books = []
    skip_books = []
    
    # 缓存阅读信息
    read_info_cache = {}
    
    for book_id, book_info in all_books.items():
        # 获取阅读进度（带缓存）
        if book_id not in read_info_cache:
            try:
                read_info_raw = weread_api.get_read_info(book_id)
                print(f"[{book_id}]read_info_raw: {read_info_raw}")
                read_info_cache[book_id] = parse_read_info(read_info_raw)
                print(f"[{book_id}]read_info_cache: {read_info_cache}")
            except Exception as e:
                print(f"  ⚠ 获取阅读信息失败 {book_id}: {e}")
                read_info_cache[book_id] = {}
        
        read_info = read_info_cache[book_id]
        print(f"[{book_id}]read_info: {read_info}")
        notion_book = notion_books.get(book_id)
        should_sync, reason = should_sync_book(book_id, notion_book, book_info, read_info)
        print(f"  [{book_id}],{should_sync},{reason}")

        if not should_sync:
            skip_books.append((book_id, reason))
            continue
        
        # 准备数据
        archive_name = archive_dict.get(book_id)
        book_data = prepare_book_data(book_id, book_info, read_info, archive_name)
        
        if notion_book is None:
            new_books.append((book_id, book_data))
        else:
            update_books.append((book_id, notion_book.get("pageId"), book_data))
    
    print(f"  ✓ 新书: {len(new_books)} 本")
    print(f"  ✓ 需更新: {len(update_books)} 本")
    print(f"  ✓ 跳过: {len(skip_books)} 本")
    
    # 4. 同步到 Notion
    print("\n" + "-" * 50)
    print("开始同步...")
    
    # 创建新书
    for i, (book_id, book_data) in enumerate(new_books, 1):
        try:
            title = book_data.get("title", "未知书名")
            print(f"  [{i}/{len(new_books)}] 创建《{title}》...", end=" ")
            page_id = create_book_page(book_id, book_data, notion_helper, weread_api)
            print("✓")
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    # 更新已有书
    for i, (book_id, page_id, book_data) in enumerate(update_books, 1):
        try:
            title = book_data.get("title", "未知书名")
            print(f"  [{i}/{len(update_books)}] 更新《{title}》...", end=" ")
            update_book_page(book_id, page_id, book_data, notion_helper)
            print("✓")
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    print("\n" + "=" * 50)
    print("同步完成！")
    print(f"  新建: {len(new_books)} 本")
    print(f"  更新: {len(update_books)} 本")
    print(f"  跳过: {len(skip_books)} 本")
    print("=" * 50)


if __name__ == "__main__":
    main()
