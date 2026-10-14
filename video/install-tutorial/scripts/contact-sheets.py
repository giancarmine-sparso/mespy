"""Optional: assemble decoded QA frames at their native 800-pixel width (Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw

for folder in sorted(Path('out/qa').glob('mespy-install-*')):
    frames = sorted(folder.glob('[0-9][0-9].png'))
    if len(frames) != 15:
        raise RuntimeError(f'{folder}: expected 15 decoded frames, found {len(frames)}')
    for start in range(0, 15, 3):
        sheet = Image.new('RGB', (800, 3 * 480), '#121717')
        draw = ImageDraw.Draw(sheet)
        for row, file in enumerate(frames[start:start+3]):
            frame = Image.open(file)
            assert frame.size == (800, 450)
            sheet.paste(frame, (0, row * 480))
            draw.text((12, row * 480 + 458), f'{folder.name} / {(start+row)*2:02d} s', fill='#ffffff')
        sheet.save(folder / f'sheet-{start//3+1}.png')
