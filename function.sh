# 定義各服務名稱及安裝路徑
L_SRV=login-server
C_SRV=char-server
M_SRV=map-server
W_SRV=web-server
INST_PATH=/opt
PKG=rathena
PKG_PATH="${INST_PATH}/${PKG}"
check_files() {
    # 確認主要執行檔是否存在
    for i in ${L_SRV} ${C_SRV} ${M_SRV} ${W_SRV}
    do
        if [ ! -f ./$i ]; then
            echo "$i does not exist... exiting..."
            exit 1;
        fi
    done
}

# 確認使用者具備安裝權限

check_inst_right(){
    if [ ! -w "${INST_PATH}" ]; then
        # 若沒有寫入權限則提醒使用 sudo
        echo "You must have sudo right to use this install (write/read permission in ${INST_PATH}/ )" && exit
    fi
}

# 若腳本與安裝目錄不同，則切換至安裝目錄執行
# 於安裝路徑中執行相關指令
inst_launch_workaround(){
  if [ -d "${PKG_PATH}" ]; then
    if [ "$(pwd)" != "${PKG_PATH}" ]; then cd "${PKG_PATH}"; fi
  fi
}
