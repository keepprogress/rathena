#!/usr/bin/env python3
"""把 kRO 介面貼圖上的韓文字換成繁中：找出字的範圍、逐列用左右底色補平、再寫上中文。

用法：python gen_tex.py <韓文貼圖目錄> <輸出目錄>
兩個目錄都以「texture/유저인터페이스/」為根，路徑與 roBrowser 請求的相同。
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc'
MAGENTA = (255, 0, 255)  # 客戶端的透明色

# (路徑規則, 中文, 版型, 搜尋範圍)；先比對到的先用，所以特例要排前面
# 版型 button = 漸層底 + 深色字；flat = 洋紅透明底 + 單色字；vertical = 直排分頁，| 分隔各頁由上而下
LABELS = [
	(r'achievement_re/btn_receive_', '領取獎勵', 'button', None),
	(r'bank/btn_1000mil_', '1000萬', 'flat', None),
	(r'bank/btn_100mil_', '100萬', 'flat', None),
	(r'bank/btn_10mil_', '10萬', 'flat', None),
	(r'bank/btn_deposit_', '存款', 'button', None),
	(r'bank/btn_withdraw_', '提款', 'button', None),
	(r'basic_interface/btn_(close|ok)', '關閉', 'button', None),  # 這組 btn_ok 圖上寫的是「닫기」
	(r'basic_interface/cancel2', '取消', 'button', None),
	(r'basic_interface/del', '刪除', 'button', None),
	(r'basic_interface/inputzeny', '輸入金額', 'button', None),
	(r'basic_interface/remail', '回覆', 'button', None),
	(r'basic_interface/return', '退回', 'button', None),
	(r'rodexsystem/renewal/btn_delete_', '刪除', 'button', None),
	(r'rodexsystem/renewal/btn_reply_', '回覆', 'button', None),
	(r'basic_interface/send', '寄送', 'button', None),
	(r'basic_interface/setzeny', '確定', 'button', None),
	(r'^btn_apply', '套用', 'button', None),
	(r'^btn_big_cancel', '取消', 'button', None),
	(r'^btn_big_change', '變更', 'button', None),
	(r'^btn_big_next', '下一步', 'button', None),
	(r'^btn_big_ok', '確定', 'button', None),
	(r'^btn_big_unused', '不使用', 'button', None),
	(r'^btn_buy', '購買', 'button', None),
	(r'^btn_cancel_res', '取消預約', 'button', None),
	(r'^btn_cancel', '取消', 'button', None),
	(r'^btn_close', '關閉', 'button', None),
	(r'^btn_del_res', '預約刪除', 'button', None),
	(r'^btn_del', '刪除', 'button', None),
	(r'^btn_disband', '解散公會', 'button', None),
	(r'^btn_edit', '編輯', 'button', None),
	(r'^btn_exchange', '交換', 'button', None),
	(r'^btn_feed', '餵食', 'button', None),
	(r'^btn_make', '製作', 'button', None),
	(r'^btn_next', '下一步', 'button', None),
	(r'^btn_ok', '確定', 'button', None),
	(r'^btn_q_active', '啟用', 'button', None),
	(r'^btn_reset', '重設', 'button', None),
	(r'^btn_rewrite', '修改', 'button', None),
	(r'^btn_sell', '販賣', 'button', None),
	(r'^btn_skill', '技能', 'button', None),
	(r'^btn_use', '使用', 'button', None),
	(r'^btn_view', '檢視', 'button', None),
	(r'^esc_01', '回到角色選擇', 'button', None),
	(r'^esc_02', '返回遊戲', 'button', None),
	(r'^esc_03', '離開遊戲', 'button', None),
	(r'^esc_04', '重新開始', 'button', None),
	(r'^esc_05', '原地復活', 'button', None),
	(r'^esc_06', '畫面設定', 'button', None),
	(r'^esc_07', '音效設定', 'button', None),
	(r'^esc_08', '快捷鍵設定', 'button', None),
	(r'guild_helper/btn_ok', '確定', 'button', None),
	(r'guild_helper/create_guild', '建立公會', 'button', None),
	(r'inventory/btn_close_', '關閉', 'button', None),
	(r'lapine/btn_cancel_', '取消', 'button', None),
	(r'lapine/btn_make_', '製作', 'button', None),
	(r'login_interface/btn_connect', '連線', 'button', None),
	(r'login_interface/btn_exit', '結束', 'button', None),
	(r'login_interface/btn_request', '申請', 'button', None),
	(r'login_interface/chk_save', '記住', 'flat', (10, 0, 34, 10)),  # 左邊 10px 是勾選框；10px 高只能用無反鋸齒粗體
	(r'make_character/btn_create_', '建立', 'button', None),
	(r'^win_msgbox', '訊息', 'button', (16, 1, 140, 16)),  # 只換標題列，避開左邊的圓形圖示
	(r'basic_interface/tab_que_0[123]', '進行|保留|全部', 'vertical', None),  # 任務視窗左側分頁
	# 新版任務視窗整張背景，只處理左側分頁條；第四頁程式裡叫 cooldown
	(r'renew_questui/bg_quest[1234]\.', '進行中|推薦|保留中|冷卻中', 'vertical', (0, 20, 30, 430)),
]


def tc_font(size):
	for index in range(10):
		font = ImageFont.truetype(FONT, size, index=index)
		if font.getname()[0] == 'Noto Sans CJK TC':
			return font
	raise SystemExit('找不到 Noto Sans CJK TC')


def lum(c):
	return (299 * c[0] + 587 * c[1] + 114 * c[2]) // 1000


def fit(label, max_w, max_h):
	for size in range(max_h + 4, 6, -1):
		font = tc_font(size)
		box = font.getbbox(label)
		if box[2] - box[0] <= max_w and box[3] - box[1] <= max_h:
			return font, box
	return font, box


def bbox(points):
	xs, ys = [p[0] for p in points], [p[1] for p in points]
	return min(xs), min(ys), max(xs), max(ys)


def vertical(im, labels):
	"""直排分頁：深色字擦成同列的分頁底色，依垂直間隔分組後逐字直排寫上。"""
	px = im.load()
	w, h = im.size
	text = [(x, y) for y in range(h) for x in range(w) if px[x, y] != MAGENTA and lum(px[x, y]) < 150]
	rows = sorted({y for _, y in text})
	groups = [[rows[0]]]
	for y in rows[1:]:
		if y - groups[-1][-1] > 7:  # 字與字間隔 ≤5 列，分頁之間 ≥9 列
			groups.append([])
		groups[-1].append(y)
	if len(groups) != len(labels):
		raise ValueError(f'找到 {len(groups)} 個分頁，預期 {len(labels)}')
	colors = {p: px[p] for p in text}
	for x, y in text:
		fill = next(px[x + d * s, y] for d in range(1, w) for s in (-1, 1)
			if 0 <= x + d * s < w and px[x + d * s, y] != MAGENTA and lum(px[x + d * s, y]) > 230)
		px[x, y] = fill
	tabs = [[p for p in text if ys[0] <= p[1] <= ys[-1]] for ys in groups]
	glyph = max(bbox(pts)[2] - bbox(pts)[0] + 1 for pts in tabs)  # 照原字寬選字級
	font, box = fit('進', glyph + 2, glyph)
	step = box[3] - box[1] + 1
	draw = ImageDraw.Draw(im)
	for pts, label in zip(tabs, labels):
		x0, y0, x1, y1 = bbox(pts)
		color = max(set(colors[p] for p in pts), key=[colors[p] for p in pts].count)
		cx, cy = (x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2
		for i, ch in enumerate(label):
			b = font.getbbox(ch)
			y = cy + (i - (len(label) - 1) / 2) * step
			draw.text((cx - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2), ch, font=font, fill=color)


def convert(im, label, kind, region):
	if kind == 'vertical':
		box = region or (0, 0, *im.size)
		tabs = im.crop(box)
		vertical(tabs, label.split('|'))
		return im.paste(tabs, box[:2])
	px = im.load()
	w, h = im.size
	x0, y0, x1, y1 = region or (3, 2, w - 3, h - 2)  # 內縮避開按鈕邊框
	area = [(x, y) for x in range(x0, x1) for y in range(y0, y1) if px[x, y] != MAGENTA]
	if kind == 'flat':
		text = area
		color = max(set(px[p] for p in text), key=[px[p] for p in text].count)
		for p in text:
			px[p] = MAGENTA
	else:
		levels = sorted(lum(px[p]) for p in area)
		bg = levels[len(levels) // 2]
		text = [p for p in area if lum(px[p]) < bg - 45]
		dark = sorted(text, key=lambda p: lum(px[p]))
		color = px[dark[len(dark) // 3]]
	if not text:
		raise ValueError('找不到字')
	tx0, ty0, tx1, ty1 = bbox(text)
	if kind == 'button':
		# 逐列在字的左右兩側取底色做線性補間，保留按鈕的漸層；
		# 外擴 2px 連字的淺色陰影一起蓋掉，取樣點才不會落在陰影上
		ex0, ex1 = max(tx0 - 3, x0 - 1), min(tx1 + 3, x1)
		for y in range(max(ty0 - 2, y0), min(ty1 + 3, y1)):
			left, right = px[ex0, y], px[ex1, y]
			for x in range(ex0 + 1, ex1):
				t = (x - ex0) / (ex1 - ex0)
				px[x, y] = tuple(round(left[i] * (1 - t) + right[i] * t) for i in range(3))
	# 容許超出範圍 1px：10px 高的勾選框選 9px 字會糊，10px 粗體被切 1px 反而清楚
	font, box = fit(label, x1 - x0 - 2, min(ty1 - ty0 + 2, y1 - y0 + 1))
	cx, cy = (tx0 + tx1 + 1) / 2, (ty0 + ty1 + 1) / 2
	if region is None:
		cx = w / 2  # 按鈕字一律水平置中
	draw = ImageDraw.Draw(im)
	if kind == 'flat':
		draw.fontmode = '1'  # 透明底不能有反鋸齒，否則邊緣會變洋紅色
	draw.text((cx - (box[0] + box[2]) / 2, cy - (box[1] + box[3]) / 2), label, font=font, fill=color)


def main():
	src, dst = Path(sys.argv[1]), Path(sys.argv[2])
	done = 0
	for path in sorted(p.relative_to(src).as_posix() for p in src.rglob('*.bmp')):
		rule = next((r for r in LABELS if re.search(r[0], path)), None)
		if not rule:
			continue
		im = Image.open(src / path).convert('RGB')
		convert(im, *rule[1:])
		out = dst / path
		out.parent.mkdir(parents=True, exist_ok=True)
		im.save(out, 'BMP')
		done += 1
	print(f'{done} 張')


if __name__ == '__main__':
	main()
