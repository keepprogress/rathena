-- ===================================================================
-- gacha audit log
-- ===================================================================
-- 紀錄每次轉蛋的中獎結果，提供：
--   * 客訴查詢（玩家說沒拿到獎品時對得上時間 / item_id）
--   * 機率審計（驗證實際中獎分佈與設定的權重相符）
--   * 防作弊（短時間內大量同 IP / 同帳號的異常拉霸）
--
-- Schema 自建，與 rAthena 上游 sql-files/*.sql 完全隔離。
-- 套用：mysql -u <user> -p <db> < sql-files/migrations/20260507_gacha.sql
-- ===================================================================

CREATE TABLE IF NOT EXISTS `gacha_log` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `char_id`       INT UNSIGNED    NOT NULL,
  `account_id`    INT UNSIGNED    NOT NULL,
  `pulled_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `tier`          TINYINT UNSIGNED NOT NULL COMMENT '0=top 1=mid 2=low',
  `item_id`       INT UNSIGNED    NOT NULL,
  `qty`           INT UNSIGNED    NOT NULL,
  `cost_zeny`     INT UNSIGNED    NOT NULL DEFAULT 0,
  `cost_item_id`  INT UNSIGNED    NOT NULL DEFAULT 0,
  `cost_item_qty` INT UNSIGNED    NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_char_time` (`char_id`, `pulled_at`),
  KEY `idx_account_time` (`account_id`, `pulled_at`),
  KEY `idx_item` (`item_id`),
  KEY `idx_tier_time` (`tier`, `pulled_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
