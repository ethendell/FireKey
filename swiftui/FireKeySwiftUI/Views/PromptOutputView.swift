import SwiftUI

struct PromptOutputView: View {
    let processedPrompt: ProcessedPrompt

    var body: some View {
        VStack(spacing: 16) {
            PromptSection(title: "System Prompt", text: processedPrompt.systemPrompt)
            PromptSection(title: "User Prompt", text: processedPrompt.userPrompt)
        }
        .padding(.vertical, 4)
    }
}

private struct PromptSection: View {
    let title: String
    let text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(title)
                    .font(.headline)
                Spacer()
                Button(action: { Clipboard.copy(text) }) {
                    Label("Copy", systemImage: "doc.on.doc")
                        .labelStyle(.iconOnly)
                        .imageScale(.medium)
                }
                .buttonStyle(.borderless)
                .accessibilityLabel("Copy \(title)")
            }

            ScrollView {
                Text(text)
                    .font(.body.monospaced())
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(minHeight: 120)
        }
    }
}

#Preview {
    PromptOutputView(processedPrompt: ProcessedPrompt(systemPrompt: "System prompt sample", userPrompt: "User prompt sample"))
}
