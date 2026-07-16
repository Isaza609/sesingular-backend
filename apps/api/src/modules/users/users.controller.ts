import { Controller, Get, Patch, Body } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { UsersService } from './users.service';
import { UpdateProfileDto } from './schemas/update-profile.schema';
import { CurrentUser } from '../../common';

@ApiTags('users')
@ApiBearerAuth()
@Controller('me')
export class UsersController {
  constructor(private readonly users: UsersService) {}

  @Get()
  me(@CurrentUser() user: { sub: string }) {
    return this.users.getProfile(user.sub);
  }

  @Patch()
  update(@CurrentUser() user: { sub: string }, @Body() dto: UpdateProfileDto) {
    return this.users.updateProfile(user.sub, dto);
  }

  @Get('addresses')
  addresses(@CurrentUser() user: { sub: string }) {
    return this.users.listAddresses(user.sub);
  }

  @Get('favorites')
  favorites(@CurrentUser() user: { sub: string }) {
    return this.users.listFavorites(user.sub);
  }
}
