export type ApiErrorBody = {
  statusCode: number;
  message: string | string[];
  error: string;
  requestId?: string;
};
