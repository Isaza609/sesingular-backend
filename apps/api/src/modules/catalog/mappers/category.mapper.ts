import type { CategoryModel } from '../models/category.model';

export function toCategoryModel(c: {
  id: string;
  slug: string;
  name: string;
  tagline: string | null;
  accent: string | null;
  _count: { products: number };
}): CategoryModel {
  return {
    id: c.id,
    slug: c.slug,
    name: c.name,
    tagline: c.tagline,
    accent: c.accent,
    count: c._count.products,
  };
}
