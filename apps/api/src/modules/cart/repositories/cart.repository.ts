import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class CartRepository {
  constructor(private readonly prisma: PrismaService) {}

  findOrCreate(userId?: string, sessionId?: string) {
    if (!userId && !sessionId) {
      return { items: [], message: 'Proporciona auth o x-session-id' };
    }
    return this.prisma.cart.findFirst({
      where: userId ? { userId } : { sessionId: sessionId! },
      include: { items: { include: { variant: { include: { product: true } } } } },
    });
  }
}
