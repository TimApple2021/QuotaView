import SwiftUI
import Charts

// Test compatibility note: Credits 等价用量

// MARK: - VisualEffectView for glassmorphism
struct VisualEffectView: NSViewRepresentable {
    var material: NSVisualEffectView.Material
    var blendingMode: NSVisualEffectView.BlendingMode
    
    func makeNSView(context: Context) -> NSVisualEffectView {
        let view = NSVisualEffectView()
        view.material = material
        view.blendingMode = blendingMode
        view.state = .active
        return view
    }
    
    func updateNSView(_ nsView: NSVisualEffectView, context: Context) {
        nsView.material = material
        nsView.blendingMode = blendingMode
    }
}

// MARK: - Page enum

enum PopoverPage { case dashboard, settings, deepseekSettings }




// MARK: - QuotaView palette

/// The menu-bar window has one palette for both pages.  Keeping semantic
/// colors here prevents system-light text from landing on the old dark
/// surfaces when the user chooses “跟随系统”.
struct QuotaViewPalette {
    let windowBackground: Color
    let cardBackground: Color
    let elevatedBackground: Color
    let inputBackground: Color
    let primaryText: Color
    let secondaryText: Color
    let tertiaryText: Color
    let disabledText: Color
    let border: Color
    let divider: Color
    let progressTrack: Color
    let selectedSegmentBackground: Color
    let selectedSegmentText: Color
    let selectedSegmentBorder: Color
    let segmentTrackBackground: Color
    let segmentTrackBorder: Color
    let segmentShadow: Color
    let inactiveSegmentText: Color
    let destructiveText: Color
    let destructiveBackground: Color
    let blue: Color
    let sourceBadgeBackground: Color
    let sourceBadgeText: Color
    let sourceBadgeBorder: Color
    let refreshButtonIcon: Color
    let orange: Color
    let red: Color
    let successText: Color
    let successBackground: Color

    init(colorScheme: ColorScheme) {
        let light = colorScheme == .light
        windowBackground = Color(nsColor: light ? .windowBackgroundColor : .windowBackgroundColor)
        cardBackground = Color(nsColor: light ? .controlBackgroundColor : .controlBackgroundColor)
        elevatedBackground = Color(nsColor: light ? .underPageBackgroundColor : .underPageBackgroundColor)
        inputBackground = Color(nsColor: light ? .textBackgroundColor : .textBackgroundColor)
        primaryText = Color(nsColor: .labelColor)
        secondaryText = Color(nsColor: .secondaryLabelColor)
        tertiaryText = Color(nsColor: .tertiaryLabelColor)
        disabledText = Color(nsColor: .disabledControlTextColor)
        border = Color(nsColor: .separatorColor).opacity(light ? 0.55 : 0.35)
        divider = Color(nsColor: .separatorColor).opacity(light ? 0.75 : 0.45)
        progressTrack = Color(nsColor: .quaternaryLabelColor).opacity(light ? 0.5 : 0.65)
        selectedSegmentBackground = light
            ? Color(nsColor: .controlAccentColor).opacity(0.18)
            : Color(nsColor: .selectedControlColor)
        selectedSegmentText = Color(nsColor: light ? .labelColor : .selectedMenuItemTextColor)
        selectedSegmentBorder = Color(nsColor: .controlAccentColor).opacity(light ? 0.18 : 0.28)
        segmentTrackBackground = Color(nsColor: light ? .controlBackgroundColor : .underPageBackgroundColor)
        segmentTrackBorder = Color(nsColor: .separatorColor).opacity(light ? 0.6 : 0.45)
        segmentShadow = Color(nsColor: .shadowColor).opacity(light ? 0.10 : 0.20)
        inactiveSegmentText = Color(nsColor: .secondaryLabelColor)
        destructiveText = Color(nsColor: .systemRed)
        destructiveBackground = Color(nsColor: .systemRed).opacity(light ? 0.12 : 0.22)
        let sourceBlue = Color(nsColor: .systemBlue)
        blue = sourceBlue
        sourceBadgeBackground = sourceBlue.opacity(light ? 0.10 : 0.18)
        sourceBadgeText = light ? Color(nsColor: .secondaryLabelColor) : Color(nsColor: .labelColor)
        sourceBadgeBorder = sourceBlue.opacity(light ? 0.15 : 0.20)
        refreshButtonIcon = Color(nsColor: .secondaryLabelColor)
        orange = Color(nsColor: .systemOrange)
        red = Color(nsColor: .systemRed)
        successText = Color(nsColor: .systemGreen)
        successBackground = Color(nsColor: .systemGreen).opacity(light ? 0.14 : 0.22)
    }
}



// A Menu-based settings control opens from its label anchor instead of
// repositioning the popup around the currently selected row, which is
// especially important for a menu-bar window near the top of the screen.
struct StableSettingsMenu<Option: Hashable & Identifiable>: View {
    @Binding var selection: Option
    let options: [Option]
    let title: (Option) -> String
    let width: CGFloat

    init(selection: Binding<Option>, options: [Option], width: CGFloat = 150,
         title: @escaping (Option) -> String) {
        self._selection = selection
        self.options = options
        self.width = width
        self.title = title
    }

    var body: some View {
        Menu {
            ForEach(options) { option in
                Button {
                    selection = option
                } label: {
                    HStack {
                        Text(title(option))
                        Spacer()
                        if selection == option {
                            Image(systemName: "checkmark")
                        }
                    }
                }
            }
        } label: {
            Text(title(selection))
                .lineLimit(1)
                .fixedSize(horizontal: true, vertical: false)
                .frame(width: width, height: 28, alignment: .trailing)
                .contentShape(Rectangle())
        }
        .menuIndicator(.hidden)
        .menuStyle(.borderlessButton)
        .frame(width: width, height: 28, alignment: .trailing)
        .accessibilityValue(title(selection))
    }
}

// MARK: - MenuBarView

struct MenuBarView: View {
    @ObservedObject var dataModel: TokenDataModel
    @State private var page: PopoverPage = .dashboard
    @State private var isModelPricingExpanded = false
    @State private var isCodexPricingExpanded = false
    @Environment(\.dismiss) private var dismiss
    @Environment(\.colorScheme) private var colorScheme

    private var effectiveColorScheme: ColorScheme {
        switch dataModel.theme {
        case .system: return colorScheme
        case .light: return .light
        case .dark: return .dark
        }
    }

    private var palette: QuotaViewPalette { QuotaViewPalette(colorScheme: effectiveColorScheme) }

    private var sourceBadgeLabel: String? {
        switch dataModel.displayedSources {
        case .all: return nil
        case .antigravityOnly: return "Antigravity"
        case .codexOnly: return "Codex"
        case .deepseekOnly: return "DeepSeek"
        }
    }

    var body: some View {
        ZStack {
            palette.windowBackground
                .ignoresSafeArea()
            
            switch page {
            case .dashboard:
                dashboardPage
            case .settings:
                settingsPage
            case .deepseekSettings:
                deepseekSettingsPage
            }

        }
        .frame(width: 360, height: 520)
        .preferredColorScheme(dataModel.theme.colorScheme)
        .id(dataModel.theme.rawValue)
    }


    private func formatExpirationTime(_ isoString: String?, expiresOn: String?) -> String {
        if let on = expiresOn {
            return formatExpiresOn(on)
        }
        
        guard let iso = isoString else { return "" }
        let isoFormatter = ISO8601DateFormatter()
        guard let date = isoFormatter.date(from: iso) else {
            if iso.count >= 10 {
                return formatExpiresOn(String(iso.prefix(10)))
            }
            return ""
        }
        
        let df = DateFormatter()
        if dataModel.language == .english {
            df.locale = Locale(identifier: "en_US_POSIX")
            df.dateFormat = "MMM d 'at' HH:mm"
            return "Expires \(df.string(from: date))"
        }
        df.locale = Locale(identifier: "zh_CN")
        df.dateFormat = "M 月 d 日 HH:mm"
        return "\(df.string(from: date)) 到期"
    }

    private func formatExpiresOn(_ dateStr: String) -> String {
        let parts = dateStr.components(separatedBy: "-")
        if parts.count == 3, let month = Int(parts[1]), let day = Int(parts[2]) {
            if dataModel.language == .english {
                let formatter = DateFormatter()
                formatter.locale = Locale(identifier: "en_US_POSIX")
                guard month >= 1, month <= formatter.shortMonthSymbols.count else { return "Expires \(dateStr)" }
                return "Expires \(formatter.shortMonthSymbols[month - 1]) \(day)"
            }
            return "\(month) 月 \(day) 日到期"
        }
        return dataModel.tr("\(dateStr) 到期", "Expires \(dateStr)")
    }

    private func formatIsoTime(_ raw: String) -> String {
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        var date = isoFormatter.date(from: raw)
        if date == nil {
            let fallbackFormatter = ISO8601DateFormatter()
            fallbackFormatter.formatOptions = [.withInternetDateTime]
            date = fallbackFormatter.date(from: raw)
        }
        
        if let d = date {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
            displayFormatter.timeZone = TimeZone.current
            return displayFormatter.string(from: d)
        }
        
        var cleaned = raw.replacingOccurrences(of: "T", with: " ")
        if let plusIndex = cleaned.firstIndex(of: "+") {
            cleaned = String(cleaned[..<plusIndex])
        }
        if let zIndex = cleaned.firstIndex(of: "Z") {
            cleaned = String(cleaned[..<zIndex])
        }
        return cleaned.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var formattedScanTime: String {
        formatIsoTime(dataModel.dashboard.lastScanTime)
    }

    private var dashboardPage: some View {
        VStack(spacing: 0) {
            // Header Row
            HStack(spacing: 6) {
                Image(nsImage: BrandAssets.headerIcon)
                    .resizable()
                    .interpolation(.high)
                    .frame(width: 16, height: 16)
                    .accessibilityLabel("QuotaView")
                Text("QuotaView").font(.system(size: 12, weight: .bold))
                    .foregroundColor(palette.primaryText)
                if let sourceBadgeLabel {
                    Text(sourceBadgeLabel)
                        .font(.system(size: 9, weight: .medium))
                        .foregroundColor(palette.sourceBadgeText)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(
                            Capsule()
                                .fill(palette.sourceBadgeBackground)
                                .overlay(
                                    Capsule()
                                        .stroke(palette.sourceBadgeBorder, lineWidth: 0.5)
                                )
                        )
                        .accessibilityLabel(dataModel.tr("当前来源：\(sourceBadgeLabel)", "Current source: \(sourceBadgeLabel)"))
                        .accessibilityAddTraits(.isStaticText)
                }
                Spacer()
                Text(formattedScanTime)
                    .font(.system(size: 9)).foregroundColor(palette.secondaryText)
                
                Button {
                    ScannerRunner.terminateActiveScan()
                    NSApplication.shared.terminate(nil)
                } label: {
                    Image(systemName: "power")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(palette.secondaryText)
                }
                .buttonStyle(.plain)
                .help(dataModel.tr("退出 QuotaView", "Quit QuotaView"))
            }
            .padding(.horizontal, 14).padding(.vertical, 9)

            if let err = dataModel.scanError {
                Text(dataModel.tr("错误：\(err)", "Error: \(err)")).font(.system(size: 9)).foregroundColor(palette.red)
                    .padding(.horizontal, 14).padding(.bottom, 4)
            }

            Divider().background(palette.divider)

            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    // AI Tool selector
                    if dataModel.shouldShowSourceSegment {
                        VStack(spacing: 6) {
                            topSegmentedControl
                        }
                        .padding(.horizontal, 14)
                        .padding(.top, 10)
                        .padding(.bottom, 6)
                    }


                    switch dataModel.selectedSource {
                    case .antigravity, .codex:
                        standardDashboardContent
                    case .deepseek:
                        deepseekDashboardContent
                    }
                }
            }

            // Footer
            Divider().background(palette.divider).padding(.top, 8)
            HStack {
                Button { dataModel.refreshCurrentSource() } label: {
                    RefreshButtonIcon(isScanning: dataModel.isScanning, palette: palette)
                        .frame(width: 32, height: 32, alignment: .center)
                }
                .buttonStyle(RefreshButtonStyle())
                .disabled(dataModel.isScanning)
                .accessibilityLabel(dataModel.isScanning ? dataModel.tr("正在刷新数据", "Refreshing Data") : dataModel.tr("刷新数据", "Refresh Data"))
                .help(dataModel.isScanning ? dataModel.tr("刷新中…", "Refreshing…") : dataModel.tr("刷新", "Refresh"))
                
                Spacer()
                
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) { page = .settings }
                } label: {
                    Image(systemName: "gearshape")
                        .font(.system(size: 20, weight: .medium))
                        .foregroundColor(palette.secondaryText)
                        .frame(width: 32, height: 32, alignment: .center)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .help(dataModel.tr("设置", "Settings"))
            }
            .padding(.horizontal, 14).padding(.vertical, 8)
        }
    }

    @ViewBuilder
    private var standardDashboardContent: some View {
        VStack(spacing: 0) {
            // Stat cards
            let s = dataModel.filteredStats
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 6) {
                statCard(dataModel.tr("模型输入", "Input Tokens"), value: dataModel.fmt(s.userInputTokens))
                statCard(dataModel.tr("模型输出", "Output Tokens"), value: dataModel.fmt(s.outputTokens))
                statCard(dataModel.tr("可识别总量", "Identifiable"), value: dataModel.fmt(s.identifiableTokens))
            }
            .padding(.horizontal, 14)
            .padding(.top, 8)

            // Secondary API equivalent cost
            HStack {
                Text(dataModel.tr("标准 API 等价成本", "Standard API Equivalent Cost"))
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(palette.secondaryText)
                Spacer()
                Text(String(format: "$%.2f", s.estimatedCost))
                    .font(.system(size: 12, weight: .bold).monospacedDigit())
                    .foregroundColor(palette.primaryText)
            }
            .padding(.horizontal, 14)
            .padding(.top, 8)

            Text(dataModel.timeRangeLabel(dataModel.selectedRange))
                .font(.system(size: 9))
                .foregroundColor(palette.secondaryText)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 14)
                .padding(.top, 3)

            // Quota monitoring section
            quotaSection
        }
    }


    private func quotaProgressColor(for usedPercent: Double) -> Color {
        let clamped = max(0.0, min(100.0, usedPercent))
        if clamped >= 80.0 {
            return palette.red
        } else if clamped >= 50.0 {
            return palette.orange
        } else {
            return palette.blue
        }
    }

    private var quotaSection: some View {
        let sourceKey = dataModel.selectedSource.jsonKey
        let quota = dataModel.dashboard.quotaStatus?[sourceKey]
        let rawItems = quota?.items ?? []
        let items = rawItems.filter { item in
            guard item.confidence == "official_live" else { return false }
            if sourceKey == "codex" && item.name.contains("五小时") {
                return false
            }
            return true
        }
        let resetEnt = quota?.resetEntitlements
        
        return VStack(alignment: .leading, spacing: 10) {
            Text(dataModel.tr("额度监控", "Quota Monitoring"))
                .font(.system(size: 11, weight: .bold))
                .foregroundColor(palette.primaryText)
                .padding(.bottom, 2)

            if quota?.status == "official_stale" {
                Text(dataModel.tr("暂时无法更新，显示上次成功数据", "Unable to refresh; showing last successful data"))
                    .font(.system(size: 9))
                    .foregroundColor(palette.secondaryText)
            }
            
            // 1. Weekly limits
            if items.isEmpty {
                let providerMessage = quota?.message.isEmpty == false ? quota!.message : nil
                let msg = providerMessage ?? (sourceKey == "codex" ? dataModel.tr("暂时无法读取当前官方额度", "Unable to read current official quota") : dataModel.tr("暂时无法读取官方额度", "Unable to read official quota"))
                Text(providerMessage == nil ? msg : (dataModel.language == .english ? "Official quota reader returned an unavailable status" : msg))
                    .font(.system(size: 10))
                    .foregroundColor(palette.secondaryText)
                    .padding(.vertical, 4)
            } else {
                ForEach(items) { item in
                    let clampedPercent = max(0.0, min(100.0, item.usedPercent))
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(dataModel.quotaLabel(item))
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(palette.primaryText)
                            Spacer()
                            if item.isExpired == true {
                Text(dataModel.tr("已用 \(Int(clampedPercent))% (额度数据可能已过期)", "Used \(Int(clampedPercent))% (quota may be stale)"))
                                    .font(.system(size: 10, weight: .bold).monospacedDigit())
                                    .foregroundColor(palette.secondaryText)
                            } else {
                                Text(dataModel.tr("已用 \(Int(clampedPercent))%", "Used \(Int(clampedPercent))%"))
                                    .font(.system(size: 10, weight: .bold).monospacedDigit())
                                    .foregroundColor(palette.primaryText)
                            }
                        }
                        
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                Capsule()
                                    .fill(palette.progressTrack)
                                    .frame(height: 4)
                                Capsule()
                                    .fill(quotaProgressColor(for: clampedPercent))
                                    .frame(width: max(0, min(geo.size.width, geo.size.width * CGFloat(clampedPercent / 100.0))), height: 4)
                            }
                        }
                        .frame(height: 4)
                        .padding(.vertical, 2)
                        
                        HStack {
                            Text(dataModel.tr("重置时间:", "Reset:"))
                            Spacer()
                            Text(formatIsoTime(item.resetTime))
                        }
                        .font(.system(size: 8).monospacedDigit())
                        .foregroundColor(palette.secondaryText)
                    }
                    .padding(.vertical, 3)
                }
            }
            
            // 2. Limit resets for Codex
            if sourceKey == "codex" {
                Divider()
                    .background(palette.divider)
                    .padding(.vertical, 4)
                
                if let ent = resetEnt {
                    if ent.status == "official_live" || ent.status == "official_stale" {
                        // Count and rows must come from the same normalized entitlement set.
                        let availableItems = ent.items.filter(\.isAvailable)
                        let count = availableItems.count
                        
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Text(dataModel.tr("使用限额重置", "Usage Limit Resets"))
                                    .font(.system(size: 10, weight: .semibold))
                                    .foregroundColor(palette.primaryText)
                                Spacer()
                                
                                Text(dataModel.tr("可用 \(count) 次", "\(count) available"))
                                    .font(.system(size: 9, weight: .bold))
                                    .foregroundColor(palette.successText)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Capsule().fill(palette.successBackground))
                            }

                            if ent.status == "official_stale" {
                                Text(dataModel.tr("暂时无法更新，显示上次成功数据", "Unable to refresh; showing last successful data"))
                                    .font(.system(size: 9))
                                    .foregroundColor(palette.secondaryText)
                            }
                            
                            if availableItems.isEmpty {
                                Text(dataModel.tr("暂无可用重置", "No resets available"))
                                    .font(.system(size: 9))
                                    .foregroundColor(palette.secondaryText)
                                    .padding(.vertical, 2)
                            } else {
                                ForEach(availableItems) { item in
                                    HStack {
                                        Text(dataModel.tr(item.displayName == "Full reset" ? "完整重置" : item.displayName, item.displayName))
                                            .font(.system(size: 9))
                                            .foregroundColor(palette.secondaryText)
                                        Spacer()
                                        Text(formatExpirationTime(item.expiresAt, expiresOn: item.expiresOn))
                                            .font(.system(size: 9).monospacedDigit())
                                            .foregroundColor(palette.tertiaryText)
                                    }
                                    .padding(.vertical, 1)
                                }
                            }
                        }
                    } else {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(dataModel.tr("使用限额重置", "Usage Limit Resets"))
                                .font(.system(size: 10, weight: .semibold))
                                .foregroundColor(palette.primaryText)
                            Text(dataModel.tr("暂时无法读取可用重置", "Unable to read available resets"))
                                .font(.system(size: 9))
                                .foregroundColor(palette.secondaryText)
                                .padding(.vertical, 2)
                        }
                    }
                } else {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(dataModel.tr("使用限额重置", "Usage Limit Resets"))
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(palette.primaryText)
                        Text(dataModel.tr("暂时无法读取可用重置", "Unable to read available resets"))
                            .font(.system(size: 9))
                            .foregroundColor(palette.secondaryText)
                            .padding(.vertical, 2)
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(palette.cardBackground)
        .cornerRadius(10)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(palette.border, lineWidth: 1)
        )
        .padding(.horizontal, 14)
        .padding(.top, 12)
    }

    private var sourceSegmentedControl: some View {
        topSegmentedControl
    }

    @ViewBuilder
    private func sourceSegment(label: String, source: AISource) -> some View {
        topTabSegment(label: label, isSelected: page == .dashboard && dataModel.selectedSource == source) {
            withAnimation(.easeInOut(duration: 0.15)) {
                dataModel.selectedSource = source
                page = .dashboard
            }
        }
    }

    private var topSegmentedControl: some View {
        HStack(spacing: 0) {
            sourceSegment(label: "Antigravity", source: .antigravity)
            sourceSegment(label: "Codex", source: .codex)
            sourceSegment(label: "DeepSeek", source: .deepseek)
        }

        .padding(3)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(palette.segmentTrackBackground)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(palette.segmentTrackBorder, lineWidth: 1)
                )
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(palette.border, lineWidth: 1)
        )
    }

    @ViewBuilder
    private func topTabSegment(label: String, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.system(size: 11, weight: isSelected ? .semibold : .regular))
                .foregroundColor(isSelected ? palette.selectedSegmentText : palette.inactiveSegmentText)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 6)
                .background(
                    RoundedRectangle(cornerRadius: 6)
                        .fill(isSelected ? palette.selectedSegmentBackground : Color.clear)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(isSelected ? palette.selectedSegmentBorder : Color.clear, lineWidth: 1)
                        )
                        .shadow(
                            color: isSelected ? palette.segmentShadow : Color.clear,
                            radius: 1.5,
                            x: 0,
                            y: 1
                        )
                )
        }
        .buttonStyle(.plain)
    }


    // MARK: - Stat card

    private func statCard(_ label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(.system(size: 9, weight: .medium))
                .foregroundColor(palette.secondaryText)
            Text(value)
                .font(.system(size: 16, weight: .bold).monospacedDigit())
                .foregroundColor(palette.primaryText)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 10).padding(.vertical, 8)
        .background(palette.cardBackground)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(palette.border, lineWidth: 1)
        )
    }

    private func statCard(_ label: String, value: String, icon: String,
                           color: Color, note: String?) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            HStack(spacing: 4) {
                Image(systemName: icon).font(.system(size: 10)).foregroundColor(color)
                Text(label).font(.system(size: 9, weight: .medium)).foregroundColor(palette.secondaryText)
                if let n = note {
                    Text("(\(n))")
                        .font(.system(size: 8, weight: n.contains("存在") ? .semibold : .regular))
                        .foregroundColor(n.contains("存在") ? palette.orange : palette.tertiaryText)
                }
            }
            Text(value)
                .font(.system(size: 15, weight: .bold).monospacedDigit())
                .foregroundColor(color)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(8)
        .background(palette.cardBackground)
        .cornerRadius(10)
        .overlay(RoundedRectangle(cornerRadius: 10)
            .stroke(palette.border, lineWidth: 1))
    }

    // MARK: - Trend chart

    @ViewBuilder
    private var trendChart: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(dataModel.tr("趋势", "Trend")).font(.system(size: 9, weight: .semibold)).foregroundColor(palette.secondaryText)
                Spacer()
                HStack(spacing: 8) {
                    legendDot(dataModel.tr("模型输入", "Input"), color: palette.blue)
                    legendDot(dataModel.tr("模型输出", "Output"), color: .purple)
                }
            }

            switch dataModel.selectedRange {
            case .today:
                todayEmptyState

            default:
                let pts = chartPoints()
                let hasData = pts.contains { $0.input > 0 || $0.output > 0 }
                if !hasData {
                    emptyChartPlaceholder(dataModel.tr("当前时间范围暂无可统计数据", "No data in the current range"))
                } else {
                    barChart(pts: pts)
                }
            }
        }
    }

    private var todayEmptyState: some View {
        let s = dataModel.filteredStats
        let hasAny = s.identifiableTokens > 0
        return VStack(spacing: 6) {
            if hasAny {
                HStack(spacing: 20) {
                    todayStat(dataModel.tr("模型输入", "Input"), value: dataModel.fmt(s.userInputTokens), color: palette.blue)
                    todayStat(dataModel.tr("模型输出", "Output"), value: dataModel.fmt(s.outputTokens), color: .purple)
                    todayStat(dataModel.tr("可识别", "Identifiable"), value: dataModel.fmt(s.identifiableTokens), color: .teal)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(palette.cardBackground)
                .cornerRadius(8)
                .overlay(RoundedRectangle(cornerRadius: 8)
                    .stroke(palette.border, lineWidth: 1))
            } else {
                emptyChartPlaceholder(dataModel.tr("今日暂无可统计数据", "No data today"))
            }
        }
    }

    private func todayStat(_ label: String, value: String, color: Color) -> some View {
        VStack(spacing: 2) {
            Text(value).font(.system(size: 13, weight: .bold).monospacedDigit()).foregroundColor(color)
            Text(label).font(.system(size: 9)).foregroundColor(palette.secondaryText)
        }
    }

    private func emptyChartPlaceholder(_ msg: String) -> some View {
        Text(msg)
            .font(.system(size: 10)).foregroundColor(palette.secondaryText)
            .frame(maxWidth: .infinity, minHeight: 50, alignment: .center)
            .background(palette.cardBackground)
            .cornerRadius(8)
            .overlay(RoundedRectangle(cornerRadius: 8)
                .stroke(palette.border, lineWidth: 1))
    }

    private func barChart(pts: [ChartPoint]) -> some View {
        let n = pts.count
        let stride: Int = n >= 30 ? 6 : (n >= 14 ? 3 : 1)
        let dateFmt = DateFormatter(); dateFmt.dateFormat = "yyyy-MM-dd"

        return Chart {
            ForEach(pts) { p in
                if let d = dateFmt.date(from: p.date) {
                    BarMark(
                        x: .value("日期", d, unit: .day),
                        y: .value("Token", p.input),
                        width: barWidth(totalPts: n)
                    )
                    .foregroundStyle(palette.blue.opacity(0.85))
                    BarMark(
                        x: .value("日期", d, unit: .day),
                        y: .value("Token", p.output),
                        width: barWidth(totalPts: n)
                    )
                    .foregroundStyle(.purple.opacity(0.85))
                }
            }
        }
        .chartYAxis {
            AxisMarks(position: .leading) { _ in AxisGridLine(); AxisValueLabel() }
        }
        .chartXAxis {
            AxisMarks(values: .stride(by: .day, count: stride)) { _ in
                AxisGridLine()
                AxisTick()
                AxisValueLabel(format: .dateTime.month().day())
            }
        }
        .frame(height: 120)
    }

    private func barWidth(totalPts: Int) -> MarkDimension {
        let available: Double = 280
        let raw = max(3, (available / Double(max(totalPts, 1))) * 0.65)
        let capped = min(raw, 30)
        return .fixed(capped)
    }

    private struct ChartPoint: Identifiable {
        let date: String; let input: Int; let output: Int
        var id: String { date }
    }

    private func chartPoints() -> [ChartPoint] {
        let series = dataModel.filteredSeries
        let srcKey = dataModel.selectedSource.jsonKey
        return series.map { entry in
            let srcData = entry.sources[srcKey]
            return ChartPoint(date: entry.date,
                              input:  srcData?.userInputTokens ?? 0,
                              output: srcData?.outputTokens ?? 0)
        }
    }

    private func legendDot(_ label: String, color: Color) -> some View {
        HStack(spacing: 3) {
            Circle().fill(color).frame(width: 5, height: 5)
            Text(label).font(.system(size: 8)).foregroundColor(palette.secondaryText)
        }
    }

    // MARK: - Settings Page

    private var settingsPage: some View {
        VStack(spacing: 0) {
            // Header Row
            HStack {
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) { page = .dashboard }
                } label: {
                    HStack(spacing: 3) {
                        Image(systemName: "chevron.left").font(.system(size: 10, weight: .bold))
                        Text(dataModel.tr("返回", "Back")).font(.system(size: 11))
                    }.foregroundColor(.accentColor)
                }.buttonStyle(.plain)

                Spacer()
                Text(dataModel.tr("设置", "Settings")).font(.system(size: 12, weight: .semibold)).foregroundColor(palette.primaryText)
                Spacer()
            }
            .padding(.horizontal, 14).padding(.vertical, 10)

            Divider().background(palette.divider)

            if let settingsError = dataModel.settingsError {
                Text(dataModel.tr("设置保存失败：\(settingsError)", "Settings save failed: \(settingsError)"))
                    .font(.system(size: 9))
                    .foregroundColor(palette.red)
                    .padding(.horizontal, 14)
                    .padding(.top, 5)
            }

            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: 14) {

                    // Display & Behaviour
                    settingsGroup {
                        settingRow(dataModel.tr("菜单栏显示", "Menu Bar Display")) {
                            StableSettingsMenu(
                                selection: $dataModel.menuBarDisplay,
                                options: Array(MenuBarDisplay.allCases),
                                width: 160,
                                title: dataModel.menuBarDisplayLabel
                            )
                        }
                        Divider()
                        settingRow(dataModel.tr("显示来源", "Displayed Sources")) {
                            StableSettingsMenu(
                                selection: $dataModel.displayedSources,
                                options: Array(DisplayedSources.allCases),
                                width: 205,
                                title: dataModel.displayedSourcesLabel
                            )
                        }
                        Divider()
                        settingRow(dataModel.tr("主页面默认范围", "Main Page Default Range")) {
                            StableSettingsMenu(
                                selection: $dataModel.selectedRange,
                                options: Array(TimeRange.allCases),
                                width: 145,
                                title: dataModel.timeRangeLabel
                            )
                        }
                        Divider()
                        settingRow(dataModel.tr("自动刷新", "Auto Refresh")) {
                            StableSettingsMenu(
                                selection: $dataModel.refreshInterval,
                                options: Array(RefreshInterval.allCases),
                                width: 128,
                                title: dataModel.refreshIntervalLabel
                            )
                        }
                        Divider()
                        settingRow(dataModel.tr("外观主题", "Appearance")) {
                            StableSettingsMenu(
                                selection: $dataModel.theme,
                                options: Array(AppTheme.allCases),
                                width: 138,
                                title: dataModel.themeLabel
                            )
                        }
                        Divider()
                        settingRow(dataModel.tr("语言", "Language")) {
                            StableSettingsMenu(
                                selection: $dataModel.language,
                                options: [.chinese, .english],
                                width: 110,
                                title: { $0 == .chinese ? "中文" : "English" }
                            )
                        }
                    }

                    // Launch
                    settingsGroup {
                        settingRow(dataModel.tr("启动时自动扫描", "Scan on Startup")) {
                            Toggle("", isOn: $dataModel.scanOnStartup)
                                .labelsHidden().toggleStyle(.switch).controlSize(.mini)
                        }
                        Divider()
                        settingRow(dataModel.tr("登录时自动启动", "Launch at Login")) {
                            Toggle("", isOn: $dataModel.launchAtLogin)
                                .labelsHidden().toggleStyle(.switch).controlSize(.mini)
                        }
                    }

                    // DeepSeek Settings Entrance
                    settingsGroup {
                        settingRow(dataModel.tr("DeepSeek 配置", "DeepSeek Settings")) {
                            Button {
                                withAnimation(.easeInOut(duration: 0.18)) {
                                    page = .deepseekSettings
                                }
                            } label: {
                                HStack(spacing: 5) {
                                    Text(
                                        dataModel.isDeepSeekConfigured
                                        ? dataModel.tr("已配置", "Configured")
                                        : dataModel.tr("未配置", "Not Configured")
                                    )
                                    .font(.system(size: 11))
                                    .foregroundColor(palette.secondaryText)

                                    Image(systemName: "chevron.right")
                                        .font(.system(size: 10, weight: .semibold))
                                        .foregroundColor(palette.secondaryText)
                                }
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    // collapsible "价格配置" section

                    settingsGroup {
                        Button {
                            withAnimation { isModelPricingExpanded.toggle() }
                        } label: {
                            HStack {
                                Text(dataModel.tr("价格配置", "Pricing")).font(.system(size: 11, weight: .semibold)).foregroundColor(palette.primaryText)
                                Spacer()
                                Image(systemName: isModelPricingExpanded ? "chevron.down" : "chevron.right")
                                    .font(.system(size: 9, weight: .bold))
                            }
                            .foregroundColor(palette.primaryText)
                        }
                        .buttonStyle(.plain)
                        .padding(.vertical, 6)
                        
                        if isModelPricingExpanded {
                            Divider()
                            
                            // Antigravity sub-section
                            VStack(alignment: .leading, spacing: 6) {
                                Text(dataModel.tr("Antigravity API 等价价格", "Antigravity API Equivalent Pricing"))
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundColor(palette.secondaryText)
                                    .padding(.top, 4)
                                
                                let agKeys = dataModel.settingsModelKeys(for: .antigravity)
                                if agKeys.isEmpty {
                                    Text(dataModel.tr("尚未发现 Antigravity 模型", "No Antigravity models found"))
                                        .font(.system(size: 9)).foregroundColor(palette.secondaryText)
                                        .padding(.vertical, 4)
                                } else {
                                    ForEach(agKeys, id: \.self) { key in
                                        let detail = dataModel.modelPriceDetail(for: key, source: .antigravity)
                                        modelPriceRow(key: key, detail: detail, source: .antigravity)
                                        if key != agKeys.last { Divider() }
                                    }
                                }
                            }
                            
                            Divider().padding(.vertical, 4)
                            
                            // Codex sub-section
                            VStack(alignment: .leading, spacing: 6) {
                                Text(dataModel.tr("Codex API 等价价格", "Codex API Equivalent Pricing"))
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundColor(palette.secondaryText)
                                
                                let codexKeys = dataModel.settingsModelKeys(for: .codex)
                                if codexKeys.isEmpty {
                                    Text(dataModel.tr("尚未发现 Codex 模型", "No Codex models found"))
                                        .font(.system(size: 9)).foregroundColor(palette.secondaryText)
                                        .padding(.vertical, 4)
                                } else {
                                    ForEach(codexKeys, id: \.self) { key in
                                        let detail = dataModel.modelPriceDetail(for: key, source: .codex)
                                        modelPriceRow(key: key, detail: detail, source: .codex)
                                        if key != codexKeys.last { Divider() }
                                    }
                                }
                            }
                        }
                    }
                }
                .padding(.bottom, 48)
                .padding(.horizontal, 14)
                .padding(.top, 12)
                .padding(.bottom, 32)
            }
            
            Divider().background(palette.divider)
            
            HStack {
                Button(dataModel.tr("恢复默认设置", "Restore Defaults"), role: .destructive) { resetDefaults() }
                    .buttonStyle(.bordered).controlSize(.small)
                    .foregroundColor(palette.destructiveText)
                    .tint(palette.destructiveText)
                    .background(palette.destructiveBackground)
                
                Spacer()
                
                Button(dataModel.tr("退出 QuotaView", "Quit QuotaView"), role: .destructive) {
                    ScannerRunner.terminateActiveScan()
                    NSApplication.shared.terminate(nil)
                }
                    .buttonStyle(.bordered).controlSize(.small)
                    .foregroundColor(palette.destructiveText)
                    .tint(palette.destructiveText)
                    .background(palette.destructiveBackground)
            }
            .padding(.horizontal, 14)
            .padding(.top, 10)
            .padding(.bottom, 16)
        }
    }

    // MARK: - DeepSeek Dashboard Content (Pure Data Presentation)

    private var deepseekDashboardContent: some View {
        let bal = dataModel.deepseekData?.balance
        let usg = dataModel.deepSeekUsageViewData()

        return VStack(alignment: .leading, spacing: 14) {
            // 1. Official Live Balance Card Group
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(dataModel.tr("官方当前余额", "Official Live Balance"))
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(palette.primaryText)
                    Spacer()
                    if let fetchedAt = bal?.fetchedAt, !fetchedAt.isEmpty {
                        Text(dataModel.tr("刷新时间: \(formatIsoTime(fetchedAt))", "Updated: \(formatIsoTime(fetchedAt))"))
                            .font(.system(size: 9))
                            .foregroundColor(palette.secondaryText)
                    }
                }

                if dataModel.isDeepSeekConfigured {
                    if let err = dataModel.deepseekBalanceError ?? bal?.errorMessage, !err.isEmpty {
                        Text(err)
                            .font(.system(size: 9))
                            .foregroundColor(palette.red)
                    }

                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 6) {
                        statCard(dataModel.tr("总余额", "Total Balance"), value: formatBalanceCardValue(raw: bal?.totalBalance, currency: bal?.currency))
                        statCard(dataModel.tr("充值余额", "Topped Up"), value: formatBalanceCardValue(raw: bal?.toppedUpBalance, currency: bal?.currency))
                        statCard(dataModel.tr("赠送余额", "Granted"), value: formatBalanceCardValue(raw: bal?.grantedBalance, currency: bal?.currency))
                    }
                } else {
                    HStack {
                        Text(dataModel.tr("余额尚未连接，请前往设置 > DeepSeek 配置。", "Balance not connected. Please go to Settings > DeepSeek Settings."))
                            .font(.system(size: 9))
                            .foregroundColor(palette.secondaryText)
                        Spacer()
                    }
                    .padding(8)
                    .background(palette.inputBackground)
                    .cornerRadius(6)
                }
            }

            // 2. Exported Usage History Card Group (from ZIP)
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(dataModel.tr("官网用量历史", "Exported Usage History"))
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(palette.primaryText)
                        if let covStart = usg?.coverageStart, !covStart.isEmpty, let covEnd = usg?.coverageEnd, !covEnd.isEmpty {
                            Text(dataModel.tr("覆盖范围: \(covStart) 至 \(covEnd)", "Coverage: \(covStart) to \(covEnd)"))
                                .font(.system(size: 9))
                                .foregroundColor(palette.secondaryText)
                        }
                    }
                    Spacer()
                    if let months = dataModel.deepseekData?.usage.availableMonths, !months.isEmpty {
                        Menu {
                            Button {
                                dataModel.deepseekSelectedMonth = "all"
                            } label: {
                                HStack {
                                    Text(dataModel.tr("累计", "All Time"))
                                    if dataModel.deepseekSelectedMonth == "all" { Image(systemName: "checkmark") }
                                }
                            }
                            ForEach(months, id: \.self) { month in
                                Button {
                                    dataModel.deepseekSelectedMonth = month
                                } label: {
                                    HStack {
                                        Text(dataModel.deepSeekMonthLabel(month))
                                        if dataModel.deepseekSelectedMonth == month { Image(systemName: "checkmark") }
                                    }
                                }
                            }
                        } label: {
                            HStack(spacing: 4) {
                                Text(dataModel.deepSeekMonthLabel(dataModel.deepseekSelectedMonth))
                            }
                            .foregroundColor(palette.secondaryText)
                        }
                        .menuStyle(.borderlessButton)
                        .font(.system(size: 9))
                    }
                }

                if usg?.hasHistory == true {
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 6) {
                        statCard(dataModel.tr("已导入累计消费", "Imported Spend"), value: "\(usg?.totalActualAmount ?? "0.00") \(usg?.currencies.first ?? "CNY")")
                        statCard(dataModel.tr("API 请求次数", "API Requests"), value: dataModel.language == .chinese ? "\(dataModel.fmt(usg?.totalRequestCount ?? 0)) 次" : dataModel.fmt(usg?.totalRequestCount ?? 0))
                        statCard(dataModel.tr("总 Token", "Total Tokens"), value: dataModel.fmt(usg?.totalTokens ?? 0))
                    }

                    // 3. Model Breakdown Card Group
                    if let models = usg?.models, !models.isEmpty {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(dataModel.tr("按模型统计", "By Model"))
                                .font(.system(size: 10, weight: .semibold))
                                .foregroundColor(palette.secondaryText)

                            ForEach(models) { m in
                                HStack(alignment: .top, spacing: 8) {
                                    Text(m.modelId)
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundColor(palette.primaryText)
                                        .lineLimit(2)
                                        .fixedSize(horizontal: false, vertical: true)

                                    Spacer()

                                    VStack(alignment: .trailing, spacing: 2) {
                                        Text("\(m.actualAmount) \(m.currency)")
                                            .font(.system(size: 10, weight: .bold).monospacedDigit())
                                            .foregroundColor(palette.primaryText)
                                        HStack(spacing: 4) {
                                            Text(dataModel.fmt(m.totalTokens) + " Tokens")
                                            Text("·")
                                            Text(dataModel.language == .chinese ? "\(m.requestCount) 次" : "\(m.requestCount) requests")
                                        }
                                        .font(.system(size: 9))
                                        .foregroundColor(palette.secondaryText)
                                    }
                                }
                                .padding(8)
                                .background(palette.cardBackground)
                                .cornerRadius(6)
                                .overlay(RoundedRectangle(cornerRadius: 6).stroke(palette.border, lineWidth: 1))
                            }
                        }
                    }

                    // 4. API Key Breakdown Card Group
                    if let keys = usg?.keys, !keys.isEmpty {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(dataModel.tr("按历史 API Key 统计", "Historical API Key Usage"))
                                .font(.system(size: 10, weight: .semibold))
                                .foregroundColor(palette.secondaryText)

                            ForEach(keys) { k in
                                HStack(alignment: .center, spacing: 8) {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(k.apiKeyName)
                                            .font(.system(size: 10, weight: .medium))
                                            .foregroundColor(palette.primaryText)
                                            .lineLimit(1)
                                        Text(k.apiKeyMasked)
                                            .font(.system(size: 9).monospacedDigit())
                                            .foregroundColor(palette.secondaryText)
                                    }

                                    Spacer()

                                    VStack(alignment: .trailing, spacing: 2) {
                                        Text("\(k.actualAmount) \(k.currency)")
                                            .font(.system(size: 10, weight: .bold).monospacedDigit())
                                            .foregroundColor(palette.primaryText)
                                        Text(dataModel.fmt(k.totalTokens) + " Tokens")
                                            .font(.system(size: 9))
                                            .foregroundColor(palette.secondaryText)
                                    }
                                }
                                .padding(8)
                                .background(palette.cardBackground)
                                .cornerRadius(6)
                                .overlay(RoundedRectangle(cornerRadius: 6).stroke(palette.border, lineWidth: 1))
                            }
                        }
                    }
                } else {
                    VStack(spacing: 6) {
                        Image(systemName: "doc.badge.plus")
                            .font(.system(size: 24))
                            .foregroundColor(palette.secondaryText)
                        Text(dataModel.tr("暂无 DeepSeek 历史用量数据", "No DeepSeek usage history yet"))
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(palette.primaryText)
                        Text(dataModel.tr("请前往 '设置 > DeepSeek 配置' 导入官网导出的 usage_data_*.zip 文件", "Please go to 'Settings > DeepSeek Settings' to import usage_data_*.zip exported from DeepSeek website"))
                            .font(.system(size: 9))
                            .foregroundColor(palette.secondaryText)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 20)
                    .background(palette.cardBackground)
                    .cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(palette.border, lineWidth: 1))
                }
            }
        }
        .padding(.horizontal, 14)
        .padding(.top, 10)
    }

    // MARK: - DeepSeek Settings Page (Key & ZIP Management)

    private var deepseekSettingsPage: some View {
        let bal = dataModel.deepseekData?.balance
        let usg = dataModel.deepseekData?.usage

        return VStack(spacing: 0) {
            // Header Row with Back button
            HStack(spacing: 8) {
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) { page = .settings }
                } label: {
                    HStack(spacing: 3) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 10, weight: .bold))
                        Text(dataModel.tr("设置", "Settings"))
                            .font(.system(size: 11))
                    }
                    .foregroundColor(.accentColor)
                }
                .buttonStyle(.plain)

                Spacer()

                Text(dataModel.tr("DeepSeek 配置", "DeepSeek Settings"))
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(palette.primaryText)

                Spacer()
                Spacer().frame(width: 45)
            }
            .padding(.horizontal, 14).padding(.vertical, 10)

            Divider().background(palette.divider)

            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: 14) {

                    // 1. API Key Card Group
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(dataModel.tr("API Key", "API Key"))
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(palette.primaryText)
                            Spacer()

                            if dataModel.isDeepSeekConfigured {
                                Text(dataModel.tr("已配置", "Set"))
                                    .font(.system(size: 9, weight: .medium))
                                    .foregroundColor(palette.successText)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Capsule().fill(palette.successBackground))
                            } else {
                                Text(dataModel.tr("未配置", "Not Set"))
                                    .font(.system(size: 9, weight: .medium))
                                    .foregroundColor(palette.secondaryText)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Capsule().fill(palette.cardBackground))
                            }
                        }

                        HStack(spacing: 8) {
                            SecureField(dataModel.tr("输入 sk-...", "Enter sk-..."), text: $dataModel.deepseekApiKeyInput)
                                .textFieldStyle(.roundedBorder)
                                .font(.system(size: 11))

                            Button(dataModel.tr("保存", "Save")) {
                                dataModel.saveDeepSeekApiKey(dataModel.deepseekApiKeyInput)
                            }
                            .buttonStyle(.borderedProminent)
                            .font(.system(size: 11))
                            .disabled(dataModel.deepseekApiKeyInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

                            if dataModel.isDeepSeekConfigured {
                                Button(dataModel.tr("删除 Key", "Delete Key")) {
                                    dataModel.deleteDeepSeekApiKey()
                                }
                                .buttonStyle(.bordered)
                                .foregroundColor(palette.red)
                                .font(.system(size: 11))
                            }
                        }

                        HStack {
                            Button {
                                dataModel.refreshDeepSeekBalance(forcedKey: nil)
                            } label: {
                                HStack(spacing: 4) {
                                    if dataModel.isDeepSeekBalanceLoading {
                                        ProgressView()
                                            .controlSize(.small)
                                            .scaleEffect(0.7)
                                    } else {
                                        Image(systemName: "arrow.clockwise")
                                            .font(.system(size: 10, weight: .medium))
                                    }
                                        Text(dataModel.tr("测试连接并刷新余额", "Test & Refresh"))
                                        .font(.system(size: 10, weight: .medium))
                                }
                            }
                            .buttonStyle(.bordered)
                            .disabled(dataModel.isDeepSeekBalanceLoading)

                            Spacer()

                            if let fetchedAt = bal?.fetchedAt, !fetchedAt.isEmpty {
                                Text(dataModel.tr("成功刷新: \(formatIsoTime(fetchedAt))", "Refreshed: \(formatIsoTime(fetchedAt))"))
                                    .font(.system(size: 9))
                                    .foregroundColor(palette.secondaryText)
                            }
                        }

                        Text(dataModel.tr("API Key 仅保存在本机 Application Support 私有文件中 (0600)。", "API Key is stored in local Application Support private file (0600) only."))
                            .font(.system(size: 9))
                            .foregroundColor(palette.secondaryText)

                        if let err = dataModel.deepseekBalanceError ?? bal?.errorMessage, !err.isEmpty {
                            Text(err)
                                .font(.system(size: 9))
                                .foregroundColor(palette.red)
                        }
                    }
                    .padding(10)
                    .background(palette.cardBackground)
                    .cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(palette.border, lineWidth: 1))

                    // 2. Exported Usage ZIP Card Group
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(dataModel.tr("官网用量数据导入 (ZIP)", "Exported Usage Import (ZIP)"))
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundColor(palette.primaryText)
                                Text(dataModel.tr("支持官网导出的 usage_data_*.zip 文件", "Supports usage_data_*.zip exported from DeepSeek website"))
                                    .font(.system(size: 9))
                                    .foregroundColor(palette.secondaryText)
                            }
                            Spacer()

                            Button {
                                selectAndImportDeepSeekZip()
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "square.and.arrow.down")
                                        .font(.system(size: 11))
                                    Text(dataModel.tr("导入 ZIP", "Import ZIP"))
                                        .font(.system(size: 11, weight: .medium))
                                }
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(dataModel.isDeepSeekImporting)
                        }

                        if let statusMsg = dataModel.deepseekStatusMessage {
                            Text(statusMsg)
                                .font(.system(size: 9))
                                .foregroundColor(palette.blue)
                        }

                        if usg?.hasHistory == true {
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Text(dataModel.tr("数据覆盖范围:", "Data Coverage:"))
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundColor(palette.secondaryText)
                                    Text(dataModel.tr("\(usg?.coverageStart ?? "") 至 \(usg?.coverageEnd ?? "")", "\(usg?.coverageStart ?? "") to \(usg?.coverageEnd ?? "")"))
                                        .font(.system(size: 10, weight: .semibold))
                                        .foregroundColor(palette.primaryText)
                                }
                                HStack {
                                    Text(dataModel.tr("已导入累计消费:", "Imported Spend:"))
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundColor(palette.secondaryText)
                                    Text("\(usg?.totalActualAmount ?? "0.00") \(usg?.currencies.first ?? "CNY")")
                                        .font(.system(size: 10, weight: .semibold))
                                        .foregroundColor(palette.primaryText)
                                    Spacer()
                                    Text(dataModel.tr("格式: 重复导入与重叠日期自动去重", "Auto-deduplicated on re-import"))
                                        .font(.system(size: 9))
                                        .foregroundColor(palette.secondaryText)
                                }
                            }
                            .padding(8)
                            .background(palette.inputBackground)
                            .cornerRadius(6)
                        } else {
                            Text(dataModel.tr("尚未导入 ZIP 历史。导入后将自动在 DeepSeek 主页面展示 Token、消费与模型明细。", "No ZIP imported yet. Imported data will automatically render in the DeepSeek dashboard."))
                                .font(.system(size: 9))
                                .foregroundColor(palette.secondaryText)
                        }
                    }
                    .padding(10)
                    .background(palette.cardBackground)
                    .cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(palette.border, lineWidth: 1))

                }
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
            }
        }
    }



    private func formatBalanceCardValue(raw: String?, currency: String?) -> String {
        if !dataModel.isDeepSeekConfigured {
            return dataModel.tr("未配置", "Not Set")
        }
        if dataModel.isDeepSeekBalanceLoading && (raw == nil || raw == "0.00" || raw == "—") {
            return dataModel.tr("刷新中...", "Loading...")
        }
        if let val = raw, !val.isEmpty, val != "0.00", val != "—" {
            return "\(val) \(currency ?? "CNY")"
        }
        if let val = raw, val == "0.00" && dataModel.deepseekData?.balance.fetchedAt.isEmpty == false {
            return "0.00 \(currency ?? "CNY")"
        }

        return "—"
    }

    private func selectAndImportDeepSeekZip() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.zip]
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.prompt = dataModel.tr("选择并导入", "Select & Import")
        panel.message = dataModel.tr("请选择从 DeepSeek 官网导出的 usage_data_*.zip", "Select usage_data_*.zip exported from DeepSeek website")

        if panel.runModal() == .OK, let url = panel.url {
            dataModel.importDeepSeekZip(at: url)
        }
    }


    private func modelPriceRow(key: String, detail: ModelPriceDetail, source: AISource) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(detail.displayName)
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(palette.primaryText)
            
            if detail.pricingProfile == "unpriced" {
                if key == "gpt-oss-120b" {
                        Text(dataModel.tr("开放权重｜无统一 API 单价", "Open weights | No unified API price"))
                        .font(.system(size: 9, weight: .medium))
                        .foregroundColor(palette.secondaryText)
                    Text(dataModel.tr("运行成本取决于托管平台或本地算力", "Cost depends on hosting or local compute"))
                        .font(.system(size: 8))
                        .foregroundColor(palette.tertiaryText)
                } else {
                    Text(dataModel.tr("未定价", "Unpriced"))
                        .font(.system(size: 9, weight: .medium))
                        .foregroundColor(palette.secondaryText)
                }
            } else if key == "gemini-3.1-pro", let threshold = detail.thresholdTokens {
                VStack(alignment: .leading, spacing: 3) {
                    if dataModel.language == .chinese {
                        Text("普通上下文（≤\(threshold / 1000)K）：输入 $\(detail.standardInputPrice ?? detail.inputPricePerMillion, specifier: "%.2f") · 缓存 $\(detail.standardCachedInputPrice ?? detail.cachedInputPricePerMillion ?? 0, specifier: "%.2f") · 输出 $\(detail.standardOutputPrice ?? detail.outputPricePerMillion, specifier: "%.2f")")
                        Text("长上下文（>\(threshold / 1000)K）：输入 $\(detail.longContextInputPrice ?? 0, specifier: "%.2f") · 缓存 $\(detail.longContextCachedInputPrice ?? 0, specifier: "%.2f") · 输出 $\(detail.longContextOutputPrice ?? 0, specifier: "%.2f")")
                    } else {
                        VStack(alignment: .leading, spacing: 3) {
                            Text("Standard context (≤\(threshold / 1000)K)")
                                .font(.system(size: 9, weight: .medium))
                                .fixedSize(horizontal: false, vertical: true)
                            HStack(spacing: 5) {
                                Text("Input").fixedSize(horizontal: true, vertical: false)
                                Text("$\(detail.standardInputPrice ?? detail.inputPricePerMillion, specifier: "%.2f")").monospacedDigit()
                                Text("·")
                                Text("Cached").fixedSize(horizontal: true, vertical: false)
                                Text("$\(detail.standardCachedInputPrice ?? detail.cachedInputPricePerMillion ?? 0, specifier: "%.2f")").monospacedDigit()
                                Text("·")
                                Text("Output").fixedSize(horizontal: true, vertical: false)
                                Text("$\(detail.standardOutputPrice ?? detail.outputPricePerMillion, specifier: "%.2f")").monospacedDigit()
                            }
                            .font(.system(size: 8))
                            .fixedSize(horizontal: false, vertical: true)
                        }
                        VStack(alignment: .leading, spacing: 3) {
                            Text("Long context (>\(threshold / 1000)K)")
                                .font(.system(size: 9, weight: .medium))
                                .fixedSize(horizontal: false, vertical: true)
                            HStack(spacing: 5) {
                                Text("Input").fixedSize(horizontal: true, vertical: false)
                                Text("$\(detail.longContextInputPrice ?? 0, specifier: "%.2f")").monospacedDigit()
                                Text("·")
                                Text("Cached").fixedSize(horizontal: true, vertical: false)
                                Text("$\(detail.longContextCachedInputPrice ?? 0, specifier: "%.2f")").monospacedDigit()
                                Text("·")
                                Text("Output").fixedSize(horizontal: true, vertical: false)
                                Text("$\(detail.longContextOutputPrice ?? 0, specifier: "%.2f")").monospacedDigit()
                            }
                            .font(.system(size: 8))
                            .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .foregroundColor(palette.secondaryText)
            } else {
                HStack(alignment: .top, spacing: 8) {
                    priceColumn(label: dataModel.tr("输入", "Input"), value: Binding(
                        get: { detail.inputPricePerMillion },
                        set: { newVal in
                            var updated = detail
                            updated.inputPricePerMillion = newVal
                            updated.userOverridden = true
                            updated.pricingSource = "User Override"
                            dataModel.updateModelPrice(key, detail: updated)
                        }
                    ))

                    if source == .codex {
                        priceColumn(label: dataModel.tr("缓存", "Cached"), value: Binding(
                            get: { detail.cachedInputPricePerMillion ?? 0.0 },
                            set: { newVal in
                                var updated = detail
                                updated.cachedInputPricePerMillion = newVal
                                updated.userOverridden = true
                                updated.pricingSource = "User Override"
                                dataModel.updateModelPrice(key, detail: updated)
                            }
                        ))
                    }

                    priceColumn(label: dataModel.tr("输出", "Output"), value: Binding(
                        get: { detail.outputPricePerMillion },
                        set: { newVal in
                            var updated = detail
                            updated.outputPricePerMillion = newVal
                            updated.userOverridden = true
                            updated.pricingSource = "User Override"
                            dataModel.updateModelPrice(key, detail: updated)
                        }
                    ))
                }
            }
        }
        .padding(.vertical, 4)
    }

    @ViewBuilder
    private func priceColumn(label: String, value: Binding<Double>) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(palette.secondaryText)
                .lineLimit(1)
                .fixedSize(horizontal: true, vertical: false)
            TextField("", value: value, format: .number)
                .textFieldStyle(.plain)
                .padding(.horizontal, 6)
                .padding(.vertical, 3)
                .background(palette.inputBackground)
                .cornerRadius(4)
                .overlay(RoundedRectangle(cornerRadius: 4).stroke(palette.border, lineWidth: 1))
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(palette.primaryText)
                .frame(maxWidth: .infinity)
                .onSubmit { dataModel.saveSettingsFile() }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Settings helpers

    @ViewBuilder
    private func settingsGroup<Content: View>(@ViewBuilder _ content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            content()
        }
        .padding(.horizontal, 10).padding(.vertical, 6)
        .background(palette.cardBackground)
        .cornerRadius(10)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(palette.border, lineWidth: 1)
        )
        .padding(.horizontal, 14)
    }

    private func settingRow<Control: View>(_ label: String,
                                           @ViewBuilder control: () -> Control) -> some View {
        HStack {
            Text(label).font(.system(size: 11)).foregroundColor(palette.primaryText)
            Spacer()
            control()
        }
        .padding(.vertical, 5)
    }

    // MARK: - Settings actions

    private func resetDefaults() {
        dataModel.menuBarDisplay  = .days7Total
        dataModel.displayedSources = .all
        dataModel.selectedRange   = .days7

        dataModel.refreshInterval = .min5
        dataModel.theme           = .system
        dataModel.scanOnStartup   = false
        dataModel.launchAtLogin   = false
        dataModel.logDirs         = "\(NSHomeDirectory())/.gemini/antigravity\n\(NSHomeDirectory())/.gemini/antigravity-cli"
        dataModel.selectedSource  = .antigravity
        dataModel.selectedModelFilter = "all"
        dataModel.systemPromptTokens = 0
        dataModel.pricingTier = "standard"
        dataModel.modelPrices = TokenDataModel.defaultPrices
        dataModel.updateMenuBarText()
        dataModel.saveSettingsFile()
    }
}

struct RefreshButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

struct RefreshButtonIcon: View {
    let isScanning: Bool
    let palette: QuotaViewPalette
    @State private var refreshAnimationStart: Date? = nil

    var body: some View {
        TimelineView(
            .animation(
                minimumInterval: 1.0 / 60.0,
                paused: !isScanning
            )
        ) { timeline in
            let elapsed = refreshAnimationStart.map {
                timeline.date.timeIntervalSince($0)
            } ?? 0

            let angle = isScanning
                ? (elapsed * 360.0).truncatingRemainder(dividingBy: 360.0)
                : 0.0

            ZStack {
                Image(systemName: "arrow.triangle.2.circlepath")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(isScanning ? palette.primaryText : palette.refreshButtonIcon)
                    .rotationEffect(.degrees(angle), anchor: .center)
            }
            .frame(width: 20, height: 20, alignment: .center)
        }
        .onChange(of: isScanning) { scanning in
            if scanning {
                refreshAnimationStart = Date()
            } else {
                refreshAnimationStart = nil
            }
        }
        .onAppear {
            if isScanning {
                refreshAnimationStart = Date()
            }
        }
    }
}
