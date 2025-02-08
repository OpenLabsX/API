import yaml
import json

from fastapi import Request, HTTPException
from starlette.datastructures import MutableHeaders

from .api import router
from .core.config import settings
from .core.setup import create_application

app = create_application(router=router, settings=settings)


@app.middleware("http")
async def convert_yaml_to_json(request: Request, call_next):
    body = await request.body()
    if request.headers.get("content-type") == "application/yaml":
        try:
            json_body = json.dumps(yaml.safe_load(body.decode("utf-8"))).encode()
        except Exception as e:
            print(str(e))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unable to parse provided YAML configuration.",
            )

        request._body = json_body
        updated_headers = MutableHeaders(request._headers)
        updated_headers["content-length"] = str(len(json_body))
        updated_headers["content-type"] = "application/json"
        request._headers = updated_headers
        request.scope.update(headers=request.headers.raw)
    response = await call_next(request)
    return response
