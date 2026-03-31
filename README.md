# 将微信读书划线和笔记同步到Notion

本项目通过 Github Action 每天定时同步微信读书划线到 Notion。

预览效果：[https://malinkang.notion.site/malinkang/534a7684b30e4a879269313f437f2185](https://malinkang.notion.site/9a311b7413b74c8788752249edd0b256?pvs=25)

## 功能特性

- 📚 自动同步微信读书书架和笔记
- 🔄 支持 CookieCloud 自动获取 Cookie（推荐）
- ⏰ 定时同步（可配置 Github Actions 定时任务）
- 📝 自动更新阅读进度和笔记

## 快速开始

### 1. Fork 本仓库

点击右上角 **Fork** 按钮，将本仓库复制到你的 Github 账号下。

### 2. 配置 Notion

#### 2.1 创建 Notion Integration

1. 访问 [Notion Integrations](https://www.notion.so/my-integrations)
2. 点击 **New integration**
3. 填写名称（如 "WeRead Sync"），选择关联的 Workspace
4. 点击 **Submit** 创建
5. 复制 **Internal Integration Token**（格式 `secret_xxx`），这个就是 `NOTION_TOKEN`

![创建 Integration](asset/notion_integration.png)

#### 2.2 复制 Notion 模板

1. 访问 [Notion 模板](https://malinkang.notion.site/9a311b7413b74c8788752249edd0b256?pvs=25)（链接见公众号文章）
2. 点击右上角 **Duplicate** 复制模板到你的 Workspace

#### 2.3 添加 Integration 到页面

1. 在复制的模板页面，点击右上角 **...**（更多）
2. 选择 **Add connections** → 找到你创建的 Integration
3. 点击 **Confirm** 确认

![添加 Integration](asset/add_connection.png)

#### 2.4 获取页面链接

1. 在模板页面，点击 **Share** → **Copy link**
2. 链接格式如：`https://www.notion.so/xxx/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. 复制整段链接作为 `NOTION_PAGE`

### 3. 配置 Cookie（二选一）

#### 方式一：CookieCloud（推荐）

本项目支持通过 [CookieCloud](https://github.com/easychen/CookieCloud) 自动同步浏览器中的微信读书 Cookie，无需手动复制。

**3.1 部署 CookieCloud 服务器**

- 使用官方服务器：`https://cookiecloud.malinkang.com`（默认）
- 或自行部署：[CookieCloud 部署文档](https://github.com/easychen/CookieCloud)

**3.2 安装浏览器插件**

1. 下载 [CookieCloud 插件](https://github.com/easychen/CookieCloud/releases)
2. Chrome/Edge 浏览器打开 `chrome://extensions/`
3. 开启 **开发者模式**
4. 将下载的 `.zip` 文件拖入页面安装

**3.3 配置浏览器插件**

1. 点击浏览器工具栏的 CookieCloud 图标
2. 填写配置：
   - **服务器地址**：`https://cookiecloud.malinkang.com`（或你的服务器）
   - **用户 UUID**：点击生成按钮或自定义（记住这个 UUID）
   - **端对端加密密码**：设置一个强密码（记住这个密码）
3. 点击 **测试连接** 确认配置正确
4. 开启 **同步域名筛选**，添加 `weread.qq.com`
5. 确保已登录 [微信读书](https://weread.qq.com)
6. 点击 **推送** 上传 Cookie

![CookieCloud 配置](asset/cookiecloud_config.png)

**3.4 配置 Github Secrets**

在仓库 **Settings** → **Secrets and variables** → **Actions** → **New repository secret** 中添加：

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `CC_URL` | CookieCloud 服务器地址 | `https://cookiecloud.malinkang.com` |
| `CC_ID` | 用户 UUID | 从浏览器插件复制 |
| `CC_PASSWORD` | 端对端加密密码 | 你设置的密码 |

![配置 Secrets](asset/github_secrets.png)

#### 方式二：手动配置 Cookie（备用）

如果 CookieCloud 不可用，可以手动设置 Cookie：

1. 在浏览器中登录 [微信读书](https://weread.qq.com)
2. 按 **F12** 打开开发者工具
3. 切换到 **Application**（或 **存储**）标签
4. 左侧选择 **Cookies** → `https://weread.qq.com`
5. 复制所有 Cookie，格式为 `name=value; name2=value2`
6. 在 Github Secrets 中添加 `WEREAD_COOKIE`，值为复制的 Cookie 字符串

![手动获取 Cookie](asset/manual_cookie.png)

### 4. 配置其他 Secrets

继续在 Github Secrets 中添加：

| Secret 名称 | 说明 | 获取方式 |
|------------|------|---------|
| `NOTION_TOKEN` | Notion Integration Token | 见 2.1 步骤 |
| `NOTION_PAGE` | Notion 页面链接 | 见 2.4 步骤 |

### 5. 配置 Variables（可选）

如需自定义数据库名称，可在 **Settings** → **Secrets and variables** → **Actions** → **Variables** 中配置：

| Variable 名称 | 默认值 | 说明 |
|--------------|--------|------|
| `BOOK_DATABASE_NAME` | 书架 | 书籍数据库名称 |
| `AUTHOR_DATABASE_NAME` | 作者 | 作者数据库名称 |
| `CATEGORY_DATABASE_NAME` | 分类 | 分类数据库名称 |
| `BOOKMARK_DATABASE_NAME` | 划线 | 划线数据库名称 |
| `REVIEW_DATABASE_NAME` | 笔记 | 笔记数据库名称 |

### 6. 运行同步

#### 6.1 手动触发

1. 进入仓库 **Actions** 标签
2. 选择 **weread note sync** 工作流
3. 点击 **Run workflow** → **Run workflow**
4. 等待运行完成

![手动触发](asset/run_workflow.png)

#### 6.2 查看同步结果

1. 点击运行记录查看详细日志
2. 如果显示 ✅ Cookie 验证成功，表示配置正确
3. 打开你的 Notion 页面查看同步的书籍和笔记

### 7. 定时同步（自动）

项目默认每 2 小时自动同步一次。如需修改：

1. 编辑 `.github/workflows/weread.yml`
2. 修改 `schedule` 部分的 cron 表达式：

```yaml
schedule:
  - cron: '0 */2 * * *'  # 每2小时（默认）
  - cron: '0 0 * * *'    # 每天0点
  - cron: '0 */6 * * *'  # 每6小时
```

cron 格式说明：`分 时 日 月 星期`

## 本地测试

如果你想在本地测试配置是否正确：

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/weread2notion-pro.git
cd weread2notion-pro

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建 .env 文件
cat > .env << EOF
CC_URL=https://cookiecloud.malinkang.com
CC_ID=你的UUID
CC_PASSWORD=你的密码
NOTION_TOKEN=secret_xxx
NOTION_PAGE=https://www.notion.so/xxx
EOF

# 4. 运行测试
python test_cookie.py
```

## 获取教程

> [!IMPORTANT]
> 关注公众号获取视频教程和 Notion 模板链接，后续有更新也会第一时间在公众号里同步。

![扫码_搜索联合传播样式-标准色版](https://github.com/malinkang/weread2notion/assets/3365208/191900c6-958e-4f9b-908d-a40a54889b5e)

## 交流群

> [!IMPORTANT]
> 欢迎加入群讨论。可以讨论使用中遇到的任何问题，也可以讨论 Notion 使用，后续我也会在群中分享更多 Notion 自动化工具。微信群失效的话可以添加我的微信malinkang，我拉你入群。

| 微信群 | QQ群 |
| --- | --- |
| 

 | 

 |

## 常见问题

### Q: CookieCloud 获取失败怎么办？

1. **确认插件配置正确**：
   
   - 服务器地址、UUID、密码是否填写正确
   - 点击「测试连接」查看是否成功
2. **确认已推送 Cookie**：
   
   - 在浏览器插件中点击「推送」按钮
   - 确认 `weread.qq.com` 在同步域名列表中
3. **检查 Github Secrets**：
   
   - `CC_ID` 和 `CC_PASSWORD` 必须与浏览器插件一致
   - 注意区分大小写和空格
4. **查看详细日志**：
   
   - 进入 Actions → 运行记录 → 查看 `Verify Cookie` 步骤日志
5. **本地测试**：
   
   ```bash
   python test_cookie.py
   ```

### Q: 提示 "Cookie 已过期"？

- CookieCloud 会自动同步最新 Cookie，确保浏览器插件保持运行
- 如果长时间未使用微信读书，可能需要重新登录并推送 Cookie
- 检查微信读书网页版是否正常登录

### Q: 同步失败或数据不完整？

- **检查 Notion Token**：确认 Token 格式为 `secret_xxx`
- **检查 Integration 权限**：确认已添加到模板页面（见 2.3 步骤）
- **检查页面链接**：确认 `NOTION_PAGE` 是完整的页面链接
- **查看 Actions 日志**：进入运行记录查看具体错误信息

### Q: 如何停止同步？

1. 进入 **Actions** → **weread note sync**
2. 点击右侧 **...** → **Disable workflow**

### Q: 如何修改同步频率？

编辑 `.github/workflows/weread.yml`，修改 `schedule` 部分的 cron 表达式：

```yaml
schedule:
  - cron: '0 0 * * *'  # 每天0点执行
```

### Q: 同步的书籍不对？

项目默认只同步「已划线」或「有笔记」的书籍。如需同步所有书籍，可修改代码或联系作者。

## 更新日志

### 2024-03

- ✅ 新增 CookieCloud 支持，自动同步 Cookie
- ✅ 新增 Cookie 自动验证和刷新
- ✅ 修复 URL 格式问题
- ✅ 优化日志输出

## 捐赠

如果你觉得本项目帮助了你，请作者喝一杯咖啡，你的支持是作者最大的动力。本项目会持续更新。

| 支付宝支付 | 微信支付 |
| --- | --- |
| 

 | 

 |

## 其他项目

* [WeRead2Notion-Pro](https://github.com/malinkang/weread2notion-pro)
* [WeRead2Notion](https://github.com/malinkang/weread2notion)
* [Podcast2Notion](https://github.com/malinkang/podcast2notion)
* [Douban2Notion](https://github.com/malinkang/douban2notion)
* [Keep2Notion](https://github.com/malinkang/keep2notion)
