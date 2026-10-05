from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(BaseModel):
    """JSON 字段驼峰，与前端约定一致。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class Result(BaseModel, Generic[T]):
    code: int = 200
    message: str = "成功"
    data: T | None = None

    @staticmethod
    def ok(data: Any = None) -> "Result":
        return Result(code=200, message="成功", data=data)

    @staticmethod
    def fail(code: int = 500, message: str = "操作失败") -> "Result":
        return Result(code=code, message=message, data=None)


class PageResult(CamelModel, Generic[T]):
    records: list[T]
    total: int
    current: int
    size: int
