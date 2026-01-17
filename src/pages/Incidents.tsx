import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { AlertTriangle, User, Clock, CheckCircle, XCircle, Download, FileText, MessageSquare } from "lucide-react";

interface SecurityIncident {
  id: string;
  ticketId: string;
  threatType: "Phishing" | "DDoS" | "Brute Force" | "Malware" | "Data Breach" | "Insider Threat";
  title: string;
  description: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  status: "Open" | "In Progress" | "Resolved" | "Closed";
  analystAssigned: string;
  reportedBy: string;
  createdAt: string;
  updatedAt: string;
  comments: Comment[];
  affectedSystems: string[];
  estimatedImpact: string;
}

interface Comment {
  id: string;
  author: string;
  content: string;
  timestamp: string;
}

const securityIncidents: SecurityIncident[] = [
  {
    id: "1",
    ticketId: "INC-2024-001",
    threatType: "Phishing",
    title: "Large-scale Phishing Campaign Targeting Finance Team",
    description: "Multiple suspicious emails detected targeting finance department with fake invoice attachments containing malware.",
    severity: "Critical",
    status: "In Progress",
    analystAssigned: "Sarah Chen",
    reportedBy: "Auto-Detection System",
    createdAt: "2024-01-15 09:15:33",
    updatedAt: "2024-01-15 14:23:45",
    comments: [
      {
        id: "c1",
        author: "Sarah Chen",
        content: "Initial analysis shows 23 emails quarantined. Investigating email headers and attachment hashes.",
        timestamp: "2024-01-15 09:30:15"
      },
      {
        id: "c2",
        author: "Mike Rodriguez",
        content: "Finance team has been notified. No successful infections reported so far.",
        timestamp: "2024-01-15 11:45:22"
      }
    ],
    affectedSystems: ["Email Gateway", "Finance Workstations"],
    estimatedImpact: "High - Potential financial fraud"
  },
  {
    id: "2",
    ticketId: "INC-2024-002",
    threatType: "DDoS",
    title: "Distributed Denial of Service Attack on Web Servers",
    description: "Coordinated DDoS attack targeting main web application servers causing intermittent service disruptions.",
    severity: "High",
    status: "Resolved",
    analystAssigned: "Alex Thompson",
    reportedBy: "Network Monitoring",
    createdAt: "2024-01-15 08:30:12",
    updatedAt: "2024-01-15 12:15:08",
    comments: [
      {
        id: "c3",
        author: "Alex Thompson",
        content: "Attack mitigated using CDN protection. Attack peaked at 50Gbps.",
        timestamp: "2024-01-15 10:15:33"
      }
    ],
    affectedSystems: ["Web Servers", "CDN", "Load Balancers"],
    estimatedImpact: "Medium - Temporary service degradation"
  },
  {
    id: "3",
    ticketId: "INC-2024-003",
    threatType: "Malware",
    title: "Ransomware Detection on Development Server",
    description: "Ransomware activity detected on development server attempting to encrypt project files.",
    severity: "Critical",
    status: "Open",
    analystAssigned: "Emily Davis",
    reportedBy: "Endpoint Detection",
    createdAt: "2024-01-15 07:45:21",
    updatedAt: "2024-01-15 07:45:21",
    comments: [],
    affectedSystems: ["Dev Server 03", "File Share"],
    estimatedImpact: "Critical - Potential data loss"
  },
  {
    id: "4",
    ticketId: "INC-2024-004",
    threatType: "Brute Force",
    title: "Multiple Failed Login Attempts on Admin Accounts",
    description: "Sustained brute force attack targeting administrative accounts from multiple IP addresses.",
    severity: "Medium",
    status: "In Progress",
    analystAssigned: "James Wilson",
    reportedBy: "Authentication System",
    createdAt: "2024-01-15 06:20:45",
    updatedAt: "2024-01-15 13:30:12",
    comments: [
      {
        id: "c4",
        author: "James Wilson",
        content: "Account lockout policies activated. Investigating source IPs and attack patterns.",
        timestamp: "2024-01-15 08:15:33"
      }
    ],
    affectedSystems: ["Active Directory", "VPN Gateway"],
    estimatedImpact: "Low - No successful breaches detected"
  }
];

const Incidents = () => {
  const [incidents, setIncidents] = useState<SecurityIncident[]>(securityIncidents);
  const [selectedIncident, setSelectedIncident] = useState<SecurityIncident | null>(null);
  const [newComment, setNewComment] = useState("");

  const openIncidents = incidents.filter(i => i.status === "Open").length;
  const inProgressIncidents = incidents.filter(i => i.status === "In Progress").length;
  const criticalIncidents = incidents.filter(i => i.severity === "Critical").length;
  const resolvedToday = incidents.filter(i => i.status === "Resolved" && i.updatedAt.startsWith("2024-01-15")).length;

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "Critical":
        return <Badge variant="destructive" className="bg-threat-high/20 text-threat-high border-threat-high/50">Critical</Badge>;
      case "High":
        return <Badge className="bg-threat-medium/20 text-threat-medium border-threat-medium/50">High</Badge>;
      case "Medium":
        return <Badge className="bg-threat-low/20 text-threat-low border-threat-low/50">Medium</Badge>;
      case "Low":
        return <Badge variant="outline" className="border-safe/50 text-safe">Low</Badge>;
      default:
        return <Badge variant="outline">{severity}</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Open":
        return <Badge variant="destructive">Open</Badge>;
      case "In Progress":
        return <Badge className="bg-cyber-blue/20 text-cyber-blue border-cyber-blue/50">In Progress</Badge>;
      case "Resolved":
        return <Badge className="bg-safe/20 text-safe border-safe/50">Resolved</Badge>;
      case "Closed":
        return <Badge variant="outline">Closed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getThreatTypeBadge = (type: string) => {
    const colors = {
      "Phishing": "bg-threat-high/20 text-threat-high border-threat-high/50",
      "DDoS": "bg-threat-medium/20 text-threat-medium border-threat-medium/50",
      "Brute Force": "bg-threat-low/20 text-threat-low border-threat-low/50",
      "Malware": "bg-threat-high/20 text-threat-high border-threat-high/50",
      "Data Breach": "bg-threat-high/20 text-threat-high border-threat-high/50",
      "Insider Threat": "bg-threat-medium/20 text-threat-medium border-threat-medium/50"
    };
    
    return (
      <Badge className={colors[type as keyof typeof colors] || "bg-muted/20 text-muted-foreground"}>
        {type}
      </Badge>
    );
  };

  const addComment = () => {
    if (!selectedIncident || !newComment.trim()) return;
    
    const comment: Comment = {
      id: Date.now().toString(),
      author: "Current User",
      content: newComment,
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 16)
    };

    setIncidents(incidents.map(incident => 
      incident.id === selectedIncident.id 
        ? { ...incident, comments: [...incident.comments, comment] }
        : incident
    ));

    setSelectedIncident({
      ...selectedIncident,
      comments: [...selectedIncident.comments, comment]
    });

    setNewComment("");
  };

  const exportIncidents = () => {
    const csvContent = incidents.map(incident => 
      `${incident.ticketId},${incident.threatType},${incident.severity},${incident.status},${incident.analystAssigned},${incident.createdAt}`
    ).join('\n');
    
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent('Ticket ID,Threat Type,Severity,Status,Analyst,Created\n' + csvContent));
    element.setAttribute('download', 'security-incidents.csv');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-grotesk font-bold text-foreground">Security Incidents</h1>
          <p className="text-muted-foreground">Incident response and ticket management</p>
        </div>
        <Button onClick={exportIncidents} className="bg-gradient-cyber hover:opacity-90 text-white">
          <Download className="h-4 w-4 mr-2" />
          Export Incidents
        </Button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-8 w-8 text-threat-high" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">{openIncidents}</p>
                <p className="text-sm text-muted-foreground">Open Incidents</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Clock className="h-8 w-8 text-cyber-blue" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">{inProgressIncidents}</p>
                <p className="text-sm text-muted-foreground">In Progress</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <XCircle className="h-8 w-8 text-threat-high" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">{criticalIncidents}</p>
                <p className="text-sm text-muted-foreground">Critical</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-safe" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">{resolvedToday}</p>
                <p className="text-sm text-muted-foreground">Resolved Today</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Incidents Table */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk">Security Incident Tickets</CardTitle>
          <CardDescription className="text-muted-foreground">
            Active security incidents and response tracking
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-muted/50">
                <TableHead className="text-muted-foreground font-medium">Ticket ID</TableHead>
                <TableHead className="text-muted-foreground font-medium">Threat Type</TableHead>
                <TableHead className="text-muted-foreground font-medium">Title</TableHead>
                <TableHead className="text-muted-foreground font-medium">Severity</TableHead>
                <TableHead className="text-muted-foreground font-medium">Status</TableHead>
                <TableHead className="text-muted-foreground font-medium">Analyst</TableHead>
                <TableHead className="text-muted-foreground font-medium">Created</TableHead>
                <TableHead className="text-muted-foreground font-medium">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {incidents.map((incident) => (
                <TableRow key={incident.id} className="border-border hover:bg-muted/20">
                  <TableCell className="font-mono text-foreground">{incident.ticketId}</TableCell>
                  <TableCell>{getThreatTypeBadge(incident.threatType)}</TableCell>
                  <TableCell className="text-foreground max-w-xs truncate">{incident.title}</TableCell>
                  <TableCell>{getSeverityBadge(incident.severity)}</TableCell>
                  <TableCell>{getStatusBadge(incident.status)}</TableCell>
                  <TableCell className="text-foreground">{incident.analystAssigned}</TableCell>
                  <TableCell className="text-muted-foreground">{incident.createdAt}</TableCell>
                  <TableCell>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedIncident(incident)}
                          className="border-border hover:bg-muted"
                        >
                          <FileText className="h-4 w-4 mr-1" />
                          View Details
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-card border-border">
                        <DialogHeader>
                          <DialogTitle className="text-foreground font-grotesk">
                            Incident Details - {selectedIncident?.ticketId}
                          </DialogTitle>
                          <DialogDescription className="text-muted-foreground">
                            Complete incident information and response timeline
                          </DialogDescription>
                        </DialogHeader>
                        {selectedIncident && (
                          <div className="space-y-6">
                            {/* Incident Overview */}
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Threat Type</label>
                                <div className="mt-1">
                                  {getThreatTypeBadge(selectedIncident.threatType)}
                                </div>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Severity</label>
                                <div className="mt-1">
                                  {getSeverityBadge(selectedIncident.severity)}
                                </div>
                              </div>
                            </div>

                            <div>
                              <label className="text-sm font-medium text-muted-foreground">Title</label>
                              <p className="text-foreground font-medium">{selectedIncident.title}</p>
                            </div>

                            <div>
                              <label className="text-sm font-medium text-muted-foreground">Description</label>
                              <p className="text-foreground">{selectedIncident.description}</p>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Status</label>
                                <div className="mt-1">
                                  {getStatusBadge(selectedIncident.status)}
                                </div>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Assigned Analyst</label>
                                <p className="text-foreground">{selectedIncident.analystAssigned}</p>
                              </div>
                            </div>

                            <div>
                              <label className="text-sm font-medium text-muted-foreground">Affected Systems</label>
                              <div className="mt-2 flex flex-wrap gap-2">
                                {selectedIncident.affectedSystems.map((system, index) => (
                                  <Badge key={index} variant="outline" className="border-border">
                                    {system}
                                  </Badge>
                                ))}
                              </div>
                            </div>

                            <div>
                              <label className="text-sm font-medium text-muted-foreground">Estimated Impact</label>
                              <p className="text-foreground">{selectedIncident.estimatedImpact}</p>
                            </div>

                            {/* Comments Section */}
                            <div className="border-t border-border pt-4">
                              <div className="flex items-center gap-2 mb-4">
                                <MessageSquare className="h-5 w-5 text-muted-foreground" />
                                <h4 className="font-medium text-foreground">Comments & Updates</h4>
                              </div>
                              
                              <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
                                {selectedIncident.comments.map((comment) => (
                                  <div key={comment.id} className="p-3 bg-muted/20 rounded-lg">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="font-medium text-foreground">{comment.author}</span>
                                      <span className="text-xs text-muted-foreground">{comment.timestamp}</span>
                                    </div>
                                    <p className="text-foreground text-sm">{comment.content}</p>
                                  </div>
                                ))}
                              </div>

                              <div className="flex gap-2">
                                <Textarea
                                  placeholder="Add a comment or update..."
                                  value={newComment}
                                  onChange={(e) => setNewComment(e.target.value)}
                                  className="flex-1 bg-input border-border"
                                />
                                <Button 
                                  onClick={addComment}
                                  className="bg-gradient-cyber hover:opacity-90 text-white"
                                >
                                  Add Comment
                                </Button>
                              </div>
                            </div>
                          </div>
                        )}
                      </DialogContent>
                    </Dialog>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default Incidents;