<template>
  <div class="docsify-shell">
    <div id="docsify-app"></div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';

function forceNoTopGap() {
  // 某些主题/插件会在运行时给 body/main/content 加 padding-top 留出导航空间
  // 这里用 inline style 兜底，确保“顶格排布”。
  document.body.style.paddingTop = '0px';
  document.body.style.marginTop = '0px';

  const main = document.querySelector('main');
  if (main) {
    main.style.paddingTop = '0px';
    main.style.marginTop = '0px';
  }

  const content = document.querySelector('.content');
  if (content) {
    content.style.paddingTop = '0px';
    content.style.marginTop = '0px';
  }
}

function setupDocsifyConfig() {
  window.$docsify = {
    name: '学习笔记',
    repo: '',
    el: '#docsify-app',
    basePath: (() => {
      const path = location.pathname;
      let base = path;
      if (base.endsWith('.html')) {
        base = base.replace(/\/[^/]*$/, '/');
      }
      if (!base.endsWith('/')) {
        base += '/';
      }
      return base;
    })(),
    loadSidebar: true,
    loadNavbar: true,
    alias: {
      '/.*/_sidebar.md': '/_sidebar.md',
      '/.*/_navbar.md': '/_navbar.md'
    },
    subMaxLevel: 0,
    sidebarDisplayLevel: 1,
    homepage: 'README.md',
    coverpage: false,
    auto2top: true,
    disableAnchors: true,
    markdown: {
      breaks: true
    },
    toc: {
      tocMaxLevel: 5,
      target: 'h1, h2, h3, h4, h5, h6'
    },
    search: {
      maxAge: 86400000,
      paths: 'auto',
      placeholder: '搜索笔记...',
      noData: '未找到结果',
      depth: 6,
      hideOtherSidebarContent: false
    }
  };
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.body.appendChild(script);
  });
}

function disableHeadingLinks() {
  const headingLinks = document.querySelectorAll(
    '.markdown-section h1 a, .markdown-section h2 a, .markdown-section h3 a, .markdown-section h4 a, .markdown-section h5 a, .markdown-section h6 a'
  );
  headingLinks.forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      event.stopPropagation();
      return false;
    });
  });
}

function setupMutationObserver() {
  const observer = new MutationObserver(() => {
    disableHeadingLinks();
    forceNoTopGap();
  });

  if (document.body) {
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
}

function setupSidebarToggles() {
  const tocToggle = document.createElement('div');
  tocToggle.className = 'sidebar-toggle-right';
  tocToggle.setAttribute('aria-label', '切换右侧目录');
  document.body.appendChild(tocToggle);

  setTimeout(() => {
    const pageToc = document.querySelector('.page_toc');
    if (pageToc) {
      tocToggle.addEventListener('click', () => {
        pageToc.classList.toggle('show');
      });
    }

    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('show');
      });
    }
  }, 500);
}

async function bootDocsify() {
  setupDocsifyConfig();
  await loadScript('https://cdn.jsdelivr.net/npm/docsify@4');
  await loadScript('https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-python.min.js');
  await loadScript('https://cdn.jsdelivr.net/npm/docsify@4/lib/plugins/search.js');
  await loadScript('https://unpkg.com/docsify-plugin-toc@1.3.1/dist/docsify-plugin-toc.min.js');

  disableHeadingLinks();
  forceNoTopGap();
  setupMutationObserver();
  setupSidebarToggles();
}

onMounted(() => {
  bootDocsify();
});
</script>
