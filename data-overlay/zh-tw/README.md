# data-overlay/zh-tw/

繁中在地化（用語對照台服）的產生腳本。產物不放這裡：伺服器端的 `db/import/*.yml` 進 repo，客戶端 overlay 只在 Pi。

`rocn` = [rAthena-ZhCN/ROchineseRE](https://github.com/rAthena-ZhCN/ROchineseRE) 的 clone（Pi `~/apps/robrowser/rocn`），只當資料來源，不跑它的腳本。

| 腳本 | 在哪跑 | 產物 |
|---|---|---|
| `gen_item_db.py` | 任一（需 rocn） | `db/import/item_db.yml`：台服道具名，Buy/Sell 照抄上游 |
| `gen_mob_db.py` | 任一（需 rocn、opencc） | `db/import/mob_db.yml`：台服卡片名 > `mob_names_extra.json` > 導航表簡轉繁 |
| `build_zhtw.py` | Pi `~/apps/robrowser` | roBrowser 的 `DATA_OVERRIDE_PATH`（文字表、技能、貼圖） |
| `gen_tex.py` | Omarchy（Pillow + Noto Sans CJK TC） | 按鈕貼圖的韓文換繁中，給 `build_zhtw.py` 的 `tex-zh/` |
| `gen_jobnames.py` | Pi | roBrowser `src/DB/Monsters/JobNameTable.js`（已含在 patch 裡） |
| `robrowser-caddo.patch` | Pi | roBrowser 改動：選角 hover、單擊空位建角、繁中職業名 |

NPC 對話另見 `npc/custom/zh/npc_zh.py`。

## 指令

```sh
# 伺服器端（在 rAthena 根目錄）
python3 -I data-overlay/zh-tw/gen_item_db.py <rocn> .
python3 -I data-overlay/zh-tw/gen_mob_db.py <rocn> .

# 客戶端（Pi ~/apps/robrowser）；輸出會先清空，不要直接指向 overlay/（容器 bind mount 的是目錄本身）
python3 -I <repo>/data-overlay/zh-tw/build_zhtw.py rocn client/data kro_msgstringtable.csv tex-zh /tmp/overlay.new
rsync -a --delete /tmp/overlay.new/ overlay/ && docker restart robrowserlegacy

# roBrowser 原始碼（Pi ~/apps/robrowser，src/ 是上游 clone，檔案是 CRLF）
git -C src apply <repo>/data-overlay/zh-tw/robrowser-caddo.patch
cd src && docker build --target slim -f ../Dockerfile.caddo -t robrowserlegacy:slim . && cd .. && docker rm -f robrowserlegacy && ./run.sh
```

## 同步上游後
- 重跑 `gen_item_db.py`：上游改價時，舊檔會把價格蓋回舊值。
- 重跑 `gen_mob_db.py`：新怪物會列在 stderr，翻好加進 `mob_names_extra.json` 再重跑。
- NPC：`npc_zh.py extract` 找新字串。
