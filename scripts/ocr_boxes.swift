import Foundation
import Vision
import AppKit

// Batch OCR with macOS Vision, box-level output (x,y,w,h kept for column reconstruction).
// Usage: swift ocr_boxes.swift <out.jsonl> <img1> [<img2> ...]
// Each line: {"image":"...","boxes":[{"x":0.1,"y":0.9,"w":0.3,"h":0.02,"text":"..."},...]}

func fail(_ msg: String) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 3 else { fail("usage: ocr_boxes.swift <out.jsonl> <img...>") }
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
    var boxes: [[String: Any]] = []
    if let obs = req.results {
        for o in obs {
            if let cand = o.topCandidates(1).first {
                let b = o.boundingBox
                boxes.append(["x": Double(b.origin.x), "y": Double(b.origin.y),
                              "w": Double(b.width), "h": Double(b.height),
                              "text": cand.string])
            }
        }
    }
    if let data = try? JSONSerialization.data(withJSONObject: ["image": imgPath, "boxes": boxes]),
       let str = String(data: data, encoding: .utf8) {
        out.write((str + "\n").data(using: .utf8)!)
    }
    out.synchronizeFile()
}
