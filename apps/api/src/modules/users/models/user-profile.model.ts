export type UserProfileModel = {
  id: string;
  email: string;
  name: string;
  phone: string | null;
  role: string;
  tier: string;
  points: number;
  memberSince: string;
};
