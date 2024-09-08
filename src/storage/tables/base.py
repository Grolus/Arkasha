
from types import NoneType
from typing import Type, Any, TypeAlias, Union
from typing_extensions import Self

from ..connection import DBConection
from exceptions import WrongColumnError, WrongDatatypeError, ColumnNotFoundError, ColumnError, ValueNotFoundError
from config import DATABASE

from logers import database as loger


_CanBeInDatabase: TypeAlias = Union[None, str, int, float, 'BaseTable']

def _finded_to_values_dict(finded: dict, required_columns: list):
    values = {}
    for column in required_columns:
        if not column.is_fk:
            values[column.name] = finded[column]
        else:
            new_kwargs = {k.name: v for k, v in finded.items() if k in column.datatype.get_columns_to_fill()}
            values[column.name] = column.datatype(**new_kwargs)
    return values

def _datatype_string_to_type(datatype: str) -> Type:
    match datatype:
        case 'int':
            return int
        case 'varchar':
            return str
        
def _format_value_to_db(value: _CanBeInDatabase) -> str:
    if value is None: return 'NULL'
    if isinstance(value, int): return str(value)
    if isinstance(value, str): return f"'{value}'"
    if isinstance(value, float): return str(value)
    if isinstance(value, BaseTable): return str(value.id_)

def _format_condition(values: dict[str: str]):
    condition = ' AND '.join([
        f'{column_name}={_format_value_to_db(value)}' if not value is None else f'ISNULL({column_name})' 
        for column_name, value in values.items()
        ])
    return condition


class Column:
    def __init__(self, name: str, datatype: Type, is_nullable: bool=False, default_value: _CanBeInDatabase=None):
        self.name = name
        self.datatype = datatype
        self.is_fk = issubclass(datatype, BaseTable)
        self.is_nullable = is_nullable
        self.default_value = default_value
    
    def find_self(self, values: dict):
        """Finds column in `values` dict. On succes returns finded column name, else `False`"""
        for col_name in values.keys():
            if col_name == self.name:
                value = values[col_name]
                return col_name
        else: 
            return False
        
    def validate(self, value: _CanBeInDatabase):
        return isinstance(value, self.datatype)
            
    def get_default(self):
        if self.default_value is None and not self.is_nullable:
            return ...
        return self.default_value

    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return f'Column({self.name}, {self.datatype!r})'





class BaseTable(object):
    _table_name: str
    _pk_column_name: str=None
    _columns: list[Column]=None
    values: 'TableValues'

    _id: int=None
    _is_in_db: bool=None
    unique_column_name: str=None
    def __init__(self, *args, **kwargs): # initialization of Table instance (row of table). Every instance corresponds to row of table
        """Only kwargs or only args. If args, every arg is a row value in correct order"""
        # get columns names, check kwargs, check types, init
        # get columns names
        if args and kwargs:
            raise AttributeError('Table.__init__ accept only one of args and kwargs')
        

        # find values
        if args:
            columns = self.get_columns()
            if len(columns) != len(args):
                raise ColumnNotFoundError(f"(table {self._table_name!r}) By using 'args' you should fill all of columns {columns}")
            self.values = TableValues(self.__class__, **{c.name: v for c, v in zip(columns, args)})
        if kwargs:
            columns_to_fill = self.get_columns_to_fill()
            _name_to_column = {c.name: c for c in columns_to_fill}
            finded: dict[Column: Any] = {} 
            for key, value in kwargs.items():
                if column := _name_to_column.get(key):
                    if isinstance(value, column.datatype) or (column.is_nullable and value is None):
                        finded[column] = value
                        del _name_to_column[key]
                    else: 
                        WrongDatatypeError(f"Value {value!r} for column {column!r} must be type {column.datatype!r}, not {type(value)!r}")
                else:
                    raise WrongColumnError(f"Column {key!r} doesn`t exist in table {self._table_name!r}, which require columns {columns_to_fill}")
            
            # log errors/warns
            if _name_to_column:
                missing_columns = []
                defaulted_columns = []
                for column in _name_to_column.values():
                    if not (value := column.get_default()) is ...:
                        finded[column] = value
                        defaulted_columns.append(column)
                    else:
                        missing_columns.append(column)
                if missing_columns:
                    enter = '\n                 ' if len(missing_columns) > 2 else ''
                    raise ColumnNotFoundError(
                        f"Table {self._table_name!r} required {len(missing_columns)} more columns: " + 
                        f"({enter}{f', {enter}'.join(map(repr, missing_columns))}" + # required columns
                        f"{(f', {enter}[' + f'], {enter}['.join(map(repr, defaulted_columns)) + ']') if defaulted_columns else ''}{enter})" # optional columns
                        )
                
            # collect values to columns
            columns = self.get_columns()
            column_name_to_value = _finded_to_values_dict(finded, columns)

            self.values = TableValues(self.__class__, **column_name_to_value)

    @classmethod
    def get_columns(cls) -> list[Column]:
        if not cls._columns:
            columns_and_types = DBConection().query(f"""
            SELECT c.COLUMN_NAME, c.DATA_TYPE, c.IS_NULLABLE, c.COLUMN_DEFAULT, IF(
            c.COLUMN_KEY='MUL', 
            (
                SELECT REFERENCED_TABLE_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA=c.TABLE_SCHEMA 
                    AND TABLE_NAME=c.TABLE_NAME AND COLUMN_NAME=c.COLUMN_NAME
            ),
            NULL
            ) AS REFERENCED_TABLE_NAME
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_SCHEMA = '{DATABASE['DATABASE']}'
            AND c.TABLE_NAME = '{cls._table_name}'
            AND NOT c.EXTRA='auto_increment'
        ORDER BY c.ORDINAL_POSITION
            """)
            if columns_and_types:
                cls._columns = []
                for row in columns_and_types:
                    column_name, datatype, is_nullable, default, ref_table_name = row
                    if ref_table_name:
                        datatype = cls._get_table(ref_table_name)
                    else: 
                        datatype = _datatype_string_to_type(datatype)
                    is_nullable = is_nullable == 'YES'
                    if datatype is int and default:
                        default = int(default)
                    cls._columns.append(Column(column_name, datatype, is_nullable, default))
            cls.get_pk_column_name()
        return cls._columns 
    @classmethod
    def get_columns_to_fill(cls) -> list[Column]:
        columns_needed = []
        for column in cls.get_columns():
            if issubclass(column.datatype, BaseTable):
                columns_needed.extend(column.datatype.get_columns_to_fill())
            else:
                columns_needed.append(column)
        return columns_needed

    @classmethod
    def get_columns_dict(cls):
        return {c.name : c for c in cls.get_columns()}
    @property
    def id_(self):
        if not self._id:
            if self.check_if_in_db():
                condition = _format_condition(self.values.as_dict())
                result = DBConection().query(
                    f"""SELECT {self._pk_column_name} FROM {self._table_name} WHERE {condition}"""
                    )
                self._id = result[0][0]
            else:
                self.insert()
                self._id = self.id_
        return self._id
    
    def check_if_in_db(self) -> bool:
        if self._is_in_db is None:
            result = DBConection().query(f"""SELECT * FROM {self._table_name} WHERE {_format_condition(self.values.as_dict())}""")
            self._is_in_db = not not result
        return self._is_in_db

    def _set_values_to_insert_stringtuple(self) -> str:
        return f"({', '.join([_format_value_to_db(val) for val in self.values.as_dict().values()])})"

    def insert(self) -> bool:
        """Inserts table value to database. If inserted returns `True`"""
        columns = list(self.values.as_dict().keys())
        if not self.check_if_in_db():
            DBConection().query(
                f"""INSERT INTO {self._table_name} ({', '.join(columns)}) 
                VALUES {self._set_values_to_insert_stringtuple()}"""
            )
            self._is_in_db = True
            return True
        loger.info(f'{self._table_name} value ({self.id_}) not inserted, because existing in db')
        return False

    @classmethod
    def insert_many(cls, table_values: list[Self]):
        columns = [f'`{col}`' for col in cls.get_columns_dict().keys()]
        query = f"INSERT INTO {cls._table_name} ({', '.join(columns)}) VALUES "
        values_tuples = []
        for instance in table_values:
            values_tuples.append(instance._set_values_to_insert_stringtuple())
        query += ','.join(values_tuples)
        DBConection().query(query)

    def as_kwargs(self) -> dict:
        kwargs = {}
        for k, v in self.values.as_dict().items():
            if issubclass(self.get_columns_dict()[k].datatype, BaseTable):
                kwargs.update(v.as_kwargs())
            else:
                kwargs[k] = v
        return kwargs
    
    @classmethod
    def get_pk_column_name(cls):
        if cls._pk_column_name is None:
            result = DBConection().query(
                    f"""SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA='{DATABASE['DATABASE']}' AND TABLE_NAME='{cls._table_name}'
                        AND COLUMN_KEY='PRI'
                    LIMIT 1""")
            cls._pk_column_name = result[0][0]
        return cls._pk_column_name


    @classmethod
    def get_by_id(cls, id_: int | str) -> Self:
        result = DBConection().query(f"SELECT * FROM {cls._table_name} WHERE {cls.get_pk_column_name()}={id_}")
        return cls.from_selected_row(result[0])
    
    @classmethod
    def from_selected_row(cls, selected: tuple[Any]) -> Self:
        columns = cls.get_columns()
        kwargs_for_init = {}
        for column, value in zip(columns, selected[1:]):
            if column.is_fk:
                kwargs_for_init.update(column.datatype.get_by_id(value).as_kwargs())
            else:
                kwargs_for_init[column.name] = value
        instance = cls(**kwargs_for_init)
        instance._id = selected[0]
        return instance

    def __repr__(self) -> str:
        return f"<object of '{self.__class__.__name__}' {self.values.as_dict()}>"

    @classmethod
    def _get_table(cls, table_name: str):
        all_tables_dict = {t._table_name: t for t in BaseTable.__subclasses__()}
        return all_tables_dict[table_name]
    
    @classmethod
    def get_by_unique_column(cls, unique_column_value: Any):
        if cls.unique_column_name:
            result = DBConection().query(
                f"SELECT * FROM {cls._table_name} WHERE {cls.unique_column_name}={_format_value_to_db(unique_column_value)}"
                )
            if len(result) > 1:
                raise ColumnError(f"Column {cls.unique_column_name!r} in table {cls._table_name!r} is not unique!")
            elif len(result) == 0:
                raise ValueNotFoundError(f'Row with {cls.unique_column_name}={unique_column_value} in table {cls._table_name} not found')
            return cls.from_selected_row(result[0])
        else: 
            raise ColumnError(f"Table {cls._table_name!r} has not an unique column!")
    @classmethod
    def get(cls, uq_column_value: Any | None=None, id_: int | None=None):
        if (uq_column_value is None) == (id_ is None):
            raise AttributeError(f"Only one of 'class_id' and 'classname' should be given")
        if not id_ is None:
            instance = cls.get_by_id(id_)
        else:
            instance = cls.get_by_unique_column(uq_column_value)
        return instance
    


class TableValues:

    def __init__(self, __table: Type[BaseTable], **kwargs):
        """Takes `table` and `kwargs` by sample `column_name=value`. Value in python-format"""
        self.__table = __table
        _columns = self.__table.get_columns()
        self.__columns_types: dict[str: Type] = {col.name: col.datatype for col in _columns}
        self.__is_column_nullable_dict: dict[str: bool] = {col.name: col.is_nullable for col in _columns}
        self.__values_dict: dict[str: Any] = kwargs
    
    def as_dict(self):
        return self.__values_dict
    
    def __getattribute__(self, name: str) -> Any:
        try:
            if name in object.__getattribute__(self, '_TableValues__values_dict').keys():
                return self.__values_dict[name]
        except AttributeError:
            pass
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        try:
            if name in list(self.__values_dict.keys()):
                self.__update_field(name, value)
            else:
                raise AttributeError
        except AttributeError:
            object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if self.__is_column_nullable_dict[name]:
            self.__update_field(name, None)

    def __update_field(self, column_name: str, value: _CanBeInDatabase):
        """Executes UPDATE query and updates `__values_dict`. `value` should be in python-format and can be `None`.
        Raises `ValueError` if `value` has wrong datatype or if tried to null anullable column"""
        datatype = self.__columns_types[column_name]
        if isinstance(value, datatype) or (value is None and self.__is_column_nullable_dict[column_name]):
            DBConection().query(
                f"""UPDATE {self.__table._table_name}
                SET {column_name}={_format_value_to_db(value)} 
                WHERE {_format_condition(self.__values_dict)}"""
                )
            self.__values_dict[column_name] = value
        else:
            raise ValueError(
                f'Attempted to update column {column_name!r}'
                f' of table {self.__table._table_name!r} with value {value!r} '
                f'of type {type(value)!r} (required: {datatype})'
                )
    
    def __repr__(self):
        return repr(self.__values_dict)

