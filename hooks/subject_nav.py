"""Keep the automatically discovered subject sections in the requested order."""


def on_nav(nav, config, files):
    subject_order = {
        "自然科学基础": ("数学基础", "物理学", "普通化学", "大学生生物学"),
        "社会科学基础": ("宏观经济学",),
        "语言": ("English", "日本語"),
    }
    for section in nav.items:
        order = subject_order.get(section.title)
        if order and getattr(section, "children", None):
            rank = {title: index for index, title in enumerate(order)}
            section.children.sort(key=lambda child: rank.get(child.title, len(rank)))
    tabs = ("自然科学基础", "社会科学基础", "语言")
    nav.items.sort(key=lambda item: tabs.index(item.title) if item.title in tabs else len(tabs))
    return nav
