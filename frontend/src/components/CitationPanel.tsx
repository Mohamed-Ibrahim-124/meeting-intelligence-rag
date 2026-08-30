import type { Citation } from "@/lib/api";

type Props = {
  citations: Citation[];
  activeTimestamp?: string;
  onSelect?: (timestamp: string) => void;
};

export function CitationPanel({ citations, activeTimestamp, onSelect }: Props) {
  if (!citations.length) {
    return <p className="text-sm text-slate-500">No citations returned.</p>;
  }
  return (
    <div className="space-y-3">
      {citations.map((citation) => (
        <button
          key={citation.chunk_id}
          type="button"
          onClick={() => onSelect?.(citation.timestamp)}
          className={`w-full rounded-lg border px-3 py-2 text-left transition ${
            activeTimestamp === citation.timestamp
              ? "border-brand-600 bg-brand-50"
              : "border-slate-200 bg-white hover:border-brand-600"
          }`}
        >
          <p className="text-sm font-medium text-slate-800">
            {citation.speaker} · {citation.timestamp}
          </p>
          <p className="mt-1 text-sm text-slate-600">{citation.snippet}</p>
        </button>
      ))}
    </div>
  );
}
