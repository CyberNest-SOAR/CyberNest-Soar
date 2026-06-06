import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { 
  Users, 
  UserPlus, 
  Shield, 
  Activity,
  Settings,
  Search,
  MoreVertical,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw
} from "lucide-react";
import { useState, useMemo } from "react";
import { useDashboardData } from "@/hooks/useDashboardData";

interface Analyst {
  id: number;
  name: string;
  username: string;
  role: string;
  status: string;
  email: string;
  incidents: number;
  avgResponseTime: string;
  lastActive: string;
}

const staticAnalysts: Analyst[] = [
  { 
    id: 1, 
    name: "John Doe", 
    username: "jdoe",
    role: "Senior Analyst", 
    status: "active", 
    email: "john.doe@secureops.com",
    incidents: 3785,
    avgResponseTime: "3.2m",
    lastActive: "2 mins ago"
  },
  { 
    id: 2, 
    name: "Sarah Garcia", 
    username: "sgarcia",
    role: "Security Analyst", 
    status: "active", 
    email: "sarah.garcia@secureops.com",
    incidents: 3901,
    avgResponseTime: "2.9m",
    lastActive: "Just now"
  },
  { 
    id: 3, 
    name: "Alex Smith", 
    username: "asmith",
    role: "Security Analyst", 
    status: "active", 
    email: "alex.smith@secureops.com",
    incidents: 3896,
    avgResponseTime: "4.1m",
    lastActive: "5 mins ago"
  },
  { 
    id: 4, 
    name: "Kevin Lee", 
    username: "klee",
    role: "Junior Analyst", 
    status: "away", 
    email: "kevin.lee@secureops.com",
    incidents: 3966,
    avgResponseTime: "5.8m",
    lastActive: "1 hour ago"
  },
  { 
    id: 5, 
    name: "Lisa Chen", 
    username: "lchen",
    role: "Senior Analyst", 
    status: "offline", 
    email: "lisa.chen@secureops.com",
    incidents: 3377,
    avgResponseTime: "3.5m",
    lastActive: "3 hours ago"
  },
];

export default function AdminDashboard() {
  const { data: auditData, loading, refetch } = useDashboardData<any>("reporting-audit.json", null);
  const [searchTerm, setSearchTerm] = useState("");

  const dynamicAnalysts = useMemo(() => {
    if (!auditData || !auditData.shift_handover || !auditData.shift_handover.analyst_activity) {
      return staticAnalysts;
    }
    const activities = auditData.shift_handover.analyst_activity;
    
    return staticAnalysts.map(analyst => {
      const key = analyst.username;
      const count = activities[key] !== undefined ? activities[key] : analyst.incidents;
      return {
        ...analyst,
        incidents: count
      };
    });
  }, [auditData]);

  const filteredAnalysts = dynamicAnalysts.filter(analyst => {
    return analyst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
           analyst.role.toLowerCase().includes(searchTerm.toLowerCase()) ||
           analyst.email.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "safe";
      case "away": return "threat-medium";
      case "offline": return "muted";
      default: return "muted";
    }
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('');
  };

  const totalIncidents = useMemo(() => {
    if (auditData?.executive_reports?.total_incidents) {
      return auditData.executive_reports.total_incidents;
    }
    return dynamicAnalysts.reduce((sum, a) => sum + a.incidents, 0);
  }, [auditData, dynamicAnalysts]);

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-grotesk font-bold text-foreground">Admin System Dashboard</h1>
          <p className="text-muted-foreground">Manage SOC analyst workloads, active shifts, and integration rules</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
            <RefreshCw className="h-3.5 w-3.5" /> Force Sync Handover
          </Button>
          <Button size="sm" className="w-fit bg-primary hover:bg-primary/95 text-white">
            <UserPlus className="h-4 w-4 mr-2" />
            Add Analyst
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="gradient-card border-border/50 bg-card/25 shadow-lg backdrop-blur-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Total Analysts</CardTitle>
            <Users className="h-4 w-4 text-cyber-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-mono font-bold text-foreground">{dynamicAnalysts.length}</div>
            <p className="text-[10px] text-muted-foreground font-semibold mt-1">Consolidated active roster</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50 bg-card/25 shadow-lg backdrop-blur-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Active Now</CardTitle>
            <Activity className="h-4 w-4 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-mono font-bold text-foreground">
              {dynamicAnalysts.filter(a => a.status === 'active').length}
            </div>
            <p className="text-[10px] text-muted-foreground font-semibold mt-1">Currently online in session</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50 bg-card/25 shadow-lg backdrop-blur-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Total Incidents</CardTitle>
            <Shield className="h-4 w-4 text-rose-400 animate-pulse" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-mono font-bold text-foreground">
              {totalIncidents?.toLocaleString()}
            </div>
            <p className="text-[10px] text-muted-foreground font-semibold mt-1">Handled this weekly shift</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50 bg-card/25 shadow-lg backdrop-blur-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Avg Response</CardTitle>
            <Clock className="h-4 w-4 text-cyber-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-mono font-bold text-foreground">3.2m</div>
            <p className="text-[10px] text-muted-foreground font-semibold mt-1">-18% SLA improvement</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="gradient-card border-border/50 bg-card/25 shadow-lg backdrop-blur-md">
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search analysts by name, role, or email..."
              className="pl-10 text-xs bg-background/50 border-border/40 focus:border-primary/50"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Analysts List */}
      <Card className="gradient-card border-border/50 bg-card/25 shadow-lg backdrop-blur-md">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk text-lg">Security Analysts Workload</CardTitle>
          <CardDescription className="text-muted-foreground">
            Manage active shift members, workloads, and authentication statuses
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredAnalysts.map((analyst) => (
              <div
                key={analyst.id}
                className="flex flex-col lg:flex-row lg:items-center justify-between p-4 rounded-lg bg-background/25 border border-border/30 hover:border-border transition-colors gap-4"
              >
                <div className="flex items-center gap-4">
                  <Avatar className="h-12 w-12 border-2 border-border/40">
                    <AvatarFallback className="bg-gradient-to-br from-primary to-accent text-white font-mono font-bold">
                      {getInitials(analyst.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-bold text-sm text-foreground">{analyst.name}</h3>
                      <Badge 
                        variant="outline"
                        style={{ 
                          backgroundColor: `hsl(var(--${getStatusColor(analyst.status)}) / 0.2)`, 
                          color: `hsl(var(--${getStatusColor(analyst.status)}))` 
                        }}
                        className="text-[9px] uppercase tracking-wider font-mono font-bold"
                      >
                        {analyst.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{analyst.role}</p>
                    <p className="text-[10px] text-muted-foreground/60 font-mono mt-0.5">{analyst.email}</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 lg:gap-6 shrink-0">
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                      <span className="text-xs font-bold font-mono text-foreground">{analyst.incidents?.toLocaleString()}</span>
                    </div>
                    <p className="text-[10px] uppercase font-bold text-muted-foreground/60 tracking-wider font-mono">Resolved</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <Clock className="h-3.5 w-3.5 text-cyber-blue" />
                      <span className="text-xs font-bold font-mono text-foreground">{analyst.avgResponseTime}</span>
                    </div>
                    <p className="text-[10px] uppercase font-bold text-muted-foreground/60 tracking-wider font-mono">Avg Time</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <Activity className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-xs font-bold font-mono text-foreground truncate">{analyst.lastActive}</span>
                    </div>
                    <p className="text-[10px] uppercase font-bold text-muted-foreground/60 tracking-wider font-mono">Active</p>
                  </div>
                </div>

                <Button variant="ghost" size="icon" className="shrink-0 hover:bg-muted/20">
                  <MoreVertical className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* System Configuration */}
      <Card className="gradient-card border-border/50 bg-card/25 shadow-lg backdrop-blur-md">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk flex items-center gap-2 text-lg">
            <Settings className="h-5 w-5 text-primary" />
            Active SOAR Trigger Policies
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            Administrative rule sets for auto-block, quarantines, and rate limit protections
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-background/25 border border-border/30">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">Auto-Block Threshold</h4>
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/35 text-[9px] font-mono">Active</Badge>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">Instantly block ingress IP addresses after 5 failed authentication attempts.</p>
            </div>
            <div className="p-4 rounded-lg bg-background/25 border border-border/30">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">Email Quarantine</h4>
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/35 text-[9px] font-mono">Active</Badge>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">Auto-quarantine rogue phishing vectors flagged by the Cognitive AI Engine.</p>
            </div>
            <div className="p-4 rounded-lg bg-background/25 border border-border/30">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">DDoS Rate Limiters</h4>
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/35 text-[9px] font-mono">Active</Badge>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">Global network rate-limiting throttle cap set at 1,000 requests per minute.</p>
            </div>
            <div className="p-4 rounded-lg bg-background/25 border border-border/30">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">Intel Center Update</h4>
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/35 text-[9px] font-mono">Active</Badge>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">Auto-update rogue IOC IP/domain feeds every 24 hours from MISP remote connectors.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
