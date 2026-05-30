import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial, Sphere, MeshWobbleMaterial, Torus, Octahedron } from "@react-three/drei";
import * as THREE from "three";

export const CyberShield = () => {
  const groupRef = useRef<THREE.Group>(null);
  const coreRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.getElapsedTime() * 0.3;
      groupRef.current.rotation.z = Math.sin(state.clock.getElapsedTime() * 0.2) * 0.1;
    }
    if (coreRef.current) {
      coreRef.current.rotation.x = state.clock.getElapsedTime() * 1;
      coreRef.current.rotation.y = state.clock.getElapsedTime() * 1;
    }
  });

  return (
    <group ref={groupRef}>
      <Float speed={3} rotationIntensity={1} floatIntensity={1}>
        {/* Central Core */}
        <mesh ref={coreRef}>
          <octahedronGeometry args={[1.5, 2]} />
          <meshStandardMaterial 
            color="#3b82f6" 
            wireframe 
            emissive="#3b82f6"
            emissiveIntensity={4}
          />
        </mesh>
        
        {/* Distorted Internal Pulse */}
        <Sphere args={[1, 64, 64]}>
          <MeshDistortMaterial
            color="#60a5fa"
            speed={4}
            distort={0.6}
            radius={1}
            emissive="#1e40af"
            emissiveIntensity={2}
          />
        </Sphere>

        {/* Orbiting Rings */}
        <group rotation={[Math.PI / 2, 0, 0]}>
          <Torus args={[2.5, 0.03, 16, 100]}>
            <meshStandardMaterial color="#3b82f6" emissive="#3b82f6" emissiveIntensity={10} transparent opacity={0.8} />
          </Torus>
        </group>

        <group rotation={[Math.PI / 3, Math.PI / 4, 0]}>
          <Torus args={[3, 0.01, 16, 100]}>
            <meshStandardMaterial color="#60a5fa" emissive="#60a5fa" emissiveIntensity={5} transparent opacity={0.5} />
          </Torus>
        </group>

        <group rotation={[-Math.PI / 4, -Math.PI / 6, 0]}>
          <Torus args={[3.5, 0.005, 16, 100]}>
            <meshStandardMaterial color="#93c5fd" emissive="#93c5fd" emissiveIntensity={3} transparent opacity={0.3} />
          </Torus>
        </group>

        {/* Outer Shield Shell */}
        <Octahedron args={[4, 0]}>
          <meshStandardMaterial 
            color="#3b82f6" 
            wireframe 
            transparent 
            opacity={0.05} 
            emissive="#3b82f6" 
            emissiveIntensity={0.5} 
          />
        </Octahedron>
      </Float>

      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={2} color="#3b82f6" />
      <pointLight position={[-10, -10, -10]} intensity={1} color="#60a5fa" />
      <spotLight position={[0, 10, 0]} angle={0.3} penumbra={1} intensity={2} color="#3b82f6" castShadow />
    </group>
  );
};
