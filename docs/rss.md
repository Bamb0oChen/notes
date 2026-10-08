---
title: 最近文章与 RSS 订阅
description: 预览最近发布和更新的笔记，并获取 RSS 订阅地址。
---

订阅范围有“杂谈随想”和“全部文件夹”，各可选择新增、修改或全部，共 6 个预设。“全部”包含新增和修改，不推送删除；列表筛选不影响订阅范围。

<a href="../feed_rss_updated.xml" type="application/rss+xml">订阅最近更新</a>

<a href="../feed_rss_essays.xml" type="application/rss+xml">订阅杂谈文章</a>（包含杂谈文章和随想，按更新时间排列。）

<div class="notes-rss-filters">
  <label class="notes-rss-filter">筛选文件夹：<select id="rss-folder"><option value="">全部文件夹</option></select></label>
  <label class="notes-rss-filter">筛选状态：<select id="rss-state"><option value="">全部状态</option><option value="add">add</option><option value="modify">modify</option><option value="delete">delete</option></select></label>
</div>

<div class="notes-rss-subscription">
  <label>订阅范围：<select id="rss-preset"><option value="">全部文件夹</option></select></label>
  <label>订阅状态：<select id="rss-preset-state"><option value="">全部</option><option value="add">add（新增）</option><option value="modify">modify（修改）</option></select></label>
  <a id="rss-subscribe" type="application/rss+xml" hidden>订阅当前预设</a>
  <button id="rss-copy" type="button" hidden>复制订阅地址</button>
  <input id="rss-subscription-url" type="url" readonly aria-label="当前预设的 RSS 订阅地址" hidden>
  <span id="rss-copy-status" role="status"></span>
</div>

<div class="notes-rss-preview" data-changes="changes.json">
  <p class="notes-rss-preview__status">正在加载最近变更…</p>
</div>

<script src="../assets/javascripts/rss-preview.js" defer></script>
