import Foundation

struct JSONResourceLoader {
    private let bundle: Bundle

    init(bundle: Bundle = .main) {
        self.bundle = bundle
    }

    func load<T: Decodable>(_ resourceName: String, as type: T.Type = T.self) throws -> T {
        guard let url = bundle.url(forResource: resourceName, withExtension: "json") else {
            throw JSONResourceLoaderError.resourceNotFound(resourceName)
        }

        let data = try Data(contentsOf: url)
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw JSONResourceLoaderError.decodingFailed(resourceName, underlying: error)
        }
    }
}

enum JSONResourceLoaderError: LocalizedError {
    case resourceNotFound(String)
    case decodingFailed(String, underlying: Error)

    var errorDescription: String? {
        switch self {
        case let .resourceNotFound(name):
            return "The resource \(name).json could not be found."
        case let .decodingFailed(name, underlying):
            return "Unable to decode \(name).json: \(underlying.localizedDescription)"
        }
    }
}
