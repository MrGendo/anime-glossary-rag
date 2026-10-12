import Foundation
import Vision
import AppKit

// Usage: swift ocr_vision.swift <image_path> [--lang ja-JP]
// Prints recognized text (top-to-bottom, line by line) to stdout.

func fail(_ msg: String) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 2 else { fail("usage: ocr_vision.swift <image> [--lang ja-JP|en-US]") }
let imgPath = args[1]
var lang = "ja-JP"
if let i = args.firstIndex(of: "--lang"), i + 1 < args.count { lang = args[i + 1] }

guard let img = NSImage(contentsOfFile: imgPath), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fail("cannot load image: \(imgPath)")
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = [lang, "en-US"]
request.usesLanguageCorrection = false

let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try? handler.perform([request])

guard let obs = request.results, !obs.isEmpty else { print(""); exit(0) }
var lines: [(Double, String)] = []
for o in obs {
    if let cand = o.topCandidates(1).first {
        let b = o.boundingBox
        lines.append((Double(b.origin.y), cand.string))
    }
}
// group by similar y (within 1.2% height) to merge boxes on same line
lines.sort { $0.0 > $1.0 }
var out: [String] = []
var curY: Double? = nil
var curLine: [String] = []
for (y, s) in lines {
    if let cy = curY, abs(cy - y) < 0.012 {
        curLine.append(s)
    } else {
        if !curLine.isEmpty { out.append(curLine.joined(separator: " ")) }
        curLine = [s]
        curY = y
    }
}
if !curLine.isEmpty { out.append(curLine.joined(separator: " ")) }
print(out.joined(separator: "\n"))
