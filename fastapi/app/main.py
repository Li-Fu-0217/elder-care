import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.api import api_router
from app.common.exceptions import DB_ERROR_HINT, BusinessException
from app.common.result import Result
from app.common.validation import format_validation_errors
from app.core.config import get_settings

logger = logging.getLogger("uvicorn.error")
settings = get_settings()

app = FastAPI(
    title="适老化社区养老智能助手",
    description="FastAPI + SQLModel · 社区养老 Agent 后端",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    # 本地 Vite 开发地址；生产请改为实际前端域名
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)


@app.exception_handler(BusinessException)
async def business_exception_handler(_request: Request, exc: BusinessException):
    status_code = 200
    if exc.code == 401:
        status_code = 401
    elif exc.code == 403:
        status_code = 403
    elif exc.code == 404:
        status_code = 404
    body = Result.fail(exc.code, exc.message).model_dump()
    return JSONResponse(status_code=status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    message = format_validation_errors(exc.errors())
    body = Result.fail(400, message).model_dump()
    return JSONResponse(status_code=400, content=body)


@app.exception_handler(OperationalError)
async def db_operational_handler(_request: Request, exc: OperationalError):
    logger.exception("数据库连接异常")
    hint = DB_ERROR_HINT
    if "Access denied" in str(exc):
        hint = DB_ERROR_HINT + "：MySQL 账号或密码错误"
    body = Result.fail(503, hint).model_dump()
    return JSONResponse(status_code=503, content=body)


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(_request: Request, exc: SQLAlchemyError):
    logger.exception("数据库异常")
    hint = DB_ERROR_HINT
    if "Access denied" in str(exc):
        hint = DB_ERROR_HINT + "：MySQL 账号或密码错误"
    body = Result.fail(503, hint).model_dump()
    return JSONResponse(status_code=503, content=body)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("未处理异常")
    body = Result.fail(500, "服务器内部错误").model_dump()
    return JSONResponse(status_code=500, content=body)


app.include_router(api_router)

upload_dir = settings.upload_root
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")


@app.get("/", include_in_schema=False)
def root():
    return {"message": "elder-care-server", "docs": "/docs"}
