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
import Logo from "../logts-nobg.png";
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


const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"login" | "signup">("login");
  const { toast } = useToast();
  const navigate = useNavigate();

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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password) {
      toast({
        title: "Validation Error",
        description: "Please enter both email and password",
        variant: "destructive",
      });
      return;
    }

    try {
      emailSchema.parse(email);
    } catch (error: any) {
      toast({
        title: "Invalid Email",
        description: error.errors?.[0]?.message || "Please enter a valid email address",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      toast({
        title: "Login Failed",
        description: error.message,
        variant: "destructive",
      });
    } else {
      toast({
        title: "Welcome back!",
        description: "Successfully signed in to CyberNest-SOAR",
      });
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password || !fullName) {
      toast({
        title: "Validation Error",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      return;
    }

    try {
      emailSchema.parse(email);
    } catch (error: any) {
      toast({
        title: "Invalid Email",
        description: error.errors?.[0]?.message || "Please enter a valid email address",
        variant: "destructive",
      });
      return;
    }

    try {
      passwordSchema.parse(password);
    } catch (error: any) {
      toast({
        title: "Weak Password",
        description: error.errors?.[0]?.message || "Password does not meet security requirements",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
        emailRedirectTo: `${window.location.origin}/`,
      },
    });

    setLoading(false);

    if (error) {
      toast({
        title: "Signup Failed",
        description: error.message,
        variant: "destructive",
      });
    } else {
      toast({
        title: "Account Created",
        description: "Your account has been created. Please login.",
      });
      setActiveTab("login");
      setPassword("");
    }
  };

  const features = [
    "AI-powered threat detection",
    "Real-time security monitoring",
    "Automated incident response",
    "Comprehensive threat intelligence",
  ];

  return (
    <div className="min-h-screen flex bg-background">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-gradient-to-br from-card via-card to-background p-12 flex-col justify-between overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-1/4 -left-1/4 w-1/2 h-1/2 bg-cyber-blue/5 rounded-full blur-3xl" />
          <div className="absolute -bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-cyber-green/5 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 border border-border/20 rounded-full" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] border border-border/10 rounded-full" />
        </div>

        {/* Left Panel Logo */}
        <div className="relative z-10">
          <img src={Logo} alt="CyberNest-SOAR Logo" className="h-12 w-auto" />
        </div>

        {/* Mobile Logo */}
        <div className="lg:hidden flex justify-center">
          <img src={Logo} alt="CyberNest-SOAR Logo" className="h-12 w-auto" />
        </div>


        <div className="relative z-10 space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl font-grotesk font-bold text-foreground leading-tight">
              Enterprise Security
              <br />
              <span className="bg-gradient-to-r from-cyber-blue to-cyber-green bg-clip-text text-transparent">
                Operations Center
              </span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-md">
              Advanced threat detection and automated response platform for modern security teams.
            </p>
          </div>

          <div className="space-y-3">
            {features.map((feature, index) => (
              <div key={index} className="flex items-center gap-3 text-muted-foreground">
                <div className="h-5 w-5 rounded-full bg-cyber-blue/10 flex items-center justify-center">
                  <CheckCircle className="h-3 w-3 text-cyber-blue" />
                </div>
                <span className="text-sm">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 text-sm text-muted-foreground">
          © 2024 CyberNest-SOAR. All rights reserved.
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile Logo */}
          <div className="lg:hidden flex justify-center">
            <img src={Logo} alt="CyberNest-SOAR Logo" className="h-12 w-auto" />
          </div>

          {/* Theme Toggle */}
          <div className="absolute top-4 right-4">
            <ThemeToggle />
          </div>

          <div className="text-center lg:text-left space-y-2">
            <h2 className="text-2xl font-grotesk font-bold text-foreground">
              {activeTab === "login" ? "Welcome back" : "Create account"}
            </h2>
            <p className="text-muted-foreground">
              {activeTab === "login"
                ? "Enter your credentials to access the dashboard"
                : "Fill in your details to get started"}
            </p>
          </div>

          <Card className="border-border/50 shadow-lg bg-card/50 backdrop-blur-sm">
            <CardContent className="pt-6">
              <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "login" | "signup")}>
                <TabsList className="grid w-full grid-cols-2 mb-6 bg-muted/50">
                  <TabsTrigger
                    value="login"
                    className="data-[state=active]:bg-background data-[state=active]:shadow-sm"
                  >
                    Sign In
                  </TabsTrigger>
                  <TabsTrigger
                    value="signup"
                    className="data-[state=active]:bg-background data-[state=active]:shadow-sm"
                  >
                    Sign Up
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="login" className="space-y-4">
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-email" className="text-sm font-medium">
                        Email Address
                      </Label>
                      <Input
                        id="login-email"
                        type="email"
                        placeholder="you@company.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="h-11 bg-background border-border focus:border-cyber-blue focus:ring-1 focus:ring-cyber-blue/20 transition-all"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="login-password" className="text-sm font-medium">
                        Password
                      </Label>
                      <div className="relative">
                        <Input
                          id="login-password"
                          type={showPassword ? "text" : "password"}
                          placeholder="Enter your password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          className="h-11 bg-background border-border focus:border-cyber-blue focus:ring-1 focus:ring-cyber-blue/20 pr-10 transition-all"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <Button
                      type="submit"
                      className="w-full h-11 bg-gradient-to-r from-cyber-blue to-primary hover:opacity-90 text-white font-medium transition-all duration-200"
                      disabled={loading}
                    >
                      {loading ? (
                        <span className="flex items-center gap-2">
                          <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Signing in...
                        </span>
                      ) : (
                        <span className="flex items-center gap-2">
                          Access Dashboard
                          <ArrowRight className="h-4 w-4" />
                        </span>
                      )}
                    </Button>
                  </form>
                </TabsContent>

                <TabsContent value="signup" className="space-y-4">
                  <form onSubmit={handleSignup} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="signup-name" className="text-sm font-medium">
                        Full Name
                      </Label>
                      <Input
                        id="signup-name"
                        type="text"
                        placeholder="John Doe"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        className="h-11 bg-background border-border focus:border-cyber-blue focus:ring-1 focus:ring-cyber-blue/20 transition-all"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="signup-email" className="text-sm font-medium">
                        Email Address
                      </Label>
                      <Input
                        id="signup-email"
                        type="email"
                        placeholder="you@company.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="h-11 bg-background border-border focus:border-cyber-blue focus:ring-1 focus:ring-cyber-blue/20 transition-all"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="signup-password" className="text-sm font-medium">
                        Password
                      </Label>
                      <div className="relative">
                        <Input
                          id="signup-password"
                          type={showPassword ? "text" : "password"}
                          placeholder="Min 8 chars, mixed case, number, symbol"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          className="h-11 bg-background border-border focus:border-cyber-blue focus:ring-1 focus:ring-cyber-blue/20 pr-10 transition-all"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <Button
                      type="submit"
                      className="w-full h-11 bg-gradient-to-r from-cyber-blue to-primary hover:opacity-90 text-white font-medium transition-all duration-200"
                      disabled={loading}
                    >
                      {loading ? (
                        <span className="flex items-center gap-2">
                          <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Creating account...
                        </span>
                      ) : (
                        <span className="flex items-center gap-2">
                          Create Account
                          <ArrowRight className="h-4 w-4" />
                        </span>
                      )}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          <p className="text-center text-sm text-muted-foreground lg:hidden">
            © 2024 CyberNest-SOAR
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
