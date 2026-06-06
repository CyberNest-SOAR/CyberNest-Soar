import { ShieldCheck, Cpu, Globe, Database } from "lucide-react";
import { motion } from "framer-motion";

export const Solution = () => {
  const solutions = [
    {
      icon: <ShieldCheck className="h-6 w-6" />,
      title: "Automated SOAR",
      description: "Orchestrate your security stack with intelligent playbooks that react in milliseconds."
    },
    {
      icon: <Cpu className="h-6 w-6" />,
      title: "AI Threat Intelligence",
      description: "Identify patterns and predict attacks before they happen using our advanced ML models."
    },
    {
      icon: <Globe className="h-6 w-6" />,
      title: "Unified Visibility",
      description: "A single pane of glass for all your cloud, on-prem, and hybrid environments."
    },
    {
      icon: <Database className="h-6 w-6" />,
      title: "Incident Repository",
      description: "Comprehensive logging and forensic analysis for every single event in your network."
    }
  ];

  return (
    <section id="solution" className="py-24 relative overflow-hidden">
      <div className="absolute top-0 right-0 -z-10 translate-x-1/2 -translate-y-1/2">
        <div className="w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px]" />
      </div>

      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl lg:text-5xl font-bold mb-8">The CyberNest <span className="text-primary">Difference</span></h2>
            <p className="text-lg text-muted-foreground mb-12">
              We've built a platform that doesn't just monitor threats, but actively defends your infrastructure using state-of-the-art AI.
            </p>

            <div className="space-y-6">
              {solutions.map((sol, index) => (
                <div key={index} className="flex gap-6 p-6 rounded-2xl border border-border/40 hover:bg-primary/5 transition-colors duration-300">
                  <div className="flex-shrink-0 p-3 rounded-xl bg-primary/10 text-primary h-fit">
                    {sol.icon}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold mb-2">{sol.title}</h3>
                    <p className="text-muted-foreground">{sol.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="relative"
          >
            <div className="glass p-4 border border-border/40 rounded-3xl overflow-hidden shadow-2xl">
              <img 
                src="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=1000" 
                alt="Cyber Dashboard" 
                className="rounded-2xl"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent flex items-end p-8">
                <div className="glass p-6 w-full border border-primary/20">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-mono text-primary">SCANNING NETWORK...</span>
                    <span className="text-xs text-muted-foreground">98% COMPLETE</span>
                  </div>
                  <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary w-[98%] animate-pulse" />
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
