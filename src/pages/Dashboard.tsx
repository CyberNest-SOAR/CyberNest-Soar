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
import { CyberCard } from "@/components/CyberCard";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useTheme } from "@/components/ThemeProvider";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import { RefreshCw, Zap, CheckCircle } from "lucide-react";

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

/* ---------------- KPI CARD ─── */
const KPI = ({ title, value, trend, icon: Icon, color, delay }) => (
  <CyberCard delay={delay} className="h-full relative overflow-hidden group border-border/60">
    <div className="flex justify-between items-start mb-6">
      <div className="p-3 rounded-2xl bg-primary/5 border border-primary/10 transition-colors group-hover:bg-primary group-hover:text-white group-hover:border-primary">
        <Icon className="h-5 w-5" />
      </div>
      <div className={`flex items-center gap-1 text-[10px] font-black tracking-widest px-2.5 py-1 rounded-lg ${
        trend > 0 ? "text-rose-500 bg-rose-500/10" : "text-emerald-500 bg-emerald-500/10"
      }`}>
        {trend > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
        {Math.abs(trend)}%
      </div>
    </div>
    
    <div className="space-y-1">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">{title}</p>
      <h3 className="text-4xl font-black tracking-tighter text-foreground group-hover:text-primary transition-colors">
        {value}
      </h3>
    </div>

    {/* Subtle Progress Bar */}
    <div className="mt-8 h-1 w-full bg-muted/30 rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: "65%" }}
        transition={{ duration: 2, delay: delay + 0.3 }}
        className="h-full bg-primary"
      />
    </div>
  </CyberCard>
);

/* ---------------- DASHBOARD ---------------- */
export default function Dashboard() {
  const { theme } = useTheme();
  const [edit, setEdit] = useState(false);
  const [filters, setFilters] = useState({ phishing: true, ddos: true, brute: true });

  const layout = {
    lg: [
      { i: "trend", x: 0, y: 0, w: 8, h: 8 },
      { i: "pie", x: 8, y: 0, w: 4, h: 8 },
      { i: "alerts", x: 0, y: 8, w: 12, h: 5 },
    ],
    md: [
      { i: "trend", x: 0, y: 0, w: 10, h: 8 },
      { i: "pie", x: 0, y: 8, w: 10, h: 8 },
    ],
    sm: [
      { i: "trend", x: 0, y: 0, w: 6, h: 8 },
      { i: "pie", x: 0, y: 8, w: 6, h: 8 },
    ],
  };

  return (
    <div className="w-full h-full space-y-10 pb-20">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-5xl font-black tracking-tighter uppercase italic">
            Command <span className="text-primary text-glow-primary">Center</span>
          </h1>
          <p className="text-muted-foreground text-[10px] font-black uppercase tracking-[0.4em] mt-2 opacity-60">
            Real-time Phishing Detection Center & Response
          </p>
        </div>
        
        <div className="flex items-center gap-4 bg-card/50 p-2 rounded-2xl border border-border/40 backdrop-blur-xl">
          <div className="flex items-center gap-3 px-4 py-2 border-r border-border/40">
            <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60">Edit Layout</span>
            <Switch checked={edit} onCheckedChange={setEdit} />
          </div>
          <Button variant="ghost" size="icon" className="rounded-xl hover:bg-primary/10 hover:text-primary">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPI title="Active Incidents" value="42" trend={12} icon={AlertTriangle} color="rose" delay={0.1} />
        <KPI title="Threat Score" value="8.4" trend={-2} icon={Shield} color="indigo" delay={0.2} />
        <KPI title="Data Throttled" value="1.2TB" trend={5} icon={Zap} color="cyan" delay={0.3} />
        <KPI title="Uptime Status" value="99.9%" trend={0} icon={CheckCircle} color="emerald" delay={0.4} />
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
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={34}
        isDraggable={edit}
        isResizable={edit}
        margin={[16, 16]}
      >

        {/* KPIs */}
        <div key="k1"><KPI title="Phishing Emails" value="247" trend={12} icon={Mail} color="--critical" delay={0.1} /></div>
        <div key="k2"><KPI title="DDoS Attempts" value="43" trend={-8} icon={Network} color="--warning" delay={0.15} /></div>
        <div key="k3"><KPI title="Brute Force" value="156" trend={23} icon={Lock} color="--critical" delay={0.2} /></div>
        <div key="k4"><KPI title="Active Incidents" value="12" trend={-3} icon={AlertTriangle} color="--cyber-blue" delay={0.25} /></div>

        {/* TREND CHART */}
        <div key="trend">
          <CyberCard className="h-full" delay={0.4}>
            <CardHeader className="flex flex-row justify-between items-center border-b border-border/40 pb-4">
              <div>
                <CardTitle className="text-lg font-bold">Threat Trends (24h)</CardTitle>
                <CardDescription>Incident volume by type</CardDescription>
              </div>
              <Dialog>
                <DialogTrigger asChild>
                  <Button size="sm" variant="outline" className="rounded-lg border-border/40">
                    <Filter className="h-4 w-4 mr-2" /> Filter
                  </Button>
                </DialogTrigger>
                <DialogContent className="glass">
                  <DialogHeader>
                    <DialogTitle>Filters</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    {Object.keys(filters).map(f => (
                      <div key={f} className="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-background/40">
                        <span className="text-sm font-bold uppercase tracking-wider">{f}</span>
                        <Switch
                          checked={filters[f]}
                          onCheckedChange={(v) =>
                            setFilters({ ...filters, [f]: v })
                          }
                        />
                      </div>
                    ))}
                  </div>
                </DialogContent>
              </Dialog>
            </CardHeader>

            <CardContent className="h-[300px] pt-6">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                  <defs>
                    <linearGradient id="colorPhishing" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--cyber-blue))" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(var(--cyber-blue))" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.1} vertical={false} />
                  <XAxis 
                    dataKey="t" 
                    stroke="hsl(var(--muted-foreground))" 
                    fontSize={10} 
                    tickLine={false} 
                    axisLine={false} 
                  />
                  <YAxis 
                    stroke="hsl(var(--muted-foreground))" 
                    fontSize={10} 
                    tickLine={false} 
                    axisLine={false} 
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme === "dark" ? "rgba(0, 0, 0, 0.8)" : "rgba(255, 255, 255, 0.9)",
                      backdropFilter: "blur(8px)",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "12px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                  {filters.phishing && (
                    <Line 
                      type="monotone"
                      dataKey="phishing" 
                      stroke="hsl(var(--cyber-blue))" 
                      strokeWidth={3} 
                      dot={{ r: 4, fill: "hsl(var(--cyber-blue))", strokeWidth: 2, stroke: "#fff" }} 
                      activeDot={{ r: 6, strokeWidth: 0 }}
                    />
                  )}
                  {filters.ddos && <Line type="monotone" dataKey="ddos" stroke="hsl(var(--warning))" strokeWidth={3} dot={false} />}
                  {filters.brute && <Line type="monotone" dataKey="brute" stroke="hsl(var(--critical))" strokeWidth={3} dot={false} />}
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </CyberCard>
        </div>

        {/* PIE CHART */}
        <div key="pie">
          <CyberCard className="h-full" delay={0.5}>
            <CardHeader className="border-b border-border/40 pb-4">
              <CardTitle className="text-lg font-bold">Threat Distribution</CardTitle>
              <CardDescription>Percentage breakdown by threat type</CardDescription>
            </CardHeader>

            <CardContent className="h-[350px] pt-6 flex flex-col items-center justify-center gap-6">
              <ResponsiveContainer width="100%" height="60%">
                <PieChart>
                  <Pie
                    data={distribution}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={8}
                  >
                    {distribution.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.color} 
                        stroke="none"
                        className="hover:opacity-80 transition-opacity cursor-pointer"
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme === "dark" ? "rgba(0, 0, 0, 0.8)" : "rgba(255, 255, 255, 0.9)",
                      backdropFilter: "blur(8px)",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "12px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>

              <div className="grid grid-cols-1 gap-3 w-full px-4">
                {distribution.map((d, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded-xl bg-background/40 border border-border/40"
                  >
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-3 h-3 rounded-full shadow-[0_0_8px_rgba(0,0,0,0.2)]" 
                        style={{ backgroundColor: d.color, boxShadow: `0 0 12px ${d.color}44` }} 
                      />
                      <span className="text-xs font-bold uppercase tracking-wider">{d.name}</span>
                    </div>
                    <span className="text-xs font-mono font-bold text-primary">{d.value}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </CyberCard>
        </div>

        {/* ALERTS FEED */}
        <div key="alerts">
          <CyberCard className="h-full" delay={0.6}>
            <CardHeader className="border-b border-border/40 flex flex-row items-center justify-between pb-4">
              <div>
                <CardTitle className="text-lg font-bold">Real-time Threat Feed</CardTitle>
                <CardDescription>Live telemetry from global nodes</CardDescription>
              </div>
              <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 animate-pulse">
                LIVE_STREAM
              </Badge>
            </CardHeader>
            <CardContent className="pt-4 px-0">
              <div className="space-y-1">
                {[
                  { time: "14:23:01", msg: "Unusual login pattern detected from UA_NODE_12", severity: "High", type: "AUTH" },
                  { time: "14:22:45", msg: "Inbound traffic spike on Port 80 (Node_04)", severity: "Medium", type: "NET" },
                  { time: "14:22:12", msg: "Malicious payload quarantined on Workstation_88", severity: "Critical", type: "EP" },
                  { time: "14:21:55", msg: "API Key rotation required for Service_Auth", severity: "Low", type: "SYS" },
                ].map((alert, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7 + i * 0.1 }}
                    className="flex items-center gap-4 px-6 py-3 hover:bg-muted/30 transition-colors border-b border-border/10 last:border-0"
                  >
                    <span className="text-[10px] font-mono text-muted-foreground">{alert.time}</span>
                    <div className={cn(
                      "h-1.5 w-1.5 rounded-full shrink-0",
                      alert.severity === "Critical" ? "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]" :
                      alert.severity === "High" ? "bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]" :
                      alert.severity === "Medium" ? "bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.5)]" :
                      "bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"
                    )} />
                    <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground/60 w-12">{alert.type}</span>
                    <span className="text-sm font-medium flex-1 truncate">{alert.msg}</span>
                    <Button variant="ghost" size="sm" className="text-[10px] uppercase font-bold text-primary hover:bg-primary/10">Investigate</Button>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </CyberCard>
        </div>



       
      
      </Grid>
    </div>
  );
}
