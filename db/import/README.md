# db/import/

rAthena 上游 YAML DB 的覆蓋點。本目錄的 YAML 會在 `db/(re|pre-re)/` 之後被讀取，
同一筆資料（例：`Item_DB`、`Mob_DB`）在這裡重定義就會覆蓋上游版本。

## 規則
- 中文化、調整數值、新增客製道具/魔物，一律放這裡
- **不要直接編輯 `db/re/` 或 `db/pre-re/`** —— 會與上游同步衝突
- 檔名與上游一致（例：`db/import/item_db.yml` 對應 `db/(re|pre-re)/item_db.yml`）

## 載入順序
詳見 `db/import-tmpl/` 與各 YAML loader 的 `Footer.Imports`。

## 目前的檔案
- `item_db.yml`：`data-overlay/zh-tw/gen_item_db.py` 產生的台服道具名，**不要手改**；檔尾 Footer 匯入 `item_db_caddo.yml`
- `item_db_caddo.yml`：手寫的道具覆蓋（新手包補品改零重量）；有 Buy/Sell 的道具要照抄上游價格
- `item_group_db.yml`：練功寶盒(1)～(175) 改成全部給（上游 1～90 級預設只隨機給一樣）並加碼補品
- `mob_db.yml`：`gen_mob_db.py` 產生的台服魔物名
