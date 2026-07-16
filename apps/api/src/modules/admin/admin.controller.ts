import { Controller, Get } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { AdminService } from './admin.service';
import { Roles, ROLES } from '../../common';

@ApiTags('admin')
@ApiBearerAuth()
@Roles(ROLES.ADMIN)
@Controller('admin')
export class AdminController {
  constructor(private readonly service: AdminService) {}

  @Get('kpis')
  kpis() {
    return this.service.getKpis();
  }
}
