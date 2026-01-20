import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/PageHeader";
import { Mail, Network, Lock, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import PhishingEmails from "./PhishingEmails";
import DDoSAttacks from "./DDoSAttacks";
import BruteForce from "./BruteForce";

const ThreatIntelligence = () => {
  const [activeTab, setActiveTab] = useState("phishing");
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Threat Intelligence"
        description="Unified threat detection and analysis across all attack vectors"
        breadcrumbs={[{ label: "Threat Intelligence" }]}
      />

      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search threats, IPs, emails..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-card border-border/50 focus:border-cyber-blue/50 focus:ring-cyber-blue/20 transition-all"
          />
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="inline-flex h-auto p-1 bg-card/50 border border-border/50 rounded-xl backdrop-blur-sm">
          <TabsTrigger
            value="phishing"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyber-blue/20 data-[state=active]:to-cyber-blue/10 data-[state=active]:text-cyber-blue data-[state=active]:border data-[state=active]:border-cyber-blue/30 data-[state=active]:shadow-[0_0_15px_rgba(59,130,246,0.15)] transition-all duration-300"
          >
            <Mail className="h-4 w-4" />
            <span className="hidden sm:inline">Phishing Emails</span>
            <span className="sm:hidden">Phishing</span>
          </TabsTrigger>
          <TabsTrigger
            value="ddos"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-threat-medium/20 data-[state=active]:to-threat-medium/10 data-[state=active]:text-threat-medium data-[state=active]:border data-[state=active]:border-threat-medium/30 data-[state=active]:shadow-[0_0_15px_rgba(251,146,60,0.15)] transition-all duration-300"
          >
            <Network className="h-4 w-4" />
            <span className="hidden sm:inline">DDoS Attacks</span>
            <span className="sm:hidden">DDoS</span>
          </TabsTrigger>
          <TabsTrigger
            value="bruteforce"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-threat-high/20 data-[state=active]:to-threat-high/10 data-[state=active]:text-threat-high data-[state=active]:border data-[state=active]:border-threat-high/30 data-[state=active]:shadow-[0_0_15px_rgba(239,68,68,0.15)] transition-all duration-300"
          >
            <Lock className="h-4 w-4" />
            <span className="hidden sm:inline">Brute Force</span>
            <span className="sm:hidden">Brute</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="phishing" className="mt-0 animate-in fade-in-50 duration-300">
          <PhishingEmails />
        </TabsContent>

        <TabsContent value="ddos" className="mt-0 animate-in fade-in-50 duration-300">
          <DDoSAttacks />
        </TabsContent>

        <TabsContent value="bruteforce" className="mt-0 animate-in fade-in-50 duration-300">
          <BruteForce />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ThreatIntelligence;
