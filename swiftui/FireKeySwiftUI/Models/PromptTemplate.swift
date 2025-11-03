import Foundation

struct PromptTemplate: Identifiable, Codable, Equatable {
    let id: String
    var name: String
    var systemPrompt: String
    var userPrompt: String

    init(id: String = UUID().uuidString, name: String, systemPrompt: String, userPrompt: String) {
        self.id = id
        self.name = name
        self.systemPrompt = systemPrompt
        self.userPrompt = userPrompt
    }

    private enum CodingKeys: String, CodingKey {
        case id
        case name
        case systemPrompt = "system_prompt"
        case userPrompt = "user_prompt"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let name = try container.decode(String.self, forKey: .name)
        let id = try container.decodeIfPresent(String.self, forKey: .id) ?? PromptTemplate.makeIdentifier(from: name)
        let systemPrompt = try container.decode(String.self, forKey: .systemPrompt)
        let userPrompt = try container.decode(String.self, forKey: .userPrompt)

        self.init(id: id, name: name, systemPrompt: systemPrompt, userPrompt: userPrompt)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(name, forKey: .name)
        try container.encode(systemPrompt, forKey: .systemPrompt)
        try container.encode(userPrompt, forKey: .userPrompt)
    }

    private static func makeIdentifier(from name: String) -> String {
        let lowercased = name.lowercased()
        let allowed = lowercased.compactMap { character -> Character? in
            if character.isLetter || character.isNumber {
                return character
            }
            if character.isWhitespace || character == "-" {
                return "-"
            }
            return nil
        }
        var collapsed = String(allowed)
        while collapsed.contains("--") {
            collapsed = collapsed.replacingOccurrences(of: "--", with: "-")
        }
        return collapsed.trimmingCharacters(in: CharacterSet(charactersIn: "-"))
    }
}
