const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Meeting = {
  meeting_id: string;
  title: string;
  uploaded_at: string;
  turn_count: number;
  chunk_count: number;
  participants: string[];
};

export type Citation = {
  speaker: string;
  timestamp: string;
  snippet: string;
  chunk_id: string;
};

export type QueryResponse = {
  answer: string;
  citations: Citation[];
  refused: boolean;
  llm_provider: string;
  model_name: string;
};

export type TranscriptTurn = {
  timestamp: string;
  speaker: string;
  text: string;
  turn_index: number;
};

export type MeetingDetail = {
  meeting: Meeting;
  turns: TranscriptTurn[];
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function listMeetings(): Promise<Meeting[]> {
  return request<Meeting[]>("/api/v1/meetings");
}

export async function uploadMeeting(title: string, file: File) {
  const form = new FormData();
  form.append("title", title);
  form.append("file", file);
  return request<{ meeting_id: string }>("/api/v1/meetings", { method: "POST", body: form });
}

export async function uploadMeetingFromAudio(
  title: string,
  file: File,
  defaultSpeaker?: string,
) {
  const form = new FormData();
  form.append("title", title);
  form.append("file", file);
  if (defaultSpeaker?.trim()) {
    form.append("default_speaker", defaultSpeaker.trim());
  }
  return request<{ meeting_id: string }>("/api/v1/meetings/from-audio", {
    method: "POST",
    body: form,
  });
}

export async function getMeeting(id: string): Promise<MeetingDetail> {
  return request<MeetingDetail>(`/api/v1/meetings/${id}`);
}

export async function queryMeeting(id: string, question: string): Promise<QueryResponse> {
  return request<QueryResponse>(`/api/v1/meetings/${id}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export async function getSummary(id: string): Promise<{ summary: string }> {
  return request(`/api/v1/meetings/${id}/summary`);
}

export async function getDecisions(id: string) {
  return request<Array<{ text: string; timestamp: string; speaker: string }>>(
    `/api/v1/meetings/${id}/decisions`,
  );
}

export async function getActionItems(id: string) {
  return request<Array<{ text: string; assignee: string | null; timestamp: string; speaker: string }>>(
    `/api/v1/meetings/${id}/action-items`,
  );
}

export async function getTopics(id: string) {
  return request<Array<{ name: string; score: number }>>(`/api/v1/meetings/${id}/topics`);
}

export async function getParticipants(id: string): Promise<string[]> {
  return request<string[]>(`/api/v1/meetings/${id}/participants`);
}
