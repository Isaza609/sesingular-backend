import type { Role } from '@singular/shared';

export type AuthUserModel = {
  id: string;
  email: string;
  name: string;
  role: Role | string;
  tier: string;
  points: number;
};
