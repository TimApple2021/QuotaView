import Foundation

class ScannerRunner {
    static var backendURL: URL? {
        Bundle.main.url(forResource: "monitor_backend", withExtension: "py")
            ?? Bundle.main.resourceURL?.appendingPathComponent("monitor_backend.py")
    }
    private static var activeProcess: Process?
    private static let lock = NSLock()

    static func terminateActiveScan() {
        lock.lock()
        defer { lock.unlock() }
        if let process = activeProcess, process.isRunning {
            process.terminate()
        }
        activeProcess = nil
    }
    
    static func runScan(completion: @escaping (Result<String, Error>) -> Void) {
        lock.lock()
        if let current = activeProcess, current.isRunning {
            lock.unlock()
            completion(.failure(NSError(domain: "ScannerRunner", code: 2,
                userInfo: [NSLocalizedDescriptionKey: "扫描进程已在运行中"])))
            return
        }
        lock.unlock()

        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            let pipe = Pipe()
            let errorPipe = Pipe()
            
            guard let backendURL = backendURL else {
                completion(.failure(NSError(domain: "ScannerRunner", code: 1,
                    userInfo: [NSLocalizedDescriptionKey: "App 资源中缺少 monitor_backend.py"])))
                return
            }
            process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
            process.arguments = ["python3", backendURL.path]
            process.environment = ProcessInfo.processInfo.environment.merging([
                "TOKEN_MONITOR_DATA_DIR": TokenRuntimePaths.appSupportDirectory.path
            ]) { _, new in new }
            process.standardOutput = pipe
            process.standardError = errorPipe
            
            do {
                lock.lock()
                activeProcess = process
                lock.unlock()
                
                try process.run()
                process.waitUntilExit()
                
                lock.lock()
                activeProcess = nil
                lock.unlock()
                
                let status = process.terminationStatus
                if status == 0 {
                    let data = pipe.fileHandleForReading.readDataToEndOfFile()
                    let output = String(data: data, encoding: .utf8) ?? ""
                    completion(.success(output))
                } else {
                    let errData = errorPipe.fileHandleForReading.readDataToEndOfFile()
                    let errOutput = String(data: errData, encoding: .utf8) ?? ""
                    let msg = errOutput.trimmingCharacters(in: .whitespacesAndNewlines)
                    let error = NSError(domain: "ScannerRunner", code: Int(status), userInfo: [NSLocalizedDescriptionKey: msg.isEmpty ? "Python 扫描器返回非零退出状态: \(status)" : msg])
                    completion(.failure(error))
                }
            } catch {
                lock.lock()
                activeProcess = nil
                lock.unlock()
                completion(.failure(error))
            }
        }
    }

    static var cliURL: URL? {
        Bundle.main.url(forResource: "quotaview_cli", withExtension: "py")
            ?? Bundle.main.resourceURL?.appendingPathComponent("quotaview_cli.py")
    }

    static func runDeepSeekImport(zipPath: String, completion: @escaping (Result<String, Error>) -> Void) {
        DispatchQueue.global(qos: .userInitiated).async {
            guard let cliURL = cliURL else {
                completion(.failure(NSError(domain: "ScannerRunner", code: 1,
                    userInfo: [NSLocalizedDescriptionKey: "App 资源中缺少 quotaview_cli.py"])))
                return
            }
            let process = Process()
            let pipe = Pipe()
            let errorPipe = Pipe()

            process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
            process.arguments = ["python3", cliURL.path, "deepseek", "import", zipPath, "--json"]
            process.environment = ProcessInfo.processInfo.environment.merging([
                "TOKEN_MONITOR_DATA_DIR": TokenRuntimePaths.appSupportDirectory.path
            ]) { _, new in new }
            process.standardOutput = pipe
            process.standardError = errorPipe

            do {
                try process.run()
                process.waitUntilExit()

                let status = process.terminationStatus
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                let output = String(data: data, encoding: .utf8) ?? ""

                if status == 0 {
                    completion(.success(output))
                } else {
                    let errData = errorPipe.fileHandleForReading.readDataToEndOfFile()
                    let errOutput = String(data: errData, encoding: .utf8) ?? ""
                    let msg = errOutput.trimmingCharacters(in: .whitespacesAndNewlines)
                    completion(.failure(NSError(domain: "ScannerRunner", code: Int(status), userInfo: [NSLocalizedDescriptionKey: msg.isEmpty ? "导入失败" : msg])))
                }
            } catch {
                completion(.failure(error))
            }
        }
    }
}
