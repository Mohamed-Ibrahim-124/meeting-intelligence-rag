import type { TranscriptTurn } from "@/lib/api";

type Props = {
  turns: TranscriptTurn[];
  highlightTimestamp?: string;
};

export function TranscriptViewer({ turns, highlightTimestamp }: Props) {
  return (
    <div className="max-h-96 space-y-2 overflow-y-auto rounded-xl border border-slate-200 bg-white p-4">
      {turns.map((turn) => (
        <div
          key={turn.turn_index}
          id={`turn-${turn.timestamp}`}
          className={`rounded-md px-2 py-1 text-sm ${
            highlightTimestamp === turn.timestamp ? "bg-brand-50" : ""
          }`}
        >
          <span className="font-medium text-brand-700">[{turn.timestamp}] {turn.speaker}:</span>{" "}
          <span className="text-slate-700">{turn.text}</span>
        </div>
      ))}
    </div>
  );
}
