import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { 
  Workflow, 
  Plus, 
  Play,
  Pause,
  Edit,
  Trash2,
  GitBranch,
  Clock,
  CheckCircle,
  AlertCircle
} from "lucide-react";

// Mock playbook data
const playbooks = [
  {
    id: 1,
    name: "Phishing Email Response",
    description: "Automated workflow for handling phishing emails",
    status: "active",
    triggers: ["Email flagged as phishing", "User reports suspicious email"],
    actions: [
      "Quarantine email",
      "Block sender domain",
      "Notify affected users",
      "Create incident ticket",
      "Log to SIEM"
    ],
    executionTime: "2-3 seconds",
    successRate: "98.5%",
    lastRun: "5 mins ago"
  },
  {
    id: 2,
    name: "Brute Force Mitigation",
    description: "Automated response to brute force attacks",
    status: "active",
    triggers: ["5+ failed login attempts", "Login from new location"],
    actions: [
      "Lock user account",
      "Block source IP",
      "Send alert to analyst",
      "Require MFA on next login",
      "Log event to database"
    ],
    executionTime: "1-2 seconds",
    successRate: "99.2%",
    lastRun: "12 mins ago"
  },
  {
    id: 3,
    name: "DDoS Traffic Filter",
    description: "Automatic traffic filtering during DDoS attacks",
    status: "active",
    triggers: ["Traffic spike > 10,000 req/sec", "Pattern match: DDoS signature"],
    actions: [
      "Enable rate limiting",
      "Route traffic through CDN",
      "Block suspicious IPs",
      "Scale infrastructure",
      "Alert security team"
    ],
    executionTime: "5-10 seconds",
    successRate: "96.8%",
    lastRun: "1 hour ago"
  },
  {
    id: 4,
    name: "Malware Containment",
    description: "Isolate and remove detected malware",
    status: "paused",
    triggers: ["Malware signature detected", "Suspicious file behavior"],
    actions: [
      "Quarantine infected file",
      "Isolate affected system",
      "Run virus scan",
      "Restore from backup",
      "Update threat database"
    ],
    executionTime: "10-30 seconds",
    successRate: "94.3%",
    lastRun: "3 hours ago"
  },
];

const PlaybookConfig = () => {
  const getStatusColor = (status: string) => {
    return status === "active" ? "safe" : "muted";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-grotesk font-bold text-foreground">Playbook Configuration</h1>
          <p className="text-muted-foreground">Automated response workflows for security incidents</p>
        </div>
        <Button className="w-fit">
          <Plus className="h-4 w-4 mr-2" />
          New Playbook
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Playbooks</CardTitle>
            <Workflow className="h-4 w-4 text-cyber-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">{playbooks.length}</div>
            <p className="text-xs text-muted-foreground">Configured workflows</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active</CardTitle>
            <Play className="h-4 w-4 text-safe" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">
              {playbooks.filter(p => p.status === 'active').length}
            </div>
            <p className="text-xs text-muted-foreground">Currently running</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Executions</CardTitle>
            <GitBranch className="h-4 w-4 text-threat-medium" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">1,247</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-safe" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">97.2%</div>
            <p className="text-xs text-muted-foreground">Average across all</p>
          </CardContent>
        </Card>
      </div>

      {/* Playbooks List */}
      <div className="space-y-4">
        {playbooks.map((playbook) => (
          <Card key={playbook.id} className="gradient-card border-border/50">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <CardTitle className="text-foreground font-grotesk">{playbook.name}</CardTitle>
                    <Badge 
                      style={{ 
                        backgroundColor: `hsl(var(--${getStatusColor(playbook.status)}) / 0.2)`, 
                        color: `hsl(var(--${getStatusColor(playbook.status)}))` 
                      }}
                    >
                      {playbook.status}
                    </Badge>
                  </div>
                  <CardDescription className="text-muted-foreground">
                    {playbook.description}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={playbook.status === "active"} />
                  <Button variant="ghost" size="icon">
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Triggers */}
                <div>
                  <h4 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-threat-medium" />
                    Triggers
                  </h4>
                  <ul className="space-y-2">
                    {playbook.triggers.map((trigger, idx) => (
                      <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                        <span className="text-cyber-blue mt-1">•</span>
                        <span>{trigger}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Actions */}
                <div>
                  <h4 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
                    <GitBranch className="h-4 w-4 text-cyber-blue" />
                    Automated Actions
                  </h4>
                  <ul className="space-y-2">
                    {playbook.actions.map((action, idx) => (
                      <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                        <CheckCircle className="h-3 w-3 text-safe mt-0.5 shrink-0" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-border/50">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Clock className="h-3 w-3 text-cyber-blue" />
                    <span className="text-sm font-medium text-foreground">{playbook.executionTime}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">Execution Time</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <CheckCircle className="h-3 w-3 text-safe" />
                    <span className="text-sm font-medium text-foreground">{playbook.successRate}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">Success Rate</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Play className="h-3 w-3 text-muted-foreground" />
                    <span className="text-sm font-medium text-foreground">{playbook.lastRun}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">Last Run</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Info Card */}
      <Card className="gradient-card border-border/50 bg-cyber-blue/5">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Workflow className="h-5 w-5 text-cyber-blue mt-0.5 shrink-0" />
            <div>
              <h4 className="font-medium text-foreground mb-1">What are Playbooks?</h4>
              <p className="text-sm text-muted-foreground">
                Playbooks are automated response workflows that execute predefined actions when specific security events occur. 
                They help reduce response time, ensure consistent handling of incidents, and free up analyst time for more complex tasks.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PlaybookConfig;
