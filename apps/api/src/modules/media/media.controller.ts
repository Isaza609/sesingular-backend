import { Body, Controller, Post } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { MediaService } from './media.service';
import { CreateUploadUrlDto } from './schemas/create-upload-url.schema';
import { Roles, ROLES } from '../../common';

@ApiTags('media')
@ApiBearerAuth()
@Roles(ROLES.ADMIN)
@Controller('media')
export class MediaController {
  constructor(private readonly service: MediaService) {}

  @Post('upload-url')
  uploadUrl(@Body() dto: CreateUploadUrlDto) {
    return this.service.createUploadUrl(dto);
  }
}
