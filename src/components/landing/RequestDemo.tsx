import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";
import { Send, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";

export const RequestDemo = () => {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [workEmail, setWorkEmail] = useState("");
  const [company, setCompany] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus("idle");

    const payload = {
      name: `${firstName} ${lastName}`,
      email: workEmail,
      company: company,
      message: "Request Demo Submission",
    };

    try {
      const response = await fetch("http://localhost:5000/api/request-demo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (data.success) {
        setStatus("success");
        toast.success("Request sent successfully!");
        // Reset form
        setFirstName("");
        setLastName("");
        setWorkEmail("");
        setCompany("");
      } else {
        throw new Error(data.message || "Failed to send request");
      }
    } catch (error) {
      console.error("Submission Error:", error);
      setStatus("error");
      toast.error("Failed to send request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="request-demo" className="py-24">
      <div className="container mx-auto px-6">
        <div className="glass p-8 lg:p-16 border border-primary/20 rounded-[40px] overflow-hidden relative">
          {/* Decor */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-[80px] -mr-32 -mt-32" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-accent/10 rounded-full blur-[80px] -ml-32 -mb-32" />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center relative z-10">
            <div>
              <h2 className="text-3xl lg:text-5xl font-bold mb-6">Ready to <span className="text-primary">Evolve</span> Your Security?</h2>
              <p className="text-lg text-muted-foreground mb-8">
                Join hundreds of industry leaders who trust CyberNest to protect their most valuable assets. Request a personalized demo today.
              </p>

              <ul className="space-y-4 mb-8">
                {["Personalized Platform Walkthrough", "Security Posture Assessment", "Custom ROI Analysis"].map((item, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center">
                      <div className="h-2 w-2 rounded-full bg-primary" />
                    </div>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="bg-background/50 backdrop-blur-sm p-8 rounded-3xl border border-border/40 shadow-2xl relative overflow-hidden"
            >
              {status === "success" ? (
                <div className="py-12 flex flex-col items-center text-center animate-scale-in">
                  <div className="h-20 w-20 rounded-full bg-green-500/20 flex items-center justify-center mb-6">
                    <CheckCircle2 className="h-10 w-10 text-green-500" />
                  </div>
                  <h3 className="text-2xl font-bold mb-2">Request Received!</h3>
                  <p className="text-muted-foreground mb-8">Our security team will reach out to you shortly to schedule your personalized walkthrough.</p>
                  <Button variant="outline" onClick={() => setStatus("idle")}>Send Another Request</Button>
                </div>
              ) : (
                <form className="space-y-4" onSubmit={handleSubmit}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">First Name</label>
                      <Input 
                        required
                        placeholder="John" 
                        className="bg-background/80" 
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        disabled={loading}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Last Name</label>
                      <Input 
                        required
                        placeholder="Doe" 
                        className="bg-background/80" 
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        disabled={loading}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Work Email</label>
                    <Input 
                      required
                      type="email" 
                      placeholder="john@company.com" 
                      className="bg-background/80" 
                      value={workEmail}
                      onChange={(e) => setWorkEmail(e.target.value)}
                      disabled={loading}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Company</label>
                    <Input 
                      required
                      placeholder="Acme Inc." 
                      className="bg-background/80" 
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      disabled={loading}
                    />
                  </div>

                  {status === "error" && (
                    <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-xs flex items-center gap-2 border border-destructive/20 animate-slide-left">
                      <AlertCircle className="h-4 w-4" />
                      Something went wrong. Please try again or contact support.
                    </div>
                  )}

                  <Button 
                    type="submit"
                    disabled={loading}
                    className="w-full btn-primary h-12 text-lg gap-2 mt-4 relative overflow-hidden group"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        Sending Request...
                      </>
                    ) : (
                      <>
                        Request Demo <Send className="h-4 w-4 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                      </>
                    )}
                  </Button>
                  <p className="text-center text-[10px] text-muted-foreground mt-4 uppercase tracking-widest font-bold opacity-60">
                    Secured by CyberNest Encryption
                  </p>
                </form>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
};
