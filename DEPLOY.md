# 部署：云端自动更新（电脑关机也跑）

本方案用 **GitHub Actions** 在云端每个交易日自动抓数据更新 `site/data.js`，并用 **GitHub Pages** 发布网页。电脑关机也照常运行，并得到一个公网访问地址。

## 一次性配置（约 3 分钟）

### 1. 创建 GitHub 仓库
登录 https://github.com → New repository → 名称随意（如 `market-brief`），**Public**，**不要**勾选 "Add a README"。点 Create。

### 2. 推送代码
在本项目根目录 `C:\Users\z\WorkBuddy\2026-11-14-05-42-06` 打开 Git Bash（或 PowerShell），执行（把 `你的用户名` 和 `仓库名` 换成你的）：

```bash
git init
git add .
git commit -m "盘前全球市场简报"
git branch -M main
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```
首次推送会让你登录 GitHub（按提示在浏览器授权即可）。

### 3. 开启 GitHub Pages
仓库页面 → **Settings** → 左侧 **Pages** → **Source** 选 **GitHub Actions**。

### 4. 手动触发一次验证
仓库页面 → **Actions** → 左侧选 "每日盘前数据更新与部署" → 右上 **Run workflow** → 等约 2 分钟跑完。

### 5. 访问网页
跑完后，访问：
```
https://你的用户名.github.io/仓库名/
```
这就是你的公网简报地址，可收藏/分享。

## 之后
- 每个交易日（北京时间 周一~周五 08:30）GitHub 云端自动跑脚本更新数据并重新部署。
- **不需要电脑开机**，不需要做任何操作。
- 想立即手动更新：Actions 页面点 Run workflow，或本地双击 `run_daily.bat`。
- 想改关键日程：编辑 `site/events.json` → push（或网页编辑提交），下次自动生效。

## 文件结构
```
site/index.html       页面（深色盘前简报，7段式）
site/data.js          数据快照（由脚本/Actions 自动生成）
site/events.json      关键日程（可编辑）
tools/update_market_data.py   数据抓取脚本（纯标准库，无第三方依赖）
.github/workflows/daily-update.yml   云端定时任务
run_daily.bat         本地一键更新（可选）
```

## 备注
- 页面打开时还会每 10 秒（A股盘中）/15 秒（美股盘中）/60 秒（休市）实时刷新行情，价格变动会闪烁高亮。
- 数据源：东方财富（行情/涨停/板块）、腾讯（A股）、新浪（美股/商品）、华尔街见闻（资讯）；财联社/金十/新华社等反爬较强，作为页脚"信息整合来源"标注。
