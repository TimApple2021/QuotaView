import AppKit

enum BrandAssets {
    static let menuBarIcon: NSImage = load(
        resource: "QuotaViewMenuTemplate-18@2x",
        pointSize: 18,
        isTemplate: true
    )

    static let headerIcon: NSImage = load(
        resource: "QuotaViewHeader-18@2x",
        pointSize: 18,
        isTemplate: false
    )

    private static func load(resource: String, pointSize: CGFloat, isTemplate: Bool) -> NSImage {
        let image: NSImage
        if let url = Bundle.main.url(forResource: resource, withExtension: "png"),
           let bundled = NSImage(contentsOf: url) {
            image = bundled
        } else {
            image = NSImage(systemSymbolName: "gauge.with.dots.needle.67percent", accessibilityDescription: "QuotaView")
                ?? NSImage(size: NSSize(width: pointSize, height: pointSize))
        }
        image.size = NSSize(width: pointSize, height: pointSize)
        image.isTemplate = isTemplate
        image.accessibilityDescription = "QuotaView AI 额度监控器"
        return image
    }
}
