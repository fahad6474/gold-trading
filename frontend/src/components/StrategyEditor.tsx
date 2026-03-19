import { useState } from "react";
import Editor from "@monaco-editor/react";
import { Play, Loader2 } from "lucide-react";
import { executeScript } from "../services/api";
import type { ExecuteResult } from "../types";

const DEFAULT_CODE = `# Execute arbitrary Python code here
# Available: close, open_, high, low, volume, df, pd, np, ta

# Example: print basic stats
print(f"Bars loaded: {len(close)}")
print(f"Latest close: {close.iloc[-1]:.4f}")
print(f"30-day high: {high.rolling(30).max().iloc[-1]:.4f}")
print(f"RSI(14): {ta.rsi(close, length=14).iloc[-1]:.2f}")

# Example: compute something
sma20 = close.rolling(20).mean()
above_ma = (close > sma20).sum()
print(f"Bars above SMA20: {above_ma} / {len(close)}")
`;

interface StrategyEditorProps {
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
}

export default function StrategyEditor({ symbol, timeframe, start, end }: StrategyEditorProps) {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [result, setResult] = useState<ExecuteResult | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const res = await executeScript({ code, language: "python", symbol, timeframe, start, end });
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
      <div className="panel overflow-hidden">
        <div className="flex items-center justify-between px-3 py-2 border-b border-dark-500">
          <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">Python Script Editor</span>
          <button className="btn-primary flex items-center gap-2" onClick={run} disabled={loading}>
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {loading ? "Running..." : "Execute"}
          </button>
        </div>
        <Editor
          height="320px"
          defaultLanguage="python"
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
              <div className="text-xs text-gray-400 mb-1">Variables:</div>
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
