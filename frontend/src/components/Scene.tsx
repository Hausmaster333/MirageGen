// === src/components/Scene.tsx ===
import { Environment } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { Avatar } from './Avatar';
import type { ChatResponse } from '../types';

interface SceneProps {
  lastResponse: ChatResponse | null;
  isThinking: boolean;
  onAnimationEnd?: () => void;
}

export function Scene({
  lastResponse,
  isThinking,
  onAnimationEnd,
}: SceneProps) {
  return (
    <div className="flex-1 relative min-h-0">
      <Canvas camera={{ position: [0, 0, 1.5], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <Environment preset="city" />
        <group position={[0, -1.6, 0]}>
          <Avatar
            lastResponse={lastResponse}
            isThinking={isThinking}
            onAnimationEnd={onAnimationEnd}
          />
        </group>
      </Canvas>
    </div>
  );
}
