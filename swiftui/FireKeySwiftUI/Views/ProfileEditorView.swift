import SwiftUI

struct ProfileEditorView: View {
    @Environment(\.dismiss) private var dismiss

    private let profile: ContextProfile?
    private let onSave: (String, String) -> Void

    @State private var name: String
    @State private var context: String

    init(profile: ContextProfile?, onSave: @escaping (String, String) -> Void) {
        self.profile = profile
        self.onSave = onSave
        _name = State(initialValue: profile?.name ?? "")
        _context = State(initialValue: profile?.context ?? "")
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Profile Name") {
                    TextField("e.g. Food Photography", text: $name)
                        .applyAutocapitalization()
                }

                Section("Context Details") {
                    TextEditor(text: $context)
                        .frame(minHeight: 160)
                }
            }
            .navigationTitle(profile == nil ? "New Profile" : "Edit Profile")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        onSave(name, context)
                        dismiss()
                    }
                    .disabled(name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ||
                              context.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }
}

#Preview {
    ProfileEditorView(profile: ContextProfile(name: "Food Photography", context: "Focus on ingredients and plating.")) { _, _ in }
}
