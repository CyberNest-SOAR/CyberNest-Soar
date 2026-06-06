import { AlertTriangle, ShieldAlert, Zap, Lock } from "lucide-react";
import { motion } from "framer-motion";

export const Problem = () => {
  const problems = [
    {
      icon: <ShieldAlert className="h-8 w-8 text-critical" />,
      title: "Complexity Overload",
      description: "Modern security stacks are fragmented, leading to alert fatigue and missed threats."
    },
    {
      icon: <Zap className="h-8 w-8 text-warning" />,
      title: "Slow Response Times",
      description: "Manual incident response is too slow to combat automated, high-speed attacks."
    },
    {
      icon: <Lock className="h-8 w-8 text-primary" />,
      title: "Visibility Gaps",
      description: "Blind spots in your network infrastructure leave you vulnerable to lateral movement."
    },
    {
      icon: <AlertTriangle className="h-8 w-8 text-destructive" />,
      title: "Skill Shortage",
      description: "The global cybersecurity talent gap makes it harder to find and retain experts."
    }
  ];

  return (
    <section id="problem" className="py-24 bg-background-subtle/50">
      <div className="container mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl lg:text-5xl font-bold mb-6">The Security <span className="text-critical">Challenge</span></h2>
          <p className="text-lg text-muted-foreground">
            Current security operations are struggling to keep up with the evolving threat landscape.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {problems.map((prob, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="glass-morphism p-10 border border-border/40 hover:border-primary/50 transition-all duration-500 group relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 p-4 opacity-[0.05] group-hover:scale-150 transition-transform duration-700">
                {prob.icon}
              </div>
              <div className="mb-8 p-4 rounded-2xl bg-primary/10 border border-primary/20 w-fit group-hover:bg-primary group-hover:text-white transition-all duration-500 shadow-xl shadow-primary/5">
                {prob.icon}
              </div>
              <h3 className="text-2xl font-black uppercase tracking-tighter mb-4 font-grotesk">{prob.title}</h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                {prob.description}
              </p>
              
              <div className="mt-8 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                Analyze Vector <Zap className="h-3 w-3 fill-current" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
