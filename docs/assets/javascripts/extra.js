// Material for MkDocs 自定义 JS 入口。
// 注意：尽量保持轻量；需要时再加。

// LaTeX / 数学公式渲染（MathJax 3）
// 说明：该配置必须在加载 MathJax 主脚本之前执行。
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true,
    processEnvironments: true,
  },
  options: {
    // 仅处理 pymdownx.arithmatex 标记出来的节点，避免误伤代码块等
    ignoreHtmlClass: '.*',
    processHtmlClass: 'arithmatex',
  },
};
