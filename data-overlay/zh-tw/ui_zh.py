#!/usr/bin/env python3
"""roBrowser 介面上寫死的英文（HTML 樣板、JS 的訊息/選單/提示）→ 繁中（台服用語）。

有 msgstringtable 編號的字（data-text、<ui-text>、DB.getMessage）已經走台服 msgstringtable.csv，這裡只換寫死的。
  python3 -I ui_zh.py extract <src>          # 列出還沒翻譯的字串（JSON）；src = roBrowser clone（未 apply 前）
  python3 -I ui_zh.py auto <rocn> <src>      # 同上，但只列台服 msgstringtable 英中對照查得到的（附譯文）
  python3 -I ui_zh.py merge <翻譯 JSON>...    # 把 {原文: 譯文} 檢查後併入翻譯記憶
  python3 -I ui_zh.py check <翻譯 JSON>...    # 只檢查，不寫入
  python3 -I ui_zh.py apply <src>            # 就地改寫 src（docker build 前跑；可重複跑）

翻譯記憶在同目錄 ui_translations.json（{原文: 譯文}）；譯文等於原文 = 不翻（程式用字串、按鍵名）。
同一句在不同視窗意思不同時，用「檔名|原文」當 key 只套在那個檔（例：Storage.html|Upgrade）。
apply 會改到 robrowser-caddo.patch 碰的檔，重產 patch 要從乾淨 clone + patch 產生，不要含翻譯。
"""
import base64
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEMORY = HERE / 'ui_translations.json'
# DB/ 是資料表（技能、地圖等由客戶端 lub 蓋掉），Vendors/ 是第三方函式庫
SKIP_DIRS = ('src/DB/', 'src/Vendors/')
# 例外：世界地圖的地名寫死在這裡（auto 依地圖 id 對台服 mapnametable）
WORLDMAP = 'src/DB/Map/WorldMap.js'
WORLDMAP_NAME = re.compile(r'\bname\s*:')

HTML_TOKEN = re.compile(r'<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|<[^>]*>', re.S | re.I)
HTML_ATTR = re.compile(r'\b(?:title|placeholder|alt)\s*=\s*"([^"]*)"')
HTML_BUTTON = re.compile(r'<input\b[^>]*\btype\s*=\s*"(?:button|submit|reset)"', re.I)
HTML_VALUE = re.compile(r'\bvalue\s*=\s*"([^"]*)"')

# 這些呼叫/屬性所在的那一行（含跨行的引數）裡的字串會顯示給玩家
JS_DISPLAY = re.compile(
	r'\b(?:addText|show(?:Message|Prompt|Error|Confirm)Box|addElement|setStatus|setTitle|alert|confirm)\s*\('
	r'|\.(?:textContent|innerText|innerHTML|placeholder|title)\s*\+?='
	r'|\b(?:title|label|description|message|tooltip|text|placeholder|header)\s*:'
	r'|setAttribute\(\s*[\'"](?:title|placeholder)'
	r'|getMessage\(\s*\d+\s*,')
JS_STRING = re.compile(r"""'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"|`((?:[^`\\\n]|\\.)*)`""")
# 緊接在這些後面的字串是程式用的（元件名、選擇器、比較、物件 key）
JS_CODE_BEFORE = re.compile(
	r'(?:getComponent|querySelector(?:All)?|getElementById|closest|matches|add|remove|toggle|contains'
	r'|(?:add|remove)EventListener|dispatchEvent|getItem|setItem|get|set|has|import|require|startsWith'
	r'|endsWith|includes|indexOf|split|join|replace|createElement|getAttribute|setAttribute)\s*\(\s*$'
	r'|(?:===?|!==?|\bcase|\bin|\[)\s*$')
JS_CODE_AFTER = re.compile(r'\s*(?:===?|!==?|\]|\bin\b)')
JS_KEY = (re.compile(r'[{,]\s*$'), re.compile(r'\s*:'))  # { 'key': ... }，三元運算的 ? 'a' : 'b' 不算
# 像識別字/路徑/選擇器的不算
CODE_LIKE = re.compile(
	r'^[a-z][\w-]*$|^[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+$|^[^\s]*[./][^\s]*$|^[#.\[]|^\w+\(|^[A-Z0-9_]+$')
# 譯文必須原樣保留：模板與格式佔位符、HTML 標籤與實體、跳脫字元、快捷鍵
KEEP = re.compile(
	r'\$\{[^}]*\}|%[-+ #0]*\d*(?:\.\d+)?[sdifxXuc%]|<[^>]+>|&#?\w+;|\\.|\{\d+\}'
	r'|\b(?:Alt|Ctrl|Shift)\s*\+\s*[^\s)]+|\bEsc\b')


def wanted(s):
	s = KEEP.sub(' ', s).strip()  # 只剩 ${…}、標籤的不算
	return re.search(r'[A-Za-z]{2}', s) and not CODE_LIKE.search(s) and not re.search(r'[{};]', s)


def html_strings(text):
	"""回傳 [(起點, 終點, 內容)]：標籤間文字（去頭尾空白）、title/placeholder/alt、按鈕的 value。"""
	found = []

	def text_node(a, b):
		s = text[a:b]
		core = s.strip()
		if core and wanted(core) and '{{' not in core:
			start = a + len(s) - len(s.lstrip())
			found.append((start, start + len(core), core))

	pos = 0
	for m in HTML_TOKEN.finditer(text):
		text_node(pos, m.start())
		tag = m.group()
		if not tag.startswith(('<!--', '<script', '<style', '<SCRIPT', '<STYLE')):
			attrs = list(HTML_ATTR.finditer(tag)) + (list(HTML_VALUE.finditer(tag)) if HTML_BUTTON.match(tag) else [])
			found += [(m.start() + a.start(1), m.start() + a.end(1), a.group(1)) for a in attrs if wanted(a.group(1))]
		pos = m.end()
	text_node(pos, len(text))
	return found


def strip_comment(line):
	"""回傳去掉 // 註解後的長度（略過字串內的 //）。"""
	quote = None
	i = 0
	while i < len(line):
		c = line[i]
		if quote:
			if c == '\\':
				i += 1
			elif c == quote:
				quote = None
		elif c in '\'"`':
			quote = c
		elif line.startswith('//', i):
			return i
		i += 1
	return len(line)


def js_strings(text, display=JS_DISPLAY):
	"""回傳 [(起點, 終點, 內容)]：顯示用呼叫那幾行裡的字串；跳過 /* */ 區塊註解。"""
	found = []
	in_block = False
	depth = 0  # 顯示用呼叫的括號還沒關，下一行也算
	offset = 0
	for line in text.split('\n'):
		start, offset = offset, offset + len(line) + 1
		if in_block:
			in_block = '*/' not in line
			continue
		if line.lstrip().startswith('/*') and '*/' not in line:
			in_block = True
			continue
		code = line[:strip_comment(line)]
		m = display.search(code)
		if m:
			depth = code[m.start():].count('(') - code[m.start():].count(')')
		elif depth > 0:
			depth += code.count('(') - code.count(')')
		else:
			continue
		for s in JS_STRING.finditer(code):
			i = next(g for g in (1, 2, 3) if s.group(g) is not None)
			v = s.group(i)
			before = code[:s.start()]
			if (wanted(v) and not JS_CODE_BEFORE.search(before) and not JS_CODE_AFTER.match(code, s.end())
					and not (JS_KEY[0].search(before) and JS_KEY[1].match(code, s.end()))):
				found.append((start + s.start(i), start + s.end(i), v))
	return found


def sources(src):
	for p in sorted(Path(src).glob('src/**/*')):
		rel = p.relative_to(src).as_posix()
		if rel == WORLDMAP:
			yield p, lambda text: js_strings(text, WORLDMAP_NAME)
		elif p.suffix in ('.html', '.js') and not rel.startswith(SKIP_DIRS):
			yield p, (html_strings if p.suffix == '.html' else js_strings)


def read(p):
	return p.read_bytes().decode('utf-8', errors='surrogateescape')  # bytes 進出，CRLF 原樣保留


def key(s):
	return re.sub(r'\s+', ' ', s)  # 跨行的 HTML 文字併成一行；JS 字串頭尾空白要留著


def check(src, dst):
	"""譯文要保留原文的佔位符、標籤、快捷鍵與前後空白，也不能多出未跳脫的引號。"""
	if sorted(KEEP.findall(src)) != sorted(KEEP.findall(dst)):
		return 'placeholder/tag/hotkey mismatch'
	if re.search('[\'"`]', KEEP.sub('', dst)) and not re.search('[\'"`]', KEEP.sub('', src)):
		return 'unescaped quote'
	if (src[:1] == ' ') != (dst[:1] == ' ') or (src[-1:] == ' ') != (dst[-1:] == ' '):
		return 'leading/trailing space mismatch'
	return None


def msgstring_pairs(rocn):
	"""台服 msgstringtable 的英中對照：同一個 MSI key 的 en/tw 字串（base64）。"""
	def table(name):
		rows = (line.split(',') for line in (rocn / 'data/msgstringtable.csv' / name).read_text('ascii').split())
		return {k: base64.b64decode(v).decode('utf-8', errors='replace') for k, v in rows}
	en, tw = table('en_msgstringtable.csv'), table('tw_msgstringtable.csv')
	votes = collections.defaultdict(collections.Counter)
	for k, e in en.items():
		if k in tw and tw[k].strip():
			votes[norm(e)][tw[k].strip()] += 1
	return {e: c.most_common(1)[0][0] for e, c in votes.items()}


def worldmap_names(rocn, src):
	"""世界地圖 {英文地名: 台服地名}：同一筆的 id 查台服 mapnametable（cp950，地圖id.rsw#地名#）。"""
	tw = {}
	for line in (rocn / 'data/mapnametable.txt/tw_mapnametable.txt').read_bytes().decode('cp950', 'replace').splitlines():
		f = line.split('#')
		if len(f) > 2 and f[1].strip():
			tw.setdefault(f[0].strip().lower(), key(f[1].strip()))
	names = {}
	for i, q, n in re.findall(r"id: '([^']+)',[^{}]*?\bname: (['\"])((?:(?!\2)[^\\]|\\.)*)\2", read(src / WORLDMAP)):
		z = tw.get(i.lower() + '.rsw')
		if z:
			num = re.search(r'\b\d{1,2}\b', n)  # 台服同一區的各號原野同名，編號照英文補上
			names.setdefault(key(n), z + (' ' + num.group() if num and not re.search(r'\d', z) else ''))
	return names


def norm(s):
	return key(s).lower().rstrip(' .:')


# 自我檢查：顯示用字串抓得到（含跨行引數），元件名、選項 value、非顯示行的字串不會被抓
assert [s for *_, s in html_strings('<b title="Close">Base Lv. <i>x</i></b><option value="BASE">Base</option>')] == [
	'Close', 'Base Lv.', 'Base']
assert [s for *_, s in js_strings("ContextMenu.addElement('View Status', f);\nUIManager.getComponent('WinPopup');\n"
	"x = a ? 'Yes' : 'No';\nshowMessageBox(\n\t'Two lines', { 'Key': 1 }\n);")] == ['View Status', 'Two lines']


def main():
	cmd, args = sys.argv[1], sys.argv[2:]
	memory = json.loads(MEMORY.read_text('utf-8')) if MEMORY.exists() else {}
	if cmd in ('extract', 'auto'):
		if cmd == 'auto':
			rocn = Path(args.pop(0))
			pairs, world = msgstring_pairs(rocn), worldmap_names(rocn, Path(args[0]))
		else:
			pairs = world = None
		todo = {}
		for p, find in sources(Path(args[0])):
			for *_, s in find(read(p)):
				k = key(s)
				if k in memory or k in todo:
					continue
				if pairs is None:
					todo[k] = ''
				elif k in world:
					todo[k] = world[k]
				elif norm(k) in pairs:
					tail = k[len(k.rstrip(' .:')):]
					todo[k] = pairs[norm(k)] + (tail if ':' in tail else '')
		print(json.dumps(todo, ensure_ascii=False, indent=0))
	elif cmd in ('merge', 'check'):
		bad = 0
		for path in args:
			for src, dst in json.loads(Path(path).read_text('utf-8')).items():
				err = check(src.split('|', 1)[-1] if re.match(r'[\w.]+\.(?:html|js)\|', src) else src, dst) if dst else 'empty'
				if err:
					bad += 1
					print(f'skip ({err}): {src!r} -> {dst!r}', file=sys.stderr)
				else:
					memory[src] = dst
		if cmd == 'merge':
			MEMORY.write_text(json.dumps(memory, ensure_ascii=False, indent='\t', sort_keys=True) + '\n', 'utf-8')
		print(f'memory {len(memory)}, rejected {bad}')
	elif cmd == 'apply':
		files = done = 0
		for p, find in sources(Path(args[0])):
			text = read(p)
			hits = [(a, b, z) for a, b, s in find(text)
				if (z := memory.get(f'{p.name}|{key(s)}', memory.get(key(s), key(s)))) != key(s)]
			for a, b, t in reversed(hits):  # 由後往前換，位置才不會跑掉
				text = text[:a] + t + text[b:]
			if hits:
				p.write_bytes(text.encode('utf-8', errors='surrogateescape'))
				files += 1
				done += len(hits)
		print(f'{done} 處、{files} 個檔已翻譯')
	else:
		sys.exit(__doc__)


if __name__ == '__main__':
	main()
