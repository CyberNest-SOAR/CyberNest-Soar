import { motion } from "framer-motion";

export const HowItWorks = () => {
  const steps = [
    {
      number: "01",
      title: "Deploy & Integrate",
      description: "Quickly connect your existing security tools through our pre-built integrations."
    },
    {
      number: "02",
      title: "Monitor & Detect",
      description: "Our AI engine analyzes millions of events per second to identify suspicious activities."
    },
    {
      number: "03",
      title: "Automated Response",
      description: "Pre-defined playbooks execute countermeasures instantly when a threat is confirmed."
    },
    {
      number: "04",
      title: "Refine & Report",
      description: "Continuously improve your security posture with detailed analytics and insights."
    }
  ];

  return (
    <section id="how-it-works" className="py-24 bg-background-subtle/30 overflow-hidden">
      <div className="container mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <h2 className="text-3xl lg:text-5xl font-bold mb-6">How It <span className="text-primary">Works</span></h2>
          <p className="text-lg text-muted-foreground">
            A seamless four-step process to secure your enterprise.
          </p>
        </div>

        <div className="relative">
          {/* Connector Line */}
          <div className="absolute top-1/2 left-0 w-full h-px bg-border/40 hidden lg:block -translate-y-1/2" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="relative z-10 text-center"
              >
                <div className="w-16 h-16 rounded-2xl bg-background border-2 border-primary/30 flex items-center justify-center mx-auto mb-8 text-2xl font-bold text-primary glass group-hover:scale-110 transition-transform duration-300">
                  {step.number}
                </div>
                <h3 className="text-xl font-bold mb-4">{step.title}</h3>
                <p className="text-muted-foreground">{step.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
