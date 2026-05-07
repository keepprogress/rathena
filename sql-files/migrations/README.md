# sql-files/migrations/

本專案自建的 schema 變更目錄（**非 rAthena 上游提供**）。

## 用途
為客製功能（轉蛋、商城、活動等）新增資料表 / 欄位 / 索引，與上游 `sql-files/*.sql` 完全隔離。

## 規則
- **不要修改上游的 `sql-files/main.sql` / `logs.sql` / `roulette_default_data.sql` 等**
- 檔名格式：`YYYYMMDD_<feature>.sql`（例：`20260507_gacha_table.sql`）
- 字元集：`utf8mb4` + `utf8mb4_unicode_ci`
- 每個檔案應可重複執行（用 `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 等）
- 套用順序依檔名排序

## 套用方式
```bash
for f in sql-files/migrations/*.sql; do
  mysql -u <user> -p <db> < "$f"
done
```
