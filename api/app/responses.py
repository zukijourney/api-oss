import ujson
from dataclasses import dataclass
from fastapi.responses import StreamingResponse, Response
from starlette.types import Send
from typing import Union, Dict, Any, Tuple, AsyncGenerator, Optional

@dataclass
class ResponseConfig:
    charset: str = 'utf-8'
    content_type: bytes = b'content-type'
    json_content_type: bytes = b'application/json'
    success_status_range: range = range(200, 300)

class StreamResponseHandler:
    def __init__(self):
        self.config = ResponseConfig()

    def _is_success_status(self, status_code: int) -> bool:
        return status_code in self.config.success_status_range

    def _encode_content(self, content: Union[str, bytes]) -> bytes:
        if isinstance(content, str):
            return content.encode(self.config.charset)
        return content

    def _update_headers_for_error(
        self,
        headers: list,
        status_code: int
    ) -> list:
        if not self._is_success_status(status_code):
            content_type_header = next(
                (h for h in headers if h[0].decode('latin-1').lower() == 'content-type'),
                None
            )
            if content_type_header:
                headers.remove(content_type_header)
                headers.append((
                    self.config.content_type,
                    self.config.json_content_type
                ))
        return headers

    async def _send_chunk(
        self,
        send: Send,
        content: Union[str, bytes],
        more_body: bool = True
    ) -> None:
        await send({
            'type': 'http.response.body',
            'body': self._encode_content(content),
            'more_body': more_body
        })

    async def _send_response_start(
        self,
        send: Send,
        status_code: int,
        headers: list
    ) -> None:
        await send({
            'type': 'http.response.start',
            'status': status_code,
            'headers': headers
        })

    def _create_error_response(self) -> str:
        error_obj = {
            'error': {
                'message': (
                    'The streaming response was empty, hence why this error was raised. '
                    'Please try again later, or contact us in our Discord server if this keeps happening.'
                ),
                'type': 'invalid_response_error',
                'code': 500
            }
        }
        return ujson.dumps(obj=error_obj, indent=4)

class StreamingResponseWithStatusCode(StreamingResponse):
    def __init__(
        self,
        content: AsyncGenerator[Tuple[str, int], None],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[Any] = None,
    ):
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background
        )
        self.handler = StreamResponseHandler()

    async def stream_response(self, send: Send) -> None:
        try:
            first_chunk_content, self.status_code = await self.body_iterator.__anext__()

            self.raw_headers = self.handler._update_headers_for_error(
                self.raw_headers,
                self.status_code
            )

            await self.handler._send_response_start(
                send,
                self.status_code,
                self.raw_headers
            )

            await self.handler._send_chunk(send, first_chunk_content)

            async for chunk_content, chunk_status in self.body_iterator:
                if not self.handler._is_success_status(chunk_status):
                    self.status_code = chunk_status
                    await self.handler._send_chunk(send, '', False)
                    return

                await self.handler._send_chunk(send, chunk_content)

            await self.handler._send_chunk(send, '', False)

        except StopAsyncIteration:
            self.raw_headers = self.handler._update_headers_for_error(
                self.raw_headers,
                500
            )

            await self.handler._send_response_start(send, 500, self.raw_headers)
            
            error_content = self.handler._create_error_response()
            await self.handler._send_chunk(send, error_content)
            await self.handler._send_chunk(send, '', False)

class PrettyJSONResponse(Response):
    media_type = 'application/json'
    
    @staticmethod
    def _serialize_json(content: Union[list, dict]) -> str:
        return ujson.dumps(
            obj=content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(', ', ': '),
            escape_forward_slashes=False
        )

    def render(self, content: Union[list, dict]) -> bytes:
        return self._serialize_json(content).encode('utf-8')