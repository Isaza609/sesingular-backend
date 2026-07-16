import { Injectable } from '@nestjs/common';
import { AdminRepository } from './repositories/admin.repository';

@Injectable()
export class AdminService {
  constructor(private readonly repo: AdminRepository) {}

  getKpis() { return this.repo.kpis(); }
}
