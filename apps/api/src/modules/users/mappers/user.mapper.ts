import type { User } from '@singular/database';
import type { UserProfileModel } from '../models/user-profile.model';

export function toUserProfileModel(user: User): UserProfileModel {
  return {
    id: user.id,
    email: user.email,
    name: user.name,
    phone: user.phone,
    role: user.role,
    tier: user.tier,
    points: user.points,
    memberSince: user.createdAt.toISOString(),
  };
}
