#!/bin/bash
# QuotaView macOS App 构建与打包脚本
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MACOS_DIR="$PROJECT_DIR/macos"
APP_NAME="QuotaView"
EXECUTABLE_NAME="QuotaView"
VERSION="1.1.4"
APP_BUNDLE="$PROJECT_DIR/$APP_NAME.app"
BIN_DIR="$APP_BUNDLE/Contents/MacOS"
RES_DIR="$APP_BUNDLE/Contents/Resources"

echo "=== 1. 生成 QuotaView 品牌图标 ==="
"$PROJECT_DIR/branding/QuotaView/generate_icons.sh"

echo "=== 2. 清理旧构建并初始化 App 目录结构 ==="
rm -rf "$APP_BUNDLE"
mkdir -p "$BIN_DIR"
mkdir -p "$RES_DIR"

echo "=== 3. 打包后端并兼容原 Application Support 数据 ==="
cp "$PROJECT_DIR/monitor_backend.py" "$RES_DIR/monitor_backend.py"
cp "$PROJECT_DIR/cli/quotaview_cli.py" "$RES_DIR/quotaview_cli.py"
cp "$PROJECT_DIR/runtime_migration.py" "$RES_DIR/runtime_migration.py"
chmod 755 "$RES_DIR/quotaview_cli.py"
SUPPORT_DIR="$HOME/Library/Application Support/Antigravity Token Monitor"
mkdir -p "$SUPPORT_DIR"
chmod 700 "$SUPPORT_DIR"
python3 "$PROJECT_DIR/runtime_migration.py" --source "$PROJECT_DIR/data" --target "$SUPPORT_DIR"

cp "$PROJECT_DIR/branding/QuotaView/QuotaView.icns" "$RES_DIR/QuotaView.icns"
cp "$PROJECT_DIR/branding/QuotaView/menu-bar/QuotaViewMenuTemplate-18.png" "$RES_DIR/QuotaViewMenuTemplate-18.png"
cp "$PROJECT_DIR/branding/QuotaView/menu-bar/QuotaViewMenuTemplate-18@2x.png" "$RES_DIR/QuotaViewMenuTemplate-18@2x.png"
cp "$PROJECT_DIR/branding/QuotaView/menu-bar/QuotaViewHeader-18.png" "$RES_DIR/QuotaViewHeader-18.png"
cp "$PROJECT_DIR/branding/QuotaView/menu-bar/QuotaViewHeader-18@2x.png" "$RES_DIR/QuotaViewHeader-18@2x.png"

echo "=== 4. 编译 QuotaView Swift 源代码 ==="
swiftc -parse-as-library \
    -o "$BIN_DIR/$EXECUTABLE_NAME" \
    "$MACOS_DIR/AntigravityTokenMonitor"/*.swift

echo "=== 5. 写入 QuotaView Info.plist ==="
cat << EOF > "$APP_BUNDLE/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>QuotaView</string>
    <key>CFBundleIdentifier</key>
    <string>com.antigravity.tokenmonitor</string>
    <key>CFBundleName</key>
    <string>QuotaView</string>
    <key>CFBundleDisplayName</key>
    <string>QuotaView</string>
    <key>CFBundleIconFile</key>
    <string>QuotaView.icns</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleVersion</key>
    <string>114</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

echo "=== 6. 安装 QuotaView 到 Applications ==="
GLOBAL_DEST="/Applications/$APP_NAME.app"
USER_DEST="$HOME/Applications/$APP_NAME.app"

if [ -w "/Applications" ]; then
    rm -rf "$GLOBAL_DEST"
    cp -R "$APP_BUNDLE" "$GLOBAL_DEST"
    echo "应用成功安装到全局 Applications 目录: $GLOBAL_DEST"
else
    echo "没有系统 /Applications 写入权限，正在安装到用户 Applications 目录..."
    mkdir -p "$HOME/Applications"
    rm -rf "$USER_DEST"
    cp -R "$APP_BUNDLE" "$USER_DEST"
    echo "应用成功安装到用户 Applications 目录: $USER_DEST"
fi

echo "=== 7. 安装全局 quotaview 命令入口 ==="
INSTALLED_APP="$GLOBAL_DEST"
if [ ! -d "$INSTALLED_APP" ]; then
    INSTALLED_APP="$USER_DEST"
fi
CLI_TARGET="$INSTALLED_APP/Contents/Resources/quotaview_cli.py"
if [ -w "/usr/local/bin" ]; then
    GLOBAL_BIN="/usr/local/bin"
elif [ -w "/opt/homebrew/bin" ]; then
    GLOBAL_BIN="/opt/homebrew/bin"
else
    GLOBAL_BIN="$HOME/.local/bin"
    mkdir -p "$GLOBAL_BIN"
fi
ln -sf "$CLI_TARGET" "$GLOBAL_BIN/quotaview"
echo "全局命令已安装: $GLOBAL_BIN/quotaview"

echo "=== 8. QuotaView 构建与安装完成！ ==="
