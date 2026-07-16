import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class InventoryRepository {
  constructor(private readonly prisma: PrismaService) {}

  list() {
    return this.prisma.productVariant.findMany({
      include: { product: { select: { id: true, name: true, slug: true } } },
      orderBy: { sku: 'asc' },
    });
  }
}
