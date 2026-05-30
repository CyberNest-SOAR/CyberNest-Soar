import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Eye, EyeOff, ArrowRight, CheckCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { z } from "zod";

export const emailSchema = z
  .string()
  .email("Invalid email address")
  .min(1, "Email is required");

export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
  .regex(/[a-z]/, "Password must contain at least one lowercase letter")
  .regex(/\d/, "Password must contain at least one number")
  .regex(/[!@#$%^&*]/, "Password must contain at least one special character (!@#$%^&*)");


import { motion, AnimatePresence } from "framer-motion";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"login" | "signup">("login");
  const { toast } = useToast();
  const navigate = useNavigate();

  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        navigate("/dashboard");
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        navigate("/dashboard");
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const validateEmail = (val: string) => {
    setEmail(val);
    try {
      emailSchema.parse(val);
      setEmailError("");
    } catch (err: any) {
      setEmailError(err.errors?.[0]?.message || "Invalid email");
    }
  };

  const validatePassword = (val: string) => {
    setPassword(val);
    if (activeTab === "signup") {
      try {
        passwordSchema.parse(val);
        setPasswordError("");
      } catch (err: any) {
        setPasswordError(err.errors?.[0]?.message || "Weak password");
      }
    } else {
      setPasswordError(val.length < 8 ? "Password too short" : "");
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (emailError || passwordError || !email || !password) {
      toast({ title: "Check inputs", description: "Please correct errors before proceeding", variant: "destructive" });
      return;
    }

    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);

    if (error) {
      toast({ title: "Login Failed", description: error.message, variant: "destructive" });
    } else {
      toast({ title: "Welcome back!", description: "Successfully signed in" });
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (emailError || passwordError || !email || !password || !fullName) {
      toast({ title: "Validation Error", description: "Please fill in all fields correctly", variant: "destructive" });
      return;
    }

    setLoading(true);
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: fullName }, emailRedirectTo: `${window.location.origin}/` },
    });
    setLoading(false);

    if (error) {
      toast({ title: "Signup Failed", description: error.message, variant: "destructive" });
    } else {
      toast({ title: "Account Created", description: "Please login with your new credentials." });
      setActiveTab("login");
      setPassword("");
    }
  };

  const features = [
    { title: "AI Threat Detection", desc: "Predictive analysis & pattern recognition" },
    { title: "Real-time Monitoring", desc: "Live dashboard with global telemetry" },
    { title: "Auto-Remediation", desc: "Self-healing security workflows" },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden p-4 sm:p-0">
      {/* Background Decor */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:60px_60px] opacity-[0.03]" />
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-primary/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] bg-accent/5 rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-6xl min-h-[90vh] md:h-[90vh] bg-card rounded-[2.5rem] border border-border/40 shadow-2xl flex flex-col md:flex-row overflow-hidden relative z-10">

      {/* Left Branding - Modern Sidebar Style */}
      <motion.div 
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        className="hidden lg:flex lg:w-[45%] p-16 flex-col justify-between relative border-r border-border/40 bg-card/20 backdrop-blur-3xl"
      >
        <div className="relative z-10">
          <Logo size="lg" />
        </div>

        <div className="relative z-10 space-y-10">
          <div className="space-y-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <h1 className="text-6xl font-black leading-[1.1] tracking-tighter uppercase italic">
                The Future of <br/>
                <span className="text-primary text-glow-primary">Cyber Defense.</span>
              </h1>
            </motion.div>
            <p className="text-xl text-muted-foreground leading-relaxed max-w-md">
              Secure your infrastructure with our enterprise-grade SOAR platform.
            </p>
          </div>

          <div className="grid gap-6">
            {features.map((f, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.1 }}
                className="flex items-start gap-4 p-4 rounded-2xl border border-border/40 hover:bg-primary/5 transition-colors group"
              >
                <div className="mt-1 w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_rgba(59,130,246,0.8)] group-hover:scale-150 transition-transform" />
                <div>
                  <h3 className="font-bold text-foreground">{f.title}</h3>
                  <p className="text-sm text-muted-foreground">{f.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-6 text-sm font-medium text-muted-foreground">
            <span>v4.2.0-STABLE</span>
            <div className="w-1 h-1 rounded-full bg-border" />
            <span>ENCRYPTED_OS_ACTIVE</span>
          </div>
        </div>
      </motion.div>

      {/* Right - Interactive Form Panel */}
      <div className="flex-1 flex flex-col items-center justify-center p-8 relative">
        <div className="absolute top-8 right-8 flex items-center gap-4">
          <ThemeToggle />
        </div>

        <motion.div 
          layout
          className="w-full max-w-[420px] space-y-8"
        >
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold tracking-tight">
              {activeTab === "login" ? "Welcome Back" : "Initialize Account"}
            </h2>
            <p className="text-muted-foreground">
              {activeTab === "login" ? "Enter credentials to access the core" : "Complete the authorization protocol"}
            </p>
          </div>

          <div className="glass-morphism p-2 rounded-[24px] border border-border/50 shadow-2xl bg-card/30">
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="w-full">
              <TabsList className="grid w-full grid-cols-2 bg-transparent p-1 h-14">
                <TabsTrigger 
                  value="login" 
                  className="rounded-2xl data-[state=active]:bg-background data-[state=active]:shadow-xl text-sm font-bold uppercase tracking-widest transition-all"
                >
                  Sign In
                </TabsTrigger>
                <TabsTrigger 
                  value="signup" 
                  className="rounded-2xl data-[state=active]:bg-background data-[state=active]:shadow-xl text-sm font-bold uppercase tracking-widest transition-all"
                >
                  Join Core
                </TabsTrigger>
              </TabsList>

              <div className="px-6 py-8">
                <AnimatePresence mode="wait">
                  {activeTab === "login" ? (
                    <motion.form 
                      key="login-form"
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      onSubmit={handleLogin} 
                      className="space-y-5"
                    >
                      <div className="space-y-1.5 group relative">
                        <Label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 ml-1">Access Identity</Label>
                        <div className="relative">
                          <Input
                            placeholder="operator@cybernest.io"
                            value={email}
                            onChange={(e) => validateEmail(e.target.value)}
                            className={`h-12 bg-background/50 border-border/60 focus:ring-primary/20 rounded-xl transition-all ${emailError ? "border-red-500/50" : "group-hover:border-primary/40"}`}
                          />
                        </div>
                        {emailError && <span className="text-[10px] text-red-500 font-bold ml-1">{emailError}</span>}
                      </div>

                      <div className="space-y-1.5 group relative">
                        <div className="flex justify-between items-center px-1">
                          <Label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">Passkey</Label>
                          <button type="button" className="text-[10px] font-bold uppercase tracking-widest text-primary hover:underline">Forgot?</button>
                        </div>
                        <div className="relative">
                          <Input
                            type={showPassword ? "text" : "password"}
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => validatePassword(e.target.value)}
                            className={`h-12 bg-background/50 border-border/60 pr-12 rounded-xl transition-all ${passwordError ? "border-red-500/50" : "group-hover:border-primary/40"}`}
                          />
                          <button
                            type="button"
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground/60 hover:text-primary transition-colors"
                            onClick={() => setShowPassword(!showPassword)}
                          >
                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                        {passwordError && <span className="text-[10px] text-red-500 font-bold ml-1">{passwordError}</span>}
                      </div>

                      <Button 
                        disabled={loading || !!emailError || !!passwordError || !email} 
                        className="w-full h-12 bg-primary hover:bg-primary/90 text-white font-bold rounded-xl shadow-lg shadow-primary/20 transition-all active:scale-[0.98]"
                      >
                        {loading ? <span className="animate-pulse">AUTHORIZING...</span> : "INITIATE SESSION"}
                      </Button>
                    </motion.form>
                  ) : (
                    <motion.form 
                      key="signup-form"
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      onSubmit={handleSignup} 
                      className="space-y-5"
                    >
                      <div className="space-y-1.5 group">
                        <Label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 ml-1">Operative Name</Label>
                        <Input
                          placeholder="John Maverick"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          className="h-12 bg-background/50 border-border/60 rounded-xl transition-all group-hover:border-primary/40"
                        />
                      </div>

                      <div className="space-y-1.5 group">
                        <Label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 ml-1">Identity Mail</Label>
                        <Input
                          placeholder="operator@cybernest.io"
                          value={email}
                          onChange={(e) => validateEmail(e.target.value)}
                          className={`h-12 bg-background/50 border-border/60 rounded-xl transition-all ${emailError ? "border-red-500/50" : "group-hover:border-primary/40"}`}
                        />
                        {emailError && <span className="text-[10px] text-red-500 font-bold ml-1">{emailError}</span>}
                      </div>

                      <div className="space-y-1.5 group">
                        <Label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 ml-1">Create Passkey</Label>
                        <div className="relative">
                          <Input
                            type={showPassword ? "text" : "password"}
                            placeholder="Min. 8 characters"
                            value={password}
                            onChange={(e) => validatePassword(e.target.value)}
                            className={`h-12 bg-background/50 border-border/60 pr-12 rounded-xl transition-all ${passwordError ? "border-red-500/50" : "group-hover:border-primary/40"}`}
                          />
                          <button
                            type="button"
                            className="absolute right-4 top-1/2 -translate-y-1/2"
                            onClick={() => setShowPassword(!showPassword)}
                          >
                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                        {passwordError && <span className="text-[10px] text-red-500 font-bold ml-1">{passwordError}</span>}
                      </div>

                      <Button 
                        disabled={loading || !!emailError || !!passwordError || !fullName}
                        className="w-full h-12 bg-primary hover:bg-primary/90 text-white font-bold rounded-xl shadow-lg shadow-primary/20 transition-all active:scale-[0.98]"
                      >
                        {loading ? <span className="animate-pulse">ENROLLING...</span> : "INITIALIZE OPERATIVE"}
                      </Button>
                    </motion.form>
                  )}
                </AnimatePresence>
              </div>
            </Tabs>
          </div>
          
          <div className="flex flex-col items-center gap-4 py-4">
            <div className="h-px w-24 bg-border" />
            <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">
              Secure Auth v4 // AES-256 Enabled
            </p>
          </div>
        </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Login;
