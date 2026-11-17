Site fonts
==========

Every font used by the documentation site is served from this directory.
Nothing is loaded from Google Fonts or another font CDN, and no face relies
on fonts installed on the visitor's computer (the @font-face rules use url()
sources only). Families, weights and fallbacks are declared once, in
../typography.css; MathJax reads its STIX2 data through
../../mathjax-config.js (inlined by conf.py).

All files below are copied unmodified from the official distributions.
Archive checksums are SHA-256 of the files as downloaded on 2026-11-17.


stix-two/ -- STIX Two Text and STIX Two Math
--------------------------------------------
Version:  2.13 b171 (name table: "Version 2.13 b171")
Source:   https://github.com/stipub/stixfonts, tag v2.13b171
          (release https://github.com/stipub/stixfonts/releases/tag/v2.13b171;
          the release has no binary assets, the fonts are in the tagged tree)
Archive:  https://github.com/stipub/stixfonts/archive/refs/tags/v2.13b171.zip
          5d5c2c2461747539c4ddd16d38590b1e422fa932d442a214c4d4c5729d5d04d6
Taken from fonts/static_ttf_woff2/ (static, TrueType outlines):
  STIXTwoText-Regular.woff2         400 normal   d44636fb9e8f2b35f5135db71ee5303ab5f8ddb7a43f2eaa6f4d73047cfd7478
  STIXTwoText-Italic.woff2          400 italic   499fe19498b9638373de989eb8b3d32bcda1ea5ddb397cb47cf8c2b99343d284
  STIXTwoText-SemiBold.woff2        600 normal   33342efbfcc280a28a50141714326ee5fd66ec8139db86a9afe1cbcf7b266f51
  STIXTwoText-SemiBoldItalic.woff2  600 italic   f6ef9279a46999c378c43d861a3adefe607f44e54c6eeee2a064c4be222d96e2
  STIXTwoText-Bold.woff2            700 normal   78fc32cd7a02cacb2a6fd4b7fb195c729e4115776aec57a9a3c40395b50a97d3
  STIXTwoText-BoldItalic.woff2      700 italic   f9d16668de9d1f352a2da424b1af7dce81e21808ed66fb7354bbab8781e360c2
  STIXTwoMath-Regular.woff2         400 normal   5f8bdddc067dd82689d7247cc96e0be46fe4cec39974c649866aa391d8d5badd
License:  SIL Open Font License 1.1, stix-two/OFL.txt (from the same tag).


jetbrains-mono/ -- JetBrains Mono
---------------------------------
Version:  2.304 (name table: "Version 2.304")
Source:   https://github.com/JetBrains/JetBrainsMono/releases/tag/v2.304
Archive:  https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip
          6f6376c6ed2960ea8a963cd7387ec9d76e3f629125bc33d1fdcd7eb7012f7bbf
Taken from fonts/webfonts/:
  JetBrainsMono-Regular.woff2       400 normal   a9cb1cd82332b23a47e3a1239d25d13c86d16c4220695e34b243effa999f45f2
  JetBrainsMono-Italic.woff2        400 italic   cb6a1b246318ed3885d7dffa14a2609297fe80e9b8e500bea33b52fa312a36a4
  JetBrainsMono-SemiBold.woff2      600 normal   918edad542a1da608fd2ba8daebaff9ac802309103fe760eed465b8b4e47faf1
  JetBrainsMono-Bold.woff2          700 normal   c503cc5ec5f8b2c7666b7ecda1adf44bd45f2e6579b2eba0fc292150416588a2
License:  SIL Open Font License 1.1, jetbrains-mono/OFL.txt (from the archive).
Note:     the programming ligatures of this font are contextual alternates
          (calt); typography.css switches them off.


mathjax-stix2-font/ -- MathJax 4 STIX2 font data (CHTML output)
---------------------------------------------------------------
Version:  @mathjax/mathjax-stix2-font 4.1.3, used with MathJax 4.1.3
          (MATHJAX_VERSION in conf.py; the two versions must match)
Source:   https://www.npmjs.com/package/@mathjax/mathjax-stix2-font/v/4.1.3
Archive:  https://registry.npmjs.org/@mathjax/mathjax-stix2-font/-/mathjax-stix2-font-4.1.3.tgz
          664c8c40d739a231016cd6108cb6401166151772913e82b802bdd4b64812acf5
          (npm integrity sha512-DjJh93JuKodoYmvWawiqa22y/dwP+hn6/DN/DepFRFaRbdndNcSD3iBsBunSrLPFIJBS83mn4iR015YRPWZWhg==)
Included, with the package's own layout (see
https://docs.mathjax.org/en/latest/web/hosting.html):
  package.json
  chtml.js              font component loaded by tex-mml-chtml-nofont.js
  chtml/dynamic/*.js    25 character ranges, loaded on demand
  chtml/woff2/*.woff2   68 glyph files, loaded on demand
Not included (unused by the CHTML output): svg.js, svg/, cjs/, mjs/, def/,
tsconfig*, examples/ and the combined tex-mml-*-mathjax-stix2.js components.
License:  the package is Apache-2.0 (package.json) but ships no license text;
          mathjax-stix2-font/LICENSE is the Apache-2.0 text from the mathjax
          4.1.3 npm package (same project and license). The woff2 glyphs are
          generated from STIX Two Math and keep its SIL Open Font License 1.1
          (their name table says so); mathjax-stix2-font/OFL.txt is the STIX
          license above.
