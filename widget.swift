import Cocoa
import WebKit

class AppDelegate: NSObject, NSApplicationDelegate, WKScriptMessageHandler {
    var window: NSPanel!
    var webView: WKWebView!

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.activate(ignoringOtherApps: true)

        // Dynamic Island style: compact pill, top center
        let w: CGFloat = 180
        let h: CGFloat = 38

        let screen = NSScreen.main!.frame
        let menuBarHeight: CGFloat = NSApp.mainMenu?.menuBarHeight ?? 25
        let origin = NSPoint(
            x: screen.midX - w / 2,
            y: screen.maxY - menuBarHeight - h - 6
        )

        window = NSPanel(
            contentRect: NSRect(origin: origin, size: NSSize(width: w, height: h)),
            styleMask: [.borderless, .nonactivatingPanel, .utilityWindow],
            backing: .buffered,
            defer: false
        )

        window.level = NSWindow.Level(Int(CGShieldingWindowLevel()))  // above everything
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = true
        window.isMovableByWindowBackground = true
        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .fullScreenAuxiliary]
        window.hidesOnDeactivate = false

        // Clip the window itself to pill shape
        window.contentView?.wantsLayer = true
        window.contentView?.layer?.cornerRadius = h / 2
        window.contentView?.layer?.masksToBounds = true

        // Visual effect (frosted glass) inside the clipped window
        let visualEffect = NSVisualEffectView(frame: NSRect(origin: .zero, size: NSSize(width: w, height: h)))
        visualEffect.material = .toolTip
        visualEffect.appearance = NSAppearance(named: .darkAqua)
        visualEffect.blendingMode = .behindWindow
        visualEffect.state = .active
        visualEffect.autoresizingMask = [.width, .height]

        // WebView on top of blur — register "shake" message handler
        let config = WKWebViewConfiguration()
        config.userContentController.add(self, name: "shake")

        webView = WKWebView(
            frame: NSRect(origin: .zero, size: NSSize(width: w, height: h)),
            configuration: config
        )
        webView.setValue(false, forKey: "drawsBackground")
        webView.autoresizingMask = [.width, .height]

        let port = ProcessInfo.processInfo.environment["OPENCLAW_HTTP_PORT"] ?? "7788"
        let url = URL(string: "http://localhost:\(port)/?widget")!
        webView.load(URLRequest(url: url))

        visualEffect.addSubview(webView)
        window.contentView?.addSubview(visualEffect)
        window.orderFrontRegardless()
    }

    // MARK: - WKScriptMessageHandler

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "shake" {
            shakeWindow()
        }
    }

    func shakeWindow() {
        let origin = window.frame.origin
        let offsets: [CGFloat] = [-6, 6, -4, 4, -2, 2, 0]
        let step = 0.04

        for (i, dx) in offsets.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + step * Double(i)) { [weak self] in
                guard let w = self?.window else { return }
                w.setFrameOrigin(NSPoint(x: origin.x + dx, y: origin.y))
            }
        }
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
