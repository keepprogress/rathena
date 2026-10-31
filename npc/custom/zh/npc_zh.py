#!/usr/bin/env python3
"""NPC 腳本中文化工具：只換顯示用字串，程式碼一個字元都不動。

  python3 npc/custom/zh/npc_zh.py extract <上游 npc 檔>...          # 列出還沒翻譯的字串（JSON）
  python3 npc/custom/zh/npc_zh.py apply <上游 npc 檔>...            # 依翻譯記憶產生 npc/custom/zh/<原路徑>
  python3 npc/custom/zh/npc_zh.py merge <翻譯 JSON>...              # 把 {原文: 譯文} 檢查後併入翻譯記憶
  python3 npc/custom/zh/npc_zh.py check <翻譯 JSON>...              # 只檢查，不寫入

翻譯記憶在 npc/custom/zh/translations.json（{原文: 譯文}）。
上游改版後重跑 extract → 翻譯新字串 → merge → apply 即可。
NPC 名稱沿用對話標頭的「[名字]」譯文；太長或要跟標頭不同時另設「#名字」。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ZH_DIR = ROOT / 'npc/custom/zh'
MEMORY = ZH_DIR / 'translations.json'

# 只有這些指令的字串會顯示給玩家
DISPLAY = re.compile(
	r'^\s*(mes|mesf|npctalk|dispbottom|announce|mapannounce|areaannounce|message|unittalk|showscript)\b'
	r'|\b(select|prompt|Disp)\s*\(|^\s*menu\b')  # Disp 是 custom/warper.txt 組選單的函式
STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')
# 譯文必須原樣保留的記號：格式佔位符、顏色碼、客戶端標籤（<NAVI> 等）與 <INFO> 裡的座標/ID
KEEP = re.compile(r'%[-+ #0]*\d*(?:\.\d+)?[sdifxXuc%]|\^[0-9A-Fa-f]{6}|<INFO>[^<]*</INFO>|</?[A-Z]+>')
# 放在地圖上的 NPC 標頭；浮動 NPC（-）與 function 沒有看得到的名字
HEADER = re.compile(
	r'^((?!function\t)[^/\t-][^\t]*\t(?:script|duplicate\([^)]*\)|shop|cashshop|itemshop|pointshop|marketshop|trader)\t)'
	r'([^\t]+)(?=\t)')
NAME_BYTES = 23  # 名稱封包 24 位元組含結尾 0，超過會把中文字切半

def strip_comment(line):
	"""回傳去掉 // 註解後的長度（略過字串內的 //）。"""
	in_str = False
	i = 0
	while i < len(line):
		c = line[i]
		if c == '\\' and in_str:
			i += 2
			continue
		if c == '"':
			in_str = not in_str
		elif not in_str and line.startswith('//', i):
			return i
		i += 1
	return len(line)


def display_strings(text):
	"""逐行找顯示用字串，回傳 [(行號, 起點, 終點, 內容)]；跳過 /* */ 區塊註解。"""
	found = []
	in_block = False
	cont = False  # 上一行的顯示指令以 , 或 + 結尾，跨到這一行（多行 menu）
	for n, line in enumerate(text.split('\n')):
		if in_block:
			if '*/' in line:
				in_block = False
			continue
		if line.lstrip().startswith('/*') and '*/' not in line:
			in_block = True
			continue
		code = line[:strip_comment(line)]
		shown, cont = cont or DISPLAY.search(code), code.rstrip().endswith((',', '+'))
		if not shown:
			cont = False
			continue
		for m in STRING.finditer(code):
			# 含非 UTF-8 位元組（韓文資源名）的字串不碰；F_InsertComma、ama_fild 這類函式名/地圖代號也不碰
			if (re.search(r'[A-Za-z]', m.group(1)) and not re.search('[\udc80-\udcff]', m.group(1))
					and not re.fullmatch(r'\w*_\w*', m.group(1))):
				found.append((n, m.start(1), m.end(1), m.group(1)))
	return found


assert [s for *_, s in display_strings(
	'menu "A",L1,\n\t"B",L2;\nset .@a$,"x";\nmes "Cost "+callfunc("F_InsertComma",1);\nDisp("C:D"); Pick("","ama_fild01");')
] == ['A', 'B', 'Cost ', 'C:D']


def name_key(disp):
	return disp if disp.startswith('[') else f'[{disp}]'


def npc_name(name, memory):
	"""回傳中文化的 NPC 名稱，沒有譯文回傳 None。寫成「中文#後綴::原唯一名」：
	#後綴留給 strnpcinfo(2) 組名稱，donpcevent、duplicate 等照舊用原唯一名。"""
	shown, _, unique = name.partition('::')
	disp, sharp, tag = shown.partition('#')
	if not re.search('[A-Za-z]', disp):
		return None
	zh = memory.get('#' + disp) or memory.get(name_key(disp), '')
	if zh and not disp.startswith('[') and not memory.get('#' + disp):
		zh = zh[1:-1]
	if not zh:
		return None
	if len(zh.encode()) > NAME_BYTES:
		print(f'名稱太長，請在翻譯記憶加 "#{disp}": {zh}', file=sys.stderr)
		return None
	return f'{zh}{sharp}{tag}::{unique or name}'


assert npc_name('Lumin#ac', {'[Lumin]': '[露敏]'}) == '露敏#ac::Lumin#ac'
assert npc_name('Kafra::kaf_1', {'[Kafra]': '[卡普拉]', '#Kafra': '卡普拉職員'}) == '卡普拉職員::kaf_1'
assert npc_name('[Armory]#a', {'[Armory]': '[軍械室]'}) == '[軍械室]#a::[Armory]#a'
assert npc_name('#hidden', {}) is None and npc_name('Nobody', {}) is None


def check(src, dst):
	"""譯文要保留原文的佔位符、顏色碼、選單 ':' 與前後空白，也不能引入未跳脫的引號。"""
	if sorted(KEEP.findall(src)) != sorted(KEEP.findall(dst)):
		return 'placeholder/color/tag mismatch'
	if src.count(':') != dst.count(':') and src.count(':') > 0:
		return 'menu separator count mismatch'
	if re.search(r'(?<!\\)"', dst) or dst.endswith('\\'):
		return 'unescaped quote/backslash'
	if (src[:1] == ' ') != (dst[:1] == ' ') or (src[-1:] == ' ') != (dst[-1:] == ' '):
		return 'leading/trailing space mismatch'
	return None


def load_memory():
	return json.loads(MEMORY.read_text('utf-8')) if MEMORY.exists() else {}


def main():
	cmd, args = sys.argv[1], sys.argv[2:]
	memory = load_memory()
	if cmd == 'extract':
		todo = {}
		for path in args:
			text = Path(path).read_text('utf-8', errors='surrogateescape')
			for *_, s in display_strings(text):
				if s not in memory:
					todo[s] = ''
			for line in text.split('\n'):
				if (m := HEADER.match(line)):
					disp = m.group(2).split('::')[0].split('#')[0]
					if re.search('[A-Za-z]', disp) and not npc_name(m.group(2), memory):
						todo['#' + disp if name_key(disp) in memory else name_key(disp)] = ''
		print(json.dumps(todo, ensure_ascii=False, indent=0))
	elif cmd in ('merge', 'check'):
		bad = 0
		for path in args:
			for src, dst in json.loads(Path(path).read_text('utf-8', errors='surrogateescape')).items():
				err = check(src, dst) if dst else 'empty'
				if err:
					bad += 1
					print(f'skip ({err}): {src!r} -> {dst!r}', file=sys.stderr)
				else:
					memory[src] = dst
		if cmd == 'merge':
			MEMORY.write_text(json.dumps(memory, ensure_ascii=False, indent='\t', sort_keys=True) + '\n', 'utf-8')
		print(f'memory {len(memory)}, rejected {bad}')
	elif cmd == 'apply':
		for path in args:
			src_path = (ROOT / path).resolve()
			text = src_path.read_text('utf-8', errors='surrogateescape')  # 保留韓文資源名等非 UTF-8 位元組
			lines = text.split('\n')
			hits = display_strings(text)
			done = 0
			for n, a, b, s in reversed(hits):  # 由後往前換，位置才不會跑掉
				if s in memory:
					lines[n] = lines[n][:a] + memory[s] + lines[n][b:]
					done += 1
			names = 0
			for n, line in enumerate(lines):
				if (m := HEADER.match(line)) and (zh := npc_name(m.group(2), memory)):
					lines[n] = m.group(1) + zh + line[m.end():]
					names += 1
			out = ZH_DIR / src_path.relative_to(ROOT / 'npc')
			out.parent.mkdir(parents=True, exist_ok=True)
			out.write_text('\n'.join(lines), 'utf-8', errors='surrogateescape')
			print(f'{out.relative_to(ROOT)}: {done}/{len(hits)} 句已翻譯, NPC 名稱 {names}')
	else:
		sys.exit(__doc__)


if __name__ == '__main__':
	main()
