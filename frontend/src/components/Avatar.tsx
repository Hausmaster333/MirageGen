import { useEffect, useRef } from 'react';
import { useGLTF, useAnimations } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { createClip } from '../utils/animationParser';
import type { ChatResponse, AnimationJson } from '../types';

import idleJson from '../assets/idle.json';
import thinkingJson from '../assets/thinking_gesture.json';

interface AvatarProps {
  lastResponse: ChatResponse | null;
  isThinking: boolean;
  onAnimationEnd?: () => void;
}

export function Avatar({
  lastResponse,
  isThinking,
  onAnimationEnd,
}: AvatarProps) {
  const { scene, nodes } = useGLTF('/models/avatar.glb'); // nodes нужны для morph targets
  const group = useRef<THREE.Group>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const { actions, mixer } = useAnimations<THREE.AnimationClip>(
    [],
    group
  ) as any;

  // 1. Создаем дефолтные клипы (Idle, Thinking)
  useEffect(() => {
    const defaultClips = [
      createClip(idleJson as AnimationJson, 'idle'),
      createClip(thinkingJson as AnimationJson, 'thinking'),
    ];

    defaultClips.forEach(clip => {
      const action = mixer.clipAction(clip, group.current!);
      actions[clip.name] = action;
    });

    // Запускаем Idle по умолчанию
    actions.idle?.reset().play();

    return () => mixer.stopAllAction();
  }, [mixer, actions]);

  // 2. Управление состояниями (Idle / Thinking)
  useEffect(() => {
    if (lastResponse) return; // Если есть ответ, мы играем его анимацию, игнорируем это

    const fadeDuration = 0.5;

    if (isThinking) {
      actions.idle?.fadeOut(fadeDuration);
      actions.thinking?.reset().fadeIn(fadeDuration).play();
    } else {
      actions.thinking?.fadeOut(fadeDuration);
      actions.idle?.reset().fadeIn(fadeDuration).play();
    }
  }, [isThinking, lastResponse, actions]);

  // 3. Обработка ОТВЕТА (ChatResponse)
  useEffect(() => {
    if (!lastResponse) return;

    // A. Создаем клип для скелетной анимации из ответа
    // Нам нужно привести MotionKeyframes к формату AnimationJson для нашего парсера
    const motionJson: AnimationJson = {
      keyframes: lastResponse.motion.keyframes.map(k => ({
        timestamp: k.timestamp,
        bone_rotations: k.bone_rotations as any, // Приведение типов если нужно
        bone_positions: k.bone_positions as any,
      })),
      emotion: lastResponse.motion.emotion,
      duration: lastResponse.motion.duration,
    };

    const clipName = `response-${Date.now()}`;
    const clip = createClip(motionJson, clipName);

    // Останавливаем текущие (idle/thinking)
    actions.idle?.fadeOut(0.5);
    actions.thinking?.fadeOut(0.5);

    // Запускаем новую эмоцию
    const action = mixer.clipAction(clip, group.current!);
    actions[clipName] = action;

    // Ставим LoopOnce (один раз), а потом clamp (застыть) или вернуться в idle
    action.setLoop(THREE.LoopOnce, 1);
    action.clampWhenFinished = true;
    action.reset().fadeIn(0.2).play();

    // Слушаем окончание анимации
    const onFinished = (e: any) => {
      if (e.action === action) {
        mixer.removeEventListener('finished', onFinished);
        action.fadeOut(0.5);
        actions.idle?.reset().fadeIn(0.5).play();
        if (onAnimationEnd) onAnimationEnd();
      }
    };
    mixer.addEventListener('finished', onFinished);

    // B. Запускаем Аудио
    if (lastResponse.audio.audio_bytes_base64) {
      const audioSrc = `data:audio/${lastResponse.audio.format};base64,${lastResponse.audio.audio_bytes_base64}`;
      if (!audioRef.current) audioRef.current = new Audio();

      audioRef.current.src = audioSrc;
      audioRef.current.play().catch(e => console.error('Audio play error', e));
    }

    // Cleanup при смене ответа
    return () => {
      action.stop();
      mixer.removeEventListener('finished', onFinished);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    };
  }, [lastResponse, mixer, actions]);

  // 4. LIP SYNC (Анимация рта в useFrame)
  useFrame(() => {
    if (!lastResponse || !audioRef.current || audioRef.current.paused) {
      // Сброс рта в нейтраль, если молчим
      // (Тут можно добавить плавный lerp к 0)
      return;
    }

    const currentTime = audioRef.current.currentTime;

    // Находим текущий фрейм blendshapes
    // Это простой линейный поиск, для длинных аудио можно оптимизировать бинарным
    const frames = lastResponse.blendshapes.frames;
    const currentFrame = frames.find((f, i) => {
      const next = frames[i + 1];
      return (
        f.timestamp <= currentTime && (!next || next.timestamp > currentTime)
      );
    });

    if (currentFrame && nodes.Wolf3D_Head) {
      // Применяем веса к мешу головы
      // ВАЖНО: У RPM голова может называться Wolf3D_Head или Wolf3D_Avatar
      const headNode = nodes.Wolf3D_Head || nodes.Wolf3D_Avatar;

      if (
        headNode &&
        'morphTargetDictionary' in headNode &&
        'morphTargetInfluences' in headNode
      ) {
        const headMesh = headNode as THREE.SkinnedMesh;

        if (headMesh.morphTargetDictionary && headMesh.morphTargetInfluences) {
          Object.entries(currentFrame.mouth_shapes).forEach(
            ([shapeName, value]) => {
              const index = headMesh.morphTargetDictionary![shapeName];

              if (index !== undefined) {
                const current = headMesh.morphTargetInfluences![index];
                // Lerp для плавности
                headMesh.morphTargetInfluences![index] = THREE.MathUtils.lerp(
                  current,
                  value,
                  0.5
                );
              }
            }
          );
        }
      }
    }
  });

  return (
    <group ref={group} dispose={null}>
      <primitive object={scene} />
    </group>
  );
}
