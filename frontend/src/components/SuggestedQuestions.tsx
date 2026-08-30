type Props = {
  questions: string[];
  onSelect: (question: string) => void;
};

export function SuggestedQuestions({ questions, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {questions.map((question) => (
        <button
          key={question}
          type="button"
          onClick={() => onSelect(question)}
          className="rounded-full border border-slate-200 bg-white px-3 py-1 text-sm text-slate-700 hover:border-brand-600 hover:text-brand-700"
        >
          {question}
        </button>
      ))}
    </div>
  );
}
