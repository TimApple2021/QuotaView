import Foundation
import Combine
import SwiftUI
import ServiceManagement

// MARK: - Enums

enum AISource: String, CaseIterable, Identifiable {
    case antigravity = "Antigravity"
    case codex       = "Codex"
    
    var id: String { rawValue }
    
    var jsonKey: String {
        switch self {
        case .antigravity: return "antigravity"
        case .codex:       return "codex"
        }
    }
}

enum TimeRange: String, CaseIterable, Identifiable {
    case today   = "今天"
    case days7   = "近 7 天"
    case days30  = "近 30 天"
    case allTime = "本地累计"
    var id: String { rawValue }
}

enum MenuBarDisplay: String, CaseIterable, Identifiable {
    case iconOnly    = "仅图标"
    case todayTotal  = "今日可识别"
    case days7Total  = "7 日可识别"
    case days30Total = "30 日可识别"
    case allTotal    = "累计可识别"
    case allCost     = "累计费用"
    var id: String { rawValue }
}

enum RefreshInterval: Int, CaseIterable, Identifiable {
    case off   = 0
    case min1  = 1
    case min5  = 5
    case min15 = 15
    var id: Int { rawValue }
    var label: String {
        switch self {
        case .off:   return "关闭"
        case .min1:  return "1 分钟"
        case .min5:  return "5 分钟"
        case .min15: return "15 分钟"
        }
    }
}

enum AppTheme: String, CaseIterable, Identifiable {
    case system = "跟随系统"
    case light  = "浅色"
    case dark   = "深色"
    var id: String { rawValue }
    var colorScheme: ColorScheme? {
        switch self {
        case .system: return nil
        case .light:  return .light
        case .dark:   return .dark
        }
    }
}

enum AppLanguage: String, CaseIterable, Identifiable {
    case chinese = "中文"
    case english = "English"
    var id: String { rawValue }
}

enum DisplayedSources: String, CaseIterable, Identifiable {
    case both
    case antigravityOnly
    case codexOnly

    var id: String { rawValue }
}

// MARK: - TokenDataModel

struct ModelFilterOption: Identifiable, Hashable {
    let id: String
    let name: String
}

struct ModelPriceDetail: Codable, Hashable {
    var displayName: String
    var provider: String
    var inputPricePerMillion: Double
    var outputPricePerMillion: Double
    var cachedInputPricePerMillion: Double?
    var rawModelId: String?
    var pricingProfile: String?
    var pricingSource: String
    var pricingVerifiedAt: String
    var userOverridden: Bool
    var actualBillingConfirmed: Bool?
    var thresholdTokens: Int? = nil
    var standardInputPrice: Double? = nil
    var standardCachedInputPrice: Double? = nil
    var standardOutputPrice: Double? = nil
    var longContextInputPrice: Double? = nil
    var longContextCachedInputPrice: Double? = nil
    var longContextOutputPrice: Double? = nil
    var standard: [String: Double]? = nil
    var longContext: [String: Double]? = nil

    enum CodingKeys: String, CodingKey {
        case displayName = "display_name"
        case provider
        case inputPricePerMillion = "input_price_per_million"
        case outputPricePerMillion = "output_price_per_million"
        case cachedInputPricePerMillion = "cached_input_price_per_million"
        case rawModelId = "raw_model_id"
        case pricingProfile = "pricing_profile"
        case pricingSource = "pricing_source"
        case pricingVerifiedAt = "pricing_verified_at"
        case userOverridden = "user_overridden"
        case actualBillingConfirmed = "actual_billing_confirmed"
        case thresholdTokens = "threshold_tokens"
        case standardInputPrice = "standard_input_price"
        case standardCachedInputPrice = "standard_cached_input_price"
        case standardOutputPrice = "standard_output_price"
        case longContextInputPrice = "long_context_input_price"
        case longContextCachedInputPrice = "long_context_cached_input_price"
        case longContextOutputPrice = "long_context_output_price"
        case standard
        case longContext = "long_context"
    }
}

struct SettingsConfig: Codable {
    var appDataDirs: [String]
    var systemPromptTokens: Int
    var modelPrices: [String: ModelPriceDetail]
    var pricingTier: String?
    var theme: String?
    var displayedSources: String?

    enum CodingKeys: String, CodingKey {
        case appDataDirs = "app_data_dirs"
        case systemPromptTokens = "system_prompt_tokens"
        case modelPrices = "model_prices"
        case pricingTier = "pricing_tier"
        case theme
        case displayedSources = "displayed_sources"
    }
}

// MARK: - TokenDataModel

class TokenDataModel: ObservableObject {
    static let defaultPrices: [String: ModelPriceDetail] = [
        "gemini-3-flash-a": ModelPriceDetail(
            displayName: "Gemini 3.5 Flash",
            provider: "Google",
            inputPricePerMillion: 1.50,
            outputPricePerMillion: 9.00,
            cachedInputPricePerMillion: 0.15,
            rawModelId: "gemini-3-flash-a",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "gemini-3.5-flash": ModelPriceDetail(
            displayName: "Gemini 3.5 Flash",
            provider: "Google",
            inputPricePerMillion: 1.50,
            outputPricePerMillion: 9.00,
            cachedInputPricePerMillion: 0.15,
            rawModelId: "gemini-3.5-flash",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "gemini-3.6-flash": ModelPriceDetail(
            displayName: "Gemini 3.6 Flash",
            provider: "Google",
            inputPricePerMillion: 1.50,
            outputPricePerMillion: 7.50,
            cachedInputPricePerMillion: 0.15,
            rawModelId: "gemini-3.6-flash",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "Google Gemini API official pricing",
            pricingVerifiedAt: "2026-07-22",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "gemini-3.1-pro": ModelPriceDetail(
            displayName: "Gemini 3.1 Pro",
            provider: "Google",
            inputPricePerMillion: 2.00,
            outputPricePerMillion: 12.00,
            cachedInputPricePerMillion: 0.20,
            rawModelId: "gemini-3.1-pro",
            pricingProfile: "api_standard_equivalent_tiered",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false,
            thresholdTokens: 200000,
            standardInputPrice: 2.00,
            standardCachedInputPrice: 0.20,
            standardOutputPrice: 12.00,
            longContextInputPrice: 4.00,
            longContextCachedInputPrice: 0.40,
            longContextOutputPrice: 18.00,
            standard: ["input": 2.00, "cached": 0.20, "output": 12.00],
            longContext: ["input": 4.00, "cached": 0.40, "output": 18.00]
        ),
        "gpt-oss-120b": ModelPriceDetail(
            displayName: "GPT-OSS 120B",
            provider: "OpenAI / Antigravity hosted",
            inputPricePerMillion: 0,
            outputPricePerMillion: 0,
            cachedInputPricePerMillion: 0,
            rawModelId: "gpt-oss-120b",
            pricingProfile: "unpriced",
            pricingSource: "provider_specific",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "claude-sonnet-4-6": ModelPriceDetail(
            displayName: "Claude Sonnet 4.6",
            provider: "Anthropic",
            inputPricePerMillion: 3.00,
            outputPricePerMillion: 15.00,
            cachedInputPricePerMillion: nil,
            rawModelId: "claude-sonnet-4-6",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "claude-opus-4-6-thinking": ModelPriceDetail(
            displayName: "Claude Opus 4.6",
            provider: "Anthropic",
            inputPricePerMillion: 5.00,
            outputPricePerMillion: 25.00,
            cachedInputPricePerMillion: nil,
            rawModelId: "claude-opus-4-6-thinking",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "gpt-5.6-luna": ModelPriceDetail(
            displayName: "GPT-5.6 Luna",
            provider: "OpenAI",
            inputPricePerMillion: 1.00,
            outputPricePerMillion: 6.00,
            cachedInputPricePerMillion: 0.10,
            rawModelId: "gpt-5.6-luna",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "gpt-5.6-sol": ModelPriceDetail(
            displayName: "GPT-5.6 Sol",
            provider: "OpenAI",
            inputPricePerMillion: 5.00,
            outputPricePerMillion: 30.00,
            cachedInputPricePerMillion: 0.50,
            rawModelId: "gpt-5.6-sol",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "gpt-5.6-terra": ModelPriceDetail(
            displayName: "GPT-5.6 Terra",
            provider: "OpenAI",
            inputPricePerMillion: 2.50,
            outputPricePerMillion: 15.00,
            cachedInputPricePerMillion: 0.25,
            rawModelId: "gpt-5.6-terra",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "gpt-5.5": ModelPriceDetail(
            displayName: "GPT-5.5",
            provider: "OpenAI",
            inputPricePerMillion: 5.00,
            outputPricePerMillion: 30.00,
            cachedInputPricePerMillion: 0.50,
            rawModelId: "gpt-5.5",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "gpt-5.4": ModelPriceDetail(
            displayName: "GPT-5.4",
            provider: "OpenAI",
            inputPricePerMillion: 2.50,
            outputPricePerMillion: 15.00,
            cachedInputPricePerMillion: 0.25,
            rawModelId: "gpt-5.4",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "gpt-5.4-mini": ModelPriceDetail(
            displayName: "GPT-5.4 Mini",
            provider: "OpenAI",
            inputPricePerMillion: 0.75,
            outputPricePerMillion: 4.50,
            cachedInputPricePerMillion: 0.075,
            rawModelId: "gpt-5.4-mini",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "official_public_api",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "codex-auto-review": ModelPriceDetail(
            displayName: "Codex Auto Review",
            provider: "OpenAI",
            inputPricePerMillion: 0.0,
            outputPricePerMillion: 0.0,
            cachedInputPricePerMillion: 0.0,
            rawModelId: "codex-auto-review",
            pricingProfile: "unpriced",
            pricingSource: "unpriced",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        ),
        "unknown_legacy": ModelPriceDetail(
            displayName: "unknown_legacy",
            provider: "Unknown",
            inputPricePerMillion: 0.0,
            outputPricePerMillion: 0.0,
            cachedInputPricePerMillion: 0.0,
            rawModelId: "unknown_legacy",
            pricingProfile: "api_standard_equivalent",
            pricingSource: "unmapped",
            pricingVerifiedAt: "2026-07-17",
            userOverridden: false,
            actualBillingConfirmed: false
        )
    ]

    // ── Dashboard data ────────────────────────────────────────────────────
    @Published var dashboard = LightDashboard.empty
    @Published var isScanning  = false
    @Published var scanError: String? = nil

    // ── UI selection state ────────────────────────────────────────────────
    @Published var selectedSource: AISource = .antigravity {
        didSet {
            selectedModelFilter = "all"
            updateMenuBarText()
        }
    }
    @Published var selectedRange:  TimeRange = .today {
        didSet {
            UserDefaults.standard.set(selectedRange.rawValue, forKey: "defaultRange")
            normalizeSelectedModelFilter()
            persistSettingsIfReady()
        }
    }
    @Published var selectedModelFilter: String = "all"

    // ── Settings ──────────────────────────────────────────────────────────
    @Published var menuBarDisplay: MenuBarDisplay = .days7Total {
        didSet { UserDefaults.standard.set(menuBarDisplay.rawValue, forKey: "menuBarDisplay3"); updateMenuBarText(); persistSettingsIfReady() }
    }
    @Published var displayedSources: DisplayedSources = .both {
        didSet {
            UserDefaults.standard.set(displayedSources.rawValue, forKey: "displayedSources")
            enforceDisplayedSourceSelection()
            updateMenuBarText()
            persistSettingsIfReady()
        }
    }
    @Published var refreshInterval: RefreshInterval = .min5 {
        didSet { UserDefaults.standard.set(refreshInterval.rawValue, forKey: "refreshInterval"); setupTimer(); persistSettingsIfReady() }
    }
    @Published var theme: AppTheme = .system {
        didSet {
            UserDefaults.standard.set(theme.rawValue, forKey: "theme")
            applyAppearance()
            persistSettingsIfReady()
        }
    }
    @Published var language: AppLanguage = .chinese {
        didSet {
            UserDefaults.standard.set(language.rawValue, forKey: "language")
            persistSettingsIfReady()
        }
    }
    @Published var scanOnStartup: Bool = false {
        didSet { UserDefaults.standard.set(scanOnStartup, forKey: "scanOnStartup"); persistSettingsIfReady() }
    }
    @Published var launchAtLogin: Bool = false {
        didSet { UserDefaults.standard.set(launchAtLogin, forKey: "launchAtLogin"); toggleLaunchAtLogin(); persistSettingsIfReady() }
    }

    func tr(_ chinese: String, _ english: String) -> String {
        language == .english ? english : chinese
    }

    func timeRangeLabel(_ range: TimeRange) -> String {
        switch range {
        case .today: return tr("今天", "Today")
        case .days7: return tr("近 7 天", "Last 7 Days")
        case .days30: return tr("近 30 天", "Last 30 Days")
        case .allTime: return tr("本地累计", "Local All-Time")
        }
    }

    func menuBarDisplayLabel(_ display: MenuBarDisplay) -> String {
        switch display {
        case .iconOnly: return tr("仅图标", "Icon Only")
        case .todayTotal: return tr("今日可识别", "Today's Identifiable")
        case .days7Total: return tr("7 日可识别", "7-Day Identifiable")
        case .days30Total: return tr("30 日可识别", "30-Day Identifiable")
        case .allTotal: return tr("累计可识别", "All-Time Identifiable")
        case .allCost: return tr("累计费用", "All-Time Cost")
        }
    }

    func displayedSourcesLabel(_ value: DisplayedSources) -> String {
        switch value {
        case .both: return tr("Antigravity 与 Codex", "Antigravity & Codex")
        case .antigravityOnly: return tr("仅 Antigravity", "Antigravity Only")
        case .codexOnly: return tr("仅 Codex", "Codex Only")
        }
    }

    var shouldShowSourceSegment: Bool { displayedSources == .both }

    private func enforceDisplayedSourceSelection() {
        switch displayedSources {
        case .both: break
        case .antigravityOnly:
            if selectedSource != .antigravity { selectedSource = .antigravity }
        case .codexOnly:
            if selectedSource != .codex { selectedSource = .codex }
        }
    }

    func refreshIntervalLabel(_ interval: RefreshInterval) -> String {
        interval == .off ? tr("关闭", "Off") : "\(interval.rawValue) \(tr("分钟", interval.rawValue == 1 ? "minute" : "minutes"))"
    }

    func themeLabel(_ value: AppTheme) -> String {
        switch value {
        case .system: return tr("跟随系统", "System")
        case .light: return tr("浅色", "Light")
        case .dark: return tr("深色", "Dark")
        }
    }

    func quotaLabel(_ item: QuotaItem) -> String {
        if item.group.hasPrefix("chatgpt_") && item.window == "weekly" {
            let known = item.planType != "unknown" && item.planDisplayName != "Unknown"
            return known ? tr("ChatGPT \(item.planDisplayName) 周额度", "ChatGPT \(item.planDisplayName) Weekly Quota") : tr("Codex 周额度", "Codex Weekly Quota")
        }
        let name = item.name
        switch name {
        case "Gemini 周额度": return tr(name, "Gemini Weekly Quota")
        case "Gemini 五小时额度": return tr(name, "Gemini 5-Hour Quota")
        case "Claude/GPT 周额度": return tr(name, "Claude/GPT Weekly Quota")
        case "Claude/GPT 五小时额度": return tr(name, "Claude/GPT 5-Hour Quota")
        case "ChatGPT Plus 周额度": return tr(name, "ChatGPT Plus Weekly Quota")
        default: return name
        }
    }
    @Published var logDirs: String = "\(NSHomeDirectory())/.gemini/antigravity\n\(NSHomeDirectory())/.gemini/antigravity-cli" {
        didSet { persistSettingsIfReady() }
    }
    @Published var systemPromptTokens: Int = 0 {
        didSet { persistSettingsIfReady() }
    }
    @Published var pricingTier: String = "standard" {
        didSet { persistSettingsIfReady() }
    }
    
    // Per-model prices parsed from settings.json
    @Published var modelPrices: [String: ModelPriceDetail] = [:] {
        didSet {
            if !isEditingPrice { persistSettingsIfReady() }
        }
    }
    @Published var settingsError: String? = nil
    @Published private(set) var historicalModelIdsBySource: [String: Set<String>] = [:]

    // ── Internal ──────────────────────────────────────────────────────────
    @Published var menuBarText: String = ""
    private var timer: Timer?
    private var isLoadingSettings = false
    private var isEditingPrice = false

    // Model options for selection
    var modelOptions: [ModelFilterOption] {
        let models = currentStats.models ?? [:]
        var options = [ModelFilterOption(id: "all", name: tr("全部模型", "All Models"))]
        let used = models.filter { $0.value.identifiableTokens > 0 }
        
        let sortedKeys = used.keys.sorted { lhs, rhs in
            if lhs == "missing_model" { return false }
            if rhs == "missing_model" { return true }
            let l = used[lhs]?.identifiableTokens ?? 0
            let r = used[rhs]?.identifiableTokens ?? 0
            return l == r ? displayName(for: lhs) < displayName(for: rhs) : l > r
        }
        
        options += sortedKeys.map { key in
            ModelFilterOption(id: key, name: displayName(for: key))
        }
        return options
    }

    private func displayName(for model: String) -> String {
        switch model {
        case "gemini-3.5-flash", "gemini-3-flash-a": return "Gemini 3.5 Flash"
        case "gemini-3.6-flash": return "Gemini 3.6 Flash"
        case "gemini-3.1-pro": return "Gemini 3.1 Pro"
        case "gpt-oss-120b": return "GPT-OSS 120B"
        case "gpt-5.6-luna": return "GPT-5.6 Luna"
        case "gpt-5.6-sol": return "GPT-5.6 Sol"
        case "gpt-5.6-terra": return "GPT-5.6 Terra"
        case "gpt-5.5": return "GPT-5.5"
        case "gpt-5.4": return "GPT-5.4"
        case "gpt-5.4-mini": return "GPT-5.4 Mini"
        case "codex-auto-review": return "Codex Auto Review"
        case "missing_model": return tr("模型未知", "Missing Model")
        default: return model
        }
    }

    /// Settings-page catalog: cumulative history + dashboard all-time + the
    /// registered settings directory. This intentionally does not use currentStats.
    func settingsModelKeys(for source: AISource) -> [String] {
        // Hidden legacy IDs: "unknown_legacy", "codex-auto-review", "gemini-default".
        // They remain in history/doctor, but never become editable price rows.
        let current = source == .codex
            ? ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5"]
            : ["claude-opus-4-6-thinking", "claude-sonnet-4-6", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-pro", "gpt-oss-120b"]
        return current
    }

    func modelPriceDetail(for key: String, source: AISource) -> ModelPriceDetail {
        if let detail = modelPrices[key] { return detail }
        if let defaultDetail = Self.defaultPrices[key] { return defaultDetail }
        return ModelPriceDetail(
            displayName: displayName(for: key),
            provider: source == .codex ? "OpenAI" : "—",
            inputPricePerMillion: 0,
            outputPricePerMillion: 0,
            cachedInputPricePerMillion: source == .codex ? 0 : nil,
            rawModelId: key,
            pricingProfile: source == .codex ? "unpriced" : "api_standard_equivalent",
            pricingSource: source == .codex ? "unpriced" : "unmapped",
            pricingVerifiedAt: "",
            userOverridden: false,
            actualBillingConfirmed: nil
        )
    }

    private func normalizeSelectedModelFilter() {
        if selectedModelFilter != "all" && !modelOptions.contains(where: { $0.id == selectedModelFilter }) {
            selectedModelFilter = "all"
        }
    }

    // MARK: - Init

    init() {
        loadSettingsFile()
        applyAppearance()
        loadLocalCache()
        if scanOnStartup { triggerScan() }
        setupTimer()
    }

    // MARK: - Computed stats for current selection

    var currentStats: TokenSummary {
        guard let ss = dashboard.sources[selectedSource.jsonKey] else { return .zero }
        return rangeStats(ss, range: selectedRange)
    }

    var filteredStats: TokenSummary {
        let stats = currentStats
        if selectedModelFilter == "all" {
            return stats
        } else {
            return stats.models?[selectedModelFilter] ?? .zero
        }
    }

    /// Series for the chart, filtered by model if selected
    var currentSeries: [DailySeriesEntry] {
        switch selectedRange {
        case .today:   return []            // no chart for today
        case .days7:   return dashboard.last7Series
        case .days30:  return dashboard.last30Series
        case .allTime: return dashboard.allSeries
        }
    }

    var filteredSeries: [DailySeriesEntry] {
        let rawSeries = currentSeries
        if selectedModelFilter == "all" {
            return rawSeries
        }
        let srcKey = selectedSource.jsonKey
        return rawSeries.map { entry in
            guard let srcData = entry.sources[srcKey] else { return entry }
            var filteredData = DailySourceData.zero
            
            let mappedKeys: Set<String>
            if selectedSource == .antigravity {
                mappedKeys = ["gemini-3-flash-a", "claude-sonnet-4-6", "claude-opus-4-6-thinking"]
            } else {
                mappedKeys = Set(srcData.models?.keys.filter { modelPrices[$0]?.pricingSource != "unmapped" } ?? [])
            }
            
            if selectedModelFilter == "unmapped" {
                var user = 0
                var output = 0
                var ident = 0
                if let models = srcData.models {
                    for (mid, sub) in models {
                        if !mappedKeys.contains(mid) {
                            user += sub.userInputTokens
                            output += sub.outputTokens
                            ident += sub.identifiableTokens
                        }
                    }
                }
                filteredData = DailySourceData(userInputTokens: user, outputTokens: output, identifiableTokens: ident, models: nil)
            } else if let sub = srcData.models?[selectedModelFilter] {
                filteredData = sub
            }
            
            var newSources = entry.sources
            newSources[srcKey] = filteredData
            return DailySeriesEntry(date: entry.date, sources: newSources)
        }
    }

    var hasUnpricedTokens: Bool {
        guard let ss = dashboard.sources[selectedSource.jsonKey] else { return false }
        if let models = ss.allTime.models {
            for (mid, sub) in models {
                if sub.identifiableTokens > 0 && mid != "missing_model" && !isConfigured(mid) {
                    return true
                }
            }
        }
        return false
    }

    var unpricedTokensCount: Int {
        guard let ss = dashboard.sources[selectedSource.jsonKey] else { return 0 }
        let currentModels = rangeStats(ss, range: selectedRange).models ?? [:]
        
        let models = selectedModelFilter == "all" ? currentModels :
            (currentModels[selectedModelFilter].map { [selectedModelFilter: $0] } ?? [:])
        return models.reduce(0) { total, pair in
            let (mid, sub) = pair
            return total + (mid != "missing_model" && !isConfigured(mid) ? sub.identifiableTokens : 0)
        }
    }

    private func isConfigured(_ model: String) -> Bool {
        guard let price = modelPrices[model] else { return false }
        return price.pricingProfile == "codex_official_credit_rate" ||
            (price.inputPricePerMillion > 0 && price.outputPricePerMillion > 0)
    }

    var creditsDisplayText: String {
        if filteredStats.identifiableTokens == 0 { return "$0.0000" }
        if unpricedTokensCount >= filteredStats.identifiableTokens { return "未计算" }
        return String(format: "$%.4f", filteredStats.estimatedCost)
    }

    var creditsDisplayNote: String? {
        if filteredStats.identifiableTokens == 0 { return "当前范围暂无可统计数据" }
        if unpricedTokensCount >= filteredStats.identifiableTokens { return "当前模型尚未配置官方费率" }
        if unpricedTokensCount > 0 { return "另有 \(fmtLarge(unpricedTokensCount)) Token 未配置费率" }
        return nil
    }

    private func rangeStats(_ ss: SourceStats, range: TimeRange) -> TokenSummary {
        switch range {
        case .today:   return ss.today
        case .days7:   return ss.last7
        case .days30:  return ss.last30
        case .allTime: return ss.allTime
        }
    }

    // MARK: - Menu bar text

    func updateMenuBarText() {
        let ss = dashboard.sources[selectedSource.jsonKey] ?? SourceStats.empty
        switch menuBarDisplay {
        case .iconOnly:   menuBarText = ""
        case .todayTotal: menuBarText = fmt(ss.today.identifiableTokens)
        case .days7Total: menuBarText = fmt(ss.last7.identifiableTokens)
        case .days30Total: menuBarText = fmt(ss.last30.identifiableTokens)
        case .allTotal:   menuBarText = fmt(ss.allTime.identifiableTokens)
        case .allCost:
            if selectedSource == .codex {
                menuBarText = "\(String(format: "%.2f", ss.allTime.estimatedCost)) C"
            } else {
                menuBarText = "$\(String(format: "%.2f", ss.allTime.estimatedCost))"
            }
        }
    }

    // MARK: - Scan

    func triggerScan() {
        guard !isScanning else { return }
        isScanning = true
        scanError  = nil
        ScannerRunner.runScan { [weak self] result in
            DispatchQueue.main.async {
                guard let self else { return }
                self.isScanning = false
                switch result {
                case .success:
                    self.scanError = nil
                    self.loadSettingsFile()
                    self.loadLocalCache()
                case .failure(let err):
                    self.scanError = err.localizedDescription
                }
            }
        }
    }

    func loadLocalCache() {
        let dash = TokenCacheReader.loadDashboard()
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            if let error = TokenCacheReader.lastError {
                self.scanError = "数据读取失败：\(error)"
                return
            }
            self.dashboard = dash
            self.historicalModelIdsBySource = TokenCacheReader.loadHistoricalModelIds()
            self.normalizeSelectedModelFilter()
            self.scanError = nil
            self.updateMenuBarText()
        }
    }

    // MARK: - Timer

    private func setupTimer() {
        timer?.invalidate()
        guard refreshInterval != .off else { return }
        timer = Timer.scheduledTimer(withTimeInterval: Double(refreshInterval.rawValue) * 60,
                                     repeats: true) { [weak self] _ in
            self?.triggerScan()
        }
    }

    // MARK: - Launch at login

    private func toggleLaunchAtLogin() {
        if #available(macOS 13.0, *) {
            do {
                if launchAtLogin { try SMAppService.mainApp.register() }
                else             { try SMAppService.mainApp.unregister() }
            } catch { print("LaunchAtLogin error: \(error)") }
        }
    }

    // MARK: - Load settings

    static let settingsPath = TokenRuntimePaths.file("settings.json").path

    /// Apply the same theme to AppKit's menu-bar window and SwiftUI's color
    /// environment. This is intentionally the single appearance entry point.
    func applyAppearance() {
        let appearance: NSAppearance?
        switch theme {
        case .system:
            appearance = nil
        case .light:
            appearance = NSAppearance(named: .aqua)
        case .dark:
            appearance = NSAppearance(named: .darkAqua)
        }

        let apply = {
            NSApp.appearance = appearance
        }
        if Thread.isMainThread {
            apply()
        } else {
            DispatchQueue.main.async(execute: apply)
        }
    }

    private func persistSettingsIfReady() {
        guard !isLoadingSettings else { return }
        saveSettingsFile()
    }

    func updateModelPrice(_ key: String, detail: ModelPriceDetail) {
        isEditingPrice = true
        modelPrices[key] = detail
        isEditingPrice = false
    }

    private func loadSettingsFile() {
        isLoadingSettings = true
        defer { isLoadingSettings = false }
        // Load UI-only settings first
        let ud = UserDefaults.standard
        if let v = ud.string(forKey: "menuBarDisplay3"),
           let m = MenuBarDisplay(rawValue: v) { menuBarDisplay = m }
        if let v = ud.string(forKey: "defaultRange"),
           let m = TimeRange(rawValue: v) {
            selectedRange = m
        } else if let v = ud.string(forKey: "defaultRange") {
            // Migrate the labels written by older builds without changing
            // the user's selected range.
            let legacy: [String: TimeRange] = ["7 天": .days7, "30 天": .days30, "累计": .allTime]
            if let m = legacy[v] { selectedRange = m }
        }
        if let n = ud.object(forKey: "refreshInterval") as? Int,
           let m = RefreshInterval(rawValue: n) { refreshInterval = m }
        if let v = ud.string(forKey: "theme"),
           let m = AppTheme(rawValue: v) { theme = m }
        if let v = ud.string(forKey: "language"), let l = AppLanguage(rawValue: v) { language = l }
        if let v = ud.string(forKey: "displayedSources"), let s = DisplayedSources(rawValue: v) { displayedSources = s }
        scanOnStartup = ud.bool(forKey: "scanOnStartup")
        launchAtLogin = ud.bool(forKey: "launchAtLogin")

        // Load json configuration file
        guard FileManager.default.fileExists(atPath: Self.settingsPath) else { return }
        do {
            let data = try Data(contentsOf: URL(fileURLWithPath: Self.settingsPath))
            let config = try JSONDecoder().decode(SettingsConfig.self, from: data)
            self.logDirs = config.appDataDirs.joined(separator: "\n")
            self.systemPromptTokens = config.systemPromptTokens
            self.pricingTier = config.pricingTier == "priority" ? "priority" : "standard"
            self.modelPrices = config.modelPrices
            if let savedTheme = config.theme, let decodedTheme = AppTheme(rawValue: savedTheme) {
                self.theme = decodedTheme
            }
            if let savedSources = config.displayedSources, let decodedSources = DisplayedSources(rawValue: savedSources) {
                self.displayedSources = decodedSources
            }
            enforceDisplayedSourceSelection()
        } catch {
            print("读取 settings.json 失败: \(error)")
        }
    }

    func saveSettingsFile() {
        guard !isLoadingSettings else { return }
        settingsError = nil
        var dirs = logDirs.components(separatedBy: "\n").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty }
        if dirs.isEmpty {
            dirs = ["\(NSHomeDirectory())/.gemini/antigravity", "\(NSHomeDirectory())/.gemini/antigravity-cli"]
        }
        
        let config = SettingsConfig(appDataDirs: dirs, systemPromptTokens: systemPromptTokens, modelPrices: modelPrices, pricingTier: pricingTier == "priority" ? "priority" : "standard", theme: theme.rawValue, displayedSources: displayedSources.rawValue)
        do {
            let encoder = JSONEncoder()
            encoder.outputFormatting = .prettyPrinted
            let data = try encoder.encode(config)
            
            let settingsURL = URL(fileURLWithPath: Self.settingsPath)
            let backupURL = settingsURL.appendingPathExtension("bak")
            let tempURL = settingsURL.appendingPathExtension("tmp")
            
            let fm = FileManager.default
            
            // 1. Create backup first
            if fm.fileExists(atPath: settingsURL.path) {
                if fm.fileExists(atPath: backupURL.path) {
                    try? fm.removeItem(at: backupURL)
                }
                try? fm.copyItem(at: settingsURL, to: backupURL)
            }
            
            // 2. Write to tempURL
            try data.write(to: tempURL, options: .atomic)
            
            // 3. Atomic replacement using replaceItemAt
            if fm.fileExists(atPath: settingsURL.path) {
                _ = try fm.replaceItemAt(settingsURL, withItemAt: tempURL, backupItemName: nil, options: [])
            } else {
                try fm.moveItem(at: tempURL, to: settingsURL)
            }
            settingsError = nil
        } catch {
            print("写入 settings.json 失败: \(error)")
            settingsError = error.localizedDescription
        }
    }

    // MARK: - Formatting helpers

    func fmt(_ n: Int) -> String {
        if n >= 1_000_000 { return String(format: "%.1fM", Double(n) / 1_000_000) }
        if n >= 1_000     { return String(format: "%.1fK", Double(n) / 1_000) }
        return "\(n)"
    }

    func fmtCost(_ v: Double) -> String { String(format: "$%.4f", v) }

    func fmtLarge(_ n: Int) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        return formatter.string(from: NSNumber(value: n)) ?? "\(n)"
    }
}
