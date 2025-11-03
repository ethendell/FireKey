import Foundation

enum ContentType: String, CaseIterable, Identifiable, Codable {
    case photo
    case video

    var id: ContentType { self }

    var displayName: String {
        switch self {
        case .photo: return "Photo"
        case .video: return "Video"
        }
    }
}
