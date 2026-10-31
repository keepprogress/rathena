#!/usr/bin/env python3
"""繁中怪物名稱 → db/import/mob_db.yml（只覆蓋 Name / JapaneseName）。

用法：python3 -I gen_mob_db.py <ROchineseRE clone> <rAthena 根目錄>
優先序：
  1. 台服卡片名：道具英文名正好是「怪物英文名 Card」，取台服 itemInfo 的「○○卡片」去掉卡片；同英文名的變體一起套用
  2. mob_names_extra.json（導航表沒有的，Haiku 翻譯）
  3. ROchineseRE 導航表 navi_mob_krpri.lub（GBK，以 AegisName 對照，OpenCC s2tw）
  4. 同英文名、已有 3 的怪物
名稱上限 23 bytes（7 個中文字）。都沒有的新怪物會列出來，翻好加進 mob_names_extra.json 再重跑。
"""
import glob
import json
import re
import sys
from pathlib import Path

import opencc

rocn, root = map(Path, sys.argv[1:3])
here = Path(__file__).resolve().parent


def fits(name):
	return name and len(name.encode()) <= 23 and '�' not in name and not any(c in name for c in '"\n\\')


mobs = [(int(i), a, n.strip().strip('"')) for i, a, n in re.findall(
	r'- Id: (\d+)\n\s+AegisName: (\S+)\n\s+Name: (.+)', (root / 'db/re/mob_db.yml').read_text('utf-8'))]

cc = opencc.OpenCC('s2tw')
t = (rocn / 'client-overlay/data/luafiles514/lua files/navigation/navi_mob_krpri.lub').read_bytes().decode('gbk', errors='replace')
navi = {}
for m in re.finditer(r'\{\s*"\w+",\s*\d+,\s*\d+,\s*\d+,\s*"([^"]*)",\s*"([^"]*)"', t):
	navi.setdefault(m.group(2).upper(), cc.convert(m.group(1)).strip())
names = {i: navi[a.upper()] for i, a, _ in mobs if fits(navi.get(a.upper()))}
known = {}
for i, _, n in mobs:
	if i in names:
		known.setdefault(n, names[i])
names.update({i: known[n] for i, _, n in mobs if i not in names and len(n) > 3 and n in known})

names.update({int(k): v for k, v in json.loads((here / 'mob_names_extra.json').read_text('utf-8')).items()})

t = (rocn / 'SystemEN/tw_SystemEN/LuaFiles514/itemInfo.lua').read_bytes().decode('cp950', errors='replace')
tw_items = {int(i): n.strip() for i, n in re.findall(
	r'\[(\d+)\]\s*=\s*\{\s*unidentifiedDisplayName.*?identifiedDisplayName\s*=\s*"([^"]*)"', t, re.S)}
card = {}
for f in glob.glob(str(root / 'db/re/item_db_*.yml')):
	for i, n in re.findall(r'- Id: (\d+)\n\s+AegisName: \S+\n\s+Name: (.+ Card)\n', open(f, encoding='utf-8').read()):
		z = tw_items.get(int(i), '')
		if z.endswith('卡片'):
			card.setdefault(n.strip().strip('"')[:-5], z[:-2].strip())
names.update({i: card[n] for i, _, n in mobs if fits(card.get(n))})

assert names[1002] == '波利' and names[1389] == '德古拉伯爵'
bad = {i: n for i, n in names.items() if not fits(n)}
assert not bad, bad
missing = [(i, n) for i, _, n in mobs if i not in names]
if missing:
	print(f'沒有中文名（維持英文）：{len(missing)} 隻，例：{missing[:10]}', file=sys.stderr)

lines = [
	'# 繁中怪物名稱：只覆蓋 Name / JapaneseName，其他欄位沿用上游 db/re/mob_db.yml。',
	'# 來源優先序：台服 itemInfo 的卡片名（○○卡片 → ○○）> ROchineseRE 導航表 navi_mob_krpri（簡轉繁）> Haiku 翻譯；',
	'# 名稱上限 23 bytes（7 個中文字）。',
	'# 生怪腳本寫死的英文名由 conf/import/battle_conf.txt 的 override_mob_names: 1 蓋掉。',
	'',
	'Header:',
	'  Type: MOB_DB',
	'  Version: 5',
	'',
	'Body:',
]
for i in sorted(names):
	q = json.dumps(names[i], ensure_ascii=False)
	lines += [f'  - Id: {i}', f'    Name: {q}', f'    JapaneseName: {q}']
out = root / 'db/import/mob_db.yml'
out.write_text('\n'.join(lines) + '\n', 'utf-8', newline='\n')
print(f'{out}: {len(names)} 隻怪物')
