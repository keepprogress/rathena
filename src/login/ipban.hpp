// Copyright (c) rAthena Dev Teams - Licensed under GNU GPL
// For more information, see LICENCE in the main folder

#ifndef IPBAN_HPP
#define IPBAN_HPP

#include <common/cbasetypes.hpp>

/**
 * 檢查指定 IP 是否已被封鎖
 * @param ip: IPv4 位址
 * @return true 代表在封鎖名單中或查詢失敗
 */
bool ipban_check(uint32 ip);

/**
 * 記錄登入失敗次數，超過限制時自動封鎖
 * @param ip: 發生錯誤的 IPv4 位址
 */
void ipban_log(uint32 ip);

/**
 * 讀取封鎖模組相關設定
 * @param key: 設定項目名稱
 * @param value: 對應的數值
 * @return 是否成功處理
 */
bool ipban_config_read(const char* key, const char* value);

/**
 * 初始化 IP 封鎖模組
 */
void ipban_init(void);

/**
 * 結束 IP 封鎖模組並釋放資源
 */
void ipban_final(void);

#endif /* IPBAN_HPP */
