import { Controller, Get } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { InventoryService } from './inventory.service';
import { Roles, ROLES } from '../../common';

@ApiTags('inventory')
@ApiBearerAuth()
@Roles(ROLES.ADMIN)
@Controller('inventory')
export class InventoryController {
  constructor(private readonly service: InventoryService) {}

  @Get()
  list() {
    return this.service.list();
  }
}
