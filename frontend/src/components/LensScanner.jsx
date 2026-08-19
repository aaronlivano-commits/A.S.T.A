import { useRef, useState } from "react";
import { Card, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useScanline, useLockOnPulse } from "@/animations/gsapHooks";
import { api } from "@/lib/api";

// Google Lens-style ROI analysis. Uploads the chosen image as `image` to
//   POST /api/v1/vision/crop-analyze
// and renders the { text, model } response.
export default function LensScanner() {
  const [imageSrc, setImageSrc] = useState(null);
  const [file, setFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [model, setModel] = useState(null);
  const [error, setError] = useState(null);
  const [lockTrigger, setLockTrigger] = useState(0);
  const fileInputRef = useRef(null);
  const scanRef = useScanline(Boolean(imageSrc) && !analyzing);
  const bracketRef = useLockOnPulse(lockTrigger);

  function handleFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setImageSrc(URL.createObjectURL(f));
    setResult(null);
    setError(null);
  }

  async function handleAnalyze() {
    if (!file) return;
    setAnalyzing(true);
    setResult(null);
    setError(null);
    setLockTrigger((n) => n + 1);

    try {
      const data = await api.upload("/vision/crop-analyze", "image", file);
      setResult(data.text || "No explanation returned.");
      setModel(data.model);
    } catch (err) {
      setError(
        err.status === 401
          ? "Sign in with Google to analyze images — backend requires a verified ID token."
          : `Backend not reachable yet — ${err.message}`
      );
      setResult(
        "Backend not reachable yet — once /api/v1/vision/crop-analyze is live, the step-by-step explanation from Gemini Vision will appear here."
      );
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <Card>
      <CardHeader designation="UNIT-02" title="Google Lens-Style Visual Inquiry" />
      <p className="text-asta-whiteDim max-w-[74ch] mb-6">
        Upload a photo of an equation, diagram, or problem set. A.S.T.A. locks onto
        the frame and reasons over it directly with Gemini Vision, returning a
        step-by-step explanation instead of a bare answer.
      </p>

      <div className="grid md:grid-cols-2 gap-8 items-start">
        <div ref={bracketRef} className="relative aspect-square bg-asta-void border border-asta-line overflow-hidden">
          {imageSrc ? (
            <img src={imageSrc} alt="Uploaded study material" className="w-full h-full object-cover" />
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full h-full flex flex-col items-center justify-center gap-2 text-asta-whiteDim font-mono text-xs"
            >
              <span>NO IMAGE LOADED</span>
              <span className="text-asta-blueBright">CLICK TO UPLOAD</span>
            </button>
          )}

          {/* corner brackets */}
          {["tl", "tr", "bl", "br"].map((pos) => (
            <span
              key={pos}
              data-bracket
              className={`absolute w-6 h-6 border-asta-yellow ${
                pos === "tl" ? "top-1.5 left-1.5 border-t-2 border-l-2" : ""
              }${pos === "tr" ? "top-1.5 right-1.5 border-t-2 border-r-2" : ""}${
                pos === "bl" ? "bottom-1.5 left-1.5 border-b-2 border-l-2" : ""
              }${pos === "br" ? "bottom-1.5 right-1.5 border-b-2 border-r-2" : ""}`}
            />
          ))}

          {imageSrc && (
            <div
              ref={scanRef}
              className="absolute left-[6%] right-[6%] h-0.5 bg-gradient-to-r from-transparent via-asta-red to-transparent shadow-[0_0_10px_theme(colors.asta.red)]"
            />
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFile}
            className="hidden"
          />
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => fileInputRef.current?.click()}>
              {imageSrc ? "REPLACE IMAGE" : "UPLOAD IMAGE"}
            </Button>
            <Button variant="primary" onClick={handleAnalyze} disabled={!imageSrc || analyzing}>
              {analyzing ? "ANALYZING…" : "ANALYZE ROI"}
            </Button>
          </div>

          {error && (
            <p className="font-mono text-xs text-asta-yellow">{error}</p>
          )}

          <div className="bg-asta-void border border-asta-line p-5 min-h-[160px] font-mono text-sm text-asta-whiteDim whitespace-pre-wrap">
            {result ?? "Step-by-step explanation will render here after analysis."}
          </div>

          {model && !error && (
            <p className="font-mono text-xs text-asta-whiteDim">
              model: <span className="text-asta-blueBright">{model}</span>
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}
