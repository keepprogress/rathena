#!/usr/bin/env python3
"""台服道具名稱 → db/import/item_db.yml（只覆蓋 Name，Buy/Sell 照抄上游）。

用法：python3 -I gen_item_db.py <ROchineseRE clone> <rAthena 根目錄>
來源是 ROchineseRE 的 SystemEN/tw_SystemEN/LuaFiles514/itemInfo.lua（cp950）的 identifiedDisplayName；
台服沒有的道具維持英文。同步上游後重跑（上游改價時，舊檔會把價格蓋回去）。
"""
import glob
import json
import re
import sys
from pathlib import Path

rocn, root = map(Path, sys.argv[1:3])
t = (rocn / 'SystemEN/tw_SystemEN/LuaFiles514/itemInfo.lua').read_bytes().decode('cp950', errors='replace')
tw = {}
for i, n in re.findall(r'\[(\d+)\]\s*=\s*\{\s*unidentifiedDisplayName.*?identifiedDisplayName\s*=\s*"([^"]*)"', t, re.S):
	n = n.strip()
	if n and n != '(null)' and '�' not in n and '\\' not in n:
		tw[int(i)] = n
# rAthena 每讀到一筆（含 import 覆蓋）就重設「有沒有寫 Buy/Sell」的旗標，載入完才用它補算另一個價格；
# 覆蓋時漏寫會讓只有 Buy 的道具賣店 0 Zeny、只有 Sell 的道具買價 0，所以照抄上游原本寫的 Buy/Sell。
prices = {}
for f in glob.glob(str(root / 'db/re/item_db_*.yml')):
	for block in open(f, encoding='utf-8').read().split('\n  - Id: ')[1:]:
		i = int(block.split('\n', 1)[0].split('#')[0])
		prices[i] = re.findall(r'\n    ((?:Buy|Sell): \d+)', block)
names = {i: tw[i] for i in sorted(set(prices) & set(tw))}
assert names[501] == '紅色藥水' and names[984] == '神之金屬'
assert prices[501] == ['Buy: 10'] and prices[6672] == ['Sell: 1']
assert all(len(n.encode()) <= 49 for n in names.values())  # ITEM_NAME_LENGTH 50
lines = [
	'# 台服道具名稱：覆蓋 Name（NPC 對話的 getitemname、伺服器訊息用），其他欄位沿用上游。',
	'# Buy/Sell 照抄上游：覆蓋時沒寫會讓 rAthena 不補算另一個價格（賣店 0 Zeny）。上游改價後要重新產生。',
	'# 來源：ROchineseRE SystemEN/tw_SystemEN/LuaFiles514/itemInfo.lua 的 identifiedDisplayName；台服沒有的道具維持英文。',
	'',
	'Header:',
	'  Type: ITEM_DB',
	'  Version: 3',
	'',
	'Body:',
]
for i, n in names.items():
	lines += [f'  - Id: {i}', f'    Name: {json.dumps(n, ensure_ascii=False)}', *(f'    {p}' for p in prices[i])]
out = root / 'db/import/item_db.yml'
out.write_text('\n'.join(lines) + '\n', 'utf-8', newline='\n')
print(f'{out}: {len(names)} 個道具')
