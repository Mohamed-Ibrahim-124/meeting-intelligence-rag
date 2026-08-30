"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { CitationPanel } from "@/components/CitationPanel";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { SuggestedQuestions } from "@/components/SuggestedQuestions";
import { TranscriptViewer } from "@/components/TranscriptViewer";
import { getMeeting, queryMeeting, type Citation, type QueryResponse } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string; citations?: Citation[] };

const SUGGESTED = [
  "What action items were assigned?",
  "What decisions were made about enrollment?",
  "What did Dr. Chen say about Trial A-102?",
  "What topics were discussed?",
];

export default function ChatPage() {
  const params = useParams<{ id: string }>();
  const meetingId = params.id;
  const [turns, setTurns] = useState<Array<{ timestamp: string; speaker: string; text: string; turn_index: number }>>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [activeTimestamp, setActiveTimestamp] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getMeeting(meetingId)
      .then((detail) => setTurns(detail.turns))
      .catch((err: Error) => setError(err.message));
  }, [meetingId]);

  async function ask(selectedQuestion?: string) {
    const q = (selectedQuestion ?? question).trim();
    if (!q) return;
    setLoading(true);
    setError("");
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    try {
      const response: QueryResponse = await queryMeeting(meetingId, q);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer, citations: response.citations },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  const latestCitations = [...messages].reverse().find((m) => m.role === "assistant")?.citations ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Meeting chat</h1>
        <Link href={`/meetings/${meetingId}`} className="text-sm text-brand-700">
          Back to meeting
        </Link>
      </div>

      <SuggestedQuestions questions={SUGGESTED} onSelect={(q) => { setQuestion(q); void ask(q); }} />

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="mb-4 max-h-[420px] space-y-3 overflow-y-auto">
            {messages.length === 0 ? (
              <p className="text-sm text-slate-500">Ask a question about this meeting transcript.</p>
            ) : null}
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`rounded-lg px-3 py-2 text-sm ${
                  message.role === "user" ? "bg-slate-100" : "bg-brand-50"
                }`}
              >
                {message.content}
              </div>
            ))}
            {loading ? <LoadingSpinner label="Generating grounded answer..." /> : null}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void ask();
            }}
            className="flex gap-2"
          >
            <input
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder="Ask about decisions, action items, speakers..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button type="submit" className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white">
              Ask
            </button>
          </form>
          {error ? <div className="mt-3"><ErrorBanner message={error} /></div> : null}
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="mb-2 font-medium">Citations</h2>
            <CitationPanel
              citations={latestCitations}
              activeTimestamp={activeTimestamp}
              onSelect={setActiveTimestamp}
            />
          </div>
          <div>
            <h2 className="mb-2 font-medium">Transcript evidence</h2>
            <TranscriptViewer turns={turns} highlightTimestamp={activeTimestamp} />
          </div>
        </section>
      </div>
    </div>
  );
}
