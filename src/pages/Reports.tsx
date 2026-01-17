import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Download, FileText, TrendingUp, Shield, Clock, Target } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, Area, AreaChart } from "recharts";

// Mock data for analytics
const detectionAccuracyData = [
  { week: "Week 1", precision: 94, recall: 92, f1Score: 93 },
  { week: "Week 2", precision: 96, recall: 94, f1Score: 95 },
  { week: "Week 3", precision: 98, recall: 96, f1Score: 97 },
  { week: "Week 4", precision: 97, recall: 95, f1Score: 96 },
];

const responseTimeData = [
  { month: "Oct", avgResponseTime: 45, slaTarget: 60 },
  { month: "Nov", avgResponseTime: 38, slaTarget: 60 },
  { month: "Dec", avgResponseTime: 42, slaTarget: 60 },
  { month: "Jan", avgResponseTime: 35, slaTarget: 60 },
];

const threatTrendsData = [
  { date: "2024-01-01", phishing: 25, ddos: 8, malware: 12, bruteforce: 15 },
  { date: "2024-01-03", phishing: 30, ddos: 5, malware: 18, bruteforce: 22 },
  { date: "2024-01-05", phishing: 28, ddos: 12, malware: 15, bruteforce: 18 },
  { date: "2024-01-07", phishing: 35, ddos: 7, malware: 20, bruteforce: 25 },
  { date: "2024-01-09", phishing: 42, ddos: 15, malware: 25, bruteforce: 28 },
  { date: "2024-01-11", phishing: 38, ddos: 9, malware: 22, bruteforce: 24 },
  { date: "2024-01-13", phishing: 45, ddos: 18, malware: 28, bruteforce: 32 },
  { date: "2024-01-15", phishing: 52, ddos: 12, malware: 30, bruteforce: 35 },
];

const incidentsByCategory = [
  { name: "Phishing", value: 45, color: "#3B82F6" },
  { name: "Malware", value: 28, color: "#EF4444" },
  { name: "Brute Force", value: 18, color: "#F59E0B" },
  { name: "DDoS", value: 9, color: "#10B981" },
];

const Reports = () => {
  const generateFullReport = async () => {
    const { SecurityReportGenerator } = await import('../utils/pdfGenerator');
    
    const reportData = {
      totalPhishing: 563,
      totalDDoS: 111,
      totalBruteForce: 224,
      totalMalware: 349,
      phishingEmails: [
        { sender: 'suspicious@fake-bank.com', subject: 'Urgent: Verify Your Account Now!', confidence: 94, action: 'Quarantined' },
        { sender: 'noreply@phishing-site.org', subject: 'Your Payment Failed - Click Here', confidence: 89, action: 'Blocked' },
        { sender: 'admin@fake-service.net', subject: 'Security Alert: Login Detected', confidence: 96, action: 'Quarantined' },
        { sender: 'support@scam-portal.com', subject: 'Account Suspended - Immediate Action Required', confidence: 91, action: 'Blocked' },
        { sender: 'security@malicious-domain.org', subject: 'Confirm Identity to Restore Access', confidence: 88, action: 'Quarantined' }
      ],
      ddosAttacks: [
        { sourceIP: '192.168.1.100', packetsPerSec: 50000, mitigation: 'IP Blocked' },
        { sourceIP: '10.0.0.45', packetsPerSec: 75000, mitigation: 'Rate Limited' },
        { sourceIP: '172.16.0.22', packetsPerSec: 32000, mitigation: 'Traffic Filtered' },
        { sourceIP: '203.45.67.89', packetsPerSec: 45000, mitigation: 'IP Blocked' }
      ],
      bruteForceAttempts: [
        { username: 'admin', attempts: 247, sourceIP: '192.168.1.150' },
        { username: 'root', attempts: 189, sourceIP: '10.0.0.85' },
        { username: 'user1', attempts: 156, sourceIP: '172.16.0.33' },
        { username: 'administrator', attempts: 201, sourceIP: '203.45.67.12' }
      ],
      malwareDetections: [
        { fileName: 'invoice_payment.exe', hash: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6', status: 'Quarantined' },
        { fileName: 'document_scanner.pdf.exe', hash: 'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7', status: 'Removed' },
        { fileName: 'system_update.bat', hash: 'c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8', status: 'Blocked' },
        { fileName: 'security_patch.scr', hash: 'd4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9', status: 'Quarantined' }
      ],
      incidents: [
        { ticketId: 'INC-2025-001', threatType: 'Phishing', status: 'Resolved', analyst: 'Sarah Chen' },
        { ticketId: 'INC-2025-002', threatType: 'DDoS', status: 'In Progress', analyst: 'Mike Rodriguez' },
        { ticketId: 'INC-2025-003', threatType: 'Malware', status: 'Open', analyst: 'Jessica Park' },
        { ticketId: 'INC-2025-004', threatType: 'Brute Force', status: 'Resolved', analyst: 'David Kim' },
        { ticketId: 'INC-2025-005', threatType: 'Phishing', status: 'Closed', analyst: 'Sarah Chen' }
      ]
    };

    const generator = new SecurityReportGenerator();
    await generator.generateFullReport(reportData, 'Senior Security Analyst');
    generator.save('security-analytics-report.pdf');
  };

  const generateExecutiveReport = async () => {
    const { SecurityReportGenerator } = await import('../utils/pdfGenerator');
    
    const reportData = {
      totalPhishing: 563,
      totalDDoS: 111,
      totalBruteForce: 224,
      totalMalware: 349,
      phishingEmails: [],
      ddosAttacks: [],
      bruteForceAttempts: [],
      malwareDetections: [],
      incidents: []
    };

    const generator = new SecurityReportGenerator();
    await generator.generateExecutiveSummary(reportData);
    generator.save('executive-security-briefing.pdf');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-grotesk font-bold text-foreground">Security Reports & Analytics</h1>
          <p className="text-muted-foreground">Comprehensive security metrics and threat intelligence</p>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            onClick={generateExecutiveReport}
            variant="outline" 
            className="border-border hover:bg-muted"
          >
            <FileText className="h-4 w-4 mr-2" />
            Executive Summary
          </Button>
          <Button 
            onClick={generateFullReport}
            className="bg-gradient-cyber hover:opacity-90 text-white"
          >
            <Download className="h-4 w-4 mr-2" />
            Full Report
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Target className="h-8 w-8 text-cyber-blue" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">96%</p>
                <p className="text-sm text-muted-foreground">Detection Accuracy</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Clock className="h-8 w-8 text-safe" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">35m</p>
                <p className="text-sm text-muted-foreground">Avg Response Time</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-cyber-green" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">99.8%</p>
                <p className="text-sm text-muted-foreground">System Uptime</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-threat-medium" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">1,247</p>
                <p className="text-sm text-muted-foreground">Threats Blocked</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Analytics Tabs */}
      <Tabs defaultValue="accuracy" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 bg-card border border-border">
          <TabsTrigger value="accuracy" className="data-[state=active]:bg-cyber-blue/20 data-[state=active]:text-cyber-blue">
            Detection Accuracy
          </TabsTrigger>
          <TabsTrigger value="response" className="data-[state=active]:bg-cyber-blue/20 data-[state=active]:text-cyber-blue">
            Response Times
          </TabsTrigger>
          <TabsTrigger value="trends" className="data-[state=active]:bg-cyber-blue/20 data-[state=active]:text-cyber-blue">
            Threat Trends
          </TabsTrigger>
          <TabsTrigger value="distribution" className="data-[state=active]:bg-cyber-blue/20 data-[state=active]:text-cyber-blue">
            Incident Distribution
          </TabsTrigger>
        </TabsList>

        <TabsContent value="accuracy" className="space-y-4">
          <Card className="gradient-card border-border/50">
            <CardHeader>
              <CardTitle className="text-foreground font-grotesk">Detection Accuracy Metrics</CardTitle>
              <CardDescription className="text-muted-foreground">
                Precision, recall, and F1-score analysis over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={detectionAccuracyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="week" stroke="#9CA3AF" />
                  <YAxis domain={[85, 100]} stroke="#9CA3AF" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1F2937', 
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F3F4F6'
                    }}
                    formatter={(value) => [`${value}%`, '']}
                  />
                  <Line type="monotone" dataKey="precision" stroke="#3B82F6" strokeWidth={3} name="Precision" />
                  <Line type="monotone" dataKey="recall" stroke="#10B981" strokeWidth={3} name="Recall" />
                  <Line type="monotone" dataKey="f1Score" stroke="#F59E0B" strokeWidth={3} name="F1-Score" />
                </LineChart>
              </ResponsiveContainer>
              
              <div className="mt-6 grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-grotesk font-bold text-cyber-blue">97%</p>
                  <p className="text-sm text-muted-foreground">Current Precision</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-grotesk font-bold text-safe">95%</p>
                  <p className="text-sm text-muted-foreground">Current Recall</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-grotesk font-bold text-threat-medium">96%</p>
                  <p className="text-sm text-muted-foreground">Current F1-Score</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="response" className="space-y-4">
          <Card className="gradient-card border-border/50">
            <CardHeader>
              <CardTitle className="text-foreground font-grotesk">Average Response Time Analysis</CardTitle>
              <CardDescription className="text-muted-foreground">
                Incident response time performance vs SLA targets
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={responseTimeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="month" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1F2937', 
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F3F4F6'
                    }}
                    formatter={(value, name) => [
                      `${value} minutes`, 
                      name === 'avgResponseTime' ? 'Avg Response Time' : 'SLA Target'
                    ]}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="slaTarget" 
                    stroke="#EF4444" 
                    fill="#EF4444" 
                    fillOpacity={0.1}
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="avgResponseTime" 
                    stroke="#10B981" 
                    fill="#10B981" 
                    fillOpacity={0.3}
                    strokeWidth={3}
                  />
                </AreaChart>
              </ResponsiveContainer>
              
              <div className="mt-6 flex items-center justify-center gap-8">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-safe rounded"></div>
                  <span className="text-sm text-muted-foreground">Average Response Time</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-dashed border-threat-high rounded"></div>
                  <span className="text-sm text-muted-foreground">SLA Target (60 min)</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card className="gradient-card border-border/50">
            <CardHeader>
              <CardTitle className="text-foreground font-grotesk">Threat Trends Analysis</CardTitle>
              <CardDescription className="text-muted-foreground">
                15-day trend analysis of detected security threats
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={threatTrendsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#9CA3AF"
                    tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1F2937', 
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F3F4F6'
                    }}
                    labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <Area type="monotone" dataKey="bruteforce" stackId="1" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.8} />
                  <Area type="monotone" dataKey="ddos" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.8} />
                  <Area type="monotone" dataKey="malware" stackId="1" stroke="#EF4444" fill="#EF4444" fillOpacity={0.8} />
                  <Area type="monotone" dataKey="phishing" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.8} />
                </AreaChart>
              </ResponsiveContainer>
              
              <div className="mt-6 grid grid-cols-4 gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-cyber-blue rounded"></div>
                  <span className="text-sm text-muted-foreground">Phishing</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-threat-high rounded"></div>
                  <span className="text-sm text-muted-foreground">Malware</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-safe rounded"></div>
                  <span className="text-sm text-muted-foreground">DDoS</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-threat-medium rounded"></div>
                  <span className="text-sm text-muted-foreground">Brute Force</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="distribution" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="gradient-card border-border/50">
              <CardHeader>
                <CardTitle className="text-foreground font-grotesk">Incident Distribution</CardTitle>
                <CardDescription className="text-muted-foreground">
                  Breakdown of security incidents by category
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={incidentsByCategory}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {incidentsByCategory.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1F2937', 
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F3F4F6'
                      }} 
                    />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="gradient-card border-border/50">
              <CardHeader>
                <CardTitle className="text-foreground font-grotesk">Security Effectiveness</CardTitle>
                <CardDescription className="text-muted-foreground">
                  Key performance indicators for security operations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-muted-foreground">Threat Detection Rate</span>
                      <span className="text-sm font-bold text-safe">96%</span>
                    </div>
                    <div className="w-full bg-muted/20 rounded-full h-2">
                      <div className="bg-gradient-to-r from-safe to-cyber-green h-2 rounded-full" style={{ width: '96%' }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-muted-foreground">Incident Response Speed</span>
                      <span className="text-sm font-bold text-cyber-blue">94%</span>
                    </div>
                    <div className="w-full bg-muted/20 rounded-full h-2">
                      <div className="bg-gradient-to-r from-cyber-blue to-primary h-2 rounded-full" style={{ width: '94%' }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-muted-foreground">False Positive Rate</span>
                      <span className="text-sm font-bold text-threat-low">2.1%</span>
                    </div>
                    <div className="w-full bg-muted/20 rounded-full h-2">
                      <div className="bg-gradient-to-r from-threat-low to-threat-medium h-2 rounded-full" style={{ width: '2.1%' }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-muted-foreground">System Uptime</span>
                      <span className="text-sm font-bold text-safe">99.8%</span>
                    </div>
                    <div className="w-full bg-muted/20 rounded-full h-2">
                      <div className="bg-gradient-to-r from-safe to-cyber-green h-2 rounded-full" style={{ width: '99.8%' }}></div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-border">
                  <h4 className="font-medium text-foreground mb-3">Recent Achievements</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Badge className="bg-safe/20 text-safe border-safe/50">✓</Badge>
                      <span className="text-muted-foreground">Zero critical breaches this month</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-safe/20 text-safe border-safe/50">✓</Badge>
                      <span className="text-muted-foreground">Response time under SLA target</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-safe/20 text-safe border-safe/50">✓</Badge>
                      <span className="text-muted-foreground">96% threat detection accuracy</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Reports;