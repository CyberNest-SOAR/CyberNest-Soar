import { Canvas } from "@react-three/fiber";
import { CyberShield } from "./CyberShield";
import { Button } from "@/components/ui/button";
import { ChevronRight, Play } from "lucide-react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export const Hero = () => {
  return (
    <section id="home" className="relative min-h-screen flex items-center pt-20 overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-0 left-0 w-full h-full -z-10">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="container mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center lg:text-left"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-[10px] sm:text-xs font-bold uppercase tracking-wider mb-6 mx-auto lg:mx-0">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            Next-Gen Security Orchestration
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold mb-6 leading-tight tracking-tighter">
            Protect Your Digital <span className="text-primary drop-shadow-[0_0_15px_rgba(59,130,246,0.3)]">Ecosystem</span> with AI.
          </h1>
          <p className="text-lg sm:text-xl text-muted-foreground mb-10 max-w-lg mx-auto lg:mx-0 leading-relaxed">
            CyberNest provides real-time threat detection, automated response, and advanced security orchestration for modern enterprises.
          </p>
          <div className="flex flex-wrap gap-4 justify-center lg:justify-start">
            <Link to="/login">
              <Button size="lg" className="btn-primary px-8 gap-2 h-14 rounded-2xl text-base shadow-xl shadow-primary/20">
                Get Started <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
            
          </div>
          
          
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="relative h-[400px] sm:h-[500px] lg:h-[600px] w-full"
        >
          <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
            <CyberShield />
          </Canvas>
          
          {/* Floating Stats Card - Hidden on small mobile */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1, duration: 0.5 }}
            className="absolute bottom-10 left-0 glass p-4 shadow-2xl border border-primary/20 max-w-[200px] hidden sm:block rounded-2xl backdrop-blur-2xl"
          >
            <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold mb-1">Real-time Events</p>
            <p className="text-2xl font-bold text-primary font-grotesk tracking-tighter">250K+</p>
            <div className="mt-2 h-1 w-full bg-muted rounded-full overflow-hidden">
              <motion.div 
                animate={{ width: ["0%", "75%", "60%", "75%"] }}
                transition={{ duration: 3, repeat: Infinity }}
                className="h-full bg-primary" 
              />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2, duration: 0.5 }}
            className="absolute top-10 right-0 glass p-4 shadow-2xl border border-accent/20 max-w-[180px] hidden sm:block rounded-2xl backdrop-blur-2xl"
          >
            <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold mb-1">Integrations</p>
            <p className="text-2xl font-bold text-accent font-grotesk tracking-tighter">12+</p>
            <div className="flex gap-1 mt-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-4 w-1.5 bg-accent rounded-full opacity-60 animate-bounce" style={{ animationDelay: `${i * 0.1}s` }} />
              ))}
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};
