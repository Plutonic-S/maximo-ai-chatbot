import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

type ChartType = "bar" | "line" | "pie" | "area";

interface ChartDataPoint {
  label: string;
  value: number;
}

interface ChartSpec {
  chart_type: ChartType;
  title: string;
  category_label: string;
  value_label: string;
  data: ChartDataPoint[];
}

const CHART_TYPES: ChartType[] = ["bar", "line", "pie", "area"];

const PALETTE = [
  "var(--accent)",
  "var(--status-ok)",
  "var(--status-warn)",
  "var(--status-critical)",
  "var(--accent-strong)",
  "var(--text-muted)",
];

const TOOLTIP_STYLE = {
  contentStyle: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 12,
    fontFamily: "var(--font-mono)",
  },
  labelStyle: { color: "var(--text-muted)" },
  itemStyle: { color: "var(--text)" },
};

function isChartSpec(spec: unknown): spec is ChartSpec {
  if (!spec || typeof spec !== "object") return false;
  const s = spec as Record<string, unknown>;
  return (
    typeof s.chart_type === "string" &&
    CHART_TYPES.includes(s.chart_type as ChartType) &&
    typeof s.title === "string" &&
    Array.isArray(s.data)
  );
}

export function ChartRenderer({ spec }: { spec: unknown }) {
  if (!isChartSpec(spec)) {
    return <div className="chart-error">Unrecognized chart data.</div>;
  }

  const { chart_type, title, category_label, value_label, data } = spec;

  return (
    <div className="chart-container">
      <div className="chart-title">{title}</div>
      <ResponsiveContainer width="100%" height={260}>
        {chart_type === "bar" ? (
          <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
            <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} allowDecimals={false} />
            <Tooltip {...TOOLTIP_STYLE} />
            <Bar dataKey="value" name={value_label} fill="var(--accent)" radius={[4, 4, 0, 0]} />
          </BarChart>
        ) : chart_type === "line" ? (
          <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
            <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} allowDecimals={false} />
            <Tooltip {...TOOLTIP_STYLE} />
            <Line
              type="monotone"
              dataKey="value"
              name={value_label}
              stroke="var(--accent)"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          </LineChart>
        ) : chart_type === "area" ? (
          <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
            <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} allowDecimals={false} />
            <Tooltip {...TOOLTIP_STYLE} />
            <Area
              type="monotone"
              dataKey="value"
              name={value_label}
              stroke="var(--accent)"
              fill="var(--accent-wash)"
              strokeWidth={2}
            />
          </AreaChart>
        ) : (
          <PieChart>
            <Tooltip {...TOOLTIP_STYLE} />
            <Legend
              wrapperStyle={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}
            />
            <Pie data={data} dataKey="value" nameKey="label" outerRadius={90} label>
              {data.map((point, i) => (
                <Cell key={point.label} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Pie>
          </PieChart>
        )}
      </ResponsiveContainer>
      <div className="chart-axis-caption">{category_label}</div>
    </div>
  );
}
