import { Controller, Get, Headers } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { CartService } from './cart.service';
import { Public, CurrentUser } from '../../common';

@ApiTags('cart')
@Controller('cart')
export class CartController {
  constructor(private readonly service: CartService) {}

  @Public()
  @Get()
  get(
    @CurrentUser() user: { sub: string } | undefined,
    @Headers('x-session-id') sessionId?: string,
  ) {
    return this.service.getCart(user?.sub, sessionId);
  }
}
