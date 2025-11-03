import Foundation

struct ContextProfile: Identifiable, Codable, Equatable {
    var id: UUID
    var name: String
    var context: String

    init(id: UUID = UUID(), name: String, context: String) {
        self.id = id
        self.name = name
        self.context = context
    }

    private enum CodingKeys: String, CodingKey {
        case id
        case name
        case context
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        let name = try container.decode(String.self, forKey: .name)
        let context = try container.decode(String.self, forKey: .context)
        self.init(id: id, name: name, context: context)
    }
}
