import { useEffect, useState } from "react";
import { Card, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { usePanelBoot } from "@/animations/gsapHooks";
import { api } from "@/lib/api";

// Topic CRUD against /api/v1/topics.
export default function TopicManager() {
  const [topics, setTopics] = useState([]);
  const [newTopic, setNewTopic] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const bootRef = usePanelBoot([topics.length]);

  useEffect(() => {
    let cancelled = false;
    async function loadTopics() {
      try {
        const data = await api.get("/topics");
        if (!cancelled) setTopics(data ?? []);
      } catch (err) {
        if (!cancelled) {
          setError(
            err.status === 401
              ? "Sign in with Google to load your topics."
              : `Backend not reachable yet — ${err.message}`
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadTopics();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    const title = newTopic.trim();
    if (!title) return;

    const optimistic = { id: `temp-${Date.now()}`, title, document_count: 0 };
    setTopics((prev) => [optimistic, ...prev]);
    setNewTopic("");

    try {
      const saved = await api.post("/topics", { title });
      setTopics((prev) => prev.map((t) => (t.id === optimistic.id ? saved : t)));
    } catch {
      // Leave the optimistic entry in place; surface the failure inline.
      setError("Could not save topic — backend rejected the request.");
    }
  }

  return (
    <Card>
      <CardHeader designation="UNIT-T0" title="Topic Manager" />
      <p className="text-asta-whiteDim max-w-[70ch] mb-6">
        Every uploaded document, chat thread, and trained model is scoped to a topic.
        Create one per subject, unit, or exam to keep retrieval grounded.
      </p>

      <form onSubmit={handleCreate} className="flex gap-3 mb-6">
        <input
          value={newTopic}
          onChange={(e) => setNewTopic(e.target.value)}
          placeholder="NEW TOPIC DESIGNATION"
          className="flex-1 bg-asta-void border border-asta-line text-asta-white placeholder:text-asta-whiteDim px-4 py-3 font-mono text-sm focus:outline-none focus:border-asta-blueBright"
        />
        <Button type="submit" variant="primary">
          ADD TOPIC
        </Button>
      </form>

      {error && <p className="text-xs font-mono text-asta-yellow mb-4">{error}</p>}

      <div ref={bootRef} className="divide-y divide-dashed divide-asta-line">
        {loading && (
          <p className="text-asta-whiteDim font-mono text-sm py-3">LOADING TOPICS…</p>
        )}
        {!loading && topics.length === 0 && (
          <p className="text-asta-whiteDim font-mono text-sm py-3">
            NO TOPICS YET — create your first one above.
          </p>
        )}
        {topics.map((topic) => (
          <div
            key={topic.id}
            data-boot-row
            className="flex items-center justify-between py-3"
          >
            <span className="text-asta-white">{topic.title}</span>
            <span className="font-mono text-xs text-asta-whiteDim">
              {topic.document_count ?? 0} DOCS
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}
