import { useEffect, useRef } from 'react';
import { useGLTF, useAnimations } from '@react-three/drei';
import * as THREE from 'three';
import { createClip } from '../utils/animationParser';
import { type Emotion, type AnimationJson } from '../types';

import idleJson from '../assets/idle.json';
import thinkingJson from '../assets/thinking_gesture.json';
import happyJson from '../assets/happy_gesture.json';
import sadJson from '../assets/sad_gesture.json';

interface AvatarProps {
  currentEmotion: Emotion;
}

export function Avatar({ currentEmotion }: AvatarProps) {
  const { scene } = useGLTF('/models/avatar.glb');
  const group = useRef<THREE.Group>(null);
  const { actions, mixer } = useAnimations<THREE.AnimationClip>(
    [],
    group
  ) as unknown as {
    actions: Record<string, THREE.AnimationAction | null>;
    mixer: THREE.AnimationMixer;
  };

  useEffect(() => {
    const clips = [
      createClip(idleJson as AnimationJson, 'idle'),
      createClip(thinkingJson as AnimationJson, 'thinking'),
      createClip(happyJson as AnimationJson, 'happy'),
      createClip(sadJson as AnimationJson, 'sad'),
    ];

    clips.forEach(clip => {
      const action = mixer.clipAction(clip, group.current!);
      actions[clip.name] = action;
    });

    if (actions.idle) {
      actions.idle.reset().fadeIn(0.5).play();
    }

    return () => {
      mixer.stopAllAction();
    };
  }, [mixer, actions]);

  useEffect(() => {
    if (!actions[currentEmotion]) return;

    const nextAction = actions[currentEmotion];
    nextAction.reset().fadeIn(0.5).play();

    return () => {
      nextAction.fadeOut(0.5);
    };
  }, [currentEmotion, actions]);

  return (
    <group ref={group} dispose={null}>
      <primitive object={scene} />
    </group>
  );
}
