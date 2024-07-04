

from typing import Type, Any
from typing_extensions import Self

from ..connection import DBConection
from exceptions import WrongColumnError, WrongDatatypeError, ColumnNotFoundedError, ColumnError
from config import DATABASE

from logers import database as loger


def _finded_to_values(finded: dict, required_columns: list):
    values = {}
    for column in required_columns:
        if not column.is_fk:
            values[column] = finded[column]
        else:
            new_kwargs = {k.name: v for k, v in finded.items() if k in column.datatype.get_columns_to_fill()}
            values[column] = column.datatype(**new_kwargs)
    return values

def _datatype_string_to_type(datatype: str) -> Type:
    match datatype:
        case 'int':
            return int
        case 'varchar':
            return str
        
def _format_value_to_db(value) -> str:
    if value is None: return 'NULL'
    if isinstance(value, int): return str(value)
    if isinstance(value, str): return f"'{value}'"
    if isinstance(value, float): return str(value)
    if isinstance(value, BaseTable): return str(value.id_)

def _format_condition(values: dict):
    return ' AND '.join([f'{k.name}={_format_value_to_db(v)}' if not v is None else f'ISNULL({k.name})' for k, v in values.items()])


class Column:
    def __init__(self, name: str, datatype: Type, is_nullable: bool=False, default_value: Any=None):
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
        
    def validate(self, value: Any):
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
    values: dict[Column: Any]
    _id: int=None
    _is_in_db: bool=None
    unique_column_name: str=None
    def __init__(self, **kwargs): # initialization of Table instance (row of table). Every instance corresponds to row of table
        """Only kwargs."""
        # get columns names, check kwargs, check types, init
        # get columns names
        columns = self.get_columns_to_fill()
        _name_to_column = {c.name: c for c in columns}

        finded: dict[Column: Any] = {} 
        for key, value in kwargs.items():
            if column := _name_to_column.get(key):
                if isinstance(value, column.datatype):
                    finded[column] = value
                    del _name_to_column[key]
                else: 
                    WrongDatatypeError(f"Value {value!r} for column {column!r} must be type {column.datatype!r}, not {type(value)!r}")
            else:
                raise WrongColumnError(f"Column {key!r} doesn`t exist in table {self._table_name!r}, which require columns {columns}")
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
                raise ColumnNotFoundedError(
                    f"Table {self._table_name!r} required {len(missing_columns)} more columns: " + 
                    f"({enter}{f', {enter}'.join(map(repr, missing_columns))}" + # required columns
                    f"{(f', {enter}[' + f'], {enter}['.join(map(repr, defaulted_columns)) + ']') if defaulted_columns else ''}{enter})" # optional columns
                    )
        self.values = _finded_to_values(finded, self.get_columns())

        self.__dict__.update({'_v_' + col.name: val for col, val in self.values.items()})
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
                    if datatype == int and default:
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

    @property
    def id_(self):
        if not self._id:
            if self.check_if_in_db():
                condition = _format_condition(self.values)
                result = DBConection().query(
                    f"""SELECT {self._pk_column_name} 
                    FROM {self._table_name}
                    WHERE {condition}"""
                    )
                self._id = result[0][0]
            else:
                self.insert()
                self._id = self.id_
        return self._id
    
    def check_if_in_db(self) -> bool:
        if self._is_in_db is None:
            result = DBConection().query(f"""SELECT * FROM {self._table_name} WHERE {_format_condition(self.values)}""")
            self._is_in_db = not not result
        return self._is_in_db

    def insert(self) -> bool:
        """Inserts table value to database. If inserted returns `True`"""
        columns = [col.name for col in self.values]
        if not self.check_if_in_db():
            DBConection().query(
                f"""INSERT INTO {self._table_name} ({', '.join(columns)}) 
                VALUES ({', '.join([_format_value_to_db(val) for val in self.values.values()])})"""
                )
            self._is_in_db = True
            return True
        return False

    def as_kwargs(self) -> dict:
        kwargs = {}
        for k, v in self.values.items():
            if issubclass(k.datatype, BaseTable):
                kwargs.update(v.as_kwargs())
            else:
                kwargs[k.name] = v
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
    def get_by_id(cls, id_: int) -> Self:
        result = DBConection().query(f"SELECT * FROM {cls._table_name} WHERE {cls.get_pk_column_name()}={id_}")
        return cls.from_selected_row(result[0])
    
    @classmethod
    def from_selected_row(cls, selected: tuple[Any]):
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
        return f"<object of '{self._table_name}' ({self.id_ if not self.unique_column_name else self.__dict__['_v_'+self.unique_column_name]})>"

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
            return cls.from_selected_row(result[0])
        else:
            raise ColumnError(f"Table {cls._table_name!r} has not an unique column!")
    @classmethod
    def get(cls, uq_column_value: Any | None=None, id_: int | None=None):
        if (uq_column_value is None) == (id_ is None):
            raise AttributeError(f"Only one of 'class_id' and 'classname' should be given")
        if not id_ is None:
            class_ = cls.get_by_id(id_)
        else:
            class_ = cls.get_by_unique_column(uq_column_value)
        return class_
 