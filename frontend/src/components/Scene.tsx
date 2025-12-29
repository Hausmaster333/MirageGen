import { Environment } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { Avatar } from './Avatar';
import type { Emotion } from '../types';

export const Scene = ({ emotion }: { emotion: Emotion }) => {
  return (
    <div className="flex-1 relative min-h-0">
      <Canvas camera={{ position: [0, 0, 1.5], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <Environment preset="city" />
        <group position={[0, -1.6, 0]}>
          <Avatar currentEmotion={emotion} />
        </group>
      </Canvas>
    </div>
  );
};
