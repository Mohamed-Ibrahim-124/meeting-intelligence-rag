"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { TranscriptViewer } from "@/components/TranscriptViewer";
import { getMeeting, getParticipants, getTopics, type MeetingDetail } from "@/lib/api";

export default function MeetingDetailPage() {
  const params = useParams<{ id: string }>();
  const meetingId = params.id;
  const [detail, setDetail] = useState<MeetingDetail | null>(null);
  const [participants, setParticipants] = useState<string[]>([]);
  const [topics, setTopics] = useState<Array<{ name: string; score: number }>>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getMeeting(meetingId), getParticipants(meetingId), getTopics(meetingId)])
      .then(([meetingDetail, speakerList, topicList]) => {
        setDetail(meetingDetail);
        setParticipants(speakerList);
        setTopics(topicList);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [meetingId]);

  if (loading) return <LoadingSpinner label="Loading meeting..." />;
  if (error) return <ErrorBanner message={error} />;
  if (!detail) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{detail.meeting.title}</h1>
          <p className="text-sm text-slate-500">
            {detail.meeting.turn_count} turns · {detail.meeting.chunk_count} chunks
          </p>
        </div>
        <div className="flex gap-2">
          <Link href={`/meetings/${meetingId}/chat`} className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white">
            Chat
          </Link>
          <Link
            href={`/meetings/${meetingId}/intelligence`}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
          >
            Intelligence
          </Link>
        </div>
      </div>

      <section className="grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-2 font-medium">Participants</h2>
          <div className="flex flex-wrap gap-2">
            {participants.map((name) => (
              <span key={name} className="rounded-full bg-slate-100 px-3 py-1 text-sm">
                {name}
              </span>
            ))}
          </div>
        </div>
        <div>
          <h2 className="mb-2 font-medium">Key topics</h2>
          <div className="flex flex-wrap gap-2">
            {topics.map((topic) => (
              <span key={topic.name} className="rounded-full bg-brand-50 px-3 py-1 text-sm text-brand-700">
                {topic.name}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section>
        <h2 className="mb-2 font-medium">Transcript</h2>
        <TranscriptViewer turns={detail.turns} />
      </section>
    </div>
  );
}
