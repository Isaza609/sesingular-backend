import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class OrdersRepository {
  constructor(private readonly prisma: PrismaService) {}

  findByUser(userId: string) {
    return this.prisma.order.findMany({
      where: { userId },
      include: { items: true },
      orderBy: { createdAt: 'desc' },
    });
  }

  findByIdForUser(userId: string, id: string) {
    return this.prisma.order.findFirst({
      where: { userId, OR: [{ id }, { publicId: id }] },
      include: { items: true },
    });
  }
}
