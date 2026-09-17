import { useState } from "react";

import { queryDataset } from "../../api-client";
import { Badge } from "../../components/Badge";
import { Card } from "../../components/Card";
import { ErrorState, LoadingSkeleton } from "../../components/StatusStates";
import { useLazyAsync } from "../../hooks/useAsync";
import { useDatasetSession } from "../../state/useDatasetSession";
import { AIExplanationBlock, AIUnavailableNotice } from "../../panels/AIExplanationBlock";
import { EvidenceSources } from "../../panels/EvidenceSources";

const EXAMPLE_QUESTIONS = [
  "How many rows are duplicated?",
  "What columns have missing values?",
  "Which features are strongly correlated?",
  "Explain the baseline model.",
];

export function QaPanel({ datasetId }: { datasetId: string }) {
  const { lastMlResult } = useDatasetSession();
  const [question, setQuestion] = useState("");
  const qa = useLazyAsync((q: string) => queryDataset(datasetId, { question: q, ml_result: lastMlResult ?? undefined }));

  async function ask(q: string) {
    if (!q.trim()) return;
    await qa.run(q);
  }

  return (
    <Card title="Ask a question" description="Answered from the same deterministic evidence — never a simulated answer.">
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => {
                setQuestion(q);
                void ask(q);
              }}
              className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-400 transition hover:border-accent hover:text-accent"
            >
              {q}
            </button>
          ))}
        </div>

        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void ask(question);
          }}
        >
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about this dataset…"
            className="flex-1 rounded-md border border-white/10 bg-surface px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600"
          />
          <button
            type="submit"
            disabled={qa.status === "loading" || !question.trim()}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-surface transition disabled:cursor-not-allowed disabled:opacity-40"
          >
            Ask
          </button>
        </form>

        {qa.status === "loading" && <LoadingSkeleton rows={2} />}
        {qa.status === "error" && <ErrorState message={qa.message} />}
        {qa.status === "success" && (
          <div className="rounded-lg border border-white/5 bg-white/[0.02] p-4">
            <div className="mb-2 flex items-center gap-2">
              <Badge tone="neutral">{qa.data.question_category.replace(/_/g, " ")}</Badge>
            </div>
            <p className="text-sm text-slate-300">{qa.data.question}</p>
            {qa.data.computed.resolved_answer && (
              <p className="mt-2 font-mono text-sm text-slate-100">{qa.data.computed.resolved_answer}</p>
            )}
            {qa.data.available ? (
              <AIExplanationBlock explanation={qa.data.ai_explanation} limitations={qa.data.limitations} />
            ) : (
              <AIUnavailableNotice reason={qa.data.reason} />
            )}
            <EvidenceSources sources={qa.data.evidence_sources} />
          </div>
        )}
      </div>
    </Card>
  );
}
