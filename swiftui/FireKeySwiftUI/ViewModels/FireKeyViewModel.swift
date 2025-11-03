import Foundation
import SwiftUI

@MainActor
final class FireKeyViewModel: ObservableObject {
    @Published private(set) var templates: [PromptTemplate] = []
    @Published private(set) var profiles: [ContextProfile] = []

    @Published var selectedTemplateID: PromptTemplate.ID?
    @Published var selectedProfileID: ContextProfile.ID?
    @Published var contentType: ContentType = .photo
    @Published var customContext: String = ""
    @Published private(set) var processedPrompt: ProcessedPrompt?

    @Published var alert: FireKeyAlert?
    @Published var profileEditor: ProfileEditorState?

    private let resourceLoader: JSONResourceLoader

    init(resourceLoader: JSONResourceLoader = JSONResourceLoader(), loadResources: Bool = true) {
        self.resourceLoader = resourceLoader
        if loadResources {
            loadInitialData()
        }
    }

    var selectedTemplate: PromptTemplate? {
        templates.first { $0.id == selectedTemplateID }
    }

    var selectedProfile: ContextProfile? {
        profiles.first { $0.id == selectedProfileID }
    }

    var canProcessPrompt: Bool {
        selectedTemplate != nil
    }

    func loadInitialData() {
        do {
            templates = try resourceLoader.load("Templates", as: [PromptTemplate].self)
            if selectedTemplateID == nil {
                selectedTemplateID = templates.first?.id
            }
        } catch {
            alert = FireKeyAlert(message: "Unable to load prompt templates. \(error.localizedDescription)")
        }

        do {
            profiles = try resourceLoader.load("ContextProfiles", as: [ContextProfile].self)
        } catch {
            profiles = []
        }
    }

    func processPrompt() {
        guard let template = selectedTemplate else {
            processedPrompt = nil
            return
        }

        let combinedContext = makeCombinedContext()
        let contextReplacement: String
        if combinedContext.isEmpty {
            contextReplacement = "No additional context provided."
        } else {
            contextReplacement = combinedContext
        }

        let typeReplacement = contentType.displayName

        let systemPrompt = template.systemPrompt
            .replacingOccurrences(of: "{type}", with: typeReplacement)
            .replacingOccurrences(of: "{context}", with: contextReplacement)

        let userPrompt = template.userPrompt
            .replacingOccurrences(of: "{type}", with: typeReplacement)
            .replacingOccurrences(of: "{context}", with: contextReplacement)

        processedPrompt = ProcessedPrompt(systemPrompt: systemPrompt, userPrompt: userPrompt)
    }

    func createProfile() {
        profileEditor = ProfileEditorState(profile: nil)
    }

    func edit(_ profile: ContextProfile) {
        profileEditor = ProfileEditorState(profile: profile)
    }

    func delete(_ profile: ContextProfile) {
        if let index = profiles.firstIndex(of: profile) {
            profiles.remove(at: index)
            if selectedProfileID == profile.id {
                selectedProfileID = nil
            }
            if processedPrompt != nil {
                processPrompt()
            }
        }
    }

    func saveProfile(name: String, context: String, editor: ProfileEditorState) {
        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedContext = context.trimmingCharacters(in: .whitespacesAndNewlines)

        guard !trimmedName.isEmpty, !trimmedContext.isEmpty else {
            alert = FireKeyAlert(message: "Both a name and context are required for a profile.")
            return
        }

        if let existing = editor.profile, let index = profiles.firstIndex(of: existing) {
            var updated = existing
            updated.name = trimmedName
            updated.context = trimmedContext
            profiles[index] = updated
            selectedProfileID = updated.id
        } else {
            let newProfile = ContextProfile(name: trimmedName, context: trimmedContext)
            profiles.append(newProfile)
            selectedProfileID = newProfile.id
        }

        if processedPrompt != nil {
            processPrompt()
        }

        profileEditor = nil
    }

    func makeCombinedContext() -> String {
        let profileContext = selectedProfile?.context.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let custom = customContext.trimmingCharacters(in: .whitespacesAndNewlines)

        var components: [String] = []
        if !profileContext.isEmpty {
            components.append(profileContext)
        }
        if !custom.isEmpty {
            components.append(custom)
        }

        return components.joined(separator: "\n\n")
    }
}

extension FireKeyViewModel {
    static var preview: FireKeyViewModel {
        let viewModel = FireKeyViewModel(resourceLoader: JSONResourceLoader(bundle: .main), loadResources: false)
        viewModel.templates = [
            PromptTemplate(name: "Preview Template", systemPrompt: "System template for {type}.", userPrompt: "Prompt with {context}.")
        ]
        viewModel.profiles = [
            ContextProfile(name: "Preview Profile", context: "Preview context details.")
        ]
        viewModel.selectedTemplateID = viewModel.templates.first?.id
        viewModel.selectedProfileID = viewModel.profiles.first?.id
        viewModel.customContext = "A cozy loft apartment with warm window light and indoor plants."
        viewModel.processPrompt()
        return viewModel
    }
}

struct FireKeyAlert: Identifiable {
    let id = UUID()
    let message: String
}

struct ProfileEditorState: Identifiable {
    let id = UUID()
    let profile: ContextProfile?
}
