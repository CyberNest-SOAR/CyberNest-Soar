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
  AlertCircle
} from "lucide-react";
import { useState } from "react";

// Mock analyst data
const analysts = [
  { 
    id: 1, 
    name: "John Doe", 
    role: "Senior Analyst", 
    status: "active", 
    email: "john.doe@secureops.com",
    incidents: 45,
    avgResponseTime: "3.2m",
    lastActive: "2 mins ago"
  },
  { 
    id: 2, 
    name: "Jane Smith", 
    role: "Security Analyst", 
    status: "active", 
    email: "jane.smith@secureops.com",
    incidents: 38,
    avgResponseTime: "4.1m",
    lastActive: "5 mins ago"
  },
  { 
    id: 3, 
    name: "Mike Johnson", 
    role: "Junior Analyst", 
    status: "away", 
    email: "mike.johnson@secureops.com",
    incidents: 22,
    avgResponseTime: "5.8m",
    lastActive: "1 hour ago"
  },
  { 
    id: 4, 
    name: "Sarah Williams", 
    role: "Senior Analyst", 
    status: "active", 
    email: "sarah.williams@secureops.com",
    incidents: 51,
    avgResponseTime: "2.9m",
    lastActive: "Just now"
  },
  { 
    id: 5, 
    name: "Robert Brown", 
    role: "Security Analyst", 
    status: "offline", 
    email: "robert.brown@secureops.com",
    incidents: 33,
    avgResponseTime: "4.5m",
    lastActive: "3 hours ago"
  },
];

const AdminDashboard = () => {
  const [searchTerm, setSearchTerm] = useState("");

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-grotesk font-bold text-foreground">Admin Dashboard</h1>
          <p className="text-muted-foreground">Manage SOC analysts and system configuration</p>
        </div>
        <Button className="w-fit">
          <UserPlus className="h-4 w-4 mr-2" />
          Add Analyst
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Analysts</CardTitle>
            <Users className="h-4 w-4 text-cyber-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">{analysts.length}</div>
            <p className="text-xs text-muted-foreground">+2 this month</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Now</CardTitle>
            <Activity className="h-4 w-4 text-safe" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">
              {analysts.filter(a => a.status === 'active').length}
            </div>
            <p className="text-xs text-muted-foreground">Currently online</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Incidents</CardTitle>
            <Shield className="h-4 w-4 text-threat-medium" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">
              {analysts.reduce((sum, a) => sum + a.incidents, 0)}
            </div>
            <p className="text-xs text-muted-foreground">Handled this week</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Response</CardTitle>
            <Clock className="h-4 w-4 text-cyber-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-grotesk font-bold text-foreground">3.7m</div>
            <p className="text-xs text-muted-foreground">-18% improvement</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="gradient-card border-border/50">
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search analysts by name, role, or email..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Analysts List */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk">Security Analysts</CardTitle>
          <CardDescription className="text-muted-foreground">
            Manage team members and their access levels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analysts.map((analyst) => (
              <div
                key={analyst.id}
                className="flex flex-col lg:flex-row lg:items-center justify-between p-4 rounded-lg bg-card/50 border border-border/50 hover:border-border transition-colors gap-4"
              >
                <div className="flex items-center gap-4">
                  <Avatar className="h-12 w-12 border-2 border-sidebar-border">
                    <AvatarFallback className="bg-gradient-cyber text-white font-grotesk">
                      {getInitials(analyst.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-foreground">{analyst.name}</h3>
                      <Badge 
                        variant="outline"
                        style={{ 
                          backgroundColor: `hsl(var(--${getStatusColor(analyst.status)}) / 0.2)`, 
                          color: `hsl(var(--${getStatusColor(analyst.status)}))` 
                        }}
                        className="text-xs"
                      >
                        {analyst.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{analyst.role}</p>
                    <p className="text-xs text-muted-foreground">{analyst.email}</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 lg:gap-6">
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <CheckCircle className="h-3 w-3 text-safe" />
                      <span className="text-sm font-medium text-foreground">{analyst.incidents}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Incidents</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <Clock className="h-3 w-3 text-cyber-blue" />
                      <span className="text-sm font-medium text-foreground">{analyst.avgResponseTime}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Avg Time</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <Activity className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs font-medium text-foreground truncate">{analyst.lastActive}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Last Active</p>
                  </div>
                </div>

                <Button variant="ghost" size="icon" className="shrink-0">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* System Configuration */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk flex items-center gap-2">
            <Settings className="h-5 w-5" />
            System Configuration
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            Manage system-wide security settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-card/50 border border-border/50">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-foreground">Auto-Block Threshold</h4>
                <Badge variant="outline">Active</Badge>
              </div>
              <p className="text-sm text-muted-foreground">Block IPs after 5 failed attempts</p>
            </div>
            <div className="p-4 rounded-lg bg-card/50 border border-border/50">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-foreground">Email Quarantine</h4>
                <Badge variant="outline">Active</Badge>
              </div>
              <p className="text-sm text-muted-foreground">Auto-quarantine suspicious emails</p>
            </div>
            <div className="p-4 rounded-lg bg-card/50 border border-border/50">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-foreground">DDoS Protection</h4>
                <Badge variant="outline">Active</Badge>
              </div>
              <p className="text-sm text-muted-foreground">Rate limiting: 1000 req/min</p>
            </div>
            <div className="p-4 rounded-lg bg-card/50 border border-border/50">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-foreground">Threat Intelligence</h4>
                <Badge variant="outline">Active</Badge>
              </div>
              <p className="text-sm text-muted-foreground">Auto-update signatures daily</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard;
