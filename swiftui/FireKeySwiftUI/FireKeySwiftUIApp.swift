import SwiftUI

@main
struct FireKeySwiftUIApp: App {
    @StateObject private var viewModel = FireKeyViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView(viewModel: viewModel)
        }
    }
}
