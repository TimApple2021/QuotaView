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

enum PopoverPage { case dashboard, settings }

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
        blue = Color(nsColor: .systemBlue)
        orange = Color(nsColor: .systemOrange)
        red = Color(nsColor: .systemRed)
        successText = Color(nsColor: .systemGreen)
        successBackground = Color(nsColor: .systemGreen).opacity(light ? 0.14 : 0.22)
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

    var body: some View {
        ZStack {
            palette.windowBackground
                .ignoresSafeArea()
            
            Group {
                if page == .dashboard { dashboardPage }
                else                  { settingsPage  }
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
                            sourceSegmentedControl
                        }
                        .padding(.horizontal, 14)
                        .padding(.top, 10)
                        .padding(.bottom, 6)
                    }

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

            // Footer
            Divider().background(palette.divider).padding(.top, 8)
            HStack {
                Button { dataModel.triggerScan() } label: {
                    RefreshButtonIcon(isScanning: dataModel.isScanning)
                        .frame(width: 32, height: 28, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .help(dataModel.isScanning ? dataModel.tr("刷新中…", "Refreshing…") : dataModel.tr("刷新", "Refresh"))
                
                Spacer()
                
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) { page = .settings }
                } label: {
                    Image(systemName: "gearshape")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(palette.secondaryText)
                        .frame(width: 32, height: 28, alignment: .trailing)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .help(dataModel.tr("设置", "Settings"))
            }
            .padding(.horizontal, 14).padding(.vertical, 8)
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
                    if ent.status == "official_live" {
                        let availableItems = ent.items.filter { $0.status.lowercased() == "available" }
                        let count = ent.availableCount ?? availableItems.count
                        
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
        HStack(spacing: 0) {
            sourceSegment(label: "Antigravity", source: .antigravity)
            sourceSegment(label: "Codex", source: .codex)
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
    private func sourceSegment(label: String, source: AISource) -> some View {
        let isSelected = dataModel.selectedSource == source
        Button {
            dataModel.selectedSource = source
        } label: {
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
                            Picker("", selection: $dataModel.menuBarDisplay) {
                                ForEach(MenuBarDisplay.allCases) { Text(dataModel.menuBarDisplayLabel($0)).tag($0) }
                            }.pickerStyle(.menu).labelsHidden().frame(maxWidth: 140)
                        }
                        Divider()
                        settingRow(dataModel.tr("显示来源", "Displayed Sources")) {
                            Picker("", selection: $dataModel.displayedSources) {
                                ForEach(DisplayedSources.allCases) { value in
                                    Text(dataModel.displayedSourcesLabel(value)).tag(value)
                                }
                            }.pickerStyle(.menu).labelsHidden().frame(maxWidth: 140)
                        }
                        Divider()
                        settingRow(dataModel.tr("主页面默认范围", "Main Page Default Range")) {
                            Picker("", selection: $dataModel.selectedRange) {
                                ForEach(TimeRange.allCases) { Text(dataModel.timeRangeLabel($0)).tag($0) }
                            }.pickerStyle(.menu).labelsHidden().frame(maxWidth: 140)
                        }
                        Divider()
                        settingRow(dataModel.tr("自动刷新", "Auto Refresh")) {
                            Picker("", selection: $dataModel.refreshInterval) {
                                ForEach(RefreshInterval.allCases) { Text(dataModel.refreshIntervalLabel($0)).tag($0) }
                            }.pickerStyle(.menu).labelsHidden().frame(maxWidth: 140)
                        }
                        Divider()
                        settingRow(dataModel.tr("外观主题", "Appearance")) {
                            Picker("", selection: $dataModel.theme) {
                                ForEach(AppTheme.allCases) { Text(dataModel.themeLabel($0)).tag($0) }
                            }.pickerStyle(.menu).labelsHidden().frame(maxWidth: 140)
                        }
                        Divider()
                        settingRow(dataModel.tr("语言", "Language")) {
                            Picker("", selection: $dataModel.language) {
                                Text("中文").tag(AppLanguage.chinese)
                                Text("English").tag(AppLanguage.english)
                            }.pickerStyle(.menu).labelsHidden().frame(maxWidth: 140)
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
                    Text("普通上下文（≤\(threshold / 1000)K）：输入 $\(detail.standardInputPrice ?? detail.inputPricePerMillion, specifier: "%.2f") · 缓存 $\(detail.standardCachedInputPrice ?? detail.cachedInputPricePerMillion ?? 0, specifier: "%.2f") · 输出 $\(detail.standardOutputPrice ?? detail.outputPricePerMillion, specifier: "%.2f")")
                    Text("长上下文（>\(threshold / 1000)K）：输入 $\(detail.longContextInputPrice ?? 0, specifier: "%.2f") · 缓存 $\(detail.longContextCachedInputPrice ?? 0, specifier: "%.2f") · 输出 $\(detail.longContextOutputPrice ?? 0, specifier: "%.2f")")
                }
                .font(.system(size: 8, design: .monospaced))
                .foregroundColor(palette.secondaryText)
            } else {
            HStack(spacing: 8) {
                // Input Price
                Text(dataModel.tr("输入:", "Input:")).font(.system(size: 9)).foregroundColor(palette.secondaryText)
                TextField("", value: Binding(
                    get: { detail.inputPricePerMillion },
                    set: { newVal in
                        var updated = detail
                        updated.inputPricePerMillion = newVal
                        updated.userOverridden = true
                        updated.pricingSource = "User Override"
                        dataModel.updateModelPrice(key, detail: updated)
                    }
                ), format: .number)
                .textFieldStyle(.plain)
                .padding(.horizontal, 6).padding(.vertical, 3)
                .background(palette.inputBackground)
                .cornerRadius(4)
                .overlay(RoundedRectangle(cornerRadius: 4).stroke(palette.border, lineWidth: 1))
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(palette.primaryText)
                .frame(width: 55)
                .onSubmit { dataModel.saveSettingsFile() }
                
                // Cached Price (only if source is Codex)
                if source == .codex {
                    Spacer()
                    Text(dataModel.tr("缓存:", "Cached:")).font(.system(size: 9)).foregroundColor(palette.secondaryText)
                    TextField("", value: Binding(
                        get: { detail.cachedInputPricePerMillion ?? 0.0 },
                        set: { newVal in
                            var updated = detail
                            updated.cachedInputPricePerMillion = newVal
                            updated.userOverridden = true
                            updated.pricingSource = "User Override"
                            dataModel.updateModelPrice(key, detail: updated)
                        }
                    ), format: .number)
                    .textFieldStyle(.plain)
                    .padding(.horizontal, 6).padding(.vertical, 3)
                    .background(palette.inputBackground)
                    .cornerRadius(4)
                    .overlay(RoundedRectangle(cornerRadius: 4).stroke(palette.border, lineWidth: 1))
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundColor(palette.primaryText)
                    .frame(width: 55)
                    .onSubmit { dataModel.saveSettingsFile() }
                }
                
                Spacer()
                
                // Output Price
                Text(dataModel.tr("输出:", "Output:")).font(.system(size: 9)).foregroundColor(palette.secondaryText)
                TextField("", value: Binding(
                    get: { detail.outputPricePerMillion },
                    set: { newVal in
                        var updated = detail
                        updated.outputPricePerMillion = newVal
                        updated.userOverridden = true
                        updated.pricingSource = "User Override"
                        dataModel.updateModelPrice(key, detail: updated)
                    }
                ), format: .number)
                .textFieldStyle(.plain)
                .padding(.horizontal, 6).padding(.vertical, 3)
                .background(palette.inputBackground)
                .cornerRadius(4)
                .overlay(RoundedRectangle(cornerRadius: 4).stroke(palette.border, lineWidth: 1))
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(palette.primaryText)
                .frame(width: 55)
                .onSubmit { dataModel.saveSettingsFile() }
            }
            }
        }
        .padding(.vertical, 4)
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
        dataModel.displayedSources = .both
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

struct RefreshButtonIcon: View {
    let isScanning: Bool
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
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(Color(nsColor: .secondaryLabelColor).opacity(isScanning ? 0.85 : 1.0))
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
