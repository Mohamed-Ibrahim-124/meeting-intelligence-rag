"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { getActionItems, getDecisions, getSummary } from "@/lib/api";

export default function IntelligencePage() {
  const params = useParams<{ id: string }>();
  const meetingId = params.id;
  const [summary, setSummary] = useState("");
  const [decisions, setDecisions] = useState<Array<{ text: string; timestamp: string; speaker: string }>>([]);
  const [actionItems, setActionItems] = useState<Array<{ text: string; assignee: string | null; timestamp: string; speaker: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getSummary(meetingId), getDecisions(meetingId), getActionItems(meetingId)])
      .then(([summaryResponse, decisionList, actionList]) => {
        setSummary(summaryResponse.summary);
        setDecisions(decisionList);
        setActionItems(actionList);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [meetingId]);

  if (loading) return <LoadingSpinner label="Loading meeting intelligence..." />;
  if (error) return <ErrorBanner message={error} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Meeting intelligence</h1>
        <Link href={`/meetings/${meetingId}`} className="text-sm text-brand-700">
          Back to meeting
        </Link>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="font-medium">Summary</h2>
        <p className="mt-2 text-sm leading-6 text-slate-700">{summary}</p>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-medium">Decisions</h2>
          <ul className="mt-3 space-y-3">
            {decisions.map((decision) => (
              <li key={`${decision.timestamp}-${decision.text}`} className="text-sm text-slate-700">
                <span className="font-medium">{decision.speaker}</span> · {decision.timestamp}
                <p className="mt-1">{decision.text}</p>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-medium">Action items</h2>
          <ul className="mt-3 space-y-3">
            {actionItems.map((item) => (
              <li key={`${item.timestamp}-${item.text}`} className="text-sm text-slate-700">
                <span className="font-medium">{item.speaker}</span> · {item.timestamp}
                <p className="mt-1">{item.text}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
