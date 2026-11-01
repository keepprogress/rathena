# conf/import/

rAthena 上游的設定覆蓋點。本目錄的 `*.conf` 會在 `conf/*.conf` 之後被讀取，
任何 key 在這裡重設都會覆蓋上游預設值，但**不會修改上游檔案本身**。

## 規則
- 客製設定一律放這裡，**不要直接編輯 `conf/*.conf`**
- 命名建議：與被覆蓋的上游檔同名（例：`conf/import/battle_conf.txt` 對應 `conf/battle_conf.txt`）
- UTF-8 **無 BOM**

## 載入順序
詳見 `conf/import-tmpl/` 與 `conf/*.conf` 末尾的 `import:` 指令。
