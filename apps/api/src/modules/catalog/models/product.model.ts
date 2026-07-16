export type ProductCardModel = {
  id: string;
  slug: string;
  name: string;
  category: string;
  price: number;
  compareAt: number | null;
  badge: string | null;
  bestseller: boolean;
  type: string | null;
  image: string | null;
  colors: string[];
  stock: number;
  createdAt: string;
};

export type ProductDetailModel = ProductCardModel & {
  shortDesc: string | null;
  description: string | null;
  categoryName: string;
  images: string[];
  variants: { id: string; color: string; sku: string; available: number }[];
};
