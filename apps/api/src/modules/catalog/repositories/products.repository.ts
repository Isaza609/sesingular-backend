import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';
import type { Prisma } from '@singular/database';

export type ProductSearchParams = {
  cat?: string;
  q?: string;
  sort?: string;
  color?: string;
  type?: string;
  maxPrice?: number;
  inStock?: boolean;
  skip: number;
  take: number;
};

const productCardInclude = {
  images: { orderBy: { sortOrder: 'asc' as const }, take: 1 },
  variants: { where: { active: true } },
  category: true,
} satisfies Prisma.ProductInclude;

@Injectable()
export class ProductsRepository {
  constructor(private readonly prisma: PrismaService) {}

  async search(params: ProductSearchParams) {
    const where: Prisma.ProductWhereInput = {
      status: 'published',
      deletedAt: null,
      ...(params.cat ? { category: { slug: params.cat } } : {}),
      ...(params.type ? { type: { contains: params.type, mode: 'insensitive' } } : {}),
      ...(params.maxPrice ? { price: { lte: params.maxPrice } } : {}),
      ...(params.q
        ? {
            OR: [
              { name: { contains: params.q, mode: 'insensitive' } },
              { type: { contains: params.q, mode: 'insensitive' } },
              { category: { name: { contains: params.q, mode: 'insensitive' } } },
            ],
          }
        : {}),
      ...(params.color
        ? { variants: { some: { color: { equals: params.color, mode: 'insensitive' }, active: true } } }
        : {}),
      ...(params.inStock
        ? { variants: { some: { active: true, stock: { gt: 0 } } } }
        : {}),
    };

    const orderBy: Prisma.ProductOrderByWithRelationInput[] =
      params.sort === 'precio-asc'
        ? [{ price: 'asc' }]
        : params.sort === 'precio-desc'
          ? [{ price: 'desc' }]
          : params.sort === 'nuevos'
            ? [{ createdAt: 'desc' }]
            : params.sort === 'vendidos'
              ? [{ bestseller: 'desc' }, { createdAt: 'desc' }]
              : [{ bestseller: 'desc' }, { createdAt: 'desc' }];

    const [items, total] = await this.prisma.$transaction([
      this.prisma.product.findMany({
        where,
        include: productCardInclude,
        orderBy,
        skip: params.skip,
        take: params.take,
      }),
      this.prisma.product.count({ where }),
    ]);

    return { items, total };
  }

  findBySlug(slug: string) {
    return this.prisma.product.findUnique({
      where: { slug },
      include: {
        images: { orderBy: { sortOrder: 'asc' } },
        variants: { where: { active: true } },
        category: true,
      },
    });
  }

  findRelated(categoryId: string, excludeId: string, take = 4) {
    return this.prisma.product.findMany({
      where: {
        categoryId,
        id: { not: excludeId },
        status: 'published',
        deletedAt: null,
      },
      include: productCardInclude,
      take,
    });
  }
}
