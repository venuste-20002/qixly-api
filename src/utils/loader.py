from functools import reduce
from typing import List, Type, TypeVar, Union, Optional, Any
from fastapi import status
from sqlalchemy.sql import Select
from sqlmodel import Session, select, col
from sqlmodel.sql.expression import SelectOfScalar
from src.database import engine
from src.utils.common import Order, Pagination
from src.utils.custom_errors import AppError
from src.utils.paginate import paginate_with_session, Paginator

"""
type definitions
"""
T_BASE_IN = TypeVar('T_BASE_IN', bound='CommonBaseModel')
T_BASE_OUT = TypeVar('T_BASE_OUT', bound='CommonBaseModelOut')


def get_search_query(table_model: Type[T_BASE_IN], search: str):
    search_where = list(
        map(lambda x: col(x).ilike(f"%{search}%"),
            table_model.searchable_fields()))
    return reduce(lambda x, y: x | y, search_where)


def load_from_db(table_model: Type[T_BASE_IN], response_model: Optional[Type[T_BASE_OUT]],
                 pagination: Pagination, relation_field: List = None,
                 conditions: dict = None, where: List = None,
                 map_each: callable = None, include_deleted=False,
                 search: str = None, order: Order = None, sort_by: str = None, session: Session = None,
                 join: List[Type] = None, isouter=True) -> dict:
    if session is None:
        with Session(engine) as session:
            return ___load_from_db(table_model, response_model, pagination, relation_field,
                                   conditions, where, map_each, include_deleted, search, order, sort_by, session,
                                   join, isouter)
    else:
        return ___load_from_db(table_model, response_model, pagination, relation_field,
                               conditions, where, map_each, include_deleted, search, order, sort_by, session,
                               join, isouter)


def ___load_from_db(table_model: Type[T_BASE_IN], response_model: Optional[Type[T_BASE_OUT]],
                    pagination: Pagination, relation_field: List = None,
                    conditions: dict = None, where: List = None,
                    map_each: callable = None, include_deleted=False,
                    search: str = None, order: Order = None, sort_by: str = None, session: Session = None,
                    join: List[Type] = None, isouter=True) -> dict:
    """
    load data from db
    @param table_model: table model associated with db table
    @param response_model: response model
    @param pagination: pagination object
    @param relation_field: list of relation fields to be loaded
    @param conditions: conditions
    @param where: list of where conditions. same as conditions but conditions is for equal
    @param map_each: map function to be applied on each data. it will be applied after loading
    @param include_deleted: if true it will include deleted data
    @param search: search string
    @param order: order object, it can be ASC or DESC
    @param sort_by: sort by field
    @param session: session object
    @param join: list of tables to be joined
    @param isouter: if true it will be left join
    @return: dict
    """
    order = order or Order.DESC
    sort_by = sort_by or 'created_at'
    sort_by_field = getattr(table_model, sort_by)
    if conditions is None:
        conditions = {}
    if where is None:
        where = []
    if join is None:
        join = []

    def apply_map(x):
        return x if map_each is None else map_each(x)

    try:
        statement = select(table_model).order_by(
            col(sort_by_field).desc() if order == Order.DESC else col(sort_by_field).asc())
        if search is not None and len(search) > 0 and len(table_model.searchable_fields()) > 0:
            search_query = get_search_query(table_model, search)
            statement = statement.where(search_query)
        if not include_deleted:
            statement = statement.where(table_model.deleted_status == False)
        for key, value in conditions.items():
            statement = statement.where(getattr(table_model, key) == value)
        for i in where:
            statement = statement.where(i)
        for i in join:
            statement = statement.join(i, isouter=isouter)

        result = paginate_with_session(session, statement, pagination.page,
                                       pagination.per_page)
        if response_model is None:
            return result
        filtered_result = []
        for i in result['data']:
            i = apply_map(i)
            filtered_result.append(
                response_model(**i.dict(), **get_fields_value(i, relation_field)))
        result['data'] = filtered_result
        return result
    except Exception as e:
        raise AppError(str(e))


def get_fields_value(model_data: T_BASE_IN, relation_field: List) -> dict:
    """
    get relation fields
    @param model_data: model data
    @param relation_field: list of relation fields to be loaded
    @return: dict
    """
    if relation_field is None:
        relation_field = []
    result = {}
    for i in relation_field:
        result[i] = getattr(model_data, i)

    return result


def load_from_db_by_field(session: Session, table_model: Type[T_BASE_IN],
                          response_model: Type[T_BASE_OUT], field_name: str, value,
                          error_message=None, relation_field=None) -> T_BASE_OUT:
    """
    load data from db by field. it will check in db if field_name == value then return data
    field must be unique or it will return first match
    @param session: session object
    @param table_model: table model associated with db table
    @param response_model: response model
    @param field_name: field name
    @param value: value of field
    @param error_message: error message
    @param relation_field: list of relation fields to be loaded
    @return: ? extends CommonBaseModelOut
    """
    if relation_field is None:
        relation_field = []
    try:
        statement = select(table_model).where(getattr(table_model, field_name) == value,
                                              table_model.deleted_status == False)
        res = session.exec(statement).first()
        return response_model(**res.dict(), **get_fields_value(res, relation_field))
    except Exception as e:
        raise AppError(error_message or str(e))


def must_not_exist(table_model: Type[T_BASE_IN],
                   conditions: dict = None, error_message: str = None) -> None:
    res = get_first(table_model, conditions, optional=True)
    if res is not None:
        raise AppError(error_message or f'already exists')


def get_first(table_model: Type[T_BASE_IN],
              conditions: dict = None, session: Session = None, optional=False,
              where: List = None,
              error_message: str = None, include_deleted=False,
              error_status=status.HTTP_404_NOT_FOUND) -> T_BASE_IN:
    """
    load data from db that meet conditions
    @param session: session object
    @param table_model: table model associated with db table
    @param conditions: conditions
    @param optional: if true it will return None if no data found
    @param error_message: error message
    @param include_deleted: if true it will include deleted data
    @param error_status: status code
    @param where: list of where conditions. same as conditions but conditions is for equal
    @return: ? extends CommonBaseModel
    """
    if where is None:
        where = []
    if conditions is None:
        conditions = {}
    if not include_deleted:
        conditions['deleted_status'] = False
    statement = select(table_model)
    for key, value in conditions.items():
        statement = statement.where(getattr(table_model, key) == value)
    for i in where:
        statement = statement.where(i)
    if session is None:
        with Session(engine) as session:
            res = session.exec(statement).first()
    else:
        res = session.exec(statement).first()
    if not optional and res is None:
        raise AppError(f'{error_message or "No data found"}', error_status)
    return res


def get_all(table_model: Type[T_BASE_IN], conditions: dict = None, session: Session = None,
            allow_deleted=False, where: List = None, search: str = None,
            map_each: callable = None, distinct: list[str] = None) -> List[T_BASE_IN]:
    """
    load all data from db that meet conditions
    @param session: session object
    @param table_model: table model associated with db table
    @param conditions: conditions
    @param allow_deleted: if true it will include deleted data
    @param where: list of where conditions. same as conditions but conditions is for equal
    @param search: search string
    @param map_each: map function to be applied on each data. it will be applied after loading
    @param distinct: list of distinct fields
    @return: List of ? extends CommonBaseModel
    """

    if conditions is None:
        conditions = {}
    if where is None:
        where = []

    statement = select(table_model)
    if not allow_deleted:
        statement = statement.where(table_model.deleted_status == False)
    if search is not None and len(search) > 0 and len(table_model.searchable_fields()) > 0:
        search_query = get_search_query(table_model, search)
        statement = statement.where(search_query)
    for key, value in conditions.items():
        statement = statement.where(getattr(table_model, key) == value)
    for i in where:
        statement = statement.where(i)
    if distinct is not None:
        statement = statement.distinct(*distinct)
    if session is None:
        with Session(engine) as session:
            res = session.exec(statement).all()
    else:
        res = session.exec(statement).all()
    res = res or []
    return res if map_each is None else list(map(map_each, res))


def get_if_exist(session: Session, table_model: Type[T_BASE_IN], field_name: str,
                 value, error_message=None) -> T_BASE_IN:
    """
    works like load_from_db_by_field but it will return table_model instead of response model
    """
    statement = select(table_model).where(getattr(table_model, field_name) == value,
                                          table_model.deleted_status == False)
    res = session.exec(statement).first()
    if res is None:
        raise AppError(error_message or f'No {field_name} equals to {value}',
                        status.HTTP_404_NOT_FOUND)
    return res


def get_max_by_field(table_model, field_name: str, conditions=None) -> int:
    """
    get max value of field from db. field values should be numeric field === column
    it will return max value that match conditions
    @param table_model: table model associated with db table
    @param field_name: field name
    @param conditions: conditions.
    @return: int
    """
    with Session(engine) as session:
        if conditions is None:
            conditions = {}
        try:
            statement = select(table_model).order_by(getattr(table_model, field_name).desc())
            for key, value in conditions.items():
                statement = statement.where(getattr(table_model, key) == value)
            res = session.exec(statement).first()
            return getattr(res, field_name)
        except Exception as e:
            raise AppError(str(e))


def get_value_by_field(table_model, field_name: str, conditions=None, session: Session = None):
    """
    get value of field from db.  field === column
    it will return value that match conditions
    @param table_model: table model associated with db table
    @param field_name: field name
    @param conditions: conditions.

    """
    if conditions is None:
        conditions = {}
    try:
        statement = select(table_model)
        for key, value in conditions.items():
            statement = statement.where(getattr(table_model, key) == value)
        if session is None:
            with Session(engine) as session:
                res = session.exec(statement).first()
        else:
            res = session.exec(statement).first()
        return getattr(res, field_name)
    except Exception as e:
        raise AppError(str(e))


def execute_and_paginate(
        statement: Union[Select, SelectOfScalar], session: Session = None, pagination: Pagination = None,
        order: Order = None, order_by: Any = None, map_each: callable = None,
):
    def apply_map(x):
        return x if map_each is None else map_each(x)

    paginator = Paginator(session, statement, pagination.page, pagination.per_page)
    result = execute(statement, session, False, pagination, order, order_by)
    return {
        'pagination': paginator.get_pagination(),
        "data": list(map(apply_map, result)) if map_each is not None else result
    }


def execute(statement: Union[Select, SelectOfScalar], session: Session = None, first: bool = False,
            pagination: Pagination = None, order: Order = None,
            order_by: Any = None):
    if pagination is not None:
        statement = statement.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page)
    if order is not None and order_by is not None:
        statement = statement.order_by(col(order_by).desc() if order == Order.DESC else col(order_by).asc())
    if session is None:
        with Session(engine) as session:
            exc = session.exec(statement)
            res = exc.first() if first else exc.all()
    else:
        exc = session.exec(statement)
        res = exc.first() if first else exc.all()
    return res or None if first else res or []
