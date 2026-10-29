# conf/import/

rAthena 上游的設定覆蓋點。本目錄的 `*.conf` 會在 `conf/*.conf` 之後被讀取，
任何 key 在這裡重設都會覆蓋上游預設值，但**不會修改上游檔案本身**。

## 規則
- 客製設定一律放這裡，**不要直接編輯 `conf/*.conf`**
- 命名建議：與被覆蓋的上游檔同名（例：`conf/import/battle_conf.txt` 對應 `conf/battle_conf.txt`）
- UTF-8 **無 BOM**

## 載入順序
詳見 `conf/import-tmpl/` 與 `conf/*.conf` 末尾的 `import:` 指令。

## 部署專屬設定（`*.local`）
密碼與 IP 不進 git：`inter_conf.txt` / `char_conf.txt` / `map_conf.txt` 只有一行
`import: conf/import/<名稱>.local`，實際值寫在被 `.gitignore` 忽略的 `.local` 檔。

- `inter.local`：`*_server_pw`、`ipban_db_pw`、`web_server_pw`、`log_db_pw`、`log_db_db`
- `char.local`：`userid`、`passwd`（login 帳號表 account_id=1）、`server_name`、`char_ip`
- `map.local`：`userid`、`passwd`、`map_ip`
