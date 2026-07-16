import type { User } from '@singular/database';
import type { AuthUserModel } from '../models/auth-user.model';

export function toAuthUserModel(user: User): AuthUserModel {
  return {
    id: user.id,
    email: user.email,
    name: user.name,
    role: user.role,
    tier: user.tier,
    points: user.points,
  };
}
