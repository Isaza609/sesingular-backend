import { Module } from '@nestjs/common';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { UsersRepository } from './repositories/users.repository';
import { AddressesRepository } from './repositories/addresses.repository';
import { FavoritesRepository } from './repositories/favorites.repository';

@Module({
  controllers: [UsersController],
  providers: [UsersService, UsersRepository, AddressesRepository, FavoritesRepository],
  exports: [UsersService, UsersRepository],
})
export class UsersModule {}
