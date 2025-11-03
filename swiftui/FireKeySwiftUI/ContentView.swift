import SwiftUI

struct ContentView: View {
    @ObservedObject var viewModel: FireKeyViewModel

    var body: some View {
        NavigationStack {
            Form {
                templateSection
                contentSection
                profileSection
                actionSection
                outputSection
            }
            .navigationTitle("FireKey")
            .alert(item: $viewModel.alert) { alert in
                Alert(title: Text("Error"), message: Text(alert.message), dismissButton: .default(Text("OK")))
            }
            .sheet(item: $viewModel.profileEditor) { editor in
                ProfileEditorView(profile: editor.profile) { name, context in
                    viewModel.saveProfile(name: name, context: context, editor: editor)
                }
            }
        }
    }

    private var templateSection: some View {
        Section("Prompt Template") {
            if viewModel.templates.isEmpty {
                ProgressView("Loading templates")
            } else {
                Picker("Template", selection: $viewModel.selectedTemplateID) {
                    ForEach(viewModel.templates) { template in
                        Text(template.name).tag(Optional(template.id))
                    }
                }
                .pickerStyle(.menu)

                if let template = viewModel.selectedTemplate {
                    Text(template.systemPrompt)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.top, 4)
                }
            }
        }
    }

    private var contentSection: some View {
        Section("Content Details") {
            Picker("Content Type", selection: $viewModel.contentType) {
                ForEach(ContentType.allCases) { type in
                    Text(type.displayName).tag(type)
                }
            }
            .pickerStyle(.segmented)

            TextEditor(text: $viewModel.customContext)
                .frame(minHeight: 120)
                .accessibilityIdentifier("customContextEditor")
                .overlay(alignment: .topLeading) {
                    if viewModel.customContext.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                        Text("Add additional context…")
                            .foregroundStyle(.secondary)
                            .padding(.top, 8)
                            .padding(.leading, 5)
                            .allowsHitTesting(false)
                    }
                }
        }
    }

    private var profileSection: some View {
        Section("Context Profile") {
            if viewModel.profiles.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("No saved profiles yet.")
                        .foregroundStyle(.secondary)
                    Button(action: viewModel.createProfile) {
                        Label("Create Profile", systemImage: "plus")
                    }
                }
            } else {
                Picker("Profile", selection: $viewModel.selectedProfileID) {
                    Text("None").tag(Optional<ContextProfile.ID>.none)
                    ForEach(viewModel.profiles) { profile in
                        Text(profile.name).tag(Optional(profile.id))
                    }
                }
                .pickerStyle(.menu)

                if let profile = viewModel.selectedProfile {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(profile.context)
                            .font(.callout)
                        HStack {
                            Button("Edit") {
                                viewModel.edit(profile)
                            }
                            Button(role: .destructive, action: { viewModel.delete(profile) }) {
                                Text("Delete")
                            }
                        }
                        .buttonStyle(.borderless)
                    }
                    .padding(.top, 4)
                }

                Button(action: viewModel.createProfile) {
                    Label("New Profile", systemImage: "plus")
                }
            }
        }
    }

    private var actionSection: some View {
        Section {
            Button(action: viewModel.processPrompt) {
                Label("Process Prompt", systemImage: "sparkles")
                    .fontWeight(.semibold)
            }
            .frame(maxWidth: .infinity, alignment: .center)
            .disabled(!viewModel.canProcessPrompt)
        }
    }

    private var outputSection: some View {
        Section("Generated Prompt") {
            if let processedPrompt = viewModel.processedPrompt {
                PromptOutputView(processedPrompt: processedPrompt)
            } else {
                Text("Processed prompt will appear here once generated.")
                    .foregroundStyle(.secondary)
            }
        }
    }
}

#Preview {
    ContentView(viewModel: .preview)
}
