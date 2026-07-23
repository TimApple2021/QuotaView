import Foundation

/// Native Swift Private Credential Store for DeepSeek API Key.
/// Saves key to `~/Library/Application Support/Antigravity Token Monitor/deepseek_credentials.json`
/// with 0700 directory permissions and 0600 file permissions.
/// Completely replaces Keychain calls with ZERO system password prompts.

struct DeepSeekCredentialStore {
    struct CredentialDTO: Codable {
        let schema_version: Int
        let api_key: String
        let updated_at: String
    }

    private static var appSupportDirectory: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let dir = base.appendingPathComponent("Antigravity Token Monitor", isDirectory: true)
        if !FileManager.default.fileExists(atPath: dir.path) {
            try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true, attributes: [
                FileAttributeKey.posixPermissions: 0o700
            ])
        } else {
            try? FileManager.default.setAttributes([FileAttributeKey.posixPermissions: 0o700], ofItemAtPath: dir.path)
        }
        return dir
    }

    private static var credentialFileURL: URL {
        appSupportDirectory.appendingPathComponent("deepseek_credentials.json")
    }

    static func save(apiKey: String) throws {
        let cleanKey = apiKey.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleanKey.isEmpty else {
            throw NSError(domain: "DeepSeekCredentialStore", code: 400, userInfo: [NSLocalizedDescriptionKey: "API Key 不能为空"])
        }

        let dir = appSupportDirectory
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime]
        let dto = CredentialDTO(schema_version: 1, api_key: cleanKey, updated_at: isoFormatter.string(from: Date()))

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(dto)

        let tempURL = dir.appendingPathComponent("deepseek_credentials.json.tmp.\(UUID().uuidString)")
        try data.write(to: tempURL, options: .atomic)
        try? FileManager.default.setAttributes([FileAttributeKey.posixPermissions: 0o600], ofItemAtPath: tempURL.path)

        let targetURL = credentialFileURL
        if FileManager.default.fileExists(atPath: targetURL.path) {
            _ = try? FileManager.default.removeItem(at: targetURL)
        }
        try FileManager.default.moveItem(at: tempURL, to: targetURL)
        try? FileManager.default.setAttributes([FileAttributeKey.posixPermissions: 0o600], ofItemAtPath: targetURL.path)
    }

    static func load() -> String? {
        let url = credentialFileURL
        guard FileManager.default.fileExists(atPath: url.path) else { return nil }
        guard let data = try? Data(contentsOf: url) else { return nil }
        guard let dto = try? JSONDecoder().decode(CredentialDTO.self, from: data) else { return nil }
        let clean = dto.api_key.trimmingCharacters(in: .whitespacesAndNewlines)
        return clean.isEmpty ? nil : clean
    }

    static func delete() throws {
        let url = credentialFileURL
        if FileManager.default.fileExists(atPath: url.path) {
            try FileManager.default.removeItem(at: url)
        }
    }

    static var isConfigured: Bool {
        guard let key = load(), !key.isEmpty else { return false }
        return true
    }
}
