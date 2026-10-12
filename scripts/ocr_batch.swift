import Foundation
import Vision
import AppKit

// Batch OCR with macOS Vision.
// Usage: swift ocr_batch.swift <out_jsonl> <img1> [<img2> ...]
// Each output line: {"image":"...","lines":[{"y":0.9,"text":"..."},...]}

func fail(_ msg: String) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 3 else { fail("usage: ocr_batch.swift <out.jsonl> <img...>") }
let outPath = args[1]
let images = Array(args[2...])

if !FileManager.default.fileExists(atPath: outPath) {
    FileManager.default.createFile(atPath: outPath, contents: nil)
}
guard let out = FileHandle(forWritingAtPath: outPath) else { fail("cannot open \(outPath)") }
out.seekToEndOfFile()
defer { out.closeFile() }

for imgPath in images {
    guard let img = NSImage(contentsOfFile: imgPath),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        out.write(("{\"image\":\"\(imgPath)\",\"error\":\"load_failed\"}\n").data(using: .utf8)!)
        continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = ["ja-JP", "en-US"]
    req.usesLanguageCorrection = false
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do { try handler.perform([req]) } catch {
        out.write(("{\"image\":\"\(imgPath)\",\"error\":\"perform_failed\"}\n").data(using: .utf8)!)
        continue
    }
    var lines: [[String: Any]] = []
    if let obs = req.results {
        var raw: [(Double, String)] = []
        for o in obs {
            if let cand = o.topCandidates(1).first {
                raw.append((Double(o.boundingBox.origin.y), cand.string))
            }
        }
        raw.sort { $0.0 > $1.0 }
        var curY: Double? = nil
        var curLine: [String] = []
        for (y, s) in raw {
            if let cy = curY, abs(cy - y) < 0.012 {
                curLine.append(s)
            } else {
                if !curLine.isEmpty {
                    lines.append(["y": curY ?? 0, "text": curLine.joined(separator: " ")])
                }
                curLine = [s]; curY = y
            }
        }
        if !curLine.isEmpty { lines.append(["y": curY ?? 0, "text": curLine.joined(separator: " ")]) }
    }
    if let data = try? JSONSerialization.data(withJSONObject: ["image": imgPath, "lines": lines]),
       let str = String(data: data, encoding: .utf8) {
        out.write((str + "\n").data(using: .utf8)!)
    }
    out.synchronizeFile()
}
