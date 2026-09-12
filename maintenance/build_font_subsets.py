"""Split the upstream Source Han Sans CN variable WOFF2 into lazy-loaded ranges.

Usage: python maintenance/build_font_subsets.py SOURCE.woff2
Requires fonttools and brotli. Keep the upstream OFL beside the output.
"""
from pathlib import Path
import sys
from fontTools.ttLib import TTFont
from fontTools import subset

destination = Path(__file__).resolve().parents[1] / 'docs/assets/fonts'
source = Path(sys.argv[1])
with TTFont(source) as font:
    points = sorted(font.getBestCmap())
rules = []
for index in range(0, len(points), 1024):
    chars = points[index:index + 1024]
    name = f'source-han-sans-cn-{index // 1024:02d}.woff2'
    font = TTFont(source)
    options = subset.Options()
    options.flavor = 'woff2'
    cutter = subset.Subsetter(options=options)
    cutter.populate(unicodes=chars)
    cutter.subset(font)
    font.save(destination / name)
    with TTFont(destination / name) as check:
        assert set(chars) <= set(check.getBestCmap())
    rules.append('@font-face {\n'
        '  font-family: "Source Han Sans CN";\n'
        '  font-style: normal; font-weight: 100 900; font-display: swap;\n'
        f'  src: url("{name}") format("woff2");\n'
        f'  unicode-range: U+{chars[0]:X}-{chars[-1]:X};\n'
        '}\n')
    print(name, flush=True)
(destination / 'source-han-sans.css').write_text('\n'.join(rules), encoding='utf-8')
print(f'Verified {len(points)} characters')
