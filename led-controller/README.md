# LED Controller

LED 燈條控制器桌面程式（GUI）。透過 USB 序列埠控制燈條，支援 **Windows** 與 **Linux**，介面採用 macOS 風格。

## 功能

- 選擇 USB 序列埠、Baud rate、LED 數量、色序、傳輸協定
- 12 種內建 Pattern，可調顏色與速度，即時預覽
- 將調好的內建 Pattern 另存為「常用 Preset」
- 自訂 Pattern：逐顆 LED 上色、多影格、影格時間、淡入淡出
- Sequence：串聯多個 Pattern，各自設定執行秒數，可循環，可匯入 / 匯出
- Debug Console：即時檢視送出（TX）與收到（RX）的資料，可手動傳送
- 未連接硬體時，仍可在底部預覽燈條查看效果

## 系統需求

| 項目 | 需求 |
|---|---|
| 作業系統 | Windows 10 / 11、Linux（X11 或 Wayland） |
| Python | 3.9 以上 |
| 套件 | PySide6、pyserial（見 `requirements.txt`） |

## 安裝

```bash
# 1. 取得專案
git clone <repo-url> led-controller
cd led-controller

# 2. 建立虛擬環境（建議）
python -m venv .venv

#    Windows (PowerShell)
.venv\Scripts\Activate.ps1
#    Linux
source .venv/bin/activate

# 3. 安裝相依套件
pip install -r requirements.txt
```

### Linux：序列埠權限

第一次使用若無法開啟序列埠（Permission denied），將自己加入 `dialout` 群組後**重新登入**：

```bash
sudo usermod -aG dialout $USER
```

### Windows：驅動程式

若裝置未出現在序列埠清單，請先安裝該 USB 轉序列晶片（CH340、CP210x、FTDI 等）的驅動程式。

## 執行

```bash
python main.py
# 或
python -m ledcontroller
```

## 使用方式

左側選單共四頁：**Device、Library、Custom、Sequence**。畫面底部固定顯示燈條預覽、連線狀態、亮度與控制按鈕。

### 1. Device：連接裝置

1. 插上 USB，**Serial Port** 清單會自動更新（也可按 *Refresh*）。
2. 選擇序列埠（Windows 為 `COM3`，Linux 為 `/dev/ttyUSB0`、`/dev/ttyACM0`）。
3. 設定 **Baud Rate**（預設 115200）與 **LED Count**。
4. 按 **Connect**；連線成功後底部狀態變為綠燈。再按一次即中斷連線。

| 設定 | 說明 |
|---|---|
| Protocol | `Adalight`：送出 `Ada` 標頭 + RGB 資料（預設）；`Raw RGB`：只送 RGB 資料 |
| Color Order | 燈條實際色序（RGB / GRB / BRG…）。顏色不對時調整此項 |
| Frame Rate | 每秒送出的畫面數（預設 30） |
| Quick test | 紅 / 綠 / 藍 / 白，用來確認連線與色序 |

> LED 數量多時（約 200 顆以上），建議提高 Baud Rate，否則畫面更新會變慢。
> 傳輸協定需與你的燈條控制器相符；本程式只負責 GUI 端送出資料。

### 2. Library：常用 Pattern

- 點選清單中的 Pattern 即開始播放，右側可調整顏色與速度，燈條即時變化。
- **Save as Preset…**：將目前參數存成常用 Preset，之後出現在清單的 *My Presets*。
- **Add to Sequence**：加入 Sequence。
- **Delete**：刪除 Preset 或自訂 Pattern。

內建 Pattern：Solid、Gradient、Rainbow、Breathing、Wave、Comet、Scanner、Theater Chase、Color Wipe、Twinkle、Fire、Strobe。

> Strobe 為快速閃爍效果，請留意光敏感族群。

### 3. Custom：自訂 Pattern

1. 按 **New Pattern**，輸入名稱。
2. 設定 **Brush** 顏色，在 LED 格子上**左鍵點擊或拖曳**上色，**右鍵**擦除。
3. 工具：Fill、Gradient（Brush → Color 2）、Rainbow、Mirror、Shift、Clear。
4. 用 **+ / Dup / −** 新增、複製、刪除影格；每個影格可設定 **Duration**，開啟 **Fade to next frame** 會漸變到下一影格。
5. **Preview** 在燈條上預覽；**Save** 儲存。儲存後可在 Library 與 Sequence 中使用。

### 4. Sequence：串聯 Pattern

1. **Add Pattern ▾**：從內建、Preset、自訂中選擇加入。
2. 在 **Duration** 欄設定每個步驟執行的秒數。
3. 用 **Move Up / Move Down / Duplicate / Remove** 調整順序。
4. **Loop** 開啟時循環播放；**Play / Stop** 控制播放，執行中的步驟會高亮並顯示進度。
5. **Export… / Import…**：匯出或匯入 JSON 檔。

### 5. Debug Console

按底部 **Debug ▸**（快捷鍵 `Ctrl+D`），視窗會向右展開 Debug Console；再按一次或點 *Hide* 收合。

| 項目 | 說明 |
|---|---|
| TX / RX | 分別開關送出 / 收到資料的顯示 |
| Pause | 暫停記錄 |
| 格式 | Hex、ASCII、Hex + ASCII |
| TX 記錄頻率 | 預設每秒記錄 5 筆畫面，避免 30 fps 資料塞滿視窗；可改為每張都記錄 |
| 每行位元組數 | 超過的部分以 `… +N B` 省略 |
| Send | 手動傳送 Hex（如 `41 64 61`）或文字 |
| Clear / Save Log | 清除畫面 / 存成 log 檔 |

TX 若為 Adalight 資料，會自動標示 `[Adalight · N LEDs]`。底部顯示 TX/RX 總量與傳輸速率。

> 手動 Send 的資料會插在畫面資料流之間；若只想測試指令，先按 **Blackout** 停止播放。

### 底部控制列

| 控制 | 說明 |
|---|---|
| 燈條預覽 | 即時顯示目前輸出（含亮度） |
| Brightness | 全域亮度 0–100% |
| Blackout | 停止播放並全部熄滅 |
| Debug | 展開 / 收合 Debug Console |

## 設定檔

Pattern Preset、自訂 Pattern、Sequence 與連線設定會自動儲存：

| 系統 | 路徑 |
|---|---|
| Windows | `%APPDATA%\LEDController\data.json` |
| Linux | `~/.config/LEDController/data.json` |

刪除此檔即可還原預設值。

## 疑難排解

| 狀況 | 處理 |
|---|---|
| 清單沒有序列埠 | 確認 USB 線可傳資料、驅動已安裝，按 Refresh |
| Linux 無法開啟序列埠 | 加入 `dialout` 群組並重新登入 |
| 連線後燈條沒反應 | 確認 Baud Rate 與 LED Count 與控制器一致；開啟 Debug 確認 TX 有資料送出 |
| 顏色錯誤（紅變綠等） | 調整 Device 頁的 Color Order，並用 Quick test 驗證 |
| 連線後前幾秒無反應 | 部分開發板在開啟序列埠時會重置，等待數秒即可 |
| 動畫卡頓 | 降低 LED 數量 / Frame Rate，或提高 Baud Rate |
| 提示 Connection lost | USB 被拔除或裝置中斷；重新插上後再按 Connect |

## 專案結構

```
led-controller/
├── main.py                  # 程式入口
├── pyproject.toml
├── requirements.txt / requirements-dev.txt
├── ledcontroller/
│   ├── app.py               # QApplication 啟動、字型與樣式
│   ├── constants.py         # 常數與預設設定
│   ├── core/                # engine（播放）、store（存檔）、colors、paths
│   ├── patterns/            # 內建 / 自訂 Pattern（不依賴 Qt）
│   ├── serial_io/           # link（收發執行緒）、ports、protocol、formatting
│   └── ui/                  # main_window、debug_panel、style、pages/、widgets/
└── tests/                   # pytest
```

## 開發

```bash
pip install -r requirements-dev.txt
python -m pytest              # 測試（無需顯示器，使用 Qt offscreen）
python -m pyflakes ledcontroller tests
```

新增內建 Pattern：在 `ledcontroller/patterns/builtin.py` 繼承 `Pattern`，宣告 `params`、實作 `render(t)`，並加入 `BUILTINS`，UI 的參數表單會自動產生。

## 已知限制（v0.1.0）

- 僅有淺色主題
- 視窗使用系統原生標題列
- Sequence 播放中修改的秒數，需停止後重新播放才會生效
