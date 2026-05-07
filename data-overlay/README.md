# data-overlay/

本專案自建的客戶端資源覆蓋來源（**非 rAthena 上游提供**）。

## 用途
存放要餵給 client 的 lub / lua / 圖檔來源，最終會被打包進 GRF 或散檔覆蓋。

## 結構
- `lub/` —— iteminfo / skillinfo / questinfo 等中文化來源（Lua）
- `grf/` —— 圖檔、texture、bgm 等資源來源

## 編碼規則（重要）
- `iteminfo.lub` 的 **頂層 Lua 檔本身用 UTF-8**
- 但 `*ResourceName` 欄位指向的 BMP / SPR 檔名，是**韓文 EUC-KR**，**永不轉碼**
- 中文顯示走 `*identifiedDisplayName` / `*unidentifiedDisplayName`

## 打包
打包腳本另立（尚未建立）。本目錄只放來源檔，產出的 `.grf` / `.lub` **不要 commit**。
