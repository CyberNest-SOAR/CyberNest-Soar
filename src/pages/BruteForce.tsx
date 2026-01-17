import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Lock, Shield, AlertTriangle, User, Clock, Globe } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

// Mock data for brute force attempts over time
const attemptData = [
  { hour: "00:00", attempts: 12 },
  { hour: "02:00", attempts: 8 },
  { hour: "04:00", attempts: 15 },
  { hour: "06:00", attempts: 25 },
  { hour: "08:00", attempts: 45 }, // Business hours spike
  { hour: "10:00", attempts: 78 },
  { hour: "12:00", attempts: 92 }, // Peak attempts
  { hour: "14:00", attempts: 65 },
  { hour: "16:00", attempts: 58 },
  { hour: "18:00", attempts: 32 },
  { hour: "20:00", attempts: 28 },
  { hour: "22:00", attempts: 18 },
];

interface BruteForceAttempt {
  id: string;
  userAccount: string;
  attempts: number;
  sourceIP: string;
  country: string;
  status: "Active" | "Blocked" | "Locked" | "Monitoring";
  lastAttempt: string;
  successfulLogin: boolean;
  attackPattern: string;
}

const bruteForceAttempts: BruteForceAttempt[] = [
  {
    id: "1",
    userAccount: "admin",
    attempts: 247,
    sourceIP: "185.220.101.42",
    country: "RU",
    status: "Blocked",
    lastAttempt: "2024-01-15 14:23:45",
    successfulLogin: false,
    attackPattern: "Dictionary Attack"
  },
  {
    id: "2",
    userAccount: "john.doe@company.com",
    attempts: 89,
    sourceIP: "103.224.182.245",
    country: "CN",
    status: "Active",
    lastAttempt: "2024-01-15 14:45:12",
    successfulLogin: false,
    attackPattern: "Credential Stuffing"
  },
  {
    id: "3",
    userAccount: "support",
    attempts: 34,
    sourceIP: "45.142.214.191",
    country: "Unknown",
    status: "Monitoring",
    lastAttempt: "2024-01-15 13:55:33",
    successfulLogin: false,
    attackPattern: "Brute Force"
  },
  {
    id: "4",
    userAccount: "admin@company.com",
    attempts: 156,
    sourceIP: "94.156.35.72",
    country: "TR",
    status: "Locked",
    lastAttempt: "2024-01-15 12:30:21",
    successfulLogin: false,
    attackPattern: "Hybrid Attack"
  },
  {
    id: "5",
    userAccount: "root",
    attempts: 312,
    sourceIP: "198.51.100.42",
    country: "US",
    status: "Blocked",
    lastAttempt: "2024-01-15 11:15:07",
    successfulLogin: false,
    attackPattern: "Dictionary Attack"
  }
];

const BruteForce = () => {
  const [attempts, setAttempts] = useState<BruteForceAttempt[]>(bruteForceAttempts);
  const [selectedAttempt, setSelectedAttempt] = useState<BruteForceAttempt | null>(null);

  const activeAttacks = attempts.filter(a => a.status === "Active").length;
  const blockedAccounts = attempts.filter(a => a.status === "Blocked" || a.status === "Locked").length;
  const totalAttempts = attempts.reduce((sum, a) => sum + a.attempts, 0);

  const handleLockAccount = (attemptId: string) => {
    setAttempts(attempts.map(attempt => 
      attempt.id === attemptId ? { ...attempt, status: "Locked" as const } : attempt
    ));
  };

  const handleBlockIP = (attemptId: string) => {
    setAttempts(attempts.map(attempt => 
      attempt.id === attemptId ? { ...attempt, status: "Blocked" as const } : attempt
    ));
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Active":
        return <Badge variant="destructive" className="bg-threat-high/20 text-threat-high border-threat-high/50">Active</Badge>;
      case "Blocked":
        return <Badge className="bg-safe/20 text-safe border-safe/50">Blocked</Badge>;
      case "Locked":
        return <Badge className="bg-threat-medium/20 text-threat-medium border-threat-medium/50">Locked</Badge>;
      case "Monitoring":
        return <Badge variant="outline" className="border-cyber-blue/50 text-cyber-blue">Monitoring</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getAttackPatternBadge = (pattern: string) => {
    const colors = {
      "Dictionary Attack": "bg-threat-high/20 text-threat-high border-threat-high/50",
      "Credential Stuffing": "bg-threat-medium/20 text-threat-medium border-threat-medium/50",
      "Brute Force": "bg-threat-low/20 text-threat-low border-threat-low/50",
      "Hybrid Attack": "bg-threat-high/20 text-threat-high border-threat-high/50"
    };
    
    return (
      <Badge className={colors[pattern as keyof typeof colors] || "bg-muted/20 text-muted-foreground"}>
        {pattern}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-grotesk font-bold text-foreground">Brute Force Detection</h1>
          <p className="text-muted-foreground">Monitor and prevent unauthorized login attempts</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{activeAttacks}</span>{" "}
            active attacks detected
          </div>
        </div>
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
              <Lock className="h-8 w-8 text-threat-medium" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">{blockedAccounts}</p>
                <p className="text-sm text-muted-foreground">Blocked/Locked</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <User className="h-8 w-8 text-cyber-blue" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">{totalAttempts}</p>
                <p className="text-sm text-muted-foreground">Total Attempts</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-safe" />
              <div>
                <p className="text-2xl font-grotesk font-bold text-foreground">99.9%</p>
                <p className="text-sm text-muted-foreground">Block Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Failed Attempts Chart */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk">Failed Login Attempts (24h)</CardTitle>
          <CardDescription className="text-muted-foreground">
            Hourly breakdown of brute force attack attempts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={attemptData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="hour" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }}
                formatter={(value) => [`${value} attempts`, 'Failed Logins']}
              />
              <Bar dataKey="attempts" fill="#EF4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Brute Force Attempts Table */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <CardTitle className="text-foreground font-grotesk">Brute Force Attempts</CardTitle>
          <CardDescription className="text-muted-foreground">
            Real-time monitoring of unauthorized login attempts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-muted/50">
                <TableHead className="text-muted-foreground font-medium">User Account</TableHead>
                <TableHead className="text-muted-foreground font-medium">Attempts</TableHead>
                <TableHead className="text-muted-foreground font-medium">Source IP</TableHead>
                <TableHead className="text-muted-foreground font-medium">Attack Pattern</TableHead>
                <TableHead className="text-muted-foreground font-medium">Status</TableHead>
                <TableHead className="text-muted-foreground font-medium">Last Attempt</TableHead>
                <TableHead className="text-muted-foreground font-medium">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {attempts.map((attempt) => (
                <TableRow key={attempt.id} className="border-border hover:bg-muted/20">
                  <TableCell className="font-medium text-foreground">{attempt.userAccount}</TableCell>
                  <TableCell className="text-foreground">
                    <span className={attempt.attempts > 100 ? "text-threat-high font-bold" : "text-foreground"}>
                      {attempt.attempts}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-foreground">{attempt.sourceIP}</span>
                      <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                        {attempt.country}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>{getAttackPatternBadge(attempt.attackPattern)}</TableCell>
                  <TableCell>{getStatusBadge(attempt.status)}</TableCell>
                  <TableCell className="text-muted-foreground">{attempt.lastAttempt}</TableCell>
                  <TableCell className="space-x-2">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedAttempt(attempt)}
                          className="border-border hover:bg-muted"
                        >
                          Details
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl bg-card border-border">
                        <DialogHeader>
                          <DialogTitle className="text-foreground font-grotesk">Attack Details</DialogTitle>
                          <DialogDescription className="text-muted-foreground">
                            Detailed analysis of brute force attempt
                          </DialogDescription>
                        </DialogHeader>
                        {selectedAttempt && (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Target Account</label>
                                <p className="text-foreground font-mono">{selectedAttempt.userAccount}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Attack Pattern</label>
                                <div className="mt-1">
                                  {getAttackPatternBadge(selectedAttempt.attackPattern)}
                                </div>
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Source IP</label>
                                <p className="text-foreground font-mono">{selectedAttempt.sourceIP}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Country</label>
                                <p className="text-foreground">{selectedAttempt.country}</p>
                              </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Total Attempts</label>
                                <p className="text-2xl font-bold text-threat-high">{selectedAttempt.attempts}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Status</label>
                                <div className="mt-1">
                                  {getStatusBadge(selectedAttempt.status)}
                                </div>
                              </div>
                            </div>

                            <div>
                              <label className="text-sm font-medium text-muted-foreground">Last Attempt</label>
                              <p className="text-foreground">{selectedAttempt.lastAttempt}</p>
                            </div>

                            <div className="pt-4 border-t border-border">
                              <h4 className="font-medium text-foreground mb-2">Recommended Actions</h4>
                              <ul className="text-sm text-muted-foreground space-y-1">
                                <li>• Enable account lockout after 5 failed attempts</li>
                                <li>• Implement IP-based rate limiting</li>
                                <li>• Require strong password policy</li>
                                <li>• Enable multi-factor authentication</li>
                              </ul>
                            </div>
                          </div>
                        )}
                      </DialogContent>
                    </Dialog>
                    
                    {attempt.status === "Active" && (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleLockAccount(attempt.id)}
                          className="border-threat-medium/50 text-threat-medium hover:bg-threat-medium/10"
                        >
                          Lock Account
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleBlockIP(attempt.id)}
                          className="border-destructive/50 text-destructive hover:bg-destructive/10"
                        >
                          Block IP
                        </Button>
                      </>
                    )}
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

export default BruteForce;