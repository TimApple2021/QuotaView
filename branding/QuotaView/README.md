# QuotaView 图标资产

QuotaView 的主图以项目内原创 SVG 为唯一可重复生成源。视觉方向先使用 OpenAI 图像生成工具制作概念稿，再根据概念稿重绘为几何 SVG，避免依赖截图、在线素材或不可重复的手工尺寸文件。

## 文件来源

- `source/QuotaView-concept-generated.png`：设计探索概念稿，不参与构建。
- `source/QuotaView-master.svg`：正式 App 图标源文件，1024×1024 画布。
- `source/QuotaView-master-1024.png`：由 master SVG 自动渲染的正式主 PNG。
- `source/QuotaView-menu-template.svg`：菜单栏单色模板图标源文件。
- `source/QuotaView-header.svg`：弹窗标题栏彩色简化标志源文件。

所有图形均为本项目原创，不包含文字、截图或第三方版权素材。

## 生成方法

在项目根目录运行：

```bash
./branding/QuotaView/generate_icons.sh
```

脚本使用 macOS 自带的 `sips` 从 SVG 生成 PNG，并使用以下命令生成 `.icns`：

```bash
iconutil -c icns branding/QuotaView/QuotaView.iconset \
  -o branding/QuotaView/QuotaView.icns
```

`app-icon/` 保存 16、32、64、128、256、512、1024 像素 PNG。`QuotaView.iconset/` 保存 macOS 标准尺寸及 Retina 文件。`menu-bar/` 保存 16、18、20 pt 对应的 1x/2x 单色模板 PNG，以及弹窗标题栏使用的 18 pt 彩色图标。

## 构建使用

`macos/build.sh` 每次构建都会先运行 `generate_icons.sh`，然后将以下文件复制到 App Resources：

- `QuotaView.icns`
- `menu-bar/QuotaViewMenuTemplate-18.png`
- `menu-bar/QuotaViewMenuTemplate-18@2x.png`
- `menu-bar/QuotaViewHeader-18.png`
- `menu-bar/QuotaViewHeader-18@2x.png`

Info.plist 的 `CFBundleIconFile` 指向 `QuotaView.icns`。

## 后续替换

替换品牌图标时，更新三个 SVG 源文件并重新运行生成脚本。若资源文件名保持不变，无需修改 Swift 或 Info.plist；若改名，则同时更新 `macos/build.sh` 与 `BrandAssets.swift` 中的资源名。
