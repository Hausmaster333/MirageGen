import { useEffect, useRef, useState, useMemo } from 'react';
import { useGLTF, useAnimations } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { createClip } from '../utils/animationParser';
import type { StreamFrame, AnimationJson } from '../types';

import idleJson from '../assets/idle.json';
import thinkingJson from '../assets/thinking_gesture.json';

interface AvatarProps {
  streamData: StreamFrame | null;
  isThinking: boolean;
}

interface QueueItem {
  audioUrl: string;
  duration: number;
  blendshapes: Record<string, number>;
  motion?: Record<string, number[]>;
}

const BONE_MAPPING: Record<string, string> = {
  hips: 'Hips',
  spine: 'Spine',
  chest: 'Spine1',
  upper_chest: 'Spine2',
  neck: 'Neck',
  head: 'Head',

  right_shoulder: 'RightShoulder',
  right_arm: 'RightArm',
  right_forearm: 'RightForeArm',
  right_hand: 'RightHand',

  left_shoulder: 'LeftShoulder',
  left_arm: 'LeftArm',
  left_forearm: 'LeftForeArm',
  left_hand: 'LeftHand',

  right_up_leg: 'RightUpLeg',
  right_leg: 'RightLeg',
  right_foot: 'RightFoot',
  left_up_leg: 'LeftUpLeg',
  left_leg: 'LeftLeg',
  left_foot: 'LeftFoot',
};

const ARM_BONES = [
  'RightArm',
  'LeftArm',
  'RightForeArm',
  'LeftForeArm',
  'RightHand',
  'LeftHand',
];

export function Avatar({ streamData, isThinking }: AvatarProps) {
  const { scene, nodes } = useGLTF('/models/avatar_g.glb');
  const group = useRef<THREE.Group>(null);

  const audioRef = useRef<HTMLAudioElement>(new Audio());
  const queue = useRef<QueueItem[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);

  const targetVisemes = useRef<Record<string, number>>({});
  const targetRotations = useRef<Record<string, THREE.Quaternion>>({});

  const { actions, mixer } = useAnimations<THREE.AnimationClip>(
    [],
    group
  ) as any;

  useEffect(() => {
    const defaultClips = [
      createClip(idleJson as AnimationJson, 'idle'),
      createClip(thinkingJson as AnimationJson, 'thinking'),
    ];

    defaultClips.forEach(clip => {
      const action = mixer.clipAction(clip, group.current!);
      actions[clip.name] = action;
    });

    actions.idle?.reset().play();

    return () => mixer.stopAllAction();
  }, [mixer, actions]);

  useFrame(() => {
    const idleAction = actions.idle;
    const thinkingAction = actions.thinking;

    if (!idleAction) return;

    const targetIdleWeight = isPlaying ? 0.1 : 1.0;

    idleAction.weight = THREE.MathUtils.lerp(
      idleAction.weight,
      targetIdleWeight,
      0.1
    );

    if (isThinking && !isPlaying) {
      if (!thinkingAction?.isRunning()) {
        thinkingAction?.reset().fadeIn(0.5).play();
        idleAction.fadeOut(0.5);
      }
    } else {
      if (thinkingAction?.isRunning()) {
        thinkingAction?.fadeOut(0.5);
        idleAction.fadeIn(0.5);
      }
    }
  });

  useEffect(() => {
    if (!streamData) return;
    if (streamData.type !== 'frame') return;

    const motionData = streamData.motion;
    const blendshapesData = streamData.blendshapes;

    if (streamData.audio_chunk) {
      const blob = b64toBlob(streamData.audio_chunk, 'audio/wav');
      const url = URL.createObjectURL(blob);

      const item: QueueItem = {
        audioUrl: url,
        duration: 0,
        blendshapes: blendshapesData || {},
        motion: motionData,
      };

      queue.current.push(item);

      if (!isPlaying && audioRef.current.paused) {
        playNext();
      }
    }
  }, [streamData]);

  const playNext = async () => {
    if (queue.current.length === 0) {
      setIsPlaying(false);

      targetVisemes.current = {};
      return;
    }

    setIsPlaying(true);
    const item = queue.current.shift()!;

    audioRef.current.src = item.audioUrl;

    // Blendshapes (Visemes)
    if (item.blendshapes) {
      targetVisemes.current = item.blendshapes;
    }

    // Motion
    if (item.motion) {
      Object.entries(item.motion).forEach(([boneName, quatArray]) => {
        const mappedName = BONE_MAPPING[boneName] || boneName;

        const q = new THREE.Quaternion(
          quatArray[0],
          quatArray[1],
          quatArray[2],
          quatArray[3]
        );
        targetRotations.current[mappedName] = q;
      });
    }

    try {
      await audioRef.current.play();
    } catch (e) {
      console.error('Play error', e);
      playNext();
    }
  };

  useEffect(() => {
    const audio = audioRef.current;
    const handleEnded = () => {
      URL.revokeObjectURL(audio.src);
      playNext();
    };
    audio.addEventListener('ended', handleEnded);
    return () => audio.removeEventListener('ended', handleEnded);
  }, []);

  useFrame((state, delta) => {
    // Анимация лица (Blendshapes)
    const headMesh = (nodes.Wolf3D_Head ||
      nodes.Wolf3D_Avatar) as THREE.SkinnedMesh;
    if (headMesh?.morphTargetDictionary && headMesh?.morphTargetInfluences) {
      if (isPlaying) {
        Object.entries(targetVisemes.current).forEach(([shape, value]) => {
          const idx = headMesh.morphTargetDictionary![shape];
          if (idx !== undefined) {
            headMesh.morphTargetInfluences![idx] = THREE.MathUtils.lerp(
              headMesh.morphTargetInfluences![idx],
              value,
              delta * 12
            );
          }
        });
      } else {
        for (let i = 0; i < headMesh.morphTargetInfluences.length; i++) {
          if (headMesh.morphTargetInfluences[i] > 0.01) {
            headMesh.morphTargetInfluences[i] = THREE.MathUtils.lerp(
              headMesh.morphTargetInfluences[i],
              0,
              delta * 8
            );
          }
        }
      }
    }

    if (isPlaying && nodes) {
      Object.entries(targetRotations.current).forEach(
        ([boneName, targetQuat]) => {
          const bone = nodes[boneName] as THREE.Bone;
          if (bone) {
            bone.quaternion.slerp(targetQuat, delta * 8);
          }
        }
      );
    } else if (!isPlaying && nodes) {
      Object.keys(targetRotations.current).forEach(boneName => {
        const bone = nodes[boneName] as THREE.Bone;
        if (bone) {
          const identityQuat = new THREE.Quaternion(0, 0, 0, 1);

          bone.quaternion.slerp(identityQuat, delta * 5);
        }
      });
    }
  });

  return (
    <group ref={group} dispose={null}>
      <primitive object={scene} />
    </group>
  );
}

function b64toBlob(b64Data: string, contentType = '', sliceSize = 512) {
  const byteCharacters = atob(b64Data);
  const byteArrays = [];
  for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
    const slice = byteCharacters.slice(offset, offset + sliceSize);
    const byteNumbers = new Array(slice.length);
    for (let i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    byteArrays.push(byteArray);
  }
  return new Blob(byteArrays, { type: contentType });
}
