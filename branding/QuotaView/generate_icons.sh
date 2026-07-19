#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$ROOT/source"
APP_DIR="$ROOT/app-icon"
ICONSET_DIR="$ROOT/QuotaView.iconset"
MENU_DIR="$ROOT/menu-bar"
MASTER_PNG="$SOURCE_DIR/QuotaView-master-1024.png"

mkdir -p "$APP_DIR" "$ICONSET_DIR" "$MENU_DIR"

# macOS ships sips and iconutil; no third-party renderer is required.
sips -s format png "$SOURCE_DIR/QuotaView-master.svg" --out "$MASTER_PNG" >/dev/null

for size in 1024 512 256 128 64 32 16; do
    sips -z "$size" "$size" "$MASTER_PNG" --out "$APP_DIR/QuotaView-$size.png" >/dev/null
done

while read -r filename size; do
    sips -z "$size" "$size" "$MASTER_PNG" --out "$ICONSET_DIR/$filename" >/dev/null
done <<'SIZES'
icon_16x16.png 16
icon_16x16@2x.png 32
icon_32x32.png 32
icon_32x32@2x.png 64
icon_128x128.png 128
icon_128x128@2x.png 256
icon_256x256.png 256
icon_256x256@2x.png 512
icon_512x512.png 512
icon_512x512@2x.png 1024
SIZES

iconutil -c icns "$ICONSET_DIR" -o "$ROOT/QuotaView.icns"

sips -s format png "$SOURCE_DIR/QuotaView-menu-template.svg" --out "$MENU_DIR/.menu-master.png" >/dev/null
while read -r filename size; do
    sips -z "$size" "$size" "$MENU_DIR/.menu-master.png" --out "$MENU_DIR/$filename" >/dev/null
done <<'SIZES'
QuotaViewMenuTemplate-16.png 16
QuotaViewMenuTemplate-16@2x.png 32
QuotaViewMenuTemplate-18.png 18
QuotaViewMenuTemplate-18@2x.png 36
QuotaViewMenuTemplate-20.png 20
QuotaViewMenuTemplate-20@2x.png 40
SIZES
rm -f "$MENU_DIR/.menu-master.png"

sips -s format png "$SOURCE_DIR/QuotaView-header.svg" --out "$MENU_DIR/.header-master.png" >/dev/null
sips -z 36 36 "$MENU_DIR/.header-master.png" --out "$MENU_DIR/QuotaViewHeader-18@2x.png" >/dev/null
sips -z 18 18 "$MENU_DIR/.header-master.png" --out "$MENU_DIR/QuotaViewHeader-18.png" >/dev/null
rm -f "$MENU_DIR/.header-master.png"

echo "QuotaView icon assets generated in $ROOT"
