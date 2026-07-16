import type { ProductCardModel, ProductDetailModel } from '../models/product.model';

type ProductWithRelations = {
  id: string;
  slug: string;
  name: string;
  price: number;
  compareAt: number | null;
  badge: string | null;
  bestseller: boolean;
  type: string | null;
  shortDesc: string | null;
  description: string | null;
  createdAt: Date;
  category: { slug: string; name: string };
  images: { url: string }[];
  variants: { id: string; color: string; sku: string; stock: number; reserved: number }[];
};

export function toProductCardModel(p: ProductWithRelations): ProductCardModel {
  const stock = p.variants.reduce((sum, v) => sum + Math.max(0, v.stock - v.reserved), 0);
  return {
    id: p.id,
    slug: p.slug,
    name: p.name,
    category: p.category.slug,
    price: p.price,
    compareAt: p.compareAt,
    badge: p.badge,
    bestseller: p.bestseller,
    type: p.type,
    image: p.images[0]?.url ?? null,
    colors: p.variants.map((v) => v.color),
    stock,
    createdAt: p.createdAt.toISOString().slice(0, 10),
  };
}

export function toProductDetailModel(p: ProductWithRelations): ProductDetailModel {
  return {
    ...toProductCardModel(p),
    shortDesc: p.shortDesc,
    description: p.description,
    categoryName: p.category.name,
    images: p.images.map((i) => i.url),
    variants: p.variants.map((v) => ({
      id: v.id,
      color: v.color,
      sku: v.sku,
      available: Math.max(0, v.stock - v.reserved),
    })),
  };
}
