import { Injectable, NotFoundException } from '@nestjs/common';
import { UsersRepository } from './repositories/users.repository';
import { AddressesRepository } from './repositories/addresses.repository';
import { FavoritesRepository } from './repositories/favorites.repository';
import { UpdateProfileDto } from './schemas/update-profile.schema';
import { toUserProfileModel } from './mappers/user.mapper';

@Injectable()
export class UsersService {
  constructor(
    private readonly users: UsersRepository,
    private readonly addresses: AddressesRepository,
    private readonly favorites: FavoritesRepository,
  ) {}

  async getProfile(userId: string) {
    const user = await this.users.findById(userId);
    if (!user) throw new NotFoundException('Usuario no encontrado');
    return toUserProfileModel(user);
  }

  async updateProfile(userId: string, dto: UpdateProfileDto) {
    const user = await this.users.update(userId, dto);
    return toUserProfileModel(user);
  }

  listAddresses(userId: string) {
    return this.addresses.findByUser(userId);
  }

  listFavorites(userId: string) {
    return this.favorites.findByUser(userId);
  }
}
