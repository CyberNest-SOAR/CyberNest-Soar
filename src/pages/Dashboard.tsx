import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  Shield, 
  Mail, 
  Network, 
  Lock, 
  AlertTriangle, 
  TrendingUp,
  TrendingDown,
  Edit,
  Save,
  ExternalLink,
  BookOpen,
  FileText,
  Youtube,
  GripVertical,
  Plus,
  Trash2,
  Filter
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { useState, useEffect } from "react";
import { Responsive, WidthProvider, Layout } from "react-grid-layout";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

const ResponsiveGridLayout = WidthProvider(Responsive);

// Mock data for charts
const threatTrendData = [
  { time: "00:00", phishing: 12, ddos: 3, bruteforce: 8 },
  { time: "04:00", phishing: 19, ddos: 1, bruteforce: 12 },
  { time: "08:00", phishing: 25, ddos: 7, bruteforce: 15 },
  { time: "12:00", phishing: 35, ddos: 12, bruteforce: 22 },
  { time: "16:00", phishing: 28, ddos: 8, bruteforce: 18 },
  { time: "20:00", phishing: 22, ddos: 4, bruteforce: 14 },
];

const threatDistributionData = [
  { name: "Phishing", value: 45, color: "#3B82F6" },
  { name: "Brute Force", value: 35, color: "#EF4444" },
  { name: "DDoS", value: 20, color: "#10B981" },
];

const iconMap: { [key: string]: any } = {
  Shield,
  Mail,
  Network,
  Lock,
  FileText,
  Youtube,
  BookOpen,
};

const Dashboard = () => {
  const { isAdmin, isAnalyst, user } = useAuth();
  const canEdit = isAdmin || isAnalyst;
  const [isEditMode, setIsEditMode] = useState(false);
  const [resources, setResources] = useState<any[]>([]);
  const [isAddResourceOpen, setIsAddResourceOpen] = useState(false);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [chartFilters, setChartFilters] = useState({
    phishing: true,
    ddos: true,
    bruteforce: true,
  });
  const [newResource, setNewResource] = useState({
    title: "",
    description: "",
    url: "",
    category: "Guide",
    icon: "FileText"
  });
  
  const defaultLayout = {
    lg: [
      { i: "kpi1", x: 0, y: 0, w: 3, h: 3, minW: 2, minH: 3 },
      { i: "kpi2", x: 3, y: 0, w: 3, h: 3, minW: 2, minH: 3 },
      { i: "kpi3", x: 6, y: 0, w: 3, h: 3, minW: 2, minH: 3 },
      { i: "kpi4", x: 9, y: 0, w: 3, h: 3, minW: 2, minH: 3 },
      { i: "chart1", x: 0, y: 3, w: 6, h: 6, minW: 4, minH: 5 },
      { i: "chart2", x: 6, y: 3, w: 6, h: 6, minW: 4, minH: 5 },
      { i: "alerts", x: 0, y: 9, w: 12, h: 4, minW: 6, minH: 3 },
      { i: "links", x: 0, y: 13, w: 12, h: 4, minW: 6, minH: 3 },
    ]
  };
  
  const [layouts, setLayouts] = useState<{ lg: Layout[] }>(defaultLayout);
  const [visibleSections, setVisibleSections] = useState<string[]>(
    defaultLayout.lg.map(item => item.i)
  );
  const [isAddSectionOpen, setIsAddSectionOpen] = useState(false);

  // Load saved layout from localStorage
  useEffect(() => {
    const savedLayout = localStorage.getItem("dashboardLayout");
    const savedSections = localStorage.getItem("dashboardSections");
    if (savedLayout) {
      try {
        setLayouts(JSON.parse(savedLayout));
      } catch (e) {
        console.error("Failed to parse saved layout");
      }
    }
    if (savedSections) {
      try {
        setVisibleSections(JSON.parse(savedSections));
      } catch (e) {
        console.error("Failed to parse saved sections");
      }
    }
  }, []);

  useEffect(() => {
    fetchResources();
  }, []);

  const fetchResources = async () => {
    const { data, error } = await supabase
      .from("attack_resources")
      .select("*")
      .order("created_at", { ascending: false });
    
    if (error) {
      console.error("Error fetching resources:", error);
      toast.error("Failed to load resources");
    } else {
      setResources(data || []);
    }
  };

  const handleAddResource = async () => {
    if (!newResource.title || !newResource.url || !newResource.description) {
      toast.error("Please fill in all fields");
      return;
    }

    const { error } = await supabase
      .from("attack_resources")
      .insert([newResource]);
    
    if (error) {
      console.error("Error adding resource:", error);
      toast.error("Failed to add resource");
    } else {
      toast.success("Resource added successfully");
      setIsAddResourceOpen(false);
      setNewResource({
        title: "",
        description: "",
        url: "",
        category: "Guide",
        icon: "FileText"
      });
      fetchResources();
    }
  };

  const handleDeleteResource = async (id: string) => {
    const { error } = await supabase
      .from("attack_resources")
      .delete()
      .eq("id", id);
    
    if (error) {
      console.error("Error deleting resource:", error);
      toast.error("Failed to delete resource");
    } else {
      toast.success("Resource deleted");
      fetchResources();
    }
  };

  const onLayoutChange = (layout: Layout[], layouts: any) => {
    if (isEditMode) {
      setLayouts(layouts);
    }
  };

  const handleSaveLayout = () => {
    localStorage.setItem("dashboardLayout", JSON.stringify(layouts));
    localStorage.setItem("dashboardSections", JSON.stringify(visibleSections));
    toast.success("Layout saved successfully");
    setIsEditMode(false);
  };

  const handleAddSection = (sectionId: string) => {
    const newSection = defaultLayout.lg.find(item => item.i === sectionId);
    if (newSection) {
      const maxY = layouts.lg.length > 0 ? Math.max(...layouts.lg.map(l => l.y + l.h)) : 0;
      setLayouts({
        lg: [...layouts.lg, { ...newSection, y: maxY }]
      });
      setVisibleSections([...visibleSections, sectionId]);
    }
    setIsAddSectionOpen(false);
  };

  const handleRemoveSection = (sectionId: string) => {
    setLayouts({
      lg: layouts.lg.filter(item => item.i !== sectionId)
    });
    setVisibleSections(visibleSections.filter(id => id !== sectionId));
    toast.success("Section removed");
  };

  // Filter chart data based on selected filters
  const filteredThreatTrendData = threatTrendData.map((item) => {
    const filtered: any = { time: item.time };
    if (chartFilters.phishing) filtered.phishing = item.phishing;
    if (chartFilters.ddos) filtered.ddos = item.ddos;
    if (chartFilters.bruteforce) filtered.bruteforce = item.bruteforce;
    return filtered;
  });

  const filteredThreatDistributionData = threatDistributionData.filter(
    (item) =>
      (item.name === "Phishing" && chartFilters.phishing) ||
      (item.name === "DDoS" && chartFilters.ddos) ||
      (item.name === "Brute Force" && chartFilters.bruteforce)
  );

  const widgets: { [key: string]: JSX.Element } = {
    kpi1: (
      <Card className="relative overflow-hidden border-cyber-blue/30 bg-gradient-to-br from-card to-card/50 hover:border-cyber-blue/60 transition-all duration-300 hover:shadow-[0_0_25px_rgba(59,130,246,0.15)] group h-full">
        <div className="absolute inset-0 bg-gradient-to-br from-cyber-blue/5 to-transparent opacity-50" />
        <CardHeader className="relative pb-2">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                Phishing Emails
              </CardTitle>
              <div className="text-4xl font-grotesk font-bold text-foreground mt-2 group-hover:text-cyber-blue transition-colors">
                247
              </div>
            </div>
            <div className="p-3 rounded-xl bg-cyber-blue/10 group-hover:bg-cyber-blue/20 transition-all duration-300 border border-cyber-blue/20 group-hover:border-cyber-blue/40 group-hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]">
              <Mail className="h-5 w-5 text-cyber-blue" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="relative pt-0 pb-4">
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-threat-high/10 border border-threat-high/20">
              <TrendingUp className="h-3.5 w-3.5 text-threat-high" />
              <span className="text-sm font-semibold text-threat-high">+12%</span>
            </div>
            <span className="text-xs text-muted-foreground">vs yesterday</span>
          </div>
        </CardContent>
      </Card>
    ),
    kpi2: (
      <Card className="relative overflow-hidden border-threat-medium/30 bg-gradient-to-br from-card to-card/50 hover:border-threat-medium/60 transition-all duration-300 hover:shadow-[0_0_25px_rgba(251,146,60,0.15)] group h-full">
        <div className="absolute inset-0 bg-gradient-to-br from-threat-medium/5 to-transparent opacity-50" />
        <CardHeader className="relative pb-2">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                DDoS Attempts
              </CardTitle>
              <div className="text-4xl font-grotesk font-bold text-foreground mt-2 group-hover:text-threat-medium transition-colors">
                43
              </div>
            </div>
            <div className="p-3 rounded-xl bg-threat-medium/10 group-hover:bg-threat-medium/20 transition-all duration-300 border border-threat-medium/20 group-hover:border-threat-medium/40 group-hover:shadow-[0_0_15px_rgba(251,146,60,0.3)]">
              <Network className="h-5 w-5 text-threat-medium" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="relative pt-0 pb-4">
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-safe/10 border border-safe/20">
              <TrendingDown className="h-3.5 w-3.5 text-safe" />
              <span className="text-sm font-semibold text-safe">-8%</span>
            </div>
            <span className="text-xs text-muted-foreground">vs yesterday</span>
          </div>
        </CardContent>
      </Card>
    ),
    kpi3: (
      <Card className="relative overflow-hidden border-threat-high/30 bg-gradient-to-br from-card to-card/50 hover:border-threat-high/60 transition-all duration-300 hover:shadow-[0_0_25px_rgba(239,68,68,0.15)] group h-full">
        <div className="absolute inset-0 bg-gradient-to-br from-threat-high/5 to-transparent opacity-50" />
        <CardHeader className="relative pb-2">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                Brute Force Attacks
              </CardTitle>
              <div className="text-4xl font-grotesk font-bold text-foreground mt-2 group-hover:text-threat-high transition-colors">
                156
              </div>
            </div>
            <div className="p-3 rounded-xl bg-threat-high/10 group-hover:bg-threat-high/20 transition-all duration-300 border border-threat-high/20 group-hover:border-threat-high/40 group-hover:shadow-[0_0_15px_rgba(239,68,68,0.3)]">
              <Lock className="h-5 w-5 text-threat-high" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="relative pt-0 pb-4">
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-threat-high/10 border border-threat-high/20">
              <TrendingUp className="h-3.5 w-3.5 text-threat-high" />
              <span className="text-sm font-semibold text-threat-high">+23%</span>
            </div>
            <span className="text-xs text-muted-foreground">vs yesterday</span>
          </div>
        </CardContent>
      </Card>
    ),
    kpi4: (
      <Card className="relative overflow-hidden border-primary/30 bg-gradient-to-br from-card to-card/50 hover:border-primary/60 transition-all duration-300 hover:shadow-[0_0_25px_rgba(59,130,246,0.15)] group h-full">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50" />
        <CardHeader className="relative pb-2">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                Active Incidents
              </CardTitle>
              <div className="text-4xl font-grotesk font-bold text-foreground mt-2 group-hover:text-primary transition-colors">
                12
              </div>
            </div>
            <div className="p-3 rounded-xl bg-primary/10 group-hover:bg-primary/20 transition-all duration-300 border border-primary/20 group-hover:border-primary/40 group-hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]">
              <AlertTriangle className="h-5 w-5 text-primary" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="relative pt-0 pb-4">
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-safe/10 border border-safe/20">
              <TrendingDown className="h-3.5 w-3.5 text-safe" />
              <span className="text-sm font-semibold text-safe">-3</span>
            </div>
            <span className="text-xs text-muted-foreground">vs yesterday</span>
          </div>
        </CardContent>
      </Card>
    ),
    chart1: (
      <Card className="gradient-card border-border/50 h-full flex flex-col overflow-hidden">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg font-grotesk text-foreground">Threat Trends (24h)</CardTitle>
              <CardDescription className="text-sm text-muted-foreground">
                Real-time security incidents over the last 24 hours
              </CardDescription>
            </div>
            <Dialog open={isFilterOpen} onOpenChange={setIsFilterOpen}>
              <DialogTrigger asChild>
                <Button size="sm" variant="outline">
                  <Filter className="h-4 w-4 mr-2" />
                  Filter
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Chart Filters</DialogTitle>
                  <DialogDescription>
                    Select which threat types to display in the charts
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="phishing"
                      checked={chartFilters.phishing}
                      onCheckedChange={(checked) =>
                        setChartFilters({ ...chartFilters, phishing: checked as boolean })
                      }
                    />
                    <label htmlFor="phishing" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                      Phishing Emails
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="ddos"
                      checked={chartFilters.ddos}
                      onCheckedChange={(checked) =>
                        setChartFilters({ ...chartFilters, ddos: checked as boolean })
                      }
                    />
                    <label htmlFor="ddos" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                      DDoS Attacks
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="bruteforce"
                      checked={chartFilters.bruteforce}
                      onCheckedChange={(checked) =>
                        setChartFilters({ ...chartFilters, bruteforce: checked as boolean })
                      }
                    />
                    <label htmlFor="bruteforce" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                      Brute Force Attacks
                    </label>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent className="flex-1 pb-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={filteredThreatTrendData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis 
                dataKey="time" 
                stroke="hsl(var(--muted-foreground))" 
                fontSize={12}
                tickLine={false}
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))" 
                fontSize={12}
                tickLine={false}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))', 
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  color: 'hsl(var(--foreground))'
                }} 
              />
              {chartFilters.phishing && (
                <Line type="monotone" dataKey="phishing" stroke="hsl(var(--cyber-blue))" strokeWidth={2.5} dot={false} />
              )}
              {chartFilters.ddos && (
                <Line type="monotone" dataKey="ddos" stroke="hsl(var(--safe))" strokeWidth={2.5} dot={false} />
              )}
              {chartFilters.bruteforce && (
                <Line type="monotone" dataKey="bruteforce" stroke="hsl(var(--threat-high))" strokeWidth={2.5} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    ),
    chart2: (
      <Card className="gradient-card border-border/50 h-full flex flex-col overflow-hidden">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-grotesk text-foreground">Threat Distribution</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">
            Breakdown of detected threats by category
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 pb-4 flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={filteredThreatDistributionData}
                cx="50%"
                cy="50%"
                outerRadius="70%"
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={{ stroke: 'hsl(var(--muted-foreground))', strokeWidth: 1 }}
              >
                {filteredThreatDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))', 
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  color: 'hsl(var(--foreground))'
                }} 
              />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    ),
    alerts: (
      <Card className="gradient-card border-border/50 h-full flex flex-col overflow-hidden">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-grotesk text-foreground">Active Alerts</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">
            Recent security incidents requiring attention
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-lg bg-destructive/10 border border-destructive/30 gap-3 transition-colors hover:bg-destructive/15">
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <div className="p-2 rounded-lg bg-destructive/20 shrink-0">
                <AlertTriangle className="h-4 w-4 text-destructive" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground mb-1 text-sm">High-Risk Phishing Campaign Detected</p>
                <p className="text-xs text-muted-foreground">Targeting finance department - 15 emails quarantined</p>
              </div>
            </div>
            <Badge variant="destructive" className="shrink-0 text-xs">Critical</Badge>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-lg bg-threat-medium/10 border border-threat-medium/30 gap-3 transition-colors hover:bg-threat-medium/15">
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <div className="p-2 rounded-lg bg-threat-medium/20 shrink-0">
                <Network className="h-4 w-4 text-threat-medium" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground mb-1 text-sm">Suspicious Traffic Spike</p>
                <p className="text-xs text-muted-foreground">DDoS attempt blocked from 192.168.1.100</p>
              </div>
            </div>
            <Badge style={{ backgroundColor: 'hsl(var(--threat-medium) / 0.2)', color: 'hsl(var(--threat-medium))' }} className="shrink-0 text-xs border-threat-medium/30">
              Medium
            </Badge>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-lg bg-safe/10 border border-safe/30 gap-3 transition-colors hover:bg-safe/15">
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <div className="p-2 rounded-lg bg-safe/20 shrink-0">
                <Shield className="h-4 w-4 text-safe" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground mb-1 text-sm">Security Update Applied</p>
                <p className="text-xs text-muted-foreground">Database updated with 1,247 new signatures</p>
              </div>
            </div>
            <Badge style={{ backgroundColor: 'hsl(var(--safe) / 0.2)', color: 'hsl(var(--safe))' }} className="shrink-0 text-xs border-safe/30">
              Info
            </Badge>
          </div>
        </CardContent>
      </Card>
    ),
    links: (
      <Card className="gradient-card border-border/50 h-full flex flex-col overflow-hidden">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-cyber-blue" />
              <CardTitle className="text-lg font-grotesk text-foreground">
                Attack Documentation & Resources
              </CardTitle>
            </div>
            {isAdmin && (
              <Dialog open={isAddResourceOpen} onOpenChange={setIsAddResourceOpen}>
                <DialogTrigger asChild>
                  <Button size="sm" variant="outline">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Resource
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Resource</DialogTitle>
                    <DialogDescription>
                      Add a new security resource for SOC analysts
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="title">Title</Label>
                      <Input
                        id="title"
                        value={newResource.title}
                        onChange={(e) => setNewResource({ ...newResource, title: e.target.value })}
                        placeholder="Resource title"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="description">Description</Label>
                      <Input
                        id="description"
                        value={newResource.description}
                        onChange={(e) => setNewResource({ ...newResource, description: e.target.value })}
                        placeholder="Brief description"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="url">URL</Label>
                      <Input
                        id="url"
                        value={newResource.url}
                        onChange={(e) => setNewResource({ ...newResource, url: e.target.value })}
                        placeholder="https://..."
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="category">Category</Label>
                      <Select value={newResource.category} onValueChange={(value) => setNewResource({ ...newResource, category: value })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Guide">Guide</SelectItem>
                          <SelectItem value="Framework">Framework</SelectItem>
                          <SelectItem value="Documentation">Documentation</SelectItem>
                          <SelectItem value="Tutorial">Tutorial</SelectItem>
                          <SelectItem value="Video">Video</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="icon">Icon</Label>
                      <Select value={newResource.icon} onValueChange={(value) => setNewResource({ ...newResource, icon: value })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Shield">Shield</SelectItem>
                          <SelectItem value="Mail">Mail</SelectItem>
                          <SelectItem value="Network">Network</SelectItem>
                          <SelectItem value="Lock">Lock</SelectItem>
                          <SelectItem value="FileText">FileText</SelectItem>
                          <SelectItem value="Youtube">Youtube</SelectItem>
                          <SelectItem value="BookOpen">BookOpen</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddResourceOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddResource}>
                      Add Resource
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}
          </div>
          <CardDescription className="text-sm text-muted-foreground">
            Quick access to security guides, frameworks, and training materials
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {resources.map((resource) => {
              const IconComponent = iconMap[resource.icon] || FileText;
              return (
                <div
                  key={resource.id}
                  className="group relative p-4 rounded-lg bg-card/50 border border-border/50 hover:border-cyber-blue/50 hover:bg-card transition-all duration-200 hover:shadow-lg hover:shadow-cyber-blue/10"
                >
                  {isAdmin && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="absolute top-2 right-2 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => handleDeleteResource(resource.id)}
                    >
                      <Trash2 className="h-3 w-3 text-destructive" />
                    </Button>
                  )}
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start gap-3"
                  >
                    <div className="p-2.5 rounded-lg bg-cyber-blue/10 group-hover:bg-cyber-blue/20 transition-colors shrink-0">
                      <IconComponent className="h-4 w-4 text-cyber-blue" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h4 className="font-medium text-foreground text-sm leading-tight group-hover:text-cyber-blue transition-colors">
                          {resource.title}
                        </h4>
                        <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-cyber-blue shrink-0 transition-colors mt-0.5" />
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-3 leading-relaxed">
                        {resource.description}
                      </p>
                      <Badge variant="outline" className="text-xs border-border/50">
                        {resource.category}
                      </Badge>
                    </div>
                  </a>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    ),
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-grotesk font-bold text-foreground mb-2">Security Dashboard</h1>
          <p className="text-sm text-muted-foreground">Real-time threat monitoring and analytics</p>
        </div>
        {canEdit && (
          <div className="flex items-center gap-3">
            {isEditMode && (
              <>
                <Dialog open={isAddSectionOpen} onOpenChange={setIsAddSectionOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" variant="outline">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Section
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Section</DialogTitle>
                      <DialogDescription>
                        Select a section to add to your dashboard
                      </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-3 py-4">
                      {Object.keys(widgets)
                        .filter(key => !visibleSections.includes(key))
                        .map(key => (
                          <Button
                            key={key}
                            variant="outline"
                            className="justify-start"
                            onClick={() => handleAddSection(key)}
                          >
                            <Plus className="h-4 w-4 mr-2" />
                            {key === "kpi1" && "Phishing Emails KPI"}
                            {key === "kpi2" && "DDoS Attempts KPI"}
                            {key === "kpi3" && "Brute Force Attacks KPI"}
                            {key === "kpi4" && "Active Incidents KPI"}
                            {key === "chart1" && "Threat Trends Chart"}
                            {key === "chart2" && "Threat Distribution Chart"}
                            {key === "alerts" && "Active Alerts"}
                            {key === "links" && "Attack Documentation & Resources"}
                          </Button>
                        ))}
                      {Object.keys(widgets).filter(key => !visibleSections.includes(key)).length === 0 && (
                        <p className="text-sm text-muted-foreground text-center py-4">
                          All sections are currently visible
                        </p>
                      )}
                    </div>
                  </DialogContent>
                </Dialog>
                <Button size="sm" onClick={handleSaveLayout}>
                  <Save className="h-4 w-4 mr-2" />
                  Save Layout
                </Button>
              </>
            )}
            <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Edit Mode</span>
              <Switch
                checked={isEditMode}
                onCheckedChange={setIsEditMode}
              />
            </div>
          </div>
        )}
      </div>

      {isEditMode && (
        <Card className="gradient-card border-cyber-blue/50 bg-cyber-blue/5">
          <CardContent className="pt-6 pb-6">
            <div className="flex items-start gap-4">
              <div className="p-2 rounded-lg bg-cyber-blue/10 shrink-0">
                <GripVertical className="h-5 w-5 text-cyber-blue" />
              </div>
              <div className="flex-1">
                <h4 className="font-grotesk font-semibold text-foreground mb-2">Edit Mode Active</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  • Drag sections to reorder them • Resize by dragging the bottom-right corner • Click the trash icon to remove sections • Click "Add Section" to add new sections • Click "Save Layout" when done
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Grid Layout */}
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={30}
        onLayoutChange={onLayoutChange}
        isDraggable={isEditMode}
        isResizable={isEditMode}
        draggableHandle={isEditMode ? ".drag-handle" : ""}
        containerPadding={[0, 0]}
        margin={[16, 16]}
      >
        {visibleSections.map((key) => (
          <div key={key} className="relative">
            {isEditMode && (
              <>
                <div className="drag-handle absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-background/90 border border-border cursor-move hover:bg-cyber-blue/10 hover:border-cyber-blue/50 transition-colors">
                  <GripVertical className="h-4 w-4 text-muted-foreground" />
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="absolute top-3 left-3 z-10 h-7 w-7 p-0 bg-background/90 border border-border hover:bg-destructive/10 hover:border-destructive/50"
                  onClick={() => handleRemoveSection(key)}
                >
                  <Trash2 className="h-3 w-3 text-destructive" />
                </Button>
              </>
            )}
            {widgets[key]}
          </div>
        ))}
      </ResponsiveGridLayout>
    </div>
  );
};

export default Dashboard;
