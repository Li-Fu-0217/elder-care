class BusinessException(Exception):
    """业务异常：默认 HTTP 200，body 内 code 表示错误（对齐 Spring 行为）。"""

    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)


DB_ERROR_HINT = (
    "数据库连接失败，请检查 MySQL 是否已启动，并修改 .env 中的数据库账号密码"
)
