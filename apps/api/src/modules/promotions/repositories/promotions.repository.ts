import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class PromotionsRepository {
  constructor(private readonly prisma: PrismaService) {}

  findActiveByCode(code: string) {
    return this.prisma.coupon.findFirst({
      where: { code: code.toUpperCase(), active: true },
    });
  }
}
