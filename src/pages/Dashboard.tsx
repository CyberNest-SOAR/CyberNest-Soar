import { useState, useEffect } from "react";
import { Responsive, WidthProvider } from "react-grid-layout";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Shield, Mail, Network, Lock, AlertTriangle,
  TrendingUp, TrendingDown, GripVertical, Save, Filter
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

const Grid = WidthProvider(Responsive);

/* ---------------- MOCK DATA ---------------- */
const trendData = [
  { t: "00:00", phishing: 12, ddos: 3, brute: 8 },
  { t: "06:00", phishing: 18, ddos: 5, brute: 10 },
  { t: "12:00", phishing: 32, ddos: 11, brute: 20 },
  { t: "18:00", phishing: 22, ddos: 6, brute: 14 },
];

const distribution = [
  { name: "Phishing", value: 45, color: "hsl(var(--cyber-blue))" },
  { name: "Brute Force", value: 35, color: "hsl(var(--critical))" },
  { name: "DDoS", value: 20, color: "hsl(var(--warning))" },
];

/* ---------------- KPI CARD ---------------- */
const KPI = ({ title, value, trend, icon: Icon, color }) => (
  <Card className="h-full relative overflow-hidden border-border/50 hover:shadow-lg transition">
    <CardHeader className="pb-2">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-[11px] tracking-widest text-muted-foreground uppercase">{title}</p>
          <p className="text-[42px] font-bold mt-2 leading-none">{value}</p>
        </div>
        <div className={`p-3 rounded-xl bg-[${color}]/10`}>
          <Icon className={`h-5 w-5 text-[${color}]`} />
        </div>
      </div>
    </CardHeader>
    <CardContent className="pt-3">
      <div className="flex items-center gap-2">
        {trend > 0 ? (
          <TrendingUp className="h-4 w-4 text-critical" />
        ) : (
          <TrendingDown className="h-4 w-4 text-safe" />
        )}
        <span className="text-xs text-muted-foreground">
          {trend > 0 ? `↑ ${trend}% increase` : `↓ ${Math.abs(trend)}% decrease`}
        </span>
      </div>
    </CardContent>
  </Card>
);

/* ---------------- DASHBOARD ---------------- */
export default function Dashboard() {
  const [edit, setEdit] = useState(false);
  const [filters, setFilters] = useState({ phishing: true, ddos: true, brute: true });

  const layout = {
    lg: [
      { i: "k1", x: 0, y: 0, w: 3, h: 4 },
      { i: "k2", x: 3, y: 0, w: 3, h: 4 },
      { i: "k3", x: 6, y: 0, w: 3, h: 4 },
      { i: "k4", x: 9, y: 0, w: 3, h: 4 },
      { i: "trend", x: 0, y: 4, w: 8, h: 8 },
      { i: "pie", x: 8, y: 4, w: 4, h: 8 },
      { i: "alerts", x: 0, y: 12, w: 12, h: 5 },
    ],
  };

  return (
    <div className="p-6 space-y-6">

      {/* HEADER */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold">Threat Analysis Dashboard </h1>
          <p className="text-muted-foreground text-sm">SOC Threat Monitoring & Analytics</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm">Edit Mode</span>
          <Switch checked={edit} onCheckedChange={setEdit} />
          {edit && <Button size="sm"><Save className="h-4 w-4 mr-2" />Save</Button>}
        </div>
      </div>

      {/* EDIT MODE BANNER */}
      {edit && (
        <div className="bg-cyber-blue/10 border border-cyber-blue/40 rounded-lg p-4 flex gap-3">
          <GripVertical className="h-5 w-5 text-cyber-blue" />
          <p className="text-sm text-muted-foreground">
            Edit mode enabled — drag & resize widgets, then save layout.
          </p>
        </div>
      )}

      {/* GRID */}
      <Grid
        layouts={layout}
        breakpoints={{ lg: 1200 }}
        cols={{ lg: 12 }}
        rowHeight={34}
        isDraggable={edit}
        isResizable={edit}
        margin={[16, 16]}
      >

        {/* KPIs */}
        <div key="k1"><KPI title="Phishing Emails" value="247" trend={12} icon={Mail} color="--critical" /></div>
        <div key="k2"><KPI title="DDoS Attempts" value="43" trend={-8} icon={Network} color="--warning" /></div>
        <div key="k3"><KPI title="Brute Force" value="156" trend={23} icon={Lock} color="--critical" /></div>
        <div key="k4"><KPI title="Active Incidents" value="12" trend={-3} icon={AlertTriangle} color="--cyber-blue" /></div>

        {/* TREND CHART */}
        <div key="trend">
          <Card className="h-full">
            <CardHeader className="flex flex-row justify-between items-center">
              <div>
                <CardTitle>Threat Trends (24h)</CardTitle>
                <CardDescription>Incident volume by type</CardDescription>
              </div>
              <Dialog>
                <DialogTrigger asChild>
                  <Button size="sm" variant="outline">
                    <Filter className="h-4 w-4 mr-2" /> Filter
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Filters</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-2 py-2">
                    {Object.keys(filters).map(f => (
                      <div key={f} className="flex items-center gap-2">
                        <Checkbox
                          checked={filters[f]}
                          onCheckedChange={(v) =>
                            setFilters({ ...filters, [f]: v as boolean })
                          }
                        />
                        <span className="text-sm capitalize">{f}</span>
                      </div>
                    ))}
                  </div>
                </DialogContent>
              </Dialog>
            </CardHeader>

            <CardContent className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                  <XAxis dataKey="t" stroke="hsl(var(--muted-foreground))" />
                  <YAxis stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      color: 'hsl(var(--foreground))',
                    }}
                  />
                  {filters.phishing && <Line dataKey="phishing" stroke="hsl(var(--cyber-blue))" strokeWidth={2.5} dot={false} />}
                  {filters.ddos && <Line dataKey="ddos" stroke="hsl(var(--warning))" strokeWidth={2.5} dot={false} />}
                  {filters.brute && <Line dataKey="brute" stroke="hsl(var(--critical))" strokeWidth={2.5} dot={false} />}
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* PIE CHART - Blue, Black & White */}
        <div key="pie">
          <Card className="h-full">
            <CardHeader className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
              <div>
                <CardTitle>Threat Distribution</CardTitle>
                <CardDescription>Percentage breakdown by threat type</CardDescription>
              </div>
            </CardHeader>

            <CardContent className="h-[350px] flex flex-col sm:flex-row items-center justify-center gap-6">
              {/* Pie */}
              <ResponsiveContainer width="50%" height="100%">
                <PieChart>
                  <Pie
                    data={distribution}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius="80%"
                    innerRadius="40%" // donut
                    paddingAngle={4}
                    label={({ name, percent }) => (
                      <text
                        x={0}
                        y={0}
                        fill="hsl(var(--foreground))"
                        fontSize={12}
                        fontWeight={600}
                        textAnchor="middle"
                        dominantBaseline="central"
                      >
                        {`${name} ${(percent * 100).toFixed(0)}%`}
                      </text>
                    )}
                    labelLine={false}
                  >
                    {distribution.map((entry, index) => {
                      // Assign colors: Blue, Black, White
                      const colors = ["#3B82F6", "#000000", "#FFFFFF"];
                      return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                    })}
                  </Pie>
                  <Tooltip
                    formatter={(value: number, name: string) => [`${value}`, name]}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',      
                      border: '1px solid hsl(var(--border))',    
                      borderRadius: '8px',
                      color: 'hsl(var(--foreground))',           
                      padding: '8px 12px',
                      fontSize: '13px',
                    }}
                    itemStyle={{
                      color: 'hsl(var(--foreground))',           
                    }}
                    labelStyle={{
                      color: 'hsl(var(--muted-foreground))',     
                    }}
                  />

                </PieChart>
              </ResponsiveContainer>

              {/* Legend */}
              <div className="flex flex-col gap-2 w-1/2">
                {distribution.map((d, i) => {
                  const colors = ["#3B82F6", "#000000", "#FFFFFF"];
                  return (
                    <div
                      key={i}
                      className="flex items-center gap-2 px-2 py-1 rounded-md transition-colors"
                      style={{
                        backgroundColor: `hsl(var(--card) / 0.3)`,
                      }}
                    >
                      <span
                        className="w-4 h-4 rounded-full shrink-0 border border-muted-foreground"
                        style={{ backgroundColor: colors[i % colors.length] }}
                      ></span>
                      <span className="text-sm font-medium text-foreground">{d.name}</span>
                      <span className="text-xs text-muted-foreground">{d.value}%</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>



       
      
      </Grid>
    </div>
  );
}
