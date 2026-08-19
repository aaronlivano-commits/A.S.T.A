import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Tabs from "@radix-ui/react-tabs";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

// Model training + portability. Talks to:
//   POST /api/v1/training/text           (CSV/JSON/XLSX under "file")
//   POST /api/v1/training/vision          (ZIP under "file")
//   GET  /api/v1/models/export/{model_id}
//   POST /api/v1/models/import            (.asta-model under "file")
export default function ModelTrainerModal({ trigger }) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState(null);
  const [tone, setTone] = useState("info"); // "info" | "error" | "ok"

  async function upload(endpoint, file) {
    if (!file) return;
    setTone("info");
    setStatus(`UPLOADING ${file.name}…`);
    try {
      const data = await api.upload(endpoint, "file", file);
      const summary =
        endpoint === "/training/text"
          ? `${data.rows_ingested ?? 0} rows ingested (${data.format}).`
          : `${data.image_count ?? 0} images registered.`;
      setTone("ok");
      setStatus(`DATASET RECEIVED — ${summary}`);
    } catch (err) {
      setTone("error");
      setStatus(
        err.status === 401
          ? "Sign in with Google to upload datasets."
          : `Upload failed: ${err.message}`
      );
    }
  }

  async function importBundle(file) {
    if (!file) return;
    setTone("info");
    setStatus(`IMPORTING ${file.name}…`);
    try {
      const data = await api.upload("/models/import", "file", file);
      setTone("ok");
      setStatus(`MODEL IMPORTED — installed at ${data.installed_at ?? "bundle"}.`);
    } catch (err) {
      setTone("error");
      setStatus(
        err.status === 401
          ? "Sign in with Google to import model bundles."
          : `Import failed: ${err.message}`
      );
    }
  }

  async function exportBundle() {
    setTone("info");
    setStatus("BUILDING BUNDLE…");
    try {
      const data = await api.get("/models/export/current");
      setTone("ok");
      setStatus(
        `Bundle ready: ${data.bundle_uri} (${data.size_bytes ?? 0} bytes, includes ${
          (data.includes ?? []).join(", ") || "manifest only"
        }).`
      );
    } catch (err) {
      setTone("error");
      setStatus(
        err.status === 401
          ? "Sign in with Google to export model bundles."
          : `Export failed: ${err.message}`
      );
    }
  }

  const statusClass =
    tone === "error"
      ? "text-asta-red"
      : tone === "ok"
      ? "text-[#3FE07A]"
      : "text-asta-yellow";

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        {trigger ?? <Button variant="primary">OPEN MODEL TRAINER</Button>}
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/70 z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(640px,92vw)] max-h-[85vh] overflow-y-auto bg-asta-panel border border-asta-line p-6 md:p-8 z-50">
          <div className="flex items-baseline gap-4 mb-2">
            <span className="designation-tag">UNIT-04</span>
            <Dialog.Title className="font-display text-xl text-asta-white m-0">
              Model Training &amp; Export
            </Dialog.Title>
          </div>
          <Dialog.Description className="text-asta-whiteDim text-sm mb-6">
            Hand A.S.T.A. your own datasets, or import a bundle someone already trained —
            zero retraining required.
          </Dialog.Description>

          <Tabs.Root defaultValue="text">
            <Tabs.List className="flex gap-2 mb-6 border-b border-asta-line">
              {[
                { value: "text", label: "TEXT DATA" },
                { value: "vision", label: "VISION DATA" },
                { value: "share", label: "EXPORT / IMPORT" },
              ].map((t) => (
                <Tabs.Trigger
                  key={t.value}
                  value={t.value}
                  className="font-mono text-xs px-4 py-2 text-asta-whiteDim border-b-2 border-transparent data-[state=active]:text-asta-white data-[state=active]:border-asta-yellow"
                >
                  {t.label}
                </Tabs.Trigger>
              ))}
            </Tabs.List>

            <Tabs.Content value="text" className="space-y-3">
              <p className="text-sm text-asta-whiteDim">
                QA pairs, terminology tables, or study profiles — .csv, .json, or .xlsx.
              </p>
              <input
                type="file"
                accept=".csv,.json,.xlsx"
                onChange={(e) => upload("/training/text", e.target.files?.[0])}
                className="block w-full text-xs font-mono text-asta-whiteDim file:mr-4 file:px-4 file:py-2 file:border-0 file:bg-asta-blueDeep file:text-asta-white file:font-display file:text-xs file:cursor-pointer"
              />
            </Tabs.Content>

            <Tabs.Content value="vision" className="space-y-3">
              <p className="text-sm text-asta-whiteDim">
                A .zip archive of labeled images for custom visual recognition.
              </p>
              <input
                type="file"
                accept=".zip"
                onChange={(e) => upload("/training/vision", e.target.files?.[0])}
                className="block w-full text-xs font-mono text-asta-whiteDim file:mr-4 file:px-4 file:py-2 file:border-0 file:bg-asta-blueDeep file:text-asta-white file:font-display file:text-xs file:cursor-pointer"
              />
            </Tabs.Content>

            <Tabs.Content value="share" className="space-y-5">
              <div>
                <p className="text-sm text-asta-whiteDim mb-2">
                  Export the current model as a self-contained <code>.asta-model</code> bundle
                  (adapters, prompt persona, vectorized knowledge graph).
                </p>
                <Button variant="ghost" onClick={exportBundle}>
                  EXPORT BUNDLE
                </Button>
              </div>
              <div>
                <p className="text-sm text-asta-whiteDim mb-2">
                  Import a bundle someone shared with you — no retraining needed.
                </p>
                <input
                  type="file"
                  accept=".asta-model"
                  onChange={(e) => importBundle(e.target.files?.[0])}
                  className="block w-full text-xs font-mono text-asta-whiteDim file:mr-4 file:px-4 file:py-2 file:border-0 file:bg-asta-blueDeep file:text-asta-white file:font-display file:text-xs file:cursor-pointer"
                />
              </div>
            </Tabs.Content>
          </Tabs.Root>

          {status && (
            <p className={`mt-6 font-mono text-xs border-t border-asta-line pt-4 ${statusClass}`}>
              {status}
            </p>
          )}

          <Dialog.Close asChild>
            <button
              type="button"
              aria-label="Close"
              className="absolute top-4 right-4 text-asta-whiteDim hover:text-asta-red font-mono text-xs"
            >
              CLOSE ✕
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
