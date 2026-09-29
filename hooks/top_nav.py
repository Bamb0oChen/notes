"""Keep only the headbar curated; MkDocs still builds every folder's children."""


def on_nav(nav, *, config, files):
    order = config.extra.get('top_tabs', [])
    labels = config.extra.get('top_tab_labels', {})
    positions = {name: index for index, name in enumerate(order)}

    def key(item):
        return item.file.src_uri if item.is_page else item.title

    original = list(nav.items)
    nav.items = sorted((item for item in original if key(item) in positions),
                       key=lambda item: positions[key(item)])
    for item in nav.items:
        item_key = key(item)
        if item_key in labels:
            item.title = labels[item_key]

    def pages(items):
        for item in items:
            if item.is_page:
                yield item
            elif item.children:
                yield from pages(item.children)

    nav.pages = list(pages(nav.items))
    for index, page in enumerate(nav.pages):
        page.previous_page = nav.pages[index - 1] if index else None
        page.next_page = nav.pages[index + 1] if index + 1 < len(nav.pages) else None
    return nav
