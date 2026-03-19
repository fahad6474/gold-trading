import { useState } from "react";
import { Plus, X } from "lucide-react";
import type { IndicatorConfig } from "../types";

const AVAILABLE_INDICATORS: Array<{
  name: string;
  label: string;
  defaultParams: Record<string, number>;
  panel: "main" | "sub";
}> = [
  { name: "SMA", label: "SMA", defaultParams: { length: 20 }, panel: "main" },
  { name: "EMA", label: "EMA", defaultParams: { length: 20 }, panel: "main" },
  { name: "RSI", label: "RSI", defaultParams: { length: 14 }, panel: "sub" },
  { name: "MACD", label: "MACD", defaultParams: { fast: 12, slow: 26, signal: 9 }, panel: "sub" },
  { name: "BBANDS", label: "Bollinger Bands", defaultParams: { length: 20, std: 2 }, panel: "main" },
  { name: "ATR", label: "ATR", defaultParams: { length: 14 }, panel: "sub" },
  { name: "STOCH", label: "Stochastic", defaultParams: { k: 5, d: 3 }, panel: "sub" },
  { name: "OBV", label: "OBV", defaultParams: {}, panel: "sub" },
  { name: "CCI", label: "CCI", defaultParams: { length: 20 }, panel: "sub" },
  { name: "WILLIAMS", label: "Williams %R", defaultParams: { length: 14 }, panel: "sub" },
  { name: "ADX", label: "ADX", defaultParams: { length: 14 }, panel: "sub" },
  { name: "MOM", label: "Momentum", defaultParams: { length: 10 }, panel: "sub" },
  { name: "ROC", label: "Rate of Change", defaultParams: { length: 10 }, panel: "sub" },
];

interface IndicatorPanelProps {
  active: IndicatorConfig[];
  onChange: (indicators: IndicatorConfig[]) => void;
}

export default function IndicatorPanel({ active, onChange }: IndicatorPanelProps) {
  const [selected, setSelected] = useState("SMA");

  const addIndicator = () => {
    const def = AVAILABLE_INDICATORS.find((i) => i.name === selected);
    if (!def) return;
    const id = `${def.name}_${Date.now()}`;
    onChange([
      ...active,
      { id, name: def.name, params: { ...def.defaultParams }, panel: def.panel },
    ]);
  };

  const removeIndicator = (id: string) => {
    onChange(active.filter((i) => i.id !== id));
  };

  const updateParam = (id: string, key: string, value: string) => {
    onChange(
      active.map((i) =>
        i.id === id ? { ...i, params: { ...i.params, [key]: Number(value) || value } } : i
      )
    );
  };

  return (
    <div className="panel p-3 flex flex-col gap-3">
      <div className="text-xs font-bold text-gray-300 uppercase tracking-wider">Indicators</div>

      {/* Add indicator */}
      <div className="flex gap-2">
        <select
          className="select flex-1"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          {AVAILABLE_INDICATORS.map((ind) => (
            <option key={ind.name} value={ind.name}>
              {ind.label}
            </option>
          ))}
        </select>
        <button className="btn-primary flex items-center gap-1" onClick={addIndicator}>
          <Plus size={14} />
          Add
        </button>
      </div>

      {/* Active indicators */}
      <div className="flex flex-col gap-2">
        {active.map((ind) => (
          <div key={ind.id} className="bg-dark-300 rounded p-2 flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-200">{ind.name}</span>
              <button
                className="text-gray-500 hover:text-red-400 transition-colors"
                onClick={() => removeIndicator(ind.id)}
              >
                <X size={14} />
              </button>
            </div>
            {Object.entries(ind.params).length > 0 && (
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(ind.params).map(([key, val]) => (
                  <div key={key}>
                    <label className="label">{key}</label>
                    <input
                      type="number"
                      className="input w-full"
                      value={val as number}
                      onChange={(e) => updateParam(ind.id, key, e.target.value)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {active.length === 0 && (
          <div className="text-xs text-gray-500 text-center py-2">No indicators added</div>
        )}
      </div>
    </div>
  );
}
