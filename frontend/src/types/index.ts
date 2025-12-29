export type Emotion = 'idle' | 'thinking' | 'happy' | 'sad';

export interface BoneRotations {
  [key: string]: number[];
}

export interface Keyframe {
  timestamp: number;
  bone_rotations: BoneRotations;
  bone_positions?: Record<string, number[]>;
}

export interface AnimationJson {
  keyframes: Keyframe[];
  emotion: string;
  duration: number;
}

export interface Message {
  text: string;
  sender: 'user' | 'bot';
}
