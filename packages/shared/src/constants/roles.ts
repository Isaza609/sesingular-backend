export const ROLES = {
  CLIENT: 'cliente',
  ADMIN: 'admin',
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];
