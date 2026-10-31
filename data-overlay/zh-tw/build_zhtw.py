#!/usr/bin/env python3
"""把 ROchineseRE 的 GBK 簡中文字表轉成台灣繁體 Big5，產生 roBrowser 的 DATA_OVERRIDE_PATH。

用法：python3 -I build_zhtw.py <ROchineseRE clone> <客戶端 data/> <kRO msgstringtable.csv> <中文貼圖目錄> <輸出目錄>
輸出目錄會先清空，再放入客戶端 data/ 的散檔、轉好的文字表與中文貼圖。
kRO msgstringtable.csv 取自 data.grf（overlay 還沒有 csv 時 curl 遠端 client 的 /data/msgstringtable.csv）。
中文貼圖由 gen_tex.py 產生，目錄以 texture/유저인터페이스/ 為根。
"""
import base64
import re
import shutil
import subprocess
import sys
from pathlib import Path

import opencc

rocn, client_data, kro_csv, tex_zh, out = map(Path, sys.argv[1:6])
src_root = rocn / 'client-overlay/data'
TW = rocn / 'data'
LUA = 'luafiles514/lua files/'
LUA_TABLES = ('skillinfoz/skillinfolist', 'skillinfoz/skilldescript', 'stateicon/stateiconinfo',
              'datainfo/addrandomoptionnametable', 'datainfo/titletable', 'worldviewdata/worldviewdata_language')
# 只挑純文字表；petinfo 這類含韓文資源名的檔不碰（資源名必須維持 EUC-KR）
# 值是台服原檔：有的優先用台服（用語才對得上台版），沒有才用簡中轉繁
FILES = {
	'msgstringtable.txt': None,
	'mapnametable.txt': 'mapnametable.txt/tw_mapnametable.txt',
	'cardprefixnametable.txt': 'cardprefixnametable.txt/tw_cardprefixnametable.txt',
	'questid2display.txt': 'questid2display.txt/tw_questid2display.txt',
	**{LUA + m + '.lua': 'luafiles514/tw_lua files/' + m + '.lua' for m in LUA_TABLES},
}
# 非 ASCII 字串旁邊出現檔名副檔名 = 可能是韓文資源路徑，寧可整檔放棄
RESOURCE = re.compile(rb'[\x80-\xff][^\n]*\.(bmp|tga|spr|act|str|wav)\b', re.I)

cc = opencc.OpenCC('s2twp')
assert cc.convert('服务器连接失败') == '伺服器連線失敗'


def big5(s):
	return s.encode('cp950', errors='replace')


LUA_TOKEN = re.compile(r'--\[(=*)\[|--[^\n]*|\[(=*)\[|["\']')


def lua_big5(text):
	"""Lua 原始碼轉 Big5。Big5 第二位元組可能是 0x5C（「功」「許」），在一般字串裡會吃掉下一個字元，
	所以只在 "..." / '...' 裡補成 \\；註解與長字串 [[ ]] 不處理跳脫，原樣輸出。"""
	out, i = [], 0
	while (m := LUA_TOKEN.search(text, i)):
		out.append(big5(text[i:m.end()]))
		tok, j = m.group(), m.end()
		if tok in '"\'':
			while text[j] != tok:
				if text[j] == '\\':  # 原本就有的跳脫序列照抄
					out.append(big5(text[j:j + 2]))
					j += 2
					continue
				c = big5(text[j])
				out.append(c + b'\\' if len(c) == 2 and c[1] == 0x5C else c)
				j += 1
			out.append(big5(tok))
			j += 1
		elif m.group(1) is not None or m.group(2) is not None:
			close = ']' + (m.group(1) if m.group(1) is not None else m.group(2)) + ']'
			k = text.index(close, j) + len(close)
			out.append(big5(text[j:k]))
			j = k
		i = j
	out.append(big5(text[i:]))
	return b''.join(out)


def merge_lines(base, tw):
	"""以 # 前的 key 對齊，台服有的行換成台服（位元組原樣保留，台服檔有 cp950 解不開的擴充字）。"""
	tw_lines = {}
	for line in tw.splitlines():
		key = line.split(b'#')[0].strip().lower()
		if key:
			tw_lines.setdefault(key, line)
	out = []
	for line in base.splitlines(keepends=True):
		body = line.rstrip(b'\r\n')
		out.append(tw_lines.get(body.split(b'#')[0].strip().lower(), body) + line[len(body):])
	return b''.join(out)


def merge_quests(base, tw):
	"""questid2display 每筆是「ID#」開頭、6 個 # 欄位（說明可跨行），以任務 ID 對齊換成台服。
	roBrowser 依 # 計數解析，欄位數不對的台服紀錄不能用，否則後面全部錯位。"""
	def split(text):
		return re.split(r'(?m)^(?=\d+#)', text)
	tw_recs = {rec.split('#')[0]: rec.rstrip() + '\n\n'
	           for rec in split(re.sub(r'(?m)^[ \t]*//.*$', '', tw)) if rec.count('#') == 6}  # 台服檔夾有 // 分類註解
	return ''.join(tw_recs.get(rec.split('#')[0], rec) if rec.count('#') == 6 else rec for rec in split(base))


def on_off(text):
	"""台服訊息的開關狀態寫成 On/Off，中文句子裡的換成開啟/關閉；純英文的指令說明不動。
	不用 \\b：中文字算 \\w，「功能On Off」中間沒有字界。"""
	if not re.search(r'[一-鿿]', text):
		return text
	text = re.sub(r'(?i)(?<![a-z])on[ /]off(?![a-z])', '開/關', text)
	return re.sub(r'(?<![A-Za-z])(On|ON|Off|OFF)(?![A-Za-z])',
	              lambda m: '開啟' if m.group().lower() == 'on' else '關閉', text)


assert on_off('技能On Off') == '技能開/關' and on_off('[/nt ON] ') == '[/nt ON] '
assert on_off('自動拒絕[/nt ON]') == '自動拒絕[/nt 開啟]' and on_off('討伐計次 Off') == '討伐計次 關閉'
assert on_off('Zoom Out 功能 (On)') == 'Zoom Out 功能 (開啟)'
assert lua_big5('a = "功" -- 功\nb = [[功]]') == b'a = "\xa5\\\\" -- \xa5\\\nb = [[\xa5\\]]'
assert merge_lines(b'a#1#\r\nb#2#\r\n', b'b#X#') == b'a#1#\r\nb#X#\r\n'
assert merge_quests('1#a#b#c#d#e#\n\n2#f#g#h#i#j#\n', '2#F#G#H#I#J#\n') == '1#a#b#c#d#e#\n\n2#F#G#H#I#J#\n\n'

shutil.rmtree(out, ignore_errors=True)
shutil.copytree(client_data, out)
for src, tw_src in FILES.items():
	raw = (src_root / src).read_bytes()
	tw = (TW / tw_src).read_bytes() if tw_src else None
	if RESOURCE.search(raw) or (tw and RESOURCE.search(tw)):
		sys.exit(f'{src}: 疑似含韓文資源路徑，停止')
	if src.endswith('.lua'):
		text = tw.decode('cp950') if tw else cc.convert(raw.decode('gbk'))
		data = lua_big5(text)
	elif src == 'questid2display.txt':
		data = big5(merge_quests(cc.convert(raw.decode('gbk')), tw.decode('cp950')))
	else:
		data = big5(cc.convert(raw.decode('gbk')))
		if tw:
			data = merge_lines(data, tw)
	if src == 'msgstringtable.txt':
		assert data.count(b'\n') == raw.count(b'\n'), '以行號為索引，行數不能變'
	target = out / (src[:-4] + '.lub' if src.endswith('.lua') else src)
	target.parent.mkdir(parents=True, exist_ok=True)
	target.write_bytes(data)
	if src.endswith('.lua') and shutil.which('luac5.1'):
		subprocess.run(['luac5.1', '-p', target], check=True)
	print(f'{target.relative_to(out)}: {len(data)} bytes, {"台服" if tw else "簡中轉繁"}')


def csv_rows(path):
	for line in path.read_text('utf-8-sig').splitlines():
		key, _, value = line.strip().partition(',')
		if value and not key.startswith('//'):
			yield key, value.split(',')[0]


# roBrowser 讀完 txt 會再讀 csv 蓋掉，而且 csv 只看行序不看 key：
# 以 kRO 原檔為骨架按 key 換成翻譯，行序才會對上這版客戶端；值是 base64 的 UTF-8，不需轉 Big5
# 優先用台服原文（盜賊、刺客等台服譯名），沒有才用簡中轉繁
tw = dict(csv_rows(rocn / 'data/msgstringtable.csv/tw_msgstringtable.csv'))
zh = dict(csv_rows(src_root / 'msgstringtable.csv'))
# 台服留英文、但遊戲畫面看得到的（導航與世界地圖的勾選框）
OVERRIDES = {'MSI_NAVIGATION_NPC': 'NPC', 'MSI_NAVIGATION_MOB': '魔物'}
lines, from_tw, missing = [], 0, 0
for key, value in csv_rows(kro_csv):
	try:
		text = base64.b64decode(tw[key]).decode('utf-8')
		from_tw += 1
	except (KeyError, ValueError):
		missing += key not in zh
		text = cc.convert(base64.b64decode(zh.get(key, value)).decode('utf-8'))
	text = OVERRIDES.get(base64.b64decode(key).decode(), text)
	lines.append(key + ',' + base64.b64encode(on_off(text).encode('utf-8')).decode())
# roBrowser 以檔尾是否為 '=' 判斷 base64 格式，'//' 開頭的行會被略過
if not lines[-1].endswith('='):
	lines.append('//=')
(out / 'msgstringtable.csv').write_text('\n'.join(lines) + '\n', 'utf-8')
print(f'msgstringtable.csv: {len(lines)} 行, 台服 {from_tw}, 無翻譯保留韓文 {missing}')

# remote client 拿 URL 解碼後的路徑直接查覆蓋目錄，而 roBrowser 送的是 EUC-KR 當 Latin-1 的寫法
ui_dir = out / 'texture' / '유저인터페이스'.encode('cp949').decode('latin1')
shutil.copytree(tex_zh, ui_dir, dirs_exist_ok=True)
print(f'中文貼圖: {sum(1 for _ in tex_zh.rglob("*.bmp"))} 張')
