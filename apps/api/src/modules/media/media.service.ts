import { Injectable } from '@nestjs/common';
import { MediaRepository } from './repositories/media.repository';
import { CreateUploadUrlDto } from './schemas/create-upload-url.schema';

@Injectable()
export class MediaService {
  constructor(private readonly repo: MediaRepository) {}

  createUploadUrl(dto: CreateUploadUrlDto) {
    return this.repo.signUpload(dto);
  }
}
