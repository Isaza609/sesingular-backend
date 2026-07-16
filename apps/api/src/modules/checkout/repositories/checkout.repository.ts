import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class CheckoutRepository {
  constructor(private readonly prisma: PrismaService) {}

  placeholder(dto: unknown) {
    return { status: 'not_implemented', phase: 3, dto };
  }
}
