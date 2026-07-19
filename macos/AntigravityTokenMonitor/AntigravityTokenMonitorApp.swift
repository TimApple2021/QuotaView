import SwiftUI

@main
struct QuotaViewApp: App {
    @StateObject private var dataModel = TokenDataModel()

    var body: some Scene {
        MenuBarExtra(content: {
            MenuBarView(dataModel: dataModel)
                .onAppear { dataModel.applyAppearance() }
        }, label: {
            HStack(spacing: 4) {
                Image(nsImage: BrandAssets.menuBarIcon)
                    .renderingMode(.template)
                    .resizable()
                    .frame(width: 18, height: 18)
                if !dataModel.menuBarText.isEmpty {
                    Text(dataModel.menuBarText)
                }
            }
            .accessibilityLabel("QuotaView AI 额度监控器 \(dataModel.menuBarText)")
            .help("QuotaView · AI 额度监控器")
        })
        .menuBarExtraStyle(.window)
        // No separate Window scenes — everything lives in the Popover
    }
}
