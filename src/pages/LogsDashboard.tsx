import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Terminal, 
  Activity, 
  User, 
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Filter,
  Download
} from "lucide-react";
import { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";

// Mock log data
const systemLogs = [
  { id: 1, timestamp: "2025-01-15 14:23:45", level: "info", source: "System", message: "Security scan completed successfully", icon: CheckCircle },
  { id: 2, timestamp: "2025-01-15 14:20:12", level: "warning", source: "Network", message: "Unusual traffic pattern detected from IP 192.168.1.105", icon: AlertCircle },
  { id: 3, timestamp: "2025-01-15 14:15:33", level: "error", source: "Authentication", message: "Failed login attempt for user: admin", icon: XCircle },
  { id: 4, timestamp: "2025-01-15 14:10:08", level: "info", source: "Database", message: "Backup completed successfully", icon: CheckCircle },
  { id: 5, timestamp: "2025-01-15 14:05:21", level: "critical", source: "Firewall", message: "DDoS attack blocked - 10,000 requests/sec", icon: XCircle },
];

const incidentLogs = [
  { id: 1, timestamp: "2025-01-15 14:25:00", type: "Phishing", status: "Resolved", analyst: "John Doe", action: "Email quarantined and sender blocked" },
  { id: 2, timestamp: "2025-01-15 14:18:30", type: "Brute Force", status: "In Progress", analyst: "Jane Smith", action: "IP blocked, investigating source" },
  { id: 3, timestamp: "2025-01-15 14:12:45", type: "DDoS", status: "Mitigated", analyst: "Mike Johnson", action: "Traffic filtered, rate limiting applied" },
  { id: 4, timestamp: "2025-01-15 14:08:15", type: "Phishing", status: "Resolved", analyst: "Sarah Williams", action: "User notified, credentials reset" },
];

const analystActions = [
  { id: 1, timestamp: "2025-01-15 14:26:12", analyst: "John Doe", action: "Blocked sender: malicious@phishing.com", target: "Email Filter" },
  { id: 2, timestamp: "2025-01-15 14:22:55", analyst: "Jane Smith", action: "Added IP to blacklist: 45.67.89.123", target: "Firewall Rules" },
  { id: 3, timestamp: "2025-01-15 14:19:30", analyst: "Mike Johnson", action: "Enabled rate limiting on /api/login", target: "Web Application" },
  { id: 4, timestamp: "2025-01-15 14:15:08", analyst: "Sarah Williams", action: "Reset password for compromised account", target: "User Management" },
];

const LogsDashboard = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [threatFilters, setThreatFilters] = useState({
    phishing: true,
    ddos: true,
    bruteforce: true,
  });

  // Filter system logs by threat type
  const filteredSystemLogs = systemLogs.filter(log => {
    const searchMatch = searchTerm === "" || 
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.source.toLowerCase().includes(searchTerm.toLowerCase());
    
    return searchMatch;
  });

  // Filter incident logs by threat type
  const filteredIncidentLogs = incidentLogs.filter(incident => {
    const searchMatch = searchTerm === "" || 
      incident.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      incident.type.toLowerCase().includes(searchTerm.toLowerCase());
    
    const typeMatch = 
      (incident.type === "Phishing" && threatFilters.phishing) ||
      (incident.type === "DDoS" && threatFilters.ddos) ||
      (incident.type === "Brute Force" && threatFilters.bruteforce);
    
    return searchMatch && typeMatch;
  });

  const getLevelColor = (level: string) => {
    switch (level) {
      case "critical": return "destructive";
      case "error": return "destructive";
      case "warning": return "default";
      case "info": return "outline";
      default: return "outline";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Resolved": return "safe";
      case "Mitigated": return "safe";
      case "In Progress": return "threat-medium";
      case "Open": return "threat-high";
      default: return "default";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-grotesk font-bold text-foreground">Logs Dashboard</h1>
          <p className="text-muted-foreground">System logs, incidents, and analyst actions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <Card className="gradient-card border-border/50">
        <CardContent className="pt-6 pb-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search logs by keyword, source, or timestamp..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-4 px-4 py-2 border border-border rounded-lg bg-card/50">
              <span className="text-sm font-medium text-muted-foreground shrink-0">Filter:</span>
              <div className="flex items-center gap-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="filter-phishing"
                    checked={threatFilters.phishing}
                    onCheckedChange={(checked) =>
                      setThreatFilters({ ...threatFilters, phishing: checked as boolean })
                    }
                  />
                  <label htmlFor="filter-phishing" className="text-sm font-medium leading-none cursor-pointer">
                    Phishing
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="filter-ddos"
                    checked={threatFilters.ddos}
                    onCheckedChange={(checked) =>
                      setThreatFilters({ ...threatFilters, ddos: checked as boolean })
                    }
                  />
                  <label htmlFor="filter-ddos" className="text-sm font-medium leading-none cursor-pointer">
                    DDoS
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="filter-bruteforce"
                    checked={threatFilters.bruteforce}
                    onCheckedChange={(checked) =>
                      setThreatFilters({ ...threatFilters, bruteforce: checked as boolean })
                    }
                  />
                  <label htmlFor="filter-bruteforce" className="text-sm font-medium leading-none cursor-pointer">
                    Brute Force
                  </label>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Logs</CardTitle>
            <Terminal className="h-4 w-4 text-cyber-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">1,247</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Incidents</CardTitle>
            <Activity className="h-4 w-4 text-threat-high" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">8</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Analyst Actions</CardTitle>
            <User className="h-4 w-4 text-safe" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">342</div>
            <p className="text-xs text-muted-foreground">Today</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-cyber-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">4.2m</div>
            <p className="text-xs text-muted-foreground">-23% from yesterday</p>
          </CardContent>
        </Card>
      </div>

      {/* Log Sections - Full Width */}
      <div className="grid grid-cols-1 gap-6">
        {/* System Logs */}
        <Card className="gradient-card border-border/50">
          <CardHeader>
            <CardTitle className="text-foreground font-grotesk flex items-center gap-2">
              <Terminal className="h-5 w-5" />
              System Logs
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              Recent system events and status updates
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-3">
                {filteredSystemLogs.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-start gap-3 p-3 rounded-lg bg-card/50 border border-border/50 hover:border-border transition-colors"
                  >
                    <log.icon className={`h-5 w-5 mt-0.5 shrink-0 ${
                      log.level === 'critical' || log.level === 'error' ? 'text-destructive' :
                      log.level === 'warning' ? 'text-threat-medium' :
                      'text-safe'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <Badge variant={getLevelColor(log.level)} className="text-xs">
                          {log.level.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-muted-foreground">{log.timestamp}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mb-1">{log.source}</p>
                      <p className="text-sm text-foreground">{log.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Incident Logs */}
        <Card className="gradient-card border-border/50">
          <CardHeader>
            <CardTitle className="text-foreground font-grotesk flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Incident Logs
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              Security incidents and their resolution status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-3">
                {filteredIncidentLogs.map((incident) => (
                  <div
                    key={incident.id}
                    className="p-3 rounded-lg bg-card/50 border border-border/50 hover:border-border transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <Badge variant="outline">{incident.type}</Badge>
                      <Badge 
                        style={{ 
                          backgroundColor: `hsl(var(--${getStatusColor(incident.status)}) / 0.2)`, 
                          color: `hsl(var(--${getStatusColor(incident.status)}))` 
                        }}
                      >
                        {incident.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mb-1">{incident.timestamp}</p>
                    <p className="text-sm text-foreground mb-2">{incident.action}</p>
                    <div className="flex items-center gap-2">
                      <User className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">{incident.analyst}</span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Analyst Actions */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Analyst Actions
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            Recent actions taken by security analysts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {analystActions.map((action) => (
              <div
                key={action.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-card/50 border border-border/50 hover:border-border transition-colors gap-2"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <User className="h-4 w-4 text-cyber-blue" />
                    <span className="text-sm font-medium text-foreground">{action.analyst}</span>
                    <span className="text-xs text-muted-foreground">• {action.timestamp}</span>
                  </div>
                  <p className="text-sm text-foreground">{action.action}</p>
                </div>
                <Badge variant="outline" className="shrink-0 self-start sm:self-center">{action.target}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LogsDashboard;
