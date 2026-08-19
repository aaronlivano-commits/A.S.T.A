import { Card, CardHeader } from "@/components/ui/card";
import TopicManager from "@/components/TopicManager";

const PILLARS = [
  {
    code: "MM",
    title: "Multimodal",
    body: "Reads PDFs, handwriting, slides, and camera-captured images as one input stream.",
  },
  {
    code: "RAG",
    title: "Grounded",
    body: "Every answer is anchored to the student's own material — not open recall.",
  },
  {
    code: "CV",
    title: "Visual",
    body: "Crops and reasons over diagrams and equations the way a tutor would point at a page.",
  },
  {
    code: "SYNC",
    title: "Portable",
    body: "Full cloud backup and offline export — topics and trained models travel with the student.",
  },
];

// Landing view: system overview + a live topic list.
export default function Dashboard() {
  return (
    <div className="space-y-8">
      <Card>
        <CardHeader designation="UNIT-00" title="Overview & Vision" />
        <p className="text-asta-whiteDim max-w-[74ch] mb-8">
          A.S.T.A. turns passive studying into an interactive, grounded, and visual
          process. It combines large multimodal models, vector-based retrieval, and
          computer vision behind one console, so every answer traces back to material
          the student actually uploaded.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {PILLARS.map((p) => (
            <div key={p.code} className="bg-asta-panelAlt border-l-2 border-asta-blueBright p-5">
              <span className="font-mono text-xs text-asta-yellow">{p.code}</span>
              <h3 className="font-display text-sm text-asta-white mt-2 mb-2">{p.title}</h3>
              <p className="text-asta-whiteDim text-sm">{p.body}</p>
            </div>
          ))}
        </div>
      </Card>

      <TopicManager />
    </div>
  );
}
