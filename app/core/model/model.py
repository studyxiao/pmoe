import re
from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Self

from sqlalchemy import BigInteger, delete, func, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

if TYPE_CHECKING:
    from sqlalchemy.sql.dml import Delete, Update
    from sqlalchemy.sql.selectable import Select

from . import session


class TableNamer:
    """自动将大写字母替换为下划线加小写字母, 并去掉首个下划线."""

    # https://github.com/miguelgrinberg/alchemical/blob/main/src/alchemical/core.py#LL18
    def __get__(self, obj: DeclarativeBase, objtype: type[DeclarativeBase]) -> str | None:
        if objtype.__dict__.get("__tablename__") is None and objtype.__dict__.get("__table__") is None:
            objtype.__tablename__ = (
                re.sub(r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))", r"_\1", objtype.__name__).lower().lstrip("_")
            )
        return getattr(objtype, "__tablename__", None)


class BaseModel(MappedAsDataclass, DeclarativeBase):
    """BaseModel 创建时(也就是 DeclarativeBase 子类化时)会创建 register(包括 metadata 和 mapper).

    之后它的子类会自动将它们自己(也就是 Table)通过它(BaseModel)的 register 属性注册到全局的 metadata 和 mapper.
    """

    __tablename__ = TableNamer()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, init=False)

    def change(self, data: dict[str, Any]) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def save(self) -> Self:
        """新增或修改时保存到数据库中."""
        with session:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self

    @classmethod
    def get_by_id(cls, id: int) -> Self | None:
        """根据 id 获得 row."""
        with session:
            return session.get(cls, id)

    @classmethod
    def get_by_attr(cls, **kwargs: Any) -> Self | None:
        """根据属性获得 row."""
        with session:
            return session.scalars(select(cls).filter_by(**kwargs)).first()

    @classmethod
    def get_all(cls, page: int = 0, count: int = 10, **kwargs: Any) -> Sequence[Self]:
        with session:
            statement = select(cls).filter_by(**kwargs).offset(page * count).limit(count)
            return session.scalars(statement).all()

    @classmethod
    def count(cls, **kwargs: Any) -> int:
        """根据条件统计数量."""
        with session:
            statement = select(func.count(cls.id)).filter_by(**kwargs)
            result = session.execute(statement)
            return result.scalar() or 0

    @classmethod
    def select(cls) -> "Select[Any]":
        """Create a select statement on this model.

        Examples:
        >>> User.select().order_by(User.username)
        """
        return select(cls)

    @classmethod
    def update(cls) -> "Update":
        """Create an update statement on this model.

        Examples:
        >>> User.update().where(User.username == 'susan').values(fullname='Susan Adams')
        """
        return update(cls)

    @classmethod
    def delete(cls) -> "Delete":
        """Create a delete statement on this model.

        Examples:
        >>> User.delete().where(User.username == 'susan')
        """
        return delete(cls)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# custom type alias
T_id = Annotated[int, mapped_column(BigInteger, primary_key=True)]  # bigint 类型主键
T_create_time = Annotated[datetime, mapped_column(insert_default=func.now(), server_default=func.utc_timestamp())]
T_update_time = Annotated[datetime, mapped_column(onupdate=func.now())]
"""
create_time: Mapped[T_create_time] = mapped_column(default=None)
update_time: Mapped[T_update_time] = mapped_column(default=None)
"""
