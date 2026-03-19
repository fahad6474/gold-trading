import { useEffect, useRef, useCallback } from "react";
import {
  createChart,
  createSeriesMarkers,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from "lightweight-charts";
import type { OHLCVBar, IndicatorSeries, TradeRecord } from "../types";

interface ChartProps {
  bars: OHLCVBar[];
  indicators: IndicatorSeries[];
  trades?: TradeRecord[];
  height?: number;
}

const CHART_COLORS = {
  bg: "#1b2838",
  grid: "#2a3f54",
  text: "#9ca3af",
  border: "#2a3f54",
  up: "#26a69a",
  down: "#ef5350",
};

export default function Chart({ bars, indicators, trades = [], height = 420 }: ChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const subChartRef = useRef<IChartApi | null>(null);
  const subContainerRef = useRef<HTMLDivElement>(null);
  const lineSeriesRefs = useRef<ISeriesApi<"Line">[]>([]);
  const subLineSeriesRefs = useRef<(ISeriesApi<"Line"> | ISeriesApi<"Histogram">)[]>([]);

  const initCharts = useCallback(() => {
    if (!containerRef.current) return;

    // Clean up
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }
    if (subChartRef.current) {
      subChartRef.current.remove();
      subChartRef.current = null;
    }
    lineSeriesRefs.current = [];
    subLineSeriesRefs.current = [];

    const baseOpts = {
      layout: {
        background: { type: ColorType.Solid, color: CHART_COLORS.bg },
        textColor: CHART_COLORS.text,
      },
      grid: {
        vertLines: { color: CHART_COLORS.grid },
        horzLines: { color: CHART_COLORS.grid },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: CHART_COLORS.border },
      timeScale: { borderColor: CHART_COLORS.border, timeVisible: true },
    };

    // Main chart
    const chart = createChart(containerRef.current, {
      ...baseOpts,
      width: containerRef.current.clientWidth,
      height,
    });
    chartRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: CHART_COLORS.up,
      downColor: CHART_COLORS.down,
      borderUpColor: CHART_COLORS.up,
      borderDownColor: CHART_COLORS.down,
      wickUpColor: CHART_COLORS.up,
      wickDownColor: CHART_COLORS.down,
    });
    candleRef.current = candleSeries;

    // Add main-panel indicator overlays
    const mainIndicators = indicators.filter((ind) => ind.panel === "main");
    for (const ind of mainIndicators) {
      const color = ind.color || "#60a5fa";
      const lineSeries = chart.addSeries(LineSeries, {
        color,
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: true,
        title: ind.name,
      });
      const formatted = ind.data.map((d) => ({ time: d.time as Time, value: d.value }));
      lineSeries.setData(formatted);
      lineSeriesRefs.current.push(lineSeries);
    }

    // Sub chart for oscillators
    const subIndicators = indicators.filter((ind) => ind.panel === "sub");
    if (subIndicators.length > 0 && subContainerRef.current) {
      const subChart = createChart(subContainerRef.current, {
        ...baseOpts,
        width: subContainerRef.current.clientWidth,
        height: 160,
        timeScale: { ...baseOpts.timeScale, visible: false },
      });
      subChartRef.current = subChart;

      for (const ind of subIndicators) {
        const color = ind.color || "#60a5fa";
        if (ind.type === "histogram") {
          const histSeries = subChart.addSeries(HistogramSeries, { color, priceLineVisible: false, title: ind.name });
          histSeries.setData(ind.data.map((d) => ({ time: d.time as Time, value: d.value })));
          subLineSeriesRefs.current.push(histSeries as unknown as ISeriesApi<"Line">);
        } else {
          const lineSeries = subChart.addSeries(LineSeries, {
            color,
            lineWidth: 1,
            priceLineVisible: false,
            title: ind.name,
          });
          lineSeries.setData(ind.data.map((d) => ({ time: d.time as Time, value: d.value })));
          subLineSeriesRefs.current.push(lineSeries);
        }
      }

      // Sync crosshair
      chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (range) subChart.timeScale().setVisibleLogicalRange(range);
      });
    }

    // Set candle data
    if (bars.length > 0) {
      const candleData = bars.map((b) => ({
        time: b.time as Time,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      }));
      candleSeries.setData(candleData);

      // Trade markers
      if (trades.length > 0) {
        const markers = trades.flatMap((t) => [
          {
            time: t.entry_time as Time,
            position: "belowBar" as const,
            color: "#26a69a",
            shape: "arrowUp" as const,
            text: `BUY $${t.entry_price.toFixed(2)}`,
          },
          {
            time: t.exit_time as Time,
            position: "aboveBar" as const,
            color: t.pnl >= 0 ? "#26a69a" : "#ef5350",
            shape: "arrowDown" as const,
            text: `SELL $${t.exit_price.toFixed(2)} (${t.pnl >= 0 ? "+" : ""}${t.pnl_pct.toFixed(1)}%)`,
          },
        ]);
        // Sort markers by time
        markers.sort((a, b) => (a.time as number) - (b.time as number));
        createSeriesMarkers(candleSeries, markers);
      }

      chart.timeScale().fitContent();
      if (subChartRef.current) subChartRef.current.timeScale().fitContent();
    }

    // Resize observer
    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
      if (subContainerRef.current && subChartRef.current) {
        subChartRef.current.applyOptions({ width: subContainerRef.current.clientWidth });
      }
    });
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [bars, indicators, trades, height]);

  useEffect(() => {
    const cleanup = initCharts();
    return () => {
      cleanup?.();
      chartRef.current?.remove();
      subChartRef.current?.remove();
      chartRef.current = null;
      subChartRef.current = null;
    };
  }, [initCharts]);

  const hasSubIndicators = indicators.some((i) => i.panel === "sub");

  return (
    <div className="w-full flex flex-col gap-0">
      <div ref={containerRef} className="w-full" style={{ height }} />
      {hasSubIndicators && (
        <div ref={subContainerRef} className="w-full border-t border-dark-500" style={{ height: 160 }} />
      )}
    </div>
  );
}
