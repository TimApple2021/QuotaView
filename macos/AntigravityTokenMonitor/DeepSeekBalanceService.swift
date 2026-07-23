import Foundation

/// Native Swift Service to fetch DeepSeek official balance via URLSession.
/// Keeps API Key isolated in memory/Keychain without subprocess or security CLI calls.
final class DeepSeekBalanceService {
    static let shared = DeepSeekBalanceService()
    private init() {}

    private let balanceURL = URL(string: "https://api.deepseek.com/user/balance")!

    func fetchBalance(apiKey: String, completion: @escaping (DeepSeekBalanceInfo?, String?) -> Void) {
        let cleanKey = apiKey.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleanKey.isEmpty else {
            completion(nil, "未配置 Key")
            return
        }

        var request = URLRequest(url: balanceURL)
        request.httpMethod = "GET"
        request.setValue("Bearer \(cleanKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("QuotaView/1.1.8", forHTTPHeaderField: "User-Agent")
        request.timeoutInterval = 10.0

        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                let code = (error as NSError).code
                let msg = (code == NSURLErrorTimedOut) ? "请求超时" : "网络连接失败"
                completion(nil, msg)
                return
            }

            guard let httpResp = response as? HTTPURLResponse else {
                completion(nil, "网络响应异常")
                return
            }

            let status = httpResp.statusCode
            if status != 200 {
                let msg: String
                switch status {
                case 401: msg = "API Key 认证失败 (HTTP 401)"
                case 402: msg = "账户余额不足 (HTTP 402)"
                case 429: msg = "请求过多，请稍后再试 (HTTP 429)"
                default: msg = "DeepSeek 服务器异常 (HTTP \(status))"
                }
                completion(nil, msg)
                return
            }

            guard let data = data else {
                completion(nil, "未收到数据")
                return
            }

            do {
                let decoded = try JSONDecoder().decode(DeepSeekBalanceResponseDTO.self, from: data)
                let balanceInfo = decoded.toBalanceInfo()
                completion(balanceInfo, nil)
            } catch {
                completion(nil, "数据解析失败")
            }
        }
        task.resume()
    }

}

// MARK: - API Decoders

struct DeepSeekBalanceResponseDTO: Codable {
    let is_available: Bool?
    let balance_infos: [DeepSeekBalanceInfoItemDTO]?

    func toBalanceInfo() -> DeepSeekBalanceInfo {
        let items = balance_infos?.map { $0.toModel() } ?? []
        let primary = items.first
        let curr = primary?.currency ?? "CNY"
        let tot = primary?.totalBalance ?? "0.00"
        let grt = primary?.grantedBalance ?? "0.00"
        let top = primary?.toppedUpBalance ?? "0.00"

        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime]
        let nowIso = isoFormatter.string(from: Date())

        return DeepSeekBalanceInfo(
            configured: true,
            isAvailable: is_available ?? true,
            currency: curr,
            totalBalance: tot,
            grantedBalance: grt,
            toppedUpBalance: top,
            balanceInfos: items,
            fetchedAt: nowIso,
            errorCode: nil,
            errorMessage: nil
        )
    }
}

struct DeepSeekBalanceInfoItemDTO: Codable {
    let currency: String?
    let total_balance: String?
    let granted_balance: String?
    let topped_up_balance: String?

    func toModel() -> DeepSeekBalanceInfoItemModel {
        DeepSeekBalanceInfoItemModel(
            currency: currency?.uppercased() ?? "CNY",
            totalBalance: total_balance ?? "0.00",
            grantedBalance: granted_balance ?? "0.00",
            toppedUpBalance: topped_up_balance ?? "0.00"
        )
    }
}
