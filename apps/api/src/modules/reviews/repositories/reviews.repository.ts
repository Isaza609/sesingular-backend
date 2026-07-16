import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class ReviewsRepository {
  constructor(private readonly prisma: PrismaService) {}

  findApprovedByProduct(productId: string) {
    return this.prisma.review.findMany({
      where: { productId, status: 'approved' },
      orderBy: { createdAt: 'desc' },
    });
  }
}
