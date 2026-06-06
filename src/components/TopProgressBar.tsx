import { motion, useScroll, useSpring } from "framer-motion";
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

export const TopProgressBar = () => {
  const [visible, setVisible] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setVisible(true);
    const timeout = setTimeout(() => setVisible(false), 600);
    return () => clearTimeout(timeout);
  }, [location]);

  if (!visible) return null;

  return (
    <motion.div
      initial={{ width: "0%", opacity: 1 }}
      animate={{ width: "100%", opacity: 0 }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      className="fixed top-0 left-0 h-[2px] bg-primary z-[9999] shadow-[0_0_8px_rgba(59,130,246,0.8)]"
    />
  );
};
