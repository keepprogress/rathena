# Project: rAthena 中文私服客製

這是一個基於 rAthena 的私服專案，目標：
1. 跟著 rAthena 上游持續同步
2. 中文化（最終靠 client `iteminfo.lub` + server `db/import/`）
3. 加入自營便利功能（轉蛋、商城、活動等）
4. 客製不與上游衝突，方便長期維護

## 紀律（Claude 必須遵守）

### 永不修改 upstream 對應的檔案
以下路徑屬於 rAthena 上游，**任何 session 都不要直接編輯**：
- `src/`
- `conf/*.conf`（不含 `conf/import/`）
- `db/(re|pre-re)/`（不含 `db/import/`）
- `npc/(re|pre-re)/`、`npc/airships`、`npc/battleground`、`npc/cashshop`、`npc/event`、`npc/guild`、`npc/instances`、`npc/jobs`、`npc/kafras`、`npc/merchants`、`npc/mobs`、`npc/other`、`npc/quests`、`npc/woe-fe`、`npc/woe-se`、`npc/woe-te`
- `sql-files/*.sql`（不含 `sql-files/migrations/`，若已建立）

### 客製只能進這些位置
- `npc/custom/`、`npc/scripts_custom.conf`（rAthena 設計給客製用）
- `conf/import/`（覆蓋 conf 用）
- `db/import/`（覆蓋 db YAML 用）
- `sql-files/migrations/`（自建，本專案的 schema 變更）
- `data-overlay/`（自建，client lub/grf 來源檔）

如果上游沒提供 import 點，需要修改原始檔才能達成目的，**先停下來跟使用者確認**，不要擅自動上游檔。

## 編碼規則
- NPC `.txt`、`.conf`：UTF-8 **無 BOM**（純 rAthena 對 BOM 不友善）
- SQL：utf8mb4 + utf8mb4_unicode_ci
- 客戶端 `iteminfo.lub` 的 `*ResourceName` 欄位是韓文 EUC-KR，**永不轉碼**

## Git 工作流
- `master` / `main` 分支：永遠等於 upstream，不寫客製
- 客製活在 `claude/*` 或 `feat/*` 分支
- 提交前先跑 `/sync-upstream`（見 `.claude/skills/sync-upstream/`）確認與上游關係

## 學「方案」不抄「程式碼」
參考 Pandas / rAthenaCN 的功能設計，但不複製其 GPL-3 程式碼。能用 rAthena 原生 script + atcommand + 設定覆蓋達成的，就不要改 C++ 原始碼。
