#!/usr/bin/env python3
"""每日簽到：產生伺服器 db/import/attendance.yml 與客戶端 System/CheckAttendance.lub。

用法：python3 -I data-overlay/zh-tw/gen_attendance.py [CheckAttendance.lub 輸出路徑]
每月一段（rAthena 一段期間最多簽到 = 獎勵天數，下個月重新開始），累計天數、斷簽不歸零。
客戶端簽到視窗（官方與 roBrowser）只畫 20 格，所以獎勵固定 20 天。
.lub 是純文字 Lua，載入時用 os.date 算當月起訖，視窗顯示的期間才會跟伺服器一致。
簽到給的商城點數不在這裡，見 npc/custom/etc/online_reward.txt。
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIRST = (2026, 11)
MONTHS = 36  # 產到 2029/10，之後重跑一次

# (道具 ID, 數量)；每 5 天一個大獎
REWARDS = [
	(12263, 3),   # 經驗值倍增書[活動專用]（30 分 +50%）
	(12912, 1),   # BOSS雷達箱子（10 個）
	(12913, 1),   # 天使之賜福 卷軸箱子（10 張）
	(12914, 1),   # 加速術 卷軸箱子（10 張）
	(14533, 2),   # ★ 高級經驗值倍增書（60 分 +100%）
	(12264, 3),   # 掉寶率倍增糖[活動專用]（30 分 +100%）
	(14592, 3),   # 職業經驗值倍增書（30 分 +50%）
	(12912, 1),   # BOSS雷達箱子
	(22979, 3),   # 經驗值&掉寶率倍增組[活動專用]
	(7621, 3),    # ★ 原地復活之證
	(12263, 5),   # 經驗值倍增書[活動專用]
	(12912, 1),   # BOSS雷達箱子
	(13584, 1),   # 天使之賜福卷軸30個箱子
	(13576, 1),   # 加速術10級卷軸30個箱子
	(14232, 1),   # ★ 天地樹果實10個箱子
	(12264, 5),   # 掉寶率倍增糖[活動專用]
	(14592, 5),   # 職業經驗值倍增書
	(12912, 1),   # BOSS雷達箱子
	(22979, 5),   # 經驗值&掉寶率倍增組[活動專用]
	(616, 1),     # ★ 老舊收集冊（隨機卡片）
]
assert len(REWARDS) == 20


def months():
	y, m = FIRST
	for _ in range(MONTHS):
		ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
		last = (date(ny, nm, 1) - date(y, m, 1)).days
		yield f'{y}{m:02d}01', f'{y}{m:02d}{last:02d}'
		y, m = ny, nm


def yml():
	out = ['# 由 data-overlay/zh-tw/gen_attendance.py 產生，不要手改。', '',
	       'Header:', '  Type: ATTENDANCE_DB', '  Version: 1', '', 'Body:']
	for start, end in months():
		out += [f'  - Start: {start}', f'    End: {end}', '    Rewards:']
		for day, (item, qty) in enumerate(REWARDS, 1):
			out += [f'      - Day: {day}', f'        ItemId: {item}'] + ([f'        Amount: {qty}'] if qty > 1 else [])
	return '\n'.join(out) + '\n'


def lub():
	start, end = next(months())
	rows = '\n'.join(f'\t{{ {d}, {i}, {q} }},' for d, (i, q) in enumerate(REWARDS, 1))
	return f'''-- 由 caddokawaRo repo data-overlay/zh-tw/gen_attendance.py 產生，不要手改。
-- 伺服器每月一段簽到期間，這裡用 os.date 算當月起訖；拿不到時間就退回第一個月。
local ok, s, e = pcall(function()
	local y, m = tonumber(os.date("%Y")), tonumber(os.date("%m"))
	local ny, nm = y, m + 1
	if nm > 12 then ny, nm = y + 1, 1 end
	local last = tonumber(os.date("%d", os.time{{year = ny, month = nm, day = 1, hour = 12}} - 86400))
	return y * 10000 + m * 100 + 1, y * 10000 + m * 100 + last
end)
if not ok then s, e = {start}, {end} end

Config = {{ EvendOnOff = 1, StartDate = s, EndDate = e }}

Reward = {{
{rows}
}}

function main()
	InsertCheckAttendanceConfig(Config.EvendOnOff, Config.StartDate, Config.EndDate)
	for _, r in ipairs(Reward) do
		InsertCheckAttendanceReward(r[1], r[2], r[3])
	end
	return true, "good"
end
'''


if __name__ == '__main__':
	(ROOT / 'db/import/attendance.yml').write_text(yml(), 'utf-8')
	print('db/import/attendance.yml:', MONTHS, '個月')
	if len(sys.argv) > 1:
		Path(sys.argv[1]).write_text(lub(), 'utf-8')
		print(sys.argv[1])
