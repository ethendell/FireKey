import SwiftUI

extension View {
    func applyAutocapitalization() -> some View {
        #if os(iOS)
        return textInputAutocapitalization(.words)
        #else
        return self
        #endif
    }
}
