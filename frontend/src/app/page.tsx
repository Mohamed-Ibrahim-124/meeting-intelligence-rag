"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ErrorBanner } from "@/components/ErrorBanner";
import { EmptyState } from "@/components/EmptyState";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import {
  listMeetings,
  uploadMeeting,
  uploadMeetingFromAudio,
  type Meeting,
} from "@/lib/api";
import { ALLOWED_AUDIO_ACCEPT, ALLOWED_TEXT_ACCEPT } from "@/lib/constants";

type UploadMode = "text" | "audio";

export default function HomePage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [defaultSpeaker, setDefaultSpeaker] = useState("Speaker");
  const [mode, setMode] = useState<UploadMode>("text");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listMeetings()
      .then(setMeetings)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  function switchMode(next: UploadMode) {
    setMode(next);
    setFile(null);
    setError("");
  }

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !title.trim()) return;
    setUploading(true);
    setError("");
    try {
      const created =
        mode === "audio"
          ? await uploadMeetingFromAudio(title.trim(), file, defaultSpeaker)
          : await uploadMeeting(title.trim(), file);
      const refreshed = await listMeetings();
      setMeetings(refreshed);
      setTitle("");
      setFile(null);
      window.location.href = `/meetings/${created.meeting_id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Upload meeting</h1>
        <p className="mt-2 text-sm text-slate-600">
          Ingest a text transcript or transcribe an audio recording into the same RAG pipeline.
        </p>

        <div className="mt-4 flex gap-2">
          <button
            type="button"
            onClick={() => switchMode("text")}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
              mode === "text"
                ? "bg-brand-600 text-white"
                : "border border-slate-300 text-slate-700"
            }`}
          >
            Text transcript
          </button>
          <button
            type="button"
            onClick={() => switchMode("audio")}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
              mode === "audio"
                ? "bg-brand-600 text-white"
                : "border border-slate-300 text-slate-700"
            }`}
          >
            Audio
          </button>
        </div>

        <form onSubmit={handleUpload} className="mt-6 space-y-4">
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            placeholder="Meeting title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          {mode === "audio" ? (
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Default speaker label"
              value={defaultSpeaker}
              onChange={(e) => setDefaultSpeaker(e.target.value)}
            />
          ) : null}
          <input
            type="file"
            accept={mode === "audio" ? ALLOWED_AUDIO_ACCEPT : ALLOWED_TEXT_ACCEPT}
            className="block w-full text-sm"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <button
            type="submit"
            disabled={uploading}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {uploading
              ? mode === "audio"
                ? "Transcribing…"
                : "Uploading..."
              : mode === "audio"
                ? "Transcribe and ingest"
                : "Upload and ingest"}
          </button>
        </form>
        {error ? (
          <div className="mt-4">
            <ErrorBanner message={error} />
          </div>
        ) : null}
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Recent meetings</h2>
        {loading ? <LoadingSpinner /> : null}
        {!loading && meetings.length === 0 ? (
          <EmptyState
            title="No meetings yet"
            description="Upload a transcript or audio file to start asking grounded questions."
          />
        ) : null}
        <div className="grid gap-4 md:grid-cols-2">
          {meetings.map((meeting) => (
            <Link
              key={meeting.meeting_id}
              href={`/meetings/${meeting.meeting_id}`}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-brand-600"
            >
              <h3 className="font-medium text-slate-900">{meeting.title}</h3>
              <p className="mt-2 text-sm text-slate-500">
                {meeting.turn_count} turns · {meeting.chunk_count} chunks
              </p>
              <p className="mt-1 text-xs text-slate-400">
                {meeting.participants.join(", ") || "No participants indexed"}
              </p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
