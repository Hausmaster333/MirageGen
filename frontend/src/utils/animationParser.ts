import * as THREE from 'three';
import { type AnimationJson } from '../types';

const BONE_MAP: Record<string, string> = {
  spine: 'Spine',
  head: 'Head',
  neck: 'Neck',
  right_arm: 'RightArm',
  left_arm: 'LeftArm',
  right_hand: 'RightHand',
  left_hand: 'LeftHand',
  right_shoulder: 'RightShoulder',
  left_shoulder: 'LeftShoulder',
};

interface BoneTrackData {
  times: number[];
  values: number[];
}

export function createClip(
  jsonAnimation: AnimationJson,
  clipName: string
): THREE.AnimationClip {
  const tracks: THREE.KeyframeTrack[] = [];
  const boneTracks: Record<string, BoneTrackData> = {};

  jsonAnimation.keyframes.forEach(frame => {
    const time = frame.timestamp;

    Object.entries(frame.bone_rotations).forEach(([boneKey, quaternion]) => {
      const modelBoneName = BONE_MAP[boneKey];
      if (!modelBoneName) return;

      if (!boneTracks[modelBoneName]) {
        boneTracks[modelBoneName] = { times: [], values: [] };
      }

      boneTracks[modelBoneName].times.push(time);
      boneTracks[modelBoneName].values.push(...quaternion);
    });
  });

  Object.entries(boneTracks).forEach(([boneName, data]) => {
    const track = new THREE.QuaternionKeyframeTrack(
      `${boneName}.quaternion`,
      data.times,
      data.values
    );
    tracks.push(track);
  });

  const duration =
    jsonAnimation.duration ||
    Math.max(...jsonAnimation.keyframes.map(k => k.timestamp));

  return new THREE.AnimationClip(clipName, duration, tracks);
}
