import { Controller, Get, Param } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { OrdersService } from './orders.service';
import { CurrentUser } from '../../common';

@ApiTags('orders')
@ApiBearerAuth()
@Controller('orders')
export class OrdersController {
  constructor(private readonly service: OrdersService) {}

  @Get()
  list(@CurrentUser() user: { sub: string }) {
    return this.service.listByUser(user.sub);
  }

  @Get(':id')
  one(@CurrentUser() user: { sub: string }, @Param('id') id: string) {
    return this.service.getById(user.sub, id);
  }
}
