import { Controller, Get } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { HealthService } from './health.service';
import { Public } from '../../common';

@ApiTags('health')
@Controller()
export class HealthController {
  constructor(private readonly health: HealthService) {}

  @Public()
  @Get('health')
  liveness() {
    return this.health.liveness();
  }

  @Public()
  @Get('ready')
  readiness() {
    return this.health.readiness();
  }
}
