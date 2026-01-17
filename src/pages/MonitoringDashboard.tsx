import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Server, Globe, Mail, Plus, Trash2, Activity, AlertTriangle, Edit, Search, Filter, X } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

interface Endpoint {
  id: string;
  name: string;
  type: string;
  ip_address: string | null;
  status: string;
  last_seen: string;
}

interface MonitoredEmail {
  id: string;
  email: string;
  department: string | null;
  status: string;
  last_checked: string;
}

const MonitoringDashboard = () => {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [monitoredEmails, setMonitoredEmails] = useState<MonitoredEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [openEndpointDialog, setOpenEndpointDialog] = useState(false);
  const [openEmailDialog, setOpenEmailDialog] = useState(false);
  const [editingEndpoint, setEditingEndpoint] = useState<Endpoint | null>(null);
  const [editingEmail, setEditingEmail] = useState<MonitoredEmail | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const [newEndpoint, setNewEndpoint] = useState({
    name: "",
    type: "server",
    ip_address: "",
  });

  const [newEmail, setNewEmail] = useState({
    email: "",
    department: "",
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [endpointsRes, emailsRes] = await Promise.all([
        supabase.from("endpoints").select("*").order("created_at", { ascending: false }),
        supabase.from("monitored_emails").select("*").order("created_at", { ascending: false }),
      ]);

      if (endpointsRes.error) throw endpointsRes.error;
      if (emailsRes.error) throw emailsRes.error;

      setEndpoints(endpointsRes.data || []);
      setMonitoredEmails(emailsRes.data || []);
    } catch (error: any) {
      toast.error("Failed to load data", { description: error.message });
    } finally {
      setLoading(false);
    }
  };

  const handleAddEndpoint = async () => {
    if (!newEndpoint.name || !newEndpoint.type) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      const { error } = await supabase.from("endpoints").insert([newEndpoint]);
      if (error) throw error;

      toast.success("Endpoint added successfully");
      setNewEndpoint({ name: "", type: "server", ip_address: "" });
      setOpenEndpointDialog(false);
      fetchData();
    } catch (error: any) {
      toast.error(error.message);
    }
  };

  const handleEditEndpoint = async () => {
    if (!editingEndpoint) return;

    try {
      const { error } = await supabase
        .from("endpoints")
        .update({
          name: editingEndpoint.name,
          type: editingEndpoint.type,
          ip_address: editingEndpoint.ip_address,
        })
        .eq("id", editingEndpoint.id);

      if (error) throw error;

      toast.success("Endpoint updated successfully");
      setEditingEndpoint(null);
      fetchData();
    } catch (error: any) {
      toast.error(error.message);
    }
  };

  const handlePingEndpoint = (endpoint: Endpoint) => {
    toast.success(`Pinging ${endpoint.name}...`, {
      description: `IP: ${endpoint.ip_address || "No IP available"}`,
    });
  };

  const handleAddEmail = async () => {
    if (!newEmail.email) {
      toast.error("Please enter an email address");
      return;
    }

    try {
      const { error } = await supabase.from("monitored_emails").insert([newEmail]);
      if (error) throw error;

      toast.success("Email added to monitoring list");
      setNewEmail({ email: "", department: "" });
      setOpenEmailDialog(false);
      fetchData();
    } catch (error: any) {
      toast.error(error.message);
    }
  };

  const handleEditEmail = async () => {
    if (!editingEmail) return;

    try {
      const { error } = await supabase
        .from("monitored_emails")
        .update({
          email: editingEmail.email,
          department: editingEmail.department,
        })
        .eq("id", editingEmail.id);

      if (error) throw error;

      toast.success("Email updated successfully");
      setEditingEmail(null);
      fetchData();
    } catch (error: any) {
      toast.error(error.message);
    }
  };

  const handleDeleteEndpoint = async (id: string) => {
    try {
      const { error } = await supabase.from("endpoints").delete().eq("id", id);
      if (error) throw error;

      toast.success("Endpoint removed");
      fetchData();
    } catch (error: any) {
      toast.error(error.message);
    }
  };

  const handleDeleteEmail = async (id: string) => {
    try {
      const { error } = await supabase.from("monitored_emails").delete().eq("id", id);
      if (error) throw error;

      toast.success("Email removed from monitoring");
      fetchData();
    } catch (error: any) {
      toast.error(error.message);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500/20 text-green-400 border-green-500/50";
      case "warning":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/50";
      case "critical":
      case "compromised":
        return "bg-red-500/20 text-red-400 border-red-500/50";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/50";
    }
  };

  // Filtering logic
  const filteredEndpoints = endpoints.filter((endpoint) => {
    const matchesSearch = endpoint.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         endpoint.ip_address?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || endpoint.status === statusFilter;
    const matchesType = typeFilter === "all" || endpoint.type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const filteredEmails = monitoredEmails.filter((email) => {
    const matchesSearch = email.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         email.department?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || email.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const servers = filteredEndpoints.filter((e) => e.type === "server");
  const networkDevices = filteredEndpoints.filter((e) => e.type === "network_device");
  const activeEndpoints = endpoints.filter((e) => e.status === "active").length;
  const downEndpoints = endpoints.filter((e) => e.status === "critical" || e.status === "warning").length;
  const criticalAlerts = endpoints.filter((e) => e.status === "critical").length + monitoredEmails.filter((e) => e.status === "compromised").length;
  const openIncidents = Math.floor(Math.random() * 5);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-blue"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-grotesk font-bold text-foreground mb-2">
            Monitoring Dashboard
          </h1>
          <p className="text-muted-foreground">
            Monitor endpoints, servers, network devices, and company emails
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="gradient-card border-border/50 hover:border-cyber-blue/50 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Up Devices
            </CardTitle>
            <Activity className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{activeEndpoints}</div>
            <p className="text-xs text-muted-foreground mt-1">of {endpoints.length} total</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50 hover:border-red-500/50 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Down Devices
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{downEndpoints}</div>
            <p className="text-xs text-muted-foreground mt-1">requires attention</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50 hover:border-yellow-500/50 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              24h Alerts
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{criticalAlerts}</div>
            <p className="text-xs text-muted-foreground mt-1">last 24 hours</p>
          </CardContent>
        </Card>

        <Card className="gradient-card border-border/50 hover:border-cyber-blue/50 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Open Incidents
            </CardTitle>
            <Mail className="h-4 w-4 text-cyber-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{openIncidents}</div>
            <p className="text-xs text-muted-foreground mt-1">pending resolution</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="gradient-card border-border/50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, IP, or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="compromised">Compromised</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-full md:w-[180px]">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="server">Servers</SelectItem>
                <SelectItem value="network_device">Network Devices</SelectItem>
                <SelectItem value="endpoint">Endpoints</SelectItem>
              </SelectContent>
            </Select>
            {(searchQuery || statusFilter !== "all" || typeFilter !== "all") && (
              <Button
                variant="ghost"
                onClick={() => {
                  setSearchQuery("");
                  setStatusFilter("all");
                  setTypeFilter("all");
                }}
              >
                <X className="h-4 w-4 mr-2" />
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Servers Section */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-xl font-grotesk text-foreground flex items-center gap-2">
                <Server className="h-5 w-5 text-cyber-blue" />
                Servers
              </CardTitle>
              <CardDescription>{servers.length} servers being monitored</CardDescription>
            </div>
            <Dialog open={openEndpointDialog} onOpenChange={setOpenEndpointDialog}>
              <DialogTrigger asChild>
                <Button className="bg-gradient-cyber hover:opacity-90 text-white">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Device
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{editingEndpoint ? "Edit Device" : "Add New Device"}</DialogTitle>
                  <DialogDescription>
                    {editingEndpoint ? "Update device information" : "Add a new device or server to monitor"}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="endpoint-name">Name</Label>
                    <Input
                      id="endpoint-name"
                      placeholder="Server name or device"
                      value={editingEndpoint ? editingEndpoint.name : newEndpoint.name}
                      onChange={(e) =>
                        editingEndpoint
                          ? setEditingEndpoint({ ...editingEndpoint, name: e.target.value })
                          : setNewEndpoint({ ...newEndpoint, name: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="endpoint-type">Type</Label>
                    <Select
                      value={editingEndpoint ? editingEndpoint.type : newEndpoint.type}
                      onValueChange={(value) =>
                        editingEndpoint
                          ? setEditingEndpoint({ ...editingEndpoint, type: value })
                          : setNewEndpoint({ ...newEndpoint, type: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="server">Server</SelectItem>
                        <SelectItem value="network_device">Network Device</SelectItem>
                        <SelectItem value="endpoint">Endpoint</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="endpoint-ip">IP Address (optional)</Label>
                    <Input
                      id="endpoint-ip"
                      placeholder="192.168.1.1"
                      value={editingEndpoint ? editingEndpoint.ip_address || "" : newEndpoint.ip_address}
                      onChange={(e) =>
                        editingEndpoint
                          ? setEditingEndpoint({ ...editingEndpoint, ip_address: e.target.value })
                          : setNewEndpoint({ ...newEndpoint, ip_address: e.target.value })
                      }
                    />
                  </div>
                </div>
                <DialogFooter>
                  {editingEndpoint ? (
                    <>
                      <Button variant="outline" onClick={() => setEditingEndpoint(null)}>
                        Cancel
                      </Button>
                      <Button onClick={handleEditEndpoint}>Save Changes</Button>
                    </>
                  ) : (
                    <Button onClick={handleAddEndpoint}>Add Device</Button>
                  )}
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Device Name</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Seen</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {servers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No servers found
                  </TableCell>
                </TableRow>
              ) : (
                servers.map((server) => (
                  <TableRow key={server.id} className="hover:bg-accent/50">
                    <TableCell className="font-medium">{server.name}</TableCell>
                    <TableCell>{server.ip_address || "—"}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(server.status)}>{server.status}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(server.last_seen).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditingEndpoint(server);
                            setOpenEndpointDialog(true);
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handlePingEndpoint(server)}>
                          <Activity className="h-4 w-4 text-green-400" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteEndpoint(server.id)}>
                          <Trash2 className="h-4 w-4 text-red-400" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Network Devices Section */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-xl font-grotesk text-foreground flex items-center gap-2">
                <Globe className="h-5 w-5 text-cyber-blue" />
                Network Devices
              </CardTitle>
              <CardDescription>{networkDevices.length} network devices being monitored</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Device Name</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Seen</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {networkDevices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No network devices found
                  </TableCell>
                </TableRow>
              ) : (
                networkDevices.map((device) => (
                  <TableRow key={device.id} className="hover:bg-accent/50">
                    <TableCell className="font-medium">{device.name}</TableCell>
                    <TableCell>{device.ip_address || "—"}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(device.status)}>{device.status}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(device.last_seen).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditingEndpoint(device);
                            setOpenEndpointDialog(true);
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handlePingEndpoint(device)}>
                          <Activity className="h-4 w-4 text-green-400" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteEndpoint(device.id)}>
                          <Trash2 className="h-4 w-4 text-red-400" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Company Emails Section */}
      <Card className="gradient-card border-border/50">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-xl font-grotesk text-foreground flex items-center gap-2">
                <Mail className="h-5 w-5 text-cyber-blue" />
                Monitored Company Emails
              </CardTitle>
              <CardDescription>{filteredEmails.length} email accounts being monitored</CardDescription>
            </div>
            <Dialog open={openEmailDialog} onOpenChange={setOpenEmailDialog}>
              <DialogTrigger asChild>
                <Button className="bg-gradient-cyber hover:opacity-90 text-white">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Email
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{editingEmail ? "Edit Email" : "Add Company Email"}</DialogTitle>
                  <DialogDescription>
                    {editingEmail ? "Update email information" : "Add an email account to monitor for security"}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="email-address">Email Address</Label>
                    <Input
                      id="email-address"
                      type="email"
                      placeholder="user@company.com"
                      value={editingEmail ? editingEmail.email : newEmail.email}
                      onChange={(e) =>
                        editingEmail
                          ? setEditingEmail({ ...editingEmail, email: e.target.value })
                          : setNewEmail({ ...newEmail, email: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email-department">Department (optional)</Label>
                    <Input
                      id="email-department"
                      placeholder="IT, HR, Finance, etc."
                      value={editingEmail ? editingEmail.department || "" : newEmail.department}
                      onChange={(e) =>
                        editingEmail
                          ? setEditingEmail({ ...editingEmail, department: e.target.value })
                          : setNewEmail({ ...newEmail, department: e.target.value })
                      }
                    />
                  </div>
                </div>
                <DialogFooter>
                  {editingEmail ? (
                    <>
                      <Button variant="outline" onClick={() => setEditingEmail(null)}>
                        Cancel
                      </Button>
                      <Button onClick={handleEditEmail}>Save Changes</Button>
                    </>
                  ) : (
                    <Button onClick={handleAddEmail}>Add Email</Button>
                  )}
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email Address</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Checked</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEmails.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No emails found
                  </TableCell>
                </TableRow>
              ) : (
                filteredEmails.map((email) => (
                  <TableRow key={email.id} className="hover:bg-accent/50">
                    <TableCell className="font-medium">{email.email}</TableCell>
                    <TableCell>{email.department || "—"}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(email.status)}>{email.status}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(email.last_checked).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditingEmail(email);
                            setOpenEmailDialog(true);
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteEmail(email.id)}>
                          <Trash2 className="h-4 w-4 text-red-400" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Alert System */}
      {criticalAlerts > 0 && (
        <Card className="gradient-card border-red-500/50 bg-red-500/5">
          <CardHeader>
            <CardTitle className="text-xl font-grotesk text-foreground flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              Active Alerts
            </CardTitle>
            <CardDescription>Devices requiring immediate attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {endpoints
                .filter((e) => e.status === "critical")
                .map((endpoint) => (
                  <div
                    key={endpoint.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-red-500/30 bg-red-500/5"
                  >
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-5 w-5 text-red-400" />
                      <div>
                        <p className="font-medium text-foreground">{endpoint.name}</p>
                        <p className="text-sm text-muted-foreground">Device offline or unreachable</p>
                      </div>
                    </div>
                    <Badge className={getStatusColor(endpoint.status)}>{endpoint.status}</Badge>
                  </div>
                ))}
              {monitoredEmails
                .filter((e) => e.status === "compromised")
                .map((email) => (
                  <div
                    key={email.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-red-500/30 bg-red-500/5"
                  >
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-5 w-5 text-red-400" />
                      <div>
                        <p className="font-medium text-foreground">{email.email}</p>
                        <p className="text-sm text-muted-foreground">Potential security breach detected</p>
                      </div>
                    </div>
                    <Badge className={getStatusColor(email.status)}>{email.status}</Badge>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MonitoringDashboard;
