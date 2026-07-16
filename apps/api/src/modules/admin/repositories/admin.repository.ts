import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class AdminRepository {
  constructor(private readonly prisma: PrismaService) {}

  async kpis() {
    const [ordersCount, paid] = await Promise.all([
      this.prisma.order.count(),
      this.prisma.order.aggregate({
        where: { paymentStatus: 'pagado' },
        _sum: { total: true },
        _avg: { total: true },
      }),
    ]);
    return {
      pedidos: ordersCount,
      ventas: paid._sum.total ?? 0,
      ticket: Math.round(paid._avg.total ?? 0),
    };
  }
}
