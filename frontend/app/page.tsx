"use client";

import { useState, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";

function getApiUrl() {
  if (typeof window !== "undefined") {
    // In the browser — always call the orchestrator via localhost
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

const API = getApiUrl();

interface TraceEvent {
  type: string;
  step_id?: string;
  agent?: string;
  tool?: string;
  status?: string;
  detail?: string;
  correlation_id?: string;
}

interface TokenUsage {
  total_input_tokens: number;
  total_output_tokens: number;
  total_calls: number;
  estimated_cost_usd?: number;
}

// ── Summary renderer ─────────────────────────────────────────────────────────

function StepBadge({ agent, tool }: { agent: string; tool: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs">
      <span className="bg-blue-900 text-blue-300 px-2 py-0.5 rounded">{agent}</span>
      <span className="text-gray-500">→</span>
      <span className="bg-gray-800 text-gray-300 px-2 py-0.5 rounded font-mono">{tool}</span>
    </span>
  );
}

function StepSummary({ stepId, data, plan }: { stepId: string; data: unknown; plan: unknown[] }) {
  const planStep = (plan as any[]).find((s) => s.step_id === stepId);
  const agent = planStep?.agent ?? "";
  const tool = planStep?.tool ?? "";
  const d = data as Record<string, unknown>;
  if (!d || typeof d !== "object") return null;

  const renderContent = () => {
    // Question extraction
    if ("questions" in d) {
      const questions = d.questions as string[];
      return (
        <div>
          <p className="text-sm text-gray-400 mb-2">
            <span className="font-semibold text-white">{d.count as number}</span> questions extracted
          </p>
          {questions.length > 0 ? (
            <ol className="list-decimal list-inside space-y-2">
              {questions.map((q, i) => (
                <li key={i} className="text-sm text-gray-200 leading-snug">{q.trim()}</li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-gray-500 italic">No questions found.</p>
          )}
        </div>
      );
    }

    // Keyword extraction
    if ("keywords" in d) {
      const keywords = d.keywords as string[];
      return (
        <div>
          <p className="text-sm text-gray-400 mb-2">
            <span className="font-semibold text-white">{keywords.length}</span> keywords extracted
          </p>
          <div className="flex flex-wrap gap-2">
            {keywords.map((k, i) => (
              <span key={i} className="bg-indigo-900 text-indigo-200 text-xs px-2 py-1 rounded-full">{k}</span>
            ))}
          </div>
        </div>
      );
    }

    // Summary / clinical brief
    if ("summary" in d || "clinical_brief" in d) {
      const extractive = d.summary as string | undefined;
      const clinical = d.clinical_brief as string | undefined;
      const llm = d.llm_enhanced as string | undefined;
      const sents = d.sentences_selected as number | undefined;
      // Prefer clinical_brief (AI-enhanced, comprehensive) over extractive summary
      const primary = clinical || extractive || "";
      const hasExtractive = extractive && clinical; // show extractive separately only if clinical exists too
      return (
        <div className="space-y-3">
          {sents !== undefined && <p className="text-xs text-gray-500">{sents} key sentences selected</p>}
          {hasExtractive && (
            <details className="text-sm">
              <summary className="text-gray-500 cursor-pointer hover:text-gray-300 text-xs">
                Extractive summary ({sents ?? "—"} sentences)
              </summary>
              <p className="text-gray-400 leading-relaxed whitespace-pre-wrap mt-2">{extractive}</p>
            </details>
          )}
          <div className="text-sm text-gray-200 leading-relaxed max-w-none [&_h1]:text-lg [&_h1]:font-bold [&_h1]:mt-4 [&_h1]:mb-2 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-3 [&_h2]:mb-1 [&_strong]:text-white [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1 [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:space-y-1 [&_p]:mb-2">
            <ReactMarkdown>{primary}</ReactMarkdown>
          </div>
          {llm && (
            <div className="mt-3 pt-3 border-t border-gray-700">
              <p className="text-xs text-gray-500 mb-1">AI-Enhanced Summary</p>
              <div className="text-sm text-gray-200 leading-relaxed max-w-none [&_h1]:text-lg [&_h1]:font-bold [&_h1]:mt-4 [&_h1]:mb-2 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-3 [&_h2]:mb-1 [&_strong]:text-white [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1 [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:space-y-1 [&_p]:mb-2">
                <ReactMarkdown>{llm}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      );
    }

    // File read (content preview)
    if ("content" in d) {
      const content = d.content as string;
      const preview = content.length > 800 ? content.slice(0, 800) + "…" : content;
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs text-gray-500">
            {"file" in d && <span>File: <span className="text-gray-300">{String(d.file)}</span></span>}
            {"chars" in d && <span>Chars: <span className="text-gray-300">{Number(d.chars).toLocaleString()}</span></span>}
            {"lines" in d && <span>Lines: <span className="text-gray-300">{String(d.lines)}</span></span>}
          </div>
          <pre className="text-xs text-gray-300 bg-gray-900 rounded p-3 overflow-auto max-h-48 whitespace-pre-wrap">{preview}</pre>
        </div>
      );
    }

    // Error
    if ("error" in d) return <p className="text-sm text-red-400">{d.error as string}</p>;

    // Fallback key-value display
    return (
      <div className="space-y-2">
        {Object.entries(d)
          .filter(([k]) => !["groq_model", "tokens_in", "tokens_out"].includes(k))
          .map(([k, v]) => (
            <div key={k}>
              <span className="text-xs text-gray-500 uppercase tracking-wide">{k.replace(/_/g, " ")}</span>
              <p className="text-sm text-gray-200 mt-0.5">
                {typeof v === "object" ? JSON.stringify(v, null, 2) : String(v)}
              </p>
            </div>
          ))}
      </div>
    );
  };

  const tokensIn = d.tokens_in as number | undefined;
  const tokensOut = d.tokens_out as number | undefined;
  const groqModel = d.groq_model as string | undefined;

  return (
    <div className="border border-gray-700 rounded-lg overflow-hidden">
      <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-gray-500">{stepId}</span>
          {agent && <StepBadge agent={agent} tool={tool} />}
        </div>
        {(tokensIn || groqModel) && (
          <span className="text-xs text-gray-600 font-mono">
            {groqModel && <span>{groqModel} · </span>}
            {tokensIn !== undefined && <span>{tokensIn}↑ {tokensOut}↓ tokens</span>}
          </span>
        )}
      </div>
      <div className="px-4 py-4 bg-gray-900">{renderContent()}</div>
    </div>
  );
}

function SummaryView({ results, plan }: { results: Record<string, unknown>; plan: unknown[] }) {
  const steps = Object.entries(results);
  if (steps.length === 0) return <p className="text-gray-500 text-sm">No results.</p>;
  return (
    <div className="space-y-4">
      {steps.map(([stepId, data]) => (
        <StepSummary key={stepId} stepId={stepId} data={data} plan={plan} />
      ))}
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function Home() {
  const [goal, setGoal] = useState("");
  const [files, setFiles] = useState("");
  const [trace, setTrace] = useState<TraceEvent[]>([]);
  const [results, setResults] = useState<Record<string, unknown> | null>(null);
  const [plan, setPlan] = useState<unknown[]>([]);
  const [tokenUsage, setTokenUsage] = useState<TokenUsage | null>(null);
  const [running, setRunning] = useState(false);
  const [correlationId, setCorrelationId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; path: string }[]>([]);
  const [outputTab, setOutputTab] = useState<"summary" | "json">("summary");
  const traceRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollTrace = useCallback(() => {
    if (traceRef.current) {
      traceRef.current.scrollTop = traceRef.current.scrollHeight;
    }
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files;
    if (!selected || selected.length === 0) return;
    setUploading(true);

    const newUploaded: { name: string; path: string }[] = [];
    for (let i = 0; i < selected.length; i++) {
      const file = selected[i];
      const formData = new FormData();
      formData.append("file", file);
      try {
        const resp = await fetch(`${API}/upload`, { method: "POST", body: formData });
        if (resp.ok) {
          const data = await resp.json();
          newUploaded.push({ name: data.filename, path: data.path });
        }
      } catch {
        // skip failed uploads silently
      }
    }

    setUploadedFiles((prev) => [...prev, ...newUploaded]);
    const allPaths = [...uploadedFiles, ...newUploaded].map((f) => f.path);
    setFiles(allPaths.join(", "));
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeUploadedFile = (index: number) => {
    setUploadedFiles((prev) => {
      const next = prev.filter((_, i) => i !== index);
      setFiles(next.map((f) => f.path).join(", "));
      return next;
    });
  };

  const startWorkflow = async () => {
    if (!goal.trim()) return;
    setRunning(true);
    setTrace([]);
    setResults(null);
    setPlan([]);
    setTokenUsage(null);

    const fileList = files
      .split(",")
      .map((f) => f.trim())
      .filter(Boolean);

    try {
      const resp = await fetch(`${API}/workflow/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal, files: fileList }),
      });

      if (!resp.ok || !resp.body) {
        setTrace([{ type: "error", detail: `HTTP ${resp.status}` }]);
        setRunning(false);
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "start") {
              setCorrelationId(event.correlation_id || "");
            } else if (event.type === "plan") {
              setPlan(event.steps || []);
            } else if (event.type === "trace") {
              setTrace((prev) => [...prev, event]);
              scrollTrace();
            } else if (event.type === "complete") {
              setResults(event.results || {});
              setTokenUsage(event.token_usage || null);
            } else if (event.type === "error") {
              setTrace((prev) => [
                ...prev,
                { type: "error", detail: event.detail },
              ]);
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch (err) {
      setTrace((prev) => [
        ...prev,
        { type: "error", detail: String(err) },
      ]);
    }

    setRunning(false);
  };

  const approveStep = async (stepId: string, approved: boolean) => {
    await fetch(`${API}/workflow/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        step_id: stepId,
        approved,
        correlation_id: correlationId,
      }),
    });
  };

  const statusColor = (s?: string) => {
    switch (s) {
      case "completed":
        return "text-green-400";
      case "failed":
        return "text-red-400";
      case "in-progress":
        return "text-yellow-400";
      case "requires-approval":
        return "text-purple-400";
      default:
        return "text-gray-400";
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Healthcare Multi-Agent Workflow</h1>
        {tokenUsage && (
          <div className="text-sm text-gray-400 font-mono">
            Tokens: {tokenUsage.total_input_tokens} in / {tokenUsage.total_output_tokens} out
            &middot; Calls: {tokenUsage.total_calls}
            {tokenUsage.estimated_cost_usd !== undefined &&
              ` · $${tokenUsage.estimated_cost_usd.toFixed(4)}`}
          </div>
        )}
      </header>

      {/* Input bar */}
      <div className="bg-gray-900 px-6 py-3 flex gap-3 items-end border-b border-gray-800">
        <div className="flex-1">
          <label className="block text-xs text-gray-400 mb-1">Goal</label>
          <input
            className="w-full bg-gray-800 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. Read sample.txt and produce a clinical brief"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !running && startWorkflow()}
          />
        </div>
        <div className="w-72">
          <label className="block text-xs text-gray-400 mb-1">Files</label>
          <div className="flex gap-2">
            <input
              className="flex-1 bg-gray-800 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="sample_data/sample.txt"
              value={files}
              onChange={(e) => setFiles(e.target.value)}
            />
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".txt,.pdf,.xlsx,.xls,.csv"
              className="hidden"
              onChange={handleFileUpload}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 px-3 py-2 rounded text-sm whitespace-nowrap"
            >
              {uploading ? "Uploading..." : "Upload"}
            </button>
          </div>
          {uploadedFiles.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {uploadedFiles.map((f, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 bg-gray-800 text-xs text-gray-300 px-2 py-0.5 rounded"
                >
                  {f.name}
                  <button
                    onClick={() => removeUploadedFile(i)}
                    className="text-gray-500 hover:text-red-400 ml-1"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={startWorkflow}
          disabled={running || !goal.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 px-5 py-2 rounded text-sm font-medium"
        >
          {running ? "Running..." : "Run Workflow"}
        </button>
      </div>

      {/* Main panels */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Trace */}
        <div className="w-1/3 border-r border-gray-800 flex flex-col">
          <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase bg-gray-900">
            Execution Trace
          </div>
          <div
            ref={traceRef}
            className="flex-1 overflow-y-auto px-4 py-2 space-y-1 text-sm font-mono"
          >
            {plan.length > 0 && (
              <div className="mb-3 pb-2 border-b border-gray-800">
                <div className="text-xs text-gray-500 mb-1">PLAN</div>
                {plan.map((s: any, i: number) => (
                  <div key={i} className="text-gray-400 text-xs">
                    {s.step_id}: {s.agent} → {s.tool}
                    {s.depends_on?.length > 0 && (
                      <span className="text-gray-600"> (after {s.depends_on.join(", ")})</span>
                    )}
                  </div>
                ))}
              </div>
            )}
            {trace.map((ev, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className={`${statusColor(ev.status)} font-bold`}>●</span>
                <span className="text-gray-300">
                  {ev.step_id && <span className="text-gray-500">[{ev.step_id}] </span>}
                  {ev.agent && <span className="text-blue-400">{ev.agent}</span>}
                  {ev.tool && <span className="text-gray-500"> → {ev.tool}</span>}
                  {ev.status && (
                    <span className={`ml-2 ${statusColor(ev.status)}`}>{ev.status}</span>
                  )}
                </span>
                {ev.status === "requires-approval" && (
                  <span className="ml-auto flex gap-1">
                    <button
                      onClick={() => approveStep(ev.step_id!, true)}
                      className="bg-green-700 hover:bg-green-600 px-2 py-0.5 rounded text-xs"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => approveStep(ev.step_id!, false)}
                      className="bg-red-700 hover:bg-red-600 px-2 py-0.5 rounded text-xs"
                    >
                      Reject
                    </button>
                  </span>
                )}
              </div>
            ))}
            {trace.length === 0 && !running && (
              <div className="text-gray-600 text-center mt-8">
                Enter a goal and click Run Workflow
              </div>
            )}
          </div>
        </div>

        {/* Right: Output with Summary / JSON tabs */}
        <div className="w-2/3 flex flex-col">
          {/* Tab bar */}
          <div className="flex items-center border-b border-gray-800 bg-gray-900">
            {(["summary", "json"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setOutputTab(tab)}
                className={`px-5 py-2 text-xs font-semibold uppercase tracking-wide border-b-2 transition-colors ${
                  outputTab === tab
                    ? "border-blue-500 text-blue-400"
                    : "border-transparent text-gray-500 hover:text-gray-300"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-4">
            {results ? (
              outputTab === "summary" ? (
                <SummaryView results={results} plan={plan} />
              ) : (
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown>
                    {"```json\n" + JSON.stringify(results, null, 2) + "\n```"}
                  </ReactMarkdown>
                </div>
              )
            ) : running ? (
              <div className="text-gray-500 text-center mt-8">Processing...</div>
            ) : (
              <div className="text-gray-600 text-center mt-8">
                Results will appear here after the workflow completes
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
