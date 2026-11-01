#!/usr/bin/env python3
"""gachas.json（台服歷代轉蛋）→ npc/custom/etc/gacha.txt（轉蛋機 NPC）。

用法：python3 -I npc/custom/gacha/gen_gacha.py
gachas.json 每筆：name、date、src（gnjoy:<轉蛋代碼> 或 ptt:<文章>）、
fixed [[道具ID, 數量, 精煉]]（每抽必得）、random [[道具ID, 數量, 權重, 精煉]]（抽一樣）、
missing（rAthena 沒有、對不上 ID 而剔除的台服道具名，留著之後補對照）。
權重 = 台服公告機率 ×1000；2022/05 前台服只公布虛寶價值等級，
依同道具在之後公告的機率中位數換算：B 12960、A 1200、S 200、SS 40、SSS 5。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PRICE = 30  # 商城點數／抽
RARE = 0.002  # 機率 ≤ 0.2%（台服 S 級以上）全服公告
CHUNK = 50


def esc(s):
	return s.replace('\\', '\\\\').replace('"', '\\"')


def arrays(name, values, quote=False):
	out = []
	for i in range(0, len(values), CHUNK):
		vals = ', '.join(f'"{esc(v)}"' if quote else str(v) for v in values[i:i + CHUNK])
		out.append(f'\tsetarray {name}[{i}], {vals};')
	return out


def build(pools):
	pools = sorted(pools, key=lambda g: g['date'])
	seen = {}
	for g in pools:  # 同名的期數加編號，選單才分得出來
		seen[g['name']] = seen.get(g['name'], 0) + 1
		if seen[g['name']] > 1:
			g['name'] += f' #{seen[g["name"]]}'
	A = {k: [] for k in ('pname$', 'ps', 'pn', 'pt', 'fs', 'fn', 'gi', 'ga', 'gw', 'gr', 'gx', 'fi', 'fa', 'fr')}
	years = []
	for g in pools:
		y = g['date'][:4]
		if not years or years[-1][0] != y:
			years.append([y, len(A['ps']), 0])
		years[-1][2] += 1
		tot = sum(w for _, _, w, _ in g['random'])
		A['pname$'].append(g['name'])
		A['ps'].append(len(A['gi']))
		A['pn'].append(len(g['random']))
		A['pt'].append(tot)
		A['fs'].append(len(A['fi']))
		A['fn'].append(len(g['fixed']))
		cum = 0
		for item, qty, w, ref in g['random']:
			cum += w
			A['gi'].append(item); A['ga'].append(qty); A['gw'].append(cum); A['gr'].append(ref)
			A['gx'].append(int(w / tot <= RARE))
		for item, qty, ref in g['fixed']:
			A['fi'].append(item); A['fa'].append(qty); A['fr'].append(ref)
	prize = max(i for i, g in enumerate(pools) if '轉蛋' in g['name'])  # 活動獎品抽最新一期轉蛋（不含禮包）
	init = [f'\t.price = {PRICE};', f'\t.pools = {len(pools)};', f'\t.prize_pool = {prize};',
	        f'\t.ymenu$ = "{":".join(y + " 年（" + str(n) + " 期）" for y, _, n in years)}:離開";']
	init += arrays('.yr$', [y for y, _, _ in years], True) + arrays('.ys', [s for _, s, _ in years]) + arrays('.yn', [n for _, _, n in years])
	for k, v in A.items():
		if v:
			init += arrays('.' + k, v, k.endswith('$'))
	return HEAD.format(first=pools[0]['date'][:4], last=pools[-1]['date'][:4]) + '\n'.join(init) + '\n\tend;\n}\n'


HEAD = '''//===== rAthena Script =======================================
//= 轉蛋機（台服歷代轉蛋）
//===== Description: =========================================
//= 由 npc/custom/gacha/gen_gacha.py 從 gachas.json 產生，不要手改。
//= 收錄台服 {first}～{last} 的轉蛋，獎池與機率照台服公告（官網機率公告、PTT 轉貼的維護公告）；
//= rAthena 沒有的道具剔除，剩下的依原權重抽。每抽給固定物品＋隨機 1 樣，收商城點數（#CASHPOINTS）。
//= 每一抽寫進 gacha_log（sql-files/migrations/20260507_gacha.sql）：tier 0 = 稀有（≤0.2%），2 = 一般，cost_zeny 記點數。
//============================================================

prontera,156,180,4	script	轉蛋機#cgacha	76,{{
	mes "[轉蛋機]";
	mes "收錄台服 {first}～{last} 年共 ^0055FF" + .pools + "^000000 期轉蛋，機率照台服公告。";
	mes "每抽 ^0055FF" + .price + "^000000 商城點數，你有 ^0055FF" + #CASHPOINTS + "^000000 點。";
	next;
	.@y = select(.ymenu$) - 1;
	if (.@y >= getarraysize(.yr$))
		close;
	for (.@i = 0; .@i < .yn[.@y]; .@i++)
		.@m$[.@i] = .pname$[.ys[.@y] + .@i];
	.@p = .ys[.@y] + select(implode(.@m$, ":")) - 1;
	while (1) {{
		mes "[轉蛋機]";
		mes "^FF0000" + .pname$[.@p] + "^000000";
		mes "你有 ^0055FF" + #CASHPOINTS + "^000000 點。";
		.@sel = select("單抽（" + .price + " 點）:10 連抽（" + (.price * 10) + " 點）:查看獎項與機率:離開");
		if (.@sel == 4)
			close;
		if (.@sel == 3) {{
			for (.@k = 0; .@k < .fn[.@p]; .@k++)
				mes "^777777必得^000000 " + getitemname(.fi[.fs[.@p] + .@k]) + " x" + .fa[.fs[.@p] + .@k];
			.@prev = 0;
			for (.@k = .ps[.@p]; .@k < .ps[.@p] + .pn[.@p]; .@k++) {{
				.@bp = (.gw[.@k] - .@prev) * 100000 / .pt[.@p];  // 千分之一個百分點
				.@prev = .gw[.@k];
				mes (.gx[.@k] ? "^FF0000" : "^000000") + getitemname(.gi[.@k]) + (.gr[.@k] ? " +" + .gr[.@k] : "") + " x" + .ga[.@k] + "^777777 " + sprintf("%d.%03d%%", .@bp / 1000, .@bp % 1000) + "^000000";
			}}
			next;
			continue;
		}}
		.@pulls = (.@sel == 1) ? 1 : 10;
		if (#CASHPOINTS < .price * .@pulls) {{
			mes "商城點數不足。";
			close;
		}}
		#CASHPOINTS -= .price * .@pulls;
		next;
		mes "[轉蛋機]";
		callsub L_Pull, .@p, .@pulls, .price;
		for (.@i = 0; .@i < .@pulls; .@i++)
			mes (@gacha_rare[.@i] ? "^FF0000" : "^0055FF") + @gacha_res$[.@i] + "^000000";
		mes "剩下 ^0055FF" + #CASHPOINTS + "^000000 點。";
		next;
	}}

// 抽 getarg(1) 次第 getarg(0) 期，getarg(2) 是每抽點數（寫進 gacha_log）；結果放 @gacha_res$、@gacha_rare
L_Pull:
	.@p = getarg(0);
	.@pulls = getarg(1);
	deletearray @gacha_res$;
	deletearray @gacha_rare;
	.@batch = gettimetick(2) * 10000 + rand(10000);
	.@values$ = "";
	for (.@n = 1; .@n <= .@pulls; .@n++) {{
		for (.@k = .fs[.@p]; .@k < .fs[.@p] + .fn[.@p]; .@k++)
			getitem2 .fi[.@k], .fa[.@k], 1, .fr[.@k], 0, 0, 0, 0, 0;
		.@r = rand(.pt[.@p]);
		.@k = .ps[.@p];
		while (.gw[.@k] <= .@r)  // .gw 是累計權重
			.@k++;
		getitem2 .gi[.@k], .ga[.@k], 1, .gr[.@k], 0, 0, 0, 0, 0;
		@gacha_res$[.@n - 1] = .@n + ". " + getitemname(.gi[.@k]) + (.gr[.@k] ? " +" + .gr[.@k] : "") + " x" + .ga[.@k];
		@gacha_rare[.@n - 1] = .gx[.@k];
		if (.gx[.@k])
			announce "[轉蛋機] " + strcharinfo(0) + " 從【" + .pname$[.@p] + "】抽中了 " + getitemname(.gi[.@k]) + "！", bc_all;
		.@values$ += (.@n > 1 ? "," : "") + "(" + getcharid(0) + "," + getcharid(3) + "," + .@batch + "," + .@n + ","
			+ (.gx[.@k] ? 0 : 2) + "," + .gi[.@k] + "," + .ga[.@k] + "," + getarg(2) + ",0,0)";
	}}
	query_sql "INSERT INTO `gacha_log` (`char_id`,`account_id`,`pull_batch_id`,`pull_idx`,`tier`,`item_id`,`qty`,`cost_zeny`,`cost_item_id`,`cost_item_qty`) VALUES " + .@values$;
	return;

// 活動獎品：免費抽最新一期轉蛋 10 次，用 doevent 帶著得獎者呼叫（咯咯雞，見 npc_zh.py TWEAKS）
OnPrize:
	dispbottom "[活動獎品] 免費抽【" + .pname$[.prize_pool] + "】10 次：";
	callsub L_Pull, .prize_pool, 10, 0;
	for (.@i = 0; .@i < 10; .@i++)
		dispbottom "[活動獎品] " + @gacha_res$[.@i];
	end;

OnInit:
'''

if __name__ == '__main__':
	pools = json.loads((ROOT / 'npc/custom/gacha/gachas.json').read_text('utf-8'))
	for g in pools:
		assert g['random'] and all(w > 0 for _, _, w, _ in g['random']), g['name']
		assert ':' not in g['name'], g['name']
	out = ROOT / 'npc/custom/etc/gacha.txt'
	out.write_text(build(pools), 'utf-8')
	print(f'{out.relative_to(ROOT)}: {len(pools)} 期')
