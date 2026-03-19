import { useState } from "react";
import Editor from "@monaco-editor/react";
import { Play, Loader2, Code } from "lucide-react";
import { executeScript } from "../services/api";
import type { ExecuteResult } from "../types";

const DEFAULT_PINE = `//@version=5
strategy("My Gold Strategy", overlay=true)

// Parameters
fastLen = input.int(10, "Fast MA Length")
slowLen = input.int(30, "Slow MA Length")

// Indicators
fastMA = ta.ema(close, fastLen)
slowMA = ta.ema(close, slowLen)

// Signals
longCondition = ta.crossover(fastMA, slowMA)
shortCondition = ta.crossunder(fastMA, slowMA)

// Strategy
strategy.entry("Long", strategy.long, when=longCondition)
strategy.close("Long", when=shortCondition)
`;

interface PineScriptEditorProps {
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
}

export default function PineScriptEditor({ symbol, timeframe, start, end }: PineScriptEditorProps) {
  const [code, setCode] = useState(DEFAULT_PINE);
  const [result, setResult] = useState<ExecuteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [showTranspiled, setShowTranspiled] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const res = await executeScript({ code, language: "pine", symbol, timeframe, start, end });
      setResult(res);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail || (e as { message?: string })?.message || "Unknown error";
      setResult({ stdout: "", stderr: msg, result: null, transpiled_code: null, success: false });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Warning banner */}
      <div className="bg-yellow-900/30 border border-yellow-700/50 rounded p-2 text-xs text-yellow-300">
        <strong>Pine Script Transpiler</strong> — Converts Pine Script v5 to Python and executes it.
        Supported: <code>ta.*</code>, <code>strategy.entry/close</code>, crossover/crossunder, math.*.
        Not supported: <code>plot()</code>, <code>request.security()</code>, <code>array.*</code>.
      </div>

      <div className="panel overflow-hidden">
        <div className="flex items-center justify-between px-3 py-2 border-b border-dark-500">
          <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">Pine Script Editor</span>
          <div className="flex gap-2">
            {result?.transpiled_code && (
              <button
                className="btn-ghost flex items-center gap-1"
                onClick={() => setShowTranspiled(!showTranspiled)}
              >
                <Code size={14} />
                {showTranspiled ? "Hide Python" : "Show Python"}
              </button>
            )}
            <button className="btn-gold flex items-center gap-2" onClick={run} disabled={loading}>
              {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              {loading ? "Transpiling..." : "Run Pine Script"}
            </button>
          </div>
        </div>
        <Editor
          height="320px"
          defaultLanguage="javascript"
          value={code}
          onChange={(v) => setCode(v || "")}
          theme="vs-dark"
          options={{
            fontSize: 13,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbers: "on",
            wordWrap: "on",
            tabSize: 4,
          }}
        />
      </div>

      {result?.transpiled_code && showTranspiled && (
        <div className="panel p-3">
          <div className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
            Generated Python Code
          </div>
          <pre className="text-xs text-blue-200 bg-dark-300 rounded p-3 overflow-x-auto whitespace-pre-wrap">
            {result.transpiled_code}
          </pre>
        </div>
      )}

      {result && (
        <div className="panel p-3 flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">Output</span>
            <span className={`text-xs px-2 py-0.5 rounded ${result.success ? "bg-green-800 text-green-200" : "bg-red-800 text-red-200"}`}>
              {result.success ? "Success" : "Error"}
            </span>
          </div>

          {result.stdout && (
            <pre className="text-xs text-green-300 bg-dark-300 rounded p-3 overflow-x-auto whitespace-pre-wrap">
              {result.stdout}
            </pre>
          )}
          {result.stderr && (
            <pre className="text-xs text-red-300 bg-dark-300 rounded p-3 overflow-x-auto whitespace-pre-wrap">
              {result.stderr}
            </pre>
          )}
          {result.result && Object.keys(result.result).length > 0 && (
            <div>
              <div className="text-xs text-gray-400 mb-1">Variables set:</div>
              <pre className="text-xs text-blue-200 bg-dark-300 rounded p-3 overflow-x-auto">
                {JSON.stringify(result.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
