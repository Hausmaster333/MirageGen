import { Environment } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { Avatar } from './Avatar';
import type { StreamFrame } from '../types';

interface SceneProps {
  streamData: StreamFrame | null;
  isThinking: boolean;
}

export function Scene({ streamData, isThinking }: SceneProps) {
  return (
    <div className="flex-1 relative min-h-0">
      <Canvas camera={{ position: [0, 0, 1.5], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <Environment preset="city" />
        <group position={[0, -1.6, 0]}>
          {/* Передаем потоковые данные в Аватар */}
          <Avatar streamData={streamData} isThinking={isThinking} />
        </group>
      </Canvas>
    </div>
  );
}
