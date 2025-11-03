# FireKey SwiftUI

This directory contains a native SwiftUI implementation of FireKey for iOS and macOS. The
app mirrors the core desktop workflow with modern platform controls:

- Choose from the bundled FireKey prompt templates.
- Apply reusable context profiles or author session-specific context.
- Combine everything into final system and user prompts that can be copied with a single tap.
- Manage profiles directly inside the app.

## Project layout

```
SwiftUI/
└── FireKeySwiftUI/
    ├── FireKeySwiftUIApp.swift      # Application entry point
    ├── ContentView.swift            # High-level UI composition
    ├── Models/                      # Codable models shared across the app
    ├── ViewModels/                  # ObservableObject powering the UI
    ├── Views/                       # Reusable SwiftUI components
    ├── Support/                     # Helpers (resource loading, clipboard, etc.)
    └── Resources/                   # Bundled templates and default profiles
```

`Templates.json` and `ContextProfiles.json` reuse the same language that ships with the
existing Tkinter application so both experiences stay aligned.

## Getting started

1. Open **FireKeySwiftUI** in Xcode 15 or newer (File ▸ Open… and choose the
   `swiftui/FireKeySwiftUI` folder).
2. Ensure the resources are included in the target (Xcode should pick them up automatically).
3. Build and run on iOS 17/macOS 14 simulators or devices.

The preview providers included in the views give an immediate sense of the design without
launching the full application.
