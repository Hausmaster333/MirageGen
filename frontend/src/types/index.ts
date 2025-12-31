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

export interface AudioSegmentResponse {
  audio_bytes_base64: string;
  sample_rate: number;
  format: 'wav' | 'mp3';
  duration: number;
}

export interface BlendshapeFrame {
  timestamp: number;
  mouth_shapes: Record<string, number>;
}

export interface BlendshapeWeights {
  frames: BlendshapeFrame[];
  fps: number;
  duration: number;
}

export interface MotionKeyframe {
  timestamp: number;
  bone_rotations: Record<string, [number, number, number, number]>;
  bone_positions: Record<string, [number, number, number]>;
}

export interface MotionKeyframes {
  keyframes: MotionKeyframe[];
  emotion: Emotion;
  duration: number;
}

export interface ChatResponse {
  full_text: string;
  audio: AudioSegmentResponse;
  blendshapes: BlendshapeWeights;
  motion: MotionKeyframes;
  processing_time: number;
}