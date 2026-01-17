import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Network, Shield, AlertTriangle, Activity, Globe } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

// Mock data for DDoS traffic
const trafficData = [
  { time: "00:00", normal: 150, attack: 0 },
  { time: "02:00", normal: 120, attack: 0 },
  { time: "04:00", normal: 200, attack: 0 },
  { time: "06:00", normal: 300, attack: 0 },
  { time: "08:00", normal: 450, attack: 1200 }, // Attack starts
  { time: "10:00", normal: 400, attack: 2800 },
  { time: "12:00", normal: 380, attack: 3500 }, // Peak attack
  { time: "14:00", normal: 420, attack: 1800 }, // Attack mitigated
  { time: "16:00", normal: 380, attack: 200 },
  { time: "18:00", normal: 350, attack: 0 }, // Attack stopped
  { time: "20:00", normal: 320, attack: 0 },
  { time: "22:00", normal: 280, attack: 0 },
];

interface AttackSource {
  id: string;
  sourceIP: string;
  packetsPerSec: number;
  country: string;
  status: "Active" | "Blocked" | "Mitigated";
  duration: string;
  attackType: string;
}

const attackSources: AttackSource[] = [
  {
    id: "1",
    sourceIP: "185.220.101.42",
    packetsPerSec: 15420,
    country: "Unknown",
    status: "Blocked",
    duration: "2h 15m",
    attackType: "UDP Flood"
  },
  {
    id: "2",
    sourceIP: "103.224.182.245",
    packetsPerSec: 12800,
    country: "CN",
    status: "Active",
    duration: "45m",
    attackType: "SYN Flood"
  },
  {
    id: "3",
    sourceIP: "45.142.214.191",
    packetsPerSec: 8950,
    country: "RU",
    status: "Mitigated",
    duration: "1h 30m",
    attackType: "HTTP Flood"
  },
  {
    id: "4",
    sourceIP: "94.156.35.72",
    packetsPerSec: 22100,
    country: "Unknown",
    status: "Active",
    duration: "20m",
    attackType: "ICMP Flood"
  },
  {
    id: "5",
    sourceIP: "198.51.100.42",
    packetsPerSec: 5420,
    country: "US",
    status: "Blocked",
    duration: "3h 5m",
    attackType: "DNS Amplification"
  }
];

const DDoSAttacks = () => {
  const activeAttacks = attackSources.filter(attack => attack.status === "Active").length;
  const totalPackets = attackSources.reduce((sum, attack) => sum + attack.packetsPerSec, 0);
  const blockedAttacks = attackSources.filter(attack => attack.status === "Blocked").length;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Active":
        return <Badge variant="destructive" className="bg-threat-high/20 text-threat-high border-threat-high/50">Active</Badge>;
      case "Blocked":
        return <Badge className="bg-safe/20 text-safe border-safe/50">Blocked</Badge>;
      case "Mitigated":
        return <Badge variant="outline" className="border-cyber-blue/50 text-cyber-blue">Mitigated</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getAttackTypeBadge = (type: string) => {
    const colors = {
      "UDP Flood": "bg-threat-medium/20 text-threat-medium border-threat-medium/50",
      "SYN Flood": "bg-threat-high/20 text-threat-high border-threat-high/50",
      "HTTP Flood": "bg-threat-low/20 text-threat-low border-threat-low/50",
      "ICMP Flood": "bg-threat-medium/20 text-threat-medium border-threat-medium/50",
      "DNS Amplification": "bg-threat-high/20 text-threat-high border-threat-high/50"
    };
    
    return (
      <Badge className={colors[type as keyof typeof colors] || "bg-muted/20 text-muted-foreground"}>
        {type}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header with Alert */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-grotesk font-bold text-foreground">DDoS Attack Monitor</h1>
            <p className="text-muted-foreground">Real-time distributed denial-of-service attack detection</p>
          </div>
        </div>

        {/* Active Attack Alert */}
        {activeAttacks > 0 && (
          <Alert className="border-destructive/50 bg-destructive/10">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            <AlertDescription className="text-destructive font-medium">
              ⚠️ Active DDoS Attack Detected - {activeAttacks} attack source{activeAttacks > 1 ? 's' : ''} currently active
            </AlertDescription>
          </Alert>
        )}
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-8 w-8 text-threat-high" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">{activeAttacks}</p>
                <p className="text-sm text-muted-foreground">Active Attacks</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-threat-medium" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">
                  {(totalPackets / 1000).toFixed(1)}K
                </p>
                <p className="text-sm text-muted-foreground">Packets/sec</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-safe" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">{blockedAttacks}</p>
                <p className="text-sm text-muted-foreground">Blocked Sources</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Globe className="h-8 w-8 text-cyber-blue" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">99.8%</p>
                <p className="text-sm text-muted-foreground">Uptime</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Traffic Chart */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk">Network Traffic Analysis</CardTitle>
          <CardDescription className="text-muted-foreground">
            Real-time traffic monitoring showing normal vs attack patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={trafficData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }}
                formatter={(value, name) => [
                  `${value} req/s`,
                  name === 'normal' ? 'Normal Traffic' : 'Attack Traffic'
                ]}
              />
              <Line 
                type="monotone" 
                dataKey="normal" 
                stroke="#10B981" 
                strokeWidth={2} 
                name="normal"
              />
              <Line 
                type="monotone" 
                dataKey="attack" 
                stroke="#EF4444" 
                strokeWidth={3} 
                name="attack"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Attack Sources Table */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk">Attack Sources</CardTitle>
          <CardDescription className="text-muted-foreground">
            Detailed breakdown of DDoS attack sources and patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-muted/50">
                <TableHead className="text-muted-foreground font-medium">Source IP</TableHead>
                <TableHead className="text-muted-foreground font-medium">Country</TableHead>
                <TableHead className="text-muted-foreground font-medium">Attack Type</TableHead>
                <TableHead className="text-muted-foreground font-medium">Packets/sec</TableHead>
                <TableHead className="text-muted-foreground font-medium">Duration</TableHead>
                <TableHead className="text-muted-foreground font-medium">Status</TableHead>
                <TableHead className="text-muted-foreground font-medium">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {attackSources.map((attack) => (
                <TableRow key={attack.id} className="border-border hover:bg-muted/20">
                  <TableCell className="font-mono text-foreground">{attack.sourceIP}</TableCell>
                  <TableCell className="text-foreground">
                    <div className="flex items-center gap-2">
                      <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                        {attack.country}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>{getAttackTypeBadge(attack.attackType)}</TableCell>
                  <TableCell className="font-mono text-foreground">
                    {attack.packetsPerSec.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{attack.duration}</TableCell>
                  <TableCell>{getStatusBadge(attack.status)}</TableCell>
                  <TableCell className="space-x-2">
                    {attack.status === "Active" && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-destructive/50 text-destructive hover:bg-destructive/10"
                      >
                        Block IP
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-border hover:bg-muted"
                    >
                      Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Mitigation Actions */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk">Automated Mitigation</CardTitle>
          <CardDescription className="text-muted-foreground">
            Real-time DDoS protection and response actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-lg bg-safe/10 border border-safe/20">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-safe" />
                <div>
                  <p className="font-medium text-foreground">Rate Limiting Activated</p>
                  <p className="text-sm text-muted-foreground">Automatically limiting requests from suspicious IPs</p>
                </div>
              </div>
              <Badge className="bg-safe/20 text-safe border-safe/50">Active</Badge>
            </div>

            <div className="flex items-center justify-between p-4 rounded-lg bg-cyber-blue/10 border border-cyber-blue/20">
              <div className="flex items-center gap-3">
                <Network className="h-5 w-5 text-cyber-blue" />
                <div>
                  <p className="font-medium text-foreground">CDN Protection Enabled</p>
                  <p className="text-sm text-muted-foreground">Traffic being filtered through edge servers</p>
                </div>
              </div>
              <Badge className="bg-cyber-blue/20 text-cyber-blue border-cyber-blue/50">Enabled</Badge>
            </div>

            <div className="flex items-center justify-between p-4 rounded-lg bg-threat-medium/10 border border-threat-medium/20">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5" style={{ color: 'hsl(var(--threat-medium))' }} />
                <div>
                  <p className="font-medium text-foreground">GeoBlocking Active</p>
                  <p className="text-sm text-muted-foreground">Blocking traffic from high-risk regions</p>
                </div>
              </div>
              <Badge style={{ backgroundColor: 'hsl(var(--threat-medium) / 0.2)', color: 'hsl(var(--threat-medium))' }}>
                Active
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DDoSAttacks;