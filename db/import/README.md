# db/import/

rAthena 上游 YAML DB 的覆蓋點。本目錄的 YAML 會在 `db/(re|pre-re)/` 之後被讀取，
同一筆資料（例：`Item_DB`、`Mob_DB`）在這裡重定義就會覆蓋上游版本。

## 規則
- 中文化、調整數值、新增客製道具/魔物，一律放這裡
- **不要直接編輯 `db/re/` 或 `db/pre-re/`** —— 會與上游同步衝突
- 檔名與上游一致（例：`db/import/item_db.yml` 對應 `db/(re|pre-re)/item_db.yml`）

## 載入順序
詳見 `db/import-tmpl/` 與各 YAML loader 的 `Footer.Imports`。
