import { useMemo, useState } from "react";

import { getTaskTypes, trainModel, validateTarget } from "../../api-client";
import type { ModelName, TaskType } from "../../api-client";
import { Badge } from "../../components/Badge";
import { Card } from "../../components/Card";
import { ErrorState, LoadingSkeleton } from "../../components/StatusStates";
import { StatValue } from "../../components/StatValue";
import { useAsync, useLazyAsync } from "../../hooks/useAsync";
import { useDatasetSession } from "../../state/useDatasetSession";
import { useWorkspaceDataset } from "../workspace/useWorkspaceDataset";

function TargetSelector({
  columns,
  value,
  onChange,
}: {
  columns: string[];
  value: string;
  onChange: (column: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm text-slate-300">
      Target column
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-white/10 bg-surface px-3 py-2 text-sm text-slate-100"
      >
        <option value="" disabled>
          Select a column…
        </option>
        {columns.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
    </label>
  );
}

export function MlPage() {
  const dataset = useWorkspaceDataset();
  const { setLastMlResult } = useDatasetSession();
  const taskTypes = useAsync(getTaskTypes, []);

  const [targetColumn, setTargetColumn] = useState("");
  const validation = useLazyAsync((column: string) => validateTarget(dataset.id, { target_column: column }));

  const [taskType, setTaskType] = useState<TaskType | "">("");
  const [modelName, setModelName] = useState<ModelName | "">("");
  const training = useLazyAsync(trainModel);

  const supportedModels = useMemo(() => {
    if (!taskType || taskTypes.status !== "success") return [];
    return taskTypes.data.task_types.find((t) => t.task_type === taskType)?.supported_models ?? [];
  }, [taskType, taskTypes]);

  async function handleTargetChange(column: string) {
    setTargetColumn(column);
    setTaskType("");
    setModelName("");
    const result = await validation.run(column);
    if (result?.suggested_task) setTaskType(result.suggested_task);
  }

  async function handleTrain() {
    if (!targetColumn || !taskType || !modelName) return;
    const result = await training.run(dataset.id, {
      target_column: targetColumn,
      task_type: taskType,
      model_name: modelName,
    });
    if (result) setLastMlResult(result);
  }

  return (
    <div className="flex flex-col gap-6">
      <Card title="Configure a baseline model" description="Every model here is a transparent, interpretable baseline — not AutoML.">
        <div className="flex flex-col gap-4">
          <TargetSelector
            columns={dataset.columns.map((c) => c.name)}
            value={targetColumn}
            onChange={handleTargetChange}
          />

          {validation.status === "loading" && <LoadingSkeleton rows={2} />}
          {validation.status === "error" && <ErrorState message={validation.message} />}
          {validation.status === "success" && (
            <div className="flex flex-col gap-2 rounded-lg border border-white/5 bg-white/[0.02] p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Suitability</p>
              <div className="flex flex-wrap gap-2">
                {validation.data.suitable_tasks.map((t) => (
                  <Badge key={t.task_type} tone={t.suitable ? "good" : "neutral"}>
                    {t.task_type}
                  </Badge>
                ))}
              </div>
              {validation.data.suitable_tasks
                .filter((t) => !t.suitable)
                .map((t) => (
                  <p key={t.task_type} className="text-xs text-slate-500">
                    {t.task_type}: {t.reason}
                  </p>
                ))}
              {validation.data.suggested_task && (
                <p className="text-xs text-slate-400">
                  Suggested task: <span className="font-mono">{validation.data.suggested_task}</span> (a suggestion
                  only — you choose the final task type).
                </p>
              )}
            </div>
          )}

          {taskTypes.status === "success" && targetColumn && (
            <div className="flex flex-wrap gap-4">
              <label className="flex flex-col gap-1 text-sm text-slate-300">
                Task type
                <select
                  value={taskType}
                  onChange={(e) => {
                    setTaskType(e.target.value as TaskType);
                    setModelName("");
                  }}
                  className="rounded-md border border-white/10 bg-surface px-3 py-2 text-sm text-slate-100"
                >
                  <option value="" disabled>
                    Select a task type…
                  </option>
                  {taskTypes.data.task_types.map((t) => (
                    <option key={t.task_type} value={t.task_type}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col gap-1 text-sm text-slate-300">
                Model
                <select
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value as ModelName)}
                  disabled={supportedModels.length === 0}
                  className="rounded-md border border-white/10 bg-surface px-3 py-2 text-sm text-slate-100 disabled:opacity-40"
                >
                  <option value="" disabled>
                    Select a model…
                  </option>
                  {supportedModels.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          <button
            type="button"
            onClick={handleTrain}
            disabled={!targetColumn || !taskType || !modelName || training.status === "loading"}
            className="w-fit rounded-md bg-accent px-4 py-2 text-sm font-medium text-surface transition disabled:cursor-not-allowed disabled:opacity-40"
          >
            {training.status === "loading" ? "Training…" : "Train baseline model"}
          </button>
        </div>
      </Card>

      {training.status === "error" && <ErrorState message={training.message} onRetry={training.reset} />}

      {training.status === "success" && (
        <Card title="Result" description={`${training.data.model_name} · ${training.data.task_type}`}>
          <div className="flex flex-col gap-6">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatValue label="Train rows" value={training.data.train_size} />
              <StatValue label="Test rows" value={training.data.test_size_actual} />
              <StatValue label="Features" value={training.data.feature_columns.length} />
              <StatValue label="Excluded" value={training.data.excluded_columns.length} />
            </div>

            <div>
              <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Metrics</p>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                {Object.entries(training.data.metrics).map(([name, value]) => (
                  <StatValue key={name} label={name} value={value} />
                ))}
              </div>
              {Object.keys(training.data.unavailable_metrics).length > 0 && (
                <ul className="mt-2 flex flex-col gap-1 text-xs text-slate-500">
                  {Object.entries(training.data.unavailable_metrics).map(([name, reason]) => (
                    <li key={name}>
                      {name}: not available — {reason}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {training.data.confusion_matrix && (
              <div>
                <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Confusion matrix</p>
                <table className="border-collapse text-xs">
                  <thead>
                    <tr>
                      <th className="p-1" />
                      {training.data.confusion_matrix.labels.map((label) => (
                        <th key={label} className="border border-white/10 p-1 font-mono text-slate-400">
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {training.data.confusion_matrix.matrix.map((row, i) => (
                      <tr key={training.data.confusion_matrix?.labels[i]}>
                        <th className="border border-white/10 p-1 font-mono text-slate-400">
                          {training.data.confusion_matrix?.labels[i]}
                        </th>
                        {row.map((cell, j) => (
                          <td key={j} className="border border-white/10 p-1 text-center font-mono text-slate-200">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {(training.data.warnings.length > 0 || training.data.limitations.length > 0) && (
              <div className="border-t border-white/5 pt-3">
                {training.data.warnings.map((w) => (
                  <p key={w} className="text-xs text-amber-300">
                    ⚠ {w}
                  </p>
                ))}
                {training.data.limitations.map((l) => (
                  <p key={l} className="text-xs text-slate-500">
                    · {l}
                  </p>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
