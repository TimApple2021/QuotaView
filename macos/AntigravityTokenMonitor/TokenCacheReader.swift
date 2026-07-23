import Foundation

enum TokenRuntimePaths {
    static let appSupportDirectory: URL = {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let url = base.appendingPathComponent("Antigravity Token Monitor", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }()

    static let cacheDirectory: URL = {
        let base = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        let url = base.appendingPathComponent("Antigravity Token Monitor", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }()

    static func file(_ name: String) -> URL { appSupportDirectory.appendingPathComponent(name) }
}

// MARK: - Lightweight dashboard structures (no conversations, no steps)
// Stat naming — Method B (honest about what we measure):
//   userInputTokens   = tokens in user messages only
//   outputTokens      = tokens the model generated
//   identifiableTokens = everything parsed from the log (user+output+tools+system+files)
//   estimatedCost     = based on userInput + output pricing (may under-estimate context amplification)

struct TokenSummary: Codable {
    let userInputTokens:    Int
    let outputTokens:       Int
    let identifiableTokens: Int
    let estimatedCost:      Double
    let pricedTokens: Int?
    let unpricedTokens: Int?
    let cachedInputTokens:  Int?
    let reasoningOutputTokens: Int?
    let callCount: Int
    let models:             [String: TokenSummary]?

    enum CodingKeys: String, CodingKey {
        case userInputTokens   = "user_input_tokens"
        case outputTokens      = "output_tokens"
        case identifiableTokens = "identifiable_tokens"
        case estimatedCost     = "estimated_cost"
        case pricedTokens = "priced_tokens"
        case unpricedTokens = "unpriced_tokens"
        case cachedInputTokens = "cached_input_tokens"
        case reasoningOutputTokens = "reasoning_output_tokens"
        case callCount = "call_count"
        case models
    }

    init(userInputTokens: Int, outputTokens: Int, identifiableTokens: Int,
         estimatedCost: Double, cachedInputTokens: Int?, reasoningOutputTokens: Int?,
         callCount: Int, models: [String: TokenSummary]?, pricedTokens: Int? = nil, unpricedTokens: Int? = nil) {
        self.userInputTokens = userInputTokens
        self.outputTokens = outputTokens
        self.identifiableTokens = identifiableTokens
        self.estimatedCost = estimatedCost
        self.pricedTokens = pricedTokens
        self.unpricedTokens = unpricedTokens
        self.cachedInputTokens = cachedInputTokens
        self.reasoningOutputTokens = reasoningOutputTokens
        self.callCount = callCount
        self.models = models
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        userInputTokens = try c.decodeIfPresent(Int.self, forKey: .userInputTokens) ?? 0
        outputTokens = try c.decodeIfPresent(Int.self, forKey: .outputTokens) ?? 0
        identifiableTokens = try c.decodeIfPresent(Int.self, forKey: .identifiableTokens) ?? 0
        estimatedCost = try c.decodeIfPresent(Double.self, forKey: .estimatedCost) ?? 0
        pricedTokens = try c.decodeIfPresent(Int.self, forKey: .pricedTokens)
        unpricedTokens = try c.decodeIfPresent(Int.self, forKey: .unpricedTokens)
        cachedInputTokens = try c.decodeIfPresent(Int.self, forKey: .cachedInputTokens)
        reasoningOutputTokens = try c.decodeIfPresent(Int.self, forKey: .reasoningOutputTokens)
        callCount = try c.decodeIfPresent(Int.self, forKey: .callCount) ?? 0
        models = try c.decodeIfPresent([String: TokenSummary].self, forKey: .models)
    }

    static let zero = TokenSummary(userInputTokens: 0, outputTokens: 0,
                                    identifiableTokens: 0, estimatedCost: 0,
                                    cachedInputTokens: 0, reasoningOutputTokens: 0,
                                    callCount: 0,
                                    models: nil)
}

struct SourceStats: Codable {
    let today:   TokenSummary
    let last7:   TokenSummary
    let last30:  TokenSummary
    let allTime: TokenSummary

    enum CodingKeys: String, CodingKey {
        case today; case last7 = "last_7"; case last30 = "last_30"; case allTime = "all_time"
    }

    init(today: TokenSummary, last7: TokenSummary, last30: TokenSummary, allTime: TokenSummary) {
        self.today = today; self.last7 = last7; self.last30 = last30; self.allTime = allTime
    }

    static let empty = SourceStats(today: .zero, last7: .zero, last30: .zero, allTime: .zero)

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        today = try c.decodeIfPresent(TokenSummary.self, forKey: .today) ?? .zero
        last7 = try c.decodeIfPresent(TokenSummary.self, forKey: .last7) ?? .zero
        last30 = try c.decodeIfPresent(TokenSummary.self, forKey: .last30) ?? .zero
        allTime = try c.decodeIfPresent(TokenSummary.self, forKey: .allTime) ?? .zero
    }
}

struct DailySourceData: Codable {
    let userInputTokens:    Int
    let outputTokens:       Int
    let identifiableTokens: Int
    let models:             [String: DailySourceData]?

    enum CodingKeys: String, CodingKey {
        case userInputTokens    = "user_input_tokens"
        case outputTokens       = "output_tokens"
        case identifiableTokens = "identifiable_tokens"
        case models
    }

    init(userInputTokens: Int, outputTokens: Int, identifiableTokens: Int,
         models: [String: DailySourceData]?) {
        self.userInputTokens = userInputTokens
        self.outputTokens = outputTokens
        self.identifiableTokens = identifiableTokens
        self.models = models
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        userInputTokens = try c.decodeIfPresent(Int.self, forKey: .userInputTokens) ?? 0
        outputTokens = try c.decodeIfPresent(Int.self, forKey: .outputTokens) ?? 0
        identifiableTokens = try c.decodeIfPresent(Int.self, forKey: .identifiableTokens) ?? 0
        models = try c.decodeIfPresent([String: DailySourceData].self, forKey: .models)
    }

    static let zero = DailySourceData(userInputTokens: 0, outputTokens: 0, identifiableTokens: 0, models: nil)
}

struct DailySeriesEntry: Codable, Identifiable {
    let date: String
    let sources: [String: DailySourceData]
    var id: String { date }
}

struct CodexAuthInfo: Codable {
    let authMode: String
    let planType: String
    
    enum CodingKeys: String, CodingKey {
        case authMode = "auth_mode"
        case planType = "plan_type"
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        authMode = (try? c.decode(String.self, forKey: .authMode)) ?? "Unknown"
        planType = (try? c.decode(String.self, forKey: .planType)) ?? "unknown_plan"
    }
}

struct AnyCodingKey: CodingKey {
    let stringValue: String
    init?(stringValue: String) { self.stringValue = stringValue; intValue = nil }
    let intValue: Int?
    init?(intValue: Int) { self.intValue = intValue; stringValue = "\(intValue)" }
}

struct LossyQuotaStatusMap: Codable {
    let values: [String: QuotaStatus]

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: AnyCodingKey.self)
        var result: [String: QuotaStatus] = [:]
        for key in c.allKeys {
            if let status = try? c.decode(QuotaStatus.self, forKey: key) { result[key.stringValue] = status }
        }
        values = result
    }

    func encode(to encoder: Encoder) throws { try values.encode(to: encoder) }
}

struct QuotaItem: Codable, Identifiable, Hashable {
    let name: String
    let group: String
    let window: String
    let planType: String
    let planDisplayName: String
    let planSource: String
    let planConfidence: String
    let usedPercent: Double
    let resetTime: String
    let isExpired: Bool?
    let confidence: String?
    
    var id: String { name }
    
    enum CodingKeys: String, CodingKey {
        case name
        case group, window
        case planType = "plan_type"
        case planDisplayName = "plan_display_name"
        case planSource = "plan_source"
        case planConfidence = "plan_confidence"
        case usedPercent = "used_percent"
        case resetTime = "reset_time"
        case isExpired = "is_expired"
        case confidence
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        let encodedGroup = (try? c.decode(String.self, forKey: .group)) ?? ""
        let encodedWindow = (try? c.decode(String.self, forKey: .window)) ?? ""
        let rawName = (try? c.decode(String.self, forKey: .name)) ?? ([encodedGroup, encodedWindow].filter { !$0.isEmpty }.joined(separator: " "))
        name = rawName
        let legacyType: String = rawName.contains("Plus") ? "plus" : rawName.contains("Pro") ? "pro" : rawName.contains("Free") ? "free" : "unknown"
        let legacyDisplay: String = legacyType == "unknown" ? "Unknown" : legacyType.capitalized
        let legacyCodex = rawName.contains("ChatGPT") || rawName.contains("Codex")
        group = encodedGroup.isEmpty && legacyCodex ? "chatgpt_\(legacyType)" : (encodedGroup.isEmpty ? "官方额度" : encodedGroup)
        window = encodedWindow.isEmpty && legacyCodex && rawName.contains("周额度") ? "weekly" : encodedWindow
        planType = (try? c.decode(String.self, forKey: .planType)) ?? legacyType
        planDisplayName = (try? c.decode(String.self, forKey: .planDisplayName)) ?? legacyDisplay
        planSource = (try? c.decode(String.self, forKey: .planSource)) ?? (rawName.isEmpty ? "none" : "legacy_dashboard")
        planConfidence = (try? c.decode(String.self, forKey: .planConfidence)) ?? "legacy_observed"
        usedPercent = (try? c.decode(Double.self, forKey: .usedPercent)) ?? 0
        resetTime = (try? c.decode(String.self, forKey: .resetTime)) ?? ""
        isExpired = try? c.decode(Bool.self, forKey: .isExpired)
        confidence = try? c.decode(String.self, forKey: .confidence)
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(name, forKey: .name)
        try c.encode(group, forKey: .group)
        try c.encode(window, forKey: .window)
        try c.encode(planType, forKey: .planType)
        try c.encode(planDisplayName, forKey: .planDisplayName)
        try c.encode(planSource, forKey: .planSource)
        try c.encode(planConfidence, forKey: .planConfidence)
        try c.encode(usedPercent, forKey: .usedPercent)
        try c.encode(resetTime, forKey: .resetTime)
        try c.encodeIfPresent(isExpired, forKey: .isExpired)
        try c.encodeIfPresent(confidence, forKey: .confidence)
    }
}

struct LossyQuotaItems: Codable {
    let values: [QuotaItem]

    init(from decoder: Decoder) throws {
        var container = try decoder.unkeyedContainer()
        var result: [QuotaItem] = []
        while !container.isAtEnd {
            if let item = try? container.decode(QuotaItem.self) { result.append(item) }
            else { _ = try? container.superDecoder() }
        }
        values = result
    }

    func encode(to encoder: Encoder) throws { try values.encode(to: encoder) }
}

struct ResetEntitlementItem: Codable, Hashable, Identifiable {
    let entitlementId: String
    let stableKey: String
    let type: String
    let status: String
    let normalizedStatus: String
    let isAvailable: Bool
    let statusInferred: Bool
    let grantedAt: String?
    let displayName: String
    let expiresOn: String?
    let expiresAt: String?
    let rawExpiration: String
    
    var id: String { entitlementId.isEmpty ? "\(type)|\(displayName)|\(rawExpiration)" : entitlementId }
    
    enum CodingKeys: String, CodingKey {
        case entitlementId = "id"
        case stableKey = "stable_key"
        case type, status, normalizedStatus = "normalized_status", isAvailable = "is_available", statusInferred = "status_inferred"
        case grantedAt = "granted_at"
        case displayName = "display_name"
        case expiresOn = "expires_on"
        case expiresAt = "expires_at"
        case rawExpiration = "raw_expiration"
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        entitlementId = (try? c.decode(String.self, forKey: .entitlementId)) ?? ""
        stableKey = (try? c.decode(String.self, forKey: .stableKey)) ?? entitlementId
        type = (try? c.decode(String.self, forKey: .type)) ?? "unknown_reset"
        // Pre-status dashboards only contained active entitlements; keep them
        // readable until the next live scan supplies the official status.
        status = (try? c.decode(String.self, forKey: .status)) ?? "available"
        normalizedStatus = (try? c.decode(String.self, forKey: .normalizedStatus)) ?? status.lowercased()
        isAvailable = (try? c.decode(Bool.self, forKey: .isAvailable)) ?? ["available", "active", "ready", "enabled"].contains(status.lowercased())
        statusInferred = (try? c.decode(Bool.self, forKey: .statusInferred)) ?? false
        grantedAt = try? c.decode(String.self, forKey: .grantedAt)
        displayName = (try? c.decode(String.self, forKey: .displayName)) ?? "Reset"
        expiresOn = try? c.decode(String.self, forKey: .expiresOn)
        expiresAt = try? c.decode(String.self, forKey: .expiresAt)
        rawExpiration = (try? c.decode(String.self, forKey: .rawExpiration)) ?? ""
    }
}

struct LossyResetEntitlementItems: Codable {
    let values: [ResetEntitlementItem]

    init(from decoder: Decoder) throws {
        var container = try decoder.unkeyedContainer()
        var result: [ResetEntitlementItem] = []
        while !container.isAtEnd {
            if let item = try? container.decode(ResetEntitlementItem.self) {
                result.append(item)
            } else {
                _ = try? container.superDecoder()
            }
        }
        values = result
    }

    func encode(to encoder: Encoder) throws { try values.encode(to: encoder) }
}

struct ResetEntitlements: Codable, Hashable {
    let status: String
    let message: String?
    let availableCount: Int?
    let items: [ResetEntitlementItem]
    let countSemantics: String?
    let sourcePath: String?
    let originalFieldName: String?
    let availableCountFieldName: String?
    let expiresAtFieldName: String?
    let observedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case status, message, items
        case availableCount = "available_count"
        case countSemantics = "count_semantics"
        case sourcePath = "source_path"
        case originalFieldName = "original_field_name"
        case availableCountFieldName = "available_count_field_name"
        case expiresAtFieldName = "expires_at_field_name"
        case observedAt = "observed_at"
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        status = (try? c.decode(String.self, forKey: .status)) ?? "unavailable"
        message = try? c.decode(String.self, forKey: .message)
        availableCount = try? c.decode(Int.self, forKey: .availableCount)
        let parsedItems = (try? c.decode(LossyResetEntitlementItems.self, forKey: .items))?.values ?? []
        items = parsedItems
        countSemantics = try? c.decode(String.self, forKey: .countSemantics)
        sourcePath = try? c.decode(String.self, forKey: .sourcePath)
        originalFieldName = try? c.decode(String.self, forKey: .originalFieldName)
        availableCountFieldName = try? c.decode(String.self, forKey: .availableCountFieldName)
        expiresAtFieldName = try? c.decode(String.self, forKey: .expiresAtFieldName)
        observedAt = try? c.decode(String.self, forKey: .observedAt)
    }
}

struct QuotaStatus: Codable, Hashable {
    let status: String
    let message: String
    let items: [QuotaItem]
    let resetEntitlements: ResetEntitlements?

    enum CodingKeys: String, CodingKey {
        case status, message, items
        case resetEntitlements = "reset_entitlements"
    }

    init(status: String, message: String, items: [QuotaItem], resetEntitlements: ResetEntitlements? = nil) {
        self.status = status
        self.message = message
        self.items = items
        self.resetEntitlements = resetEntitlements
    }

    init(from decoder: Decoder) throws {
        if let array = try? decoder.singleValueContainer().decode(LossyQuotaItems.self) {
            self.init(status: array.values.isEmpty ? "unavailable" : "official_live", message: "", items: array.values, resetEntitlements: nil)
            return
        }
        let c = try decoder.container(keyedBy: CodingKeys.self)
        let parsedItems = (try? c.decode(LossyQuotaItems.self, forKey: .items))?.values ?? []
        self.init(
            status: (try? c.decode(String.self, forKey: .status)) ?? "unavailable",
            message: (try? c.decode(String.self, forKey: .message)) ?? "",
            items: parsedItems,
            resetEntitlements: try? c.decode(ResetEntitlements.self, forKey: .resetEntitlements)
        )
    }
}

struct LightDashboard: Codable {
    let lastScanTime:   String
    let scanDurationMs: Int
    let todayHasHourly: Bool
    let sources:        [String: SourceStats]
    let last7Series:    [DailySeriesEntry]
    let last30Series:   [DailySeriesEntry]
    let allSeries:      [DailySeriesEntry]
    let codexAuthInfo:  CodexAuthInfo?
    let quotaStatus:    [String: QuotaStatus]?
    let deepseek:       DeepSeekDashboardData?

    enum CodingKeys: String, CodingKey {
        case lastScanTime   = "last_scan_time"
        case scanDurationMs = "scan_duration_ms"
        case todayHasHourly = "today_has_hourly"
        case sources
        case last7Series    = "last_7_series"
        case last30Series   = "last_30_series"
        case allSeries      = "all_series"
        case codexAuthInfo  = "codex_auth_info"
        case quotaStatus    = "quota_status"
        case deepseek
    }

    init(lastScanTime: String, scanDurationMs: Int, todayHasHourly: Bool,
         sources: [String: SourceStats], last7Series: [DailySeriesEntry],
         last30Series: [DailySeriesEntry], allSeries: [DailySeriesEntry],
         codexAuthInfo: CodexAuthInfo?, quotaStatus: [String: QuotaStatus]?,
         deepseek: DeepSeekDashboardData? = nil) {
        self.lastScanTime = lastScanTime
        self.scanDurationMs = scanDurationMs
        self.todayHasHourly = todayHasHourly
        self.sources = sources
        self.last7Series = last7Series
        self.last30Series = last30Series
        self.allSeries = allSeries
        self.codexAuthInfo = codexAuthInfo
        self.quotaStatus = quotaStatus
        self.deepseek = deepseek
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        lastScanTime = try c.decodeIfPresent(String.self, forKey: .lastScanTime) ?? "—"
        scanDurationMs = try c.decodeIfPresent(Int.self, forKey: .scanDurationMs) ?? 0
        todayHasHourly = try c.decodeIfPresent(Bool.self, forKey: .todayHasHourly) ?? false
        sources = try c.decodeIfPresent([String: SourceStats].self, forKey: .sources) ?? [:]
        last7Series = try c.decodeIfPresent([DailySeriesEntry].self, forKey: .last7Series) ?? []
        last30Series = try c.decodeIfPresent([DailySeriesEntry].self, forKey: .last30Series) ?? []
        allSeries = try c.decodeIfPresent([DailySeriesEntry].self, forKey: .allSeries) ?? []
        codexAuthInfo = try c.decodeIfPresent(CodexAuthInfo.self, forKey: .codexAuthInfo)
        quotaStatus = (try? c.decode(LossyQuotaStatusMap.self, forKey: .quotaStatus))?.values
        deepseek = try? c.decodeIfPresent(DeepSeekDashboardData.self, forKey: .deepseek)
    }

    static let empty = LightDashboard(
        lastScanTime: "—", scanDurationMs: 0, todayHasHourly: false,
        sources: [:], last7Series: [], last30Series: [], allSeries: [],
        codexAuthInfo: nil, quotaStatus: nil, deepseek: nil
    )
}

// MARK: - DeepSeek Data Structures

struct DeepSeekBalanceInfoItemModel: Codable, Hashable, Identifiable {
    let currency: String
    let totalBalance: String
    let grantedBalance: String
    let toppedUpBalance: String

    var id: String { currency }

    enum CodingKeys: String, CodingKey {
        case currency
        case totalBalance = "total_balance"
        case grantedBalance = "granted_balance"
        case toppedUpBalance = "topped_up_balance"
    }

    init(currency: String, totalBalance: String, grantedBalance: String, toppedUpBalance: String) {
        self.currency = currency
        self.totalBalance = totalBalance
        self.grantedBalance = grantedBalance
        self.toppedUpBalance = toppedUpBalance
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        currency = (try? c.decode(String.self, forKey: .currency)) ?? "CNY"
        totalBalance = (try? c.decode(String.self, forKey: .totalBalance)) ?? "0.00"
        grantedBalance = (try? c.decode(String.self, forKey: .grantedBalance)) ?? "0.00"
        toppedUpBalance = (try? c.decode(String.self, forKey: .toppedUpBalance)) ?? "0.00"
    }
}

struct DeepSeekBalanceInfo: Codable, Hashable {
    let configured: Bool
    let isAvailable: Bool
    let currency: String
    let totalBalance: String
    let grantedBalance: String
    let toppedUpBalance: String
    let balanceInfos: [DeepSeekBalanceInfoItemModel]
    let fetchedAt: String
    let errorCode: String?
    let errorMessage: String?

    enum CodingKeys: String, CodingKey {
        case configured
        case isAvailable = "is_available"
        case currency
        case totalBalance = "total_balance"
        case grantedBalance = "granted_balance"
        case toppedUpBalance = "topped_up_balance"
        case balanceInfos = "balance_infos"
        case fetchedAt = "fetched_at"
        case errorCode = "error_code"
        case errorMessage = "error_message"
    }

    init(configured: Bool, isAvailable: Bool, currency: String, totalBalance: String,
         grantedBalance: String, toppedUpBalance: String,
         balanceInfos: [DeepSeekBalanceInfoItemModel] = [],
         fetchedAt: String, errorCode: String? = nil, errorMessage: String? = nil) {
        self.configured = configured
        self.isAvailable = isAvailable
        self.currency = currency
        self.totalBalance = totalBalance
        self.grantedBalance = grantedBalance
        self.toppedUpBalance = toppedUpBalance
        self.balanceInfos = balanceInfos
        self.fetchedAt = fetchedAt
        self.errorCode = errorCode
        self.errorMessage = errorMessage
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        configured = (try? c.decode(Bool.self, forKey: .configured)) ?? false
        isAvailable = (try? c.decode(Bool.self, forKey: .isAvailable)) ?? false
        currency = (try? c.decode(String.self, forKey: .currency)) ?? "CNY"
        totalBalance = (try? c.decode(String.self, forKey: .totalBalance)) ?? "0.00"
        grantedBalance = (try? c.decode(String.self, forKey: .grantedBalance)) ?? "0.00"
        toppedUpBalance = (try? c.decode(String.self, forKey: .toppedUpBalance)) ?? "0.00"
        balanceInfos = (try? c.decode([DeepSeekBalanceInfoItemModel].self, forKey: .balanceInfos)) ?? []
        fetchedAt = (try? c.decode(String.self, forKey: .fetchedAt)) ?? ""
        errorCode = try? c.decode(String.self, forKey: .errorCode)
        errorMessage = try? c.decode(String.self, forKey: .errorMessage)
    }
}


struct DeepSeekModelItem: Codable, Hashable, Identifiable {
    let modelId: String
    let requestCount: Int
    let inputTokens: Int
    let outputTokens: Int
    let totalTokens: Int
    let actualAmount: String
    let currency: String

    var id: String { modelId }

    enum CodingKeys: String, CodingKey {
        case modelId = "model_id"
        case requestCount = "request_count"
        case inputTokens = "input_tokens"
        case outputTokens = "output_tokens"
        case totalTokens = "total_tokens"
        case actualAmount = "actual_amount"
        case currency
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        modelId = (try? c.decode(String.self, forKey: .modelId)) ?? "unknown"
        requestCount = (try? c.decode(Int.self, forKey: .requestCount)) ?? 0
        inputTokens = (try? c.decode(Int.self, forKey: .inputTokens)) ?? 0
        outputTokens = (try? c.decode(Int.self, forKey: .outputTokens)) ?? 0
        totalTokens = (try? c.decode(Int.self, forKey: .totalTokens)) ?? (inputTokens + outputTokens)
        actualAmount = (try? c.decode(String.self, forKey: .actualAmount)) ?? "0.00"
        currency = (try? c.decode(String.self, forKey: .currency)) ?? "CNY"
    }
}

struct DeepSeekKeyItem: Codable, Hashable, Identifiable {
    let canonicalKeyId: String?
    let apiKeyName: String
    let apiKeyMasked: String
    let requestCount: Int
    let inputTokens: Int
    let outputTokens: Int
    let totalTokens: Int
    let actualAmount: String
    let currency: String

    var id: String { canonicalKeyId ?? "\(apiKeyName)_\(apiKeyMasked)" }

    enum CodingKeys: String, CodingKey {
        case canonicalKeyId = "canonical_key_id"
        case apiKeyName = "api_key_name"
        case apiKeyMasked = "api_key_masked"
        case requestCount = "request_count"
        case inputTokens = "input_tokens"
        case outputTokens = "output_tokens"
        case totalTokens = "total_tokens"
        case actualAmount = "actual_amount"
        case currency
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        canonicalKeyId = try? c.decode(String.self, forKey: .canonicalKeyId)
        apiKeyName = (try? c.decode(String.self, forKey: .apiKeyName)) ?? "默认"
        apiKeyMasked = (try? c.decode(String.self, forKey: .apiKeyMasked)) ?? "sk-****"
        requestCount = (try? c.decode(Int.self, forKey: .requestCount)) ?? 0
        inputTokens = (try? c.decode(Int.self, forKey: .inputTokens)) ?? 0
        outputTokens = (try? c.decode(Int.self, forKey: .outputTokens)) ?? 0
        totalTokens = (try? c.decode(Int.self, forKey: .totalTokens)) ?? (inputTokens + outputTokens)
        actualAmount = (try? c.decode(String.self, forKey: .actualAmount)) ?? "0.00"
        currency = (try? c.decode(String.self, forKey: .currency)) ?? "CNY"
    }
}

struct DeepSeekDailyEntry: Codable, Hashable, Identifiable {
    let date: String
    let requestCount: Int
    let inputTokens: Int
    let outputTokens: Int
    let totalTokens: Int
    let actualAmount: String
    let currency: String

    var id: String { date }

    enum CodingKeys: String, CodingKey {
        case date
        case requestCount = "request_count"
        case inputTokens = "input_tokens"
        case outputTokens = "output_tokens"
        case totalTokens = "total_tokens"
        case actualAmount = "actual_amount"
        case currency
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        date = (try? c.decode(String.self, forKey: .date)) ?? ""
        requestCount = (try? c.decode(Int.self, forKey: .requestCount)) ?? 0
        inputTokens = (try? c.decode(Int.self, forKey: .inputTokens)) ?? 0
        outputTokens = (try? c.decode(Int.self, forKey: .outputTokens)) ?? 0
        totalTokens = (try? c.decode(Int.self, forKey: .totalTokens)) ?? (inputTokens + outputTokens)
        actualAmount = (try? c.decode(String.self, forKey: .actualAmount)) ?? "0.00"
        currency = (try? c.decode(String.self, forKey: .currency)) ?? "CNY"
    }
}

struct DeepSeekMonthlySummary: Codable, Hashable, Identifiable {
    let month: String
    let coverageStart: String
    let coverageEnd: String
    let totalActualAmount: String
    let totalRequestCount: Int
    let totalInputTokens: Int
    let totalOutputTokens: Int
    let totalTokens: Int
    let models: [DeepSeekModelItem]
    let keys: [DeepSeekKeyItem]

    var id: String { month }

    enum CodingKeys: String, CodingKey {
        case month
        case coverageStart = "coverage_start"
        case coverageEnd = "coverage_end"
        case totalActualAmount = "total_actual_amount"
        case totalRequestCount = "total_request_count"
        case totalInputTokens = "total_input_tokens"
        case totalOutputTokens = "total_output_tokens"
        case totalTokens = "total_tokens"
        case models, keys
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        month = (try? c.decode(String.self, forKey: .month)) ?? ""
        coverageStart = (try? c.decode(String.self, forKey: .coverageStart)) ?? ""
        coverageEnd = (try? c.decode(String.self, forKey: .coverageEnd)) ?? ""
        totalActualAmount = (try? c.decode(String.self, forKey: .totalActualAmount)) ?? "0.00"
        totalRequestCount = (try? c.decode(Int.self, forKey: .totalRequestCount)) ?? 0
        totalInputTokens = (try? c.decode(Int.self, forKey: .totalInputTokens)) ?? 0
        totalOutputTokens = (try? c.decode(Int.self, forKey: .totalOutputTokens)) ?? 0
        totalTokens = (try? c.decode(Int.self, forKey: .totalTokens)) ?? (totalInputTokens + totalOutputTokens)
        models = (try? c.decode([DeepSeekModelItem].self, forKey: .models)) ?? []
        keys = (try? c.decode([DeepSeekKeyItem].self, forKey: .keys)) ?? []
    }
}

struct DeepSeekUsageInfo: Codable, Hashable {
    let hasHistory: Bool
    let coverageStart: String
    let coverageEnd: String
    let lastImportAt: String
    let currencies: [String]
    let totalRequestCount: Int
    let totalInputTokens: Int
    let totalOutputTokens: Int
    let totalTokens: Int
    let totalActualAmount: String
    let models: [DeepSeekModelItem]
    let keys: [DeepSeekKeyItem]
    let dailySeries: [DeepSeekDailyEntry]
    let availableMonths: [String]
    let monthlySummaries: [DeepSeekMonthlySummary]

    enum CodingKeys: String, CodingKey {
        case hasHistory = "has_history"
        case coverageStart = "coverage_start"
        case coverageEnd = "coverage_end"
        case lastImportAt = "last_import_at"
        case currencies
        case totalRequestCount = "total_request_count"
        case totalInputTokens = "total_input_tokens"
        case totalOutputTokens = "total_output_tokens"
        case totalTokens = "total_tokens"
        case totalActualAmount = "total_actual_amount"
        case models, keys
        case dailySeries = "daily_series"
        case availableMonths = "available_months"
        case monthlySummaries = "monthly_summaries"
    }

    init(hasHistory: Bool, coverageStart: String, coverageEnd: String, lastImportAt: String,
         currencies: [String] = ["CNY"], totalRequestCount: Int = 0, totalInputTokens: Int = 0,
         totalOutputTokens: Int = 0, totalTokens: Int = 0, totalActualAmount: String = "0.00",
         models: [DeepSeekModelItem] = [], keys: [DeepSeekKeyItem] = [], dailySeries: [DeepSeekDailyEntry] = []) {
        self.hasHistory = hasHistory
        self.coverageStart = coverageStart
        self.coverageEnd = coverageEnd
        self.lastImportAt = lastImportAt
        self.currencies = currencies
        self.totalRequestCount = totalRequestCount
        self.totalInputTokens = totalInputTokens
        self.totalOutputTokens = totalOutputTokens
        self.totalTokens = totalTokens
        self.totalActualAmount = totalActualAmount
        self.models = models
        self.keys = keys
        self.dailySeries = dailySeries
        self.availableMonths = []
        self.monthlySummaries = []
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        hasHistory = (try? c.decode(Bool.self, forKey: .hasHistory)) ?? false
        coverageStart = (try? c.decode(String.self, forKey: .coverageStart)) ?? ""
        coverageEnd = (try? c.decode(String.self, forKey: .coverageEnd)) ?? ""
        lastImportAt = (try? c.decode(String.self, forKey: .lastImportAt)) ?? ""
        currencies = (try? c.decode([String].self, forKey: .currencies)) ?? ["CNY"]
        totalRequestCount = (try? c.decode(Int.self, forKey: .totalRequestCount)) ?? 0
        totalInputTokens = (try? c.decode(Int.self, forKey: .totalInputTokens)) ?? 0
        totalOutputTokens = (try? c.decode(Int.self, forKey: .totalOutputTokens)) ?? 0
        totalTokens = (try? c.decode(Int.self, forKey: .totalTokens)) ?? (totalInputTokens + totalOutputTokens)
        totalActualAmount = (try? c.decode(String.self, forKey: .totalActualAmount)) ?? "0.00"
        models = (try? c.decode([DeepSeekModelItem].self, forKey: .models)) ?? []
        keys = (try? c.decode([DeepSeekKeyItem].self, forKey: .keys)) ?? []
        dailySeries = (try? c.decode([DeepSeekDailyEntry].self, forKey: .dailySeries)) ?? []
        availableMonths = (try? c.decode([String].self, forKey: .availableMonths)) ?? []
        monthlySummaries = (try? c.decode([DeepSeekMonthlySummary].self, forKey: .monthlySummaries)) ?? []
    }
}

struct DeepSeekUsageViewData: Hashable {
    let coverageStart: String
    let coverageEnd: String
    let totalActualAmount: String
    let totalRequestCount: Int
    let totalTokens: Int
    let currencies: [String]
    let models: [DeepSeekModelItem]
    let keys: [DeepSeekKeyItem]

    var hasHistory: Bool {
        totalTokens > 0 || totalRequestCount > 0 || totalActualAmount != "0.00"
    }

    init(_ usage: DeepSeekUsageInfo) {
        coverageStart = usage.coverageStart; coverageEnd = usage.coverageEnd
        totalActualAmount = usage.totalActualAmount; totalRequestCount = usage.totalRequestCount
        totalTokens = usage.totalTokens; currencies = usage.currencies; models = usage.models; keys = usage.keys
    }

    init(_ summary: DeepSeekMonthlySummary, currencies: [String]) {
        coverageStart = summary.coverageStart; coverageEnd = summary.coverageEnd
        totalActualAmount = summary.totalActualAmount; totalRequestCount = summary.totalRequestCount
        totalTokens = summary.totalTokens; self.currencies = currencies; models = summary.models; keys = summary.keys
    }
}

struct DeepSeekDashboardData: Codable, Hashable {
    var balance: DeepSeekBalanceInfo
    let usage: DeepSeekUsageInfo

    init(balance: DeepSeekBalanceInfo, usage: DeepSeekUsageInfo) {
        self.balance = balance
        self.usage = usage
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        let defaultBal = try? c.decode(DeepSeekBalanceInfo.self, forKey: .balance)
        let defaultUsg = try? c.decode(DeepSeekUsageInfo.self, forKey: .usage)
        if let b = defaultBal, let u = defaultUsg {
            balance = b
            usage = u
        } else {
            balance = DeepSeekBalanceInfo(configured: false, isAvailable: false, currency: "CNY", totalBalance: "0.00", grantedBalance: "0.00", toppedUpBalance: "0.00", fetchedAt: "", errorCode: "unconfigured", errorMessage: nil)
            usage = DeepSeekUsageInfo(hasHistory: false, coverageStart: "", coverageEnd: "", lastImportAt: "")
        }
    }
}



// MARK: - TokenCacheReader

struct TokenCacheReader {
    static let dashboardPath = TokenRuntimePaths.file("dashboard.json").path
    static let dailyHistoryPath = TokenRuntimePaths.file("daily_history.json").path
    static let dashboardBackupPath = TokenRuntimePaths.file("dashboard.json.bak").path
    private(set) static var lastError: String?

    static func loadDashboard() -> LightDashboard {
        let candidates = [dashboardPath, dashboardBackupPath]
        var diagnostics: [String] = []
        for (index, path) in candidates.enumerated() {
            for attempt in 0..<(index == 0 ? 2 : 1) {
                guard FileManager.default.fileExists(atPath: path) else { break }
                do {
                    let data = try Data(contentsOf: URL(fileURLWithPath: path))
                    let dashboard = try JSONDecoder().decode(LightDashboard.self, from: data)
                    if index == 1 {
                        restorePrimaryDashboard(data)
                    }
                    lastError = nil
                    return dashboard
                } catch {
                    let detail = describe(error)
                    diagnostics.append("\(path) [attempt \(attempt + 1)]: \(detail)")
                    print("解析 dashboard.json 失败: \(detail)")
                    if index == 0 && attempt == 0 { Thread.sleep(forTimeInterval: 0.15) }
                }
            }
        }
        lastError = diagnostics.joined(separator: " | ")
        return .empty
    }

    private static func restorePrimaryDashboard(_ data: Data) {
        let temporary = dashboardPath + ".restore.tmp"
        do {
            try data.write(to: URL(fileURLWithPath: temporary), options: .atomic)
            let primary = URL(fileURLWithPath: dashboardPath)
            if FileManager.default.fileExists(atPath: dashboardPath) {
                _ = try FileManager.default.replaceItemAt(primary, withItemAt: URL(fileURLWithPath: temporary))
            } else {
                try FileManager.default.moveItem(at: URL(fileURLWithPath: temporary), to: primary)
            }
        } catch {
            try? FileManager.default.removeItem(atPath: temporary)
        }
    }

    private static func describe(_ error: Error) -> String {
        switch error {
        case let DecodingError.keyNotFound(key, context):
            return "keyNotFound key=\(key.stringValue) codingPath=\(context.codingPath.map(\.stringValue).joined(separator: "."))"
        case let DecodingError.typeMismatch(type, context):
            return "typeMismatch expected=\(type) codingPath=\(context.codingPath.map(\.stringValue).joined(separator: "."))"
        case let DecodingError.valueNotFound(type, context):
            return "valueNotFound expected=\(type) codingPath=\(context.codingPath.map(\.stringValue).joined(separator: "."))"
        case let DecodingError.dataCorrupted(context):
            return "dataCorrupted codingPath=\(context.codingPath.map(\.stringValue).joined(separator: ".")) debug=\(context.debugDescription)"
        default:
            return error.localizedDescription
        }
    }

    /// Model IDs discovered across the complete historical ledger, independent
    /// of the dashboard's current range or source selection.
    static func loadHistoricalModelIds() -> [String: Set<String>] {
        var result: [String: Set<String>] = ["antigravity": [], "codex": []]
        guard FileManager.default.fileExists(atPath: dailyHistoryPath),
              let data = try? Data(contentsOf: URL(fileURLWithPath: dailyHistoryPath)),
              let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let days = root["days"] as? [String: Any] else { return result }

        for dayValue in days.values {
            guard let day = dayValue as? [String: Any] else { continue }
            guard let sources = day["sources"] as? [String: Any] else { continue }
            for sourceKey in result.keys {
                guard let source = sources[sourceKey] as? [String: Any],
                      let models = source["models"] as? [String: Any] else { continue }
                result[sourceKey, default: []].formUnion(models.keys)
            }
        }
        return result
    }
}
