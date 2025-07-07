# rAthena 私服架設指南

本文件簡要介紹 rAthena 專案的目錄架構以及在 Linux 環境下建置私服的流程。

## 專案目錄概觀

- **src/**：伺服器端 C++ 原始碼。
- **conf/**：伺服器設定檔範例，包含登入、角色與地圖伺服器設定。
- **db/**：以文字或 YAML 格式撰寫的資料庫設定檔。
- **sql-files/**：MySQL/MariaDB 使用的 SQL 匯入腳本。
- **npc/**：NPC 與腳本相關檔案。
- **doc/**：官方文件與指令參考。

## 建置步驟

1. 安裝必要套件：`gcc`、`make`、`mysql` 或 `mariadb` 等。
2. 下載原始碼並進入資料夾：
   ```bash
   git clone https://github.com/rathena/rathena.git
   cd rathena
   ```
3. 執行組態與編譯：
   ```bash
   ./configure
   make server
   ```
4. 建立資料庫並匯入 `sql-files` 內的 SQL 檔案，主要為 `main.sql` 與 `logs.sql` 等。
5. 依需求編輯 `conf/` 目錄下的設定檔，例如 `login_athena.conf`、`char_athena.conf`、`map_athena.conf`。
6. 透過 `athena-start` 指令啟動伺服器：
   ```bash
   ./athena-start start
   ```

## 架設流程圖

```mermaid
flowchart TD
    A[取得原始碼] --> B[安裝依賴]
    B --> C[執行 ./configure]
    C --> D[make server]
    D --> E[匯入 SQL 資料]
    E --> F[修改 conf 設定]
    F --> G[./athena-start start]
```

完成以上步驟後，即可連線測試自建的 rAthena 私服。

